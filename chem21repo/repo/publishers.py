import json
import os
import tempfile
import zipfile
import logging

from ..google import YouTubeCaptionServiceMixin
from .models import Topic
from chem21repo.quiz.models import Quiz
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.storage import get_storage_class
from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from subprocess import check_output as check_subprocess
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile


class PublicStorageMixin(object):
    def __init__(self):
        storage_class = get_storage_class(settings.PUBLIC_SITE_STORAGE)
        self.storage = storage_class()
        super(PublicStorageMixin, self).__init__()


class StaticStorageMixin(object):
    def __init__(self):
        storage_class = get_storage_class(settings.STATICFILES_STORAGE)
        self.storage = storage_class()
        super(StaticStorageMixin, self).__init__()


class MediaStorageMixin(object):
    def __init__(self):
        storage_class = get_storage_class()
        self.storage = storage_class()
        super(MediaStorageMixin, self).__init__()


class BasePublisher(object):
    def __init__(self, request, pages, *args, **kwargs):
        self.pages = pages
        # these should each have unique URL
        # i.e. associated with a single parent module etc as necessary
        # n.b. this can be achieved using a loader from .object_loaders
        self.request = request
        self.errors = []  # return this
        # self.no_pages = {} # return debug book-keeping for instances with no
        # pages (should be orphans)
        self.num_succeeded = 0  # return debug/notification tally
        super(BasePublisher, self).__init__()

    def publish_all(self):
        success_pks = {}
        paths = []
        for obj in self.pages:
            paths += self.publish(obj)
            model = type(obj)
            # book-keep the pks for bulk flag change
            if model not in success_pks:
                success_pks[model] = []
            success_pks[model].append(obj.pk)
            # debug/notification tally to return
            self.num_succeeded += 1
        # bulk flag all published pages as unchanged (persist)
        """
        for model, pks in success_pks.iteritems():
            model.objects.filter(pk__in=pks).update(changed=False)
        """
        return paths

    def upload_replace_file(self, path, file):
        try:
            # upload (replacing if exists)
            if issubclass(
                self.storage.__class__, FileSystemStorage
            ) and self.storage.exists(path):
                self.storage.delete(path)
            self.storage.save(path, file)
        except Exception, e:
            e.upload_path = path
            raise e
        return path


class GenerateHTMLMixin(object):

    topic_structures = {}

    @classmethod
    def topic_structure(kls, topic):
        if topic.pk not in kls.topic_structures:
            manager = Topic.objects_with_structure
            manager2 = manager.structure_exclude(archived=True)
            kls.topic_structures[topic.pk] = manager2.get(pk=topic.pk)
        return kls.topic_structures[topic.pk]

    def generate_html(self, page):
        # generate template context for learning object page
        context = {
            'object': page,
            'class_tree': self.topic_structure(page.current_topic),
            'current_topic': page.current_topic,
            'breadcrumbs': page.get_ancestors(),
            'request': self.request,
            'user': self.request.user,
            'staticgenerator': True
        }

        try:
            context['current_module'] = page.current_module
        except AttributeError:
            pass

        try:
            context['current_lesson'] = page.current_lesson
        except AttributeError:
            pass

        # add optional back / next buttons to context
        nxt = page.get_next_object()
        prev = page.get_previous_object()

        if nxt:
            context['next'] = nxt
        if prev:
            context['previous'] = prev

        # set up upload file
        if page.template:
            template_name = page.template.name
        else:
            template_name = type(page)._meta.object_name.lower()
        return render_to_string("chem21/%s.html" % template_name, context)


class HTMLPublisher(BasePublisher, PublicStorageMixin, GenerateHTMLMixin):

    def publish(self, page):
        html = self.generate_html(page)
        # publishes a resolved learning object to HTML and returns the storage
        # path
        file = ContentFile(html, name="index.html")
        file.content_type = "text/html;charset=utf-8"  # for S3

        # set up upload path
        path = page.get_absolute_url() + "index.html"
        if path[0] == "/":
            path = path[1:]

        # upload
        self.upload_replace_file(path, file)

        # return storage path
        return [path, ]


class CircularNavigationException(Exception):
    pass


