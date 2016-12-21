from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from chem21repo.repo.models import Question, Lesson, Module, Topic, PresentationAction
from django.core.files.storage import DefaultStorage, get_storage_class
from django.template.loader import render_to_string
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from os import chmod, environ, path as os_path
from subprocess import call as call_subprocess
from tempfile import NamedTemporaryFile
import tempfile
import json
import os
import sys
import zipfile

class PublicStorageMixin(object):
    def __init__(self, *args, **kwargs):
        storage_class = get_storage_class(settings.PUBLIC_SITE_STORAGE)
        self.storage = storage_class()
        super(PublicStorageMixin, self).__init__()

class BasePublisher(PublicStorageMixin):
    def __init__(self, request, objects, *args, **kwargs):
        self.objects = objects
        self.request = request
        self.errors = [] # return this
        #self.no_pages = {} # return debug book-keeping for instances with no pages (should be orphans)
        self.num_succeeded = 0 # return debug/notification tally
        super(BasePublisher, self).__init__(self, *args, **kwargs)

    def publish_all(self):
        success_pks = {}
        paths = []
        """
        for page in self.objects:
            inst_error = False
            num_pages = 0

            # each object can be used in many locations
            # so iterate over each path it appears at and publish
            # iter_publishable sets up the object with parent objects (qualifies it)
        """
        for obj in self.objects:
            obj_error = False
            #try:
                # publish this page and book-keep storage paths for return
            paths += self.publish(obj)
            """
            except Exception, e:
            e_details = (sys.exc_info()[0].__name__, os.path.basename(sys.exc_info()[2].tb_frame.f_code.co_filename), sys.exc_info()[2].tb_lineno) 
            try:
                self.errors.append((obj.title, e.upload_path) + e_details)
            except AttributeError:
                self.errors.append((obj.title, ) + e_details)
            obj_error = True
            """
            model = type(obj)
            if not obj_error:
                # book-keep the pks for bulk flag change
                if model not in success_pks:
                    success_pks[model] = []
                success_pks[model].append(obj.pk)
                # debug/notification tally to return
                self.num_succeeded += 1
        """
        if num_pages == 0:
            # book-keep these pks for bulk archiving 
            if model not in self.no_pages:
                self.no_pages[model] = []
            self.no_pages[model].append(inst.pk)
        """
        # bulk flag all published pages as unchanged (persist)
        for model, pks in success_pks.iteritems():
            model.objects.filter(pk__in=pks).update(changed=False)
        """
        # bulk archive all orphan pages (persist)
        for model, pks in self.no_pages.iteritems():
            model.objects.filter(pk__in=pks).update(archived=True)
        """
        return paths


    def upload_replace_file(self, path, file):
        try:
            # upload (replacing if exists)
            if issubclass(self.storage.__class__, FileSystemStorage) and self.storage.exists(path):
                self.storage.delete(path)                    
            self.storage.save(path, file)
        except Exception, e:
            e.upload_path = path
            raise e
        return path

class HTMLPublisher(BasePublisher):
    topic_structures = {}

    @classmethod
    def topic_structure(kls, topic):
        if topic.pk not in kls.topic_structures:
            manager = Topic.objects_with_structure
            manager2 = manager.structure_exclude(archived=True)
            kls.topic_structures[topic.pk] = manager2.get(pk=topic.pk)


    def publish(self, page):
        # publishes a resolved learning object to HTML and returns the storage path
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
        model_name = type(page)._meta.object_name
        html = render_to_string("chem21/%s.html" % model_name.lower(), context)
        file = ContentFile(html, name="index.html")
        file.content_type = "text/html;charset=utf-8" # for S3

        # set up upload path
        path = page.get_absolute_url()+"index.html"
        if path[0] == "/":
            path = path[1:]

        # upload
        self.upload_replace_file(path, file)

        # return storage path
        return [path, ]

class PDFPublisher(BasePublisher):
    def publish(self, root):
        storage = self.storage
        root_path = root.get_absolute_url()
        path_set = set([])
        to_render = []
        end = False
        page = root

        # generate ordered set of pages 
        while not end and page:
            new_path = page.get_absolute_url()
            ancestors = frozenset([p.get_absolute_url() for p in obj.get_ancestors()])
            if new_path in path_set or (new_path != root_path and root_path not in ancestors):
                # if we have a hit a circular route, or this is not a child of the root element
                end = True
            else:
                path_set.add(new_path)
                to_render.append(page)
                page = page.get_next_object()

        # generate html for combined pdf
        html = render_to_string("pdf_template.html", {'objects': to_render})

        # generate pdfs from html        
        base_options = ["-s","A4",]
        american_options = ["-s","Letter"]
     
        letter_filename = "%s-letter.pdf" % root.slug
        a4_filename = "%s-a4.pdf" % root.slug
        
        a4_pdf = self.generate_pdf(html, options = base_options)
        letter_pdf = self.generate_pdf(html, options = american_options)

        # upload the pdfs
        pdf_path = "pdf/%d" % root.pk
        letter_pdf_path = "%s/%s" % (pdf_path, letter_filename)
        a4_pdf_path = "%s/%s" % (pdf_path, a4_filename)

        self.upload_replace_file(letter_pdf_path, letter_pdf)
        self.upload_replace_file(a4_pdf_path, a4_pdf)
        return [letter_pdf_path, a4_pdf_path]


    def generate_pdf(self, html, options=[]):
        wkhtmltopdf_default = 'wkhtmltopdf-heroku'
        # Reference command
        wkhtmltopdf_cmd = environ.get('WKHTMLTOPDF_CMD', wkhtmltopdf_default)
        # Set up return file
        pdf_file = NamedTemporaryFile(delete=False, suffix='.pdf')
        html_file = NamedTemporaryFile(delete=False, suffix='.html')
        html_file.write(html)
        html_file.close()
        # wkhtmltopdf
        call_subprocess([wkhtmltopdf_cmd, '-q'] + options + [html_file.name, pdf_file.name,])
        return pdf_file