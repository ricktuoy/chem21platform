from chem21repo.storage import S3StaticFileSystem
from staticgenerator import StaticGenerator
from django.contrib.contenttypes.models import ContentType
from chem21repo.repo.models import Question, Lesson, Module, Topic, PresentationAction
from django.core.management.base import BaseCommand
from django.core.files.storage import DefaultStorage, get_storage_class
from django.core.urlresolvers import reverse
from django.conf import settings
import tempfile
import json
import os
import zipfile

class Command(BaseCommand):
    help = 'Publish to SCORM'
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument('type',
                    type=str)
        parser.add_argument('id',
                    type=int)

    def handle(self, *args, **options):
        storage = get_storage_class(settings.STATICFILES_STORAGE)()
        ct = ContentType.objects.get(app_label="repo", model=options['type'])
        obj = ct.get_object_for_this_type(pk=options['id'])
        paths = []
        path_set = set([])
        circular = False
        while not circular and obj:
            new_path = obj.get_absolute_url()
            if new_path in path_set:
                circular = True
            path_set.add(new_path)
            paths.append(new_path)
            obj = obj.get_next_object()
        if circular:
            print "Circular link path .. stopping here and writing"
            print "(returned to %s)" % new_path

        with storage.open("SCORM/scorm_template.zip") as f:
            dat = f.read()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(dat)
            tmpname = f.name
        d = tempfile.gettempdir()
        scorm_d = os.path.join(d, "SCORM")
        outzip = os.path.join(d, "SCORM_out.zip")
        try:
            os.mkdir(scorm_d)
        except OSError:
            pass
        os.chdir(scorm_d)
        with zipfile.ZipFile(os.path.join(d,tmpname)) as zf:
            zf.extractall()
        html_dir = os.path.join(scorm_d, "pages")
        os.chdir(html_dir)

        gen = StaticGenerator()
        self.url_map = {}
        start = paths.pop(0)
        self.save_page(gen, "start", start)
        self.url_map[start] = "start"
        end = paths.pop()
        self.save_page(gen, "end", end)
        self.url_map[end] = "end"
        i = 1
        for path in paths:
            nm = "page%d" % i
            self.save_page(gen, nm, path)
            self.url_map[path] = nm
            i += 1

        map_dir = os.path.join(scorm_d, "js", "src", "config")
        map_file = os.path.join(map_dir, "urlmap.js")
        with open(map_file,'w') as f:
            f.write("define(function() {\n\treturn ")
            f.write(json.dumps(self.url_map)+"\n")
            f.write("});")
        with zipfile.ZipFile(outzip,'w') as zf:
            for root, dirs, files in os.walk(scorm_d):
                rel_root = root.replace(scorm_d,"")
                for file in files:
                    arc_file = os.path.join(rel_root, file)
                    full_file = os.path.join(root, file)
                    zf.write(full_file, arc_file)
        with open(outzip) as f:
            zipc = f.read()
        with storage.open("SCORM/generated.zip",'w') as sf:
            sf.write(zipc)

    def save_page(self, gen, name, path):
        content = gen.get_content_from_path(path)
        filename = os.path.join(os.getcwd(), name+".html")
        with open(filename, 'w') as f:
            f.write(content)