class PageSetMixin(object):
    def get_page_set(self, root, root_path):
        path_set = set([])
        to_render = []
        end = False
        page = root
        while page:
            new_path = page.get_absolute_url()
            ancestor_paths = frozenset(
                [p.get_absolute_url() for p in page.get_ancestors()])
            if new_path in path_set:
                #raise CircularNavigationException
                break
            elif new_path != root_path and root_path not in ancestor_paths:
                # end as current page is not a descendent of root
                break
            else:
                path_set.add(new_path)
                to_render.append(page)
                page = page.get_next_object()
        return to_render


class PDFPublisher(
        BasePublisher, MediaStorageMixin,
        PageSetMixin, YouTubeCaptionServiceMixin):

    def __init__(self, *args, **kwargs):
        if 'youtube_service' not in kwargs:
            raise ValueError("Missing youtube_service kwarg")
        self.youtube = kwargs['youtube_service']
        self._static_storage = None
        super(PDFPublisher, self).__init__(*args, **kwargs)

    def publish(self, root):
        root_path = root.get_absolute_url()
        to_render = self.get_page_set(root, root_path)
        video_transcripts = []
        quizzes = []

        for obj in to_render:
            vid = obj.video
            if vid and vid.youtube_id:
                caption = self.get_recent_caption(self.youtube, vid.youtube_id)
                if caption is not None:
                    transcript = self.get_srt(self.youtube, caption['id'])
                    transcript = " ".join(
                        [line for line in transcript.split("\n")
                            if line != "" and
                            not line.isdigit() and
                            "-->" not in line]
                    )
                    obj.transcript = "\n".join(
                        ["<p>%s.</p>" % s for s in transcript.split(". ")])

            if obj.quiz and obj.template and obj.template.name:
                quizzes.append(obj)

        # generate html for combined pdf
        html = render_to_string(
            "pdf_template.html", {
                'objects': to_render,
                'request': self.request,
                'user': self.request.user,
                'video_transcripts': video_transcripts,
                'quizzes': quizzes,
                'staticgenerator': True})

        # generate pdfs from html
        base_options = ["-s", "A4", ]
        american_options = ["-s", "Letter"]

        a4_pdf = self.generate_pdf(html, options=base_options)
        a4_pdf.content_type = "application/pdf"  # for S3

        letter_pdf = self.generate_pdf(html, options=american_options)
        letter_pdf.content_type = "application/pdf"  # for S3

        # upload the pdfs
        letter_pdf_path = root.get_pdf_version_path("letter")
        a4_pdf_path = root.get_pdf_version_path("a4")
        self.upload_replace_file(
            letter_pdf_path,
            letter_pdf)
        self.upload_replace_file(
            a4_pdf_path,
            a4_pdf)
        return [letter_pdf_path, a4_pdf_path]

    def save_local_from_storage(self, infile, suffix=None):
        if not self._static_storage:
            self._static_storage = get_storage_class(
                settings.STATICFILES_STORAGE)()
        if suffix is None:
            suffix = os.path.splitext(infile)[1]
        local_file = NamedTemporaryFile(delete=False)
        with self._static_storage.open(infile) as f:
            local_file.write(f.read())
        local_file.close()
        return os.path.join(tempfile.gettempdir(), local_file.name)

    def generate_pdf(self, html, options=[]):
        resources = {
            "chem21_pdf_logo.png": "img/logo.png",
            "chem21_pdf_style.css": "css/chem21_pdf.css",
            "jqmath.css": "css/jquery.math.css",
            "video.png": "img/video.png",
            "require.js": "js/lib/require.js",
            "pdf-gen.js": "js/pdf-gen.js"
        }
        for lname, spath in resources.iteritems():
            lpath = os.path.join(tempfile.gettempdir(), lname)
            if not os.path.exists(lpath):
                tmp_path = self.save_local_from_storage(spath)
                os.rename(tmp_path, lpath)
        wkhtmltopdf_default = 'wkhtmltopdf'
        # Reference command
        wkhtmltopdf_cmd = os.environ.get(
            'WKHTMLTOPDF_CMD',
            wkhtmltopdf_default)
        # Set up return file
        footer_html = render_to_string("pdf_template_footer.html", {})
        pdf_file = NamedTemporaryFile(delete=False, suffix='.pdf')
        html_file = NamedTemporaryFile(delete=False, suffix='.html')
        html_file.write(html.encode("utf-8"))
        html_file.close()
        html_footer_file = NamedTemporaryFile(delete=False, suffix='.html')
        html_footer_file.write(footer_html.encode("utf-8"))
        html_footer_file.close()
        options += [
            '-B', '40mm',
            # '--load-error-handling', 'ignore',
            '--footer-html', os.path.join(
                tempfile.gettempdir(),
                html_footer_file.name),
            '--javascript-delay', 1000]
        # wkhtmltopdf
        args = [wkhtmltopdf_cmd, '-q'] + options + [
            os.path.join(tempfile.gettempdir(), html_file.name),
            os.path.join(tempfile.gettempdir(), pdf_file.name)]
        try:
            out = check_subprocess(args)
        except CalledProcessError as e:
            raise Exception("wkhtmltopdf error: %s %s" % (repr(e.args), args) )
        
        return pdf_file


class SCORMPublisher(
        BasePublisher, StaticStorageMixin,
        GenerateHTMLMixin, PageSetMixin):

    @staticmethod
    def initialise_scorm_dir(self):
        with self.storage.open("SCORM/scorm_template.zip") as f:
            dat = f.read()

        d = tempfile.gettempdir()
        self.scorm_dir = os.path.join(d, "SCORM")
        self.out_zip_path = os.path.join(d, "SCORM_out.zip")
        try:
            os.mkdir(self.scorm_dir)
        except OSError:
            pass
        os.chdir(self.scorm_dir)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(dat)
            tmpname = f.name

        with zipfile.ZipFile(os.path.join(d, tmpname)) as zf:
            zf.extractall()

        return self.scorm_dir

    @staticmethod
    def write_requirejs_settings_file(in_var, file_name):
        with open(file_name, 'w') as f:
            f.write("define(function() {\n\treturn ")
            f.write(json.dumps(in_var) + "\n")
            f.write("});")

    @staticmethod
    def save_scorm_dir(self, page):
        with zipfile.ZipFile(outzip, 'w') as zf:
            for root, dirs, files in os.walk(self.scorm_dir):
                rel_root = root.replace(self.scorm_dir, "")
                for file in files:
                    arc_file = os.path.join(rel_root, file)
                    full_file = os.path.join(root, file)
                    zf.write(full_file, arc_file)
        with open(self.out_zip_path) as f:
            zipc = f.read()
        with self.storage.open("SCORM/%d/%s.zip" % (root_page.pk, root_page.slug), 'w') as sf:
            sf.write(zipc)

    def publisher(self, root):
        root_path = root.get_absolute_url()
        pages = self.get_page_set(root, root_path)
        page_names = ["start", ] + ["page%d" %
                                    i for i in range(len(pages) - 2)] + ["end"]
        to_render = zip(page_names, to_render)
        url_map = [(name, page.get_absolute_url()) for name, page in to_render]

        scorm_dir = self.initialise_scorm_dir()

        # write javascript config
        config_dir = os.path.join(scorm_dir, "js", "src", "config")

        self.write_requirejs_settings_file(dict(url_map),
                                           os.path.join(config_dir, "urlmap.js"))

        self.write_requirejs_settings_file([name for name, page in to_render],
                                           os.path.join(config_dir, "pageorder.js"))

        # write manifest
        manifest_file = os.path.join(scorm_dir, "imsmanifest.xml")
        with open(manifest_file, 'r') as f:
            manifest = f.read()
        manifest = manifest.replace('%%TITLE%%', title)
        manifest = manifest.replace('%%SHORT_NAME%%', machine_name)
        xml_markup = "\n".join(["<file href=\"%s\" />" %
                                url for name, url in url_map])
        manifest = manifest.replace('%%RESOURCES%%', xml_markup)

        with open(manifest_file, 'w') as f:
            f.write(manifest)

        # write HTML pages
        html_dir = os.path.join(scorm_dir, "pages")

        for name, page in to_render:
            with open(os.path.join(html_dir, name + ".html"), 'w') as f:
                f.write(self.generate_html(page))

        # save zip file
        self.save_scorm_dir()
