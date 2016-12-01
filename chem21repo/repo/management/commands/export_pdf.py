from chem21repo.storage import S3StaticFileSystem
from staticgenerator import StaticGenerator
from django.contrib.contenttypes.models import ContentType
from chem21repo.repo.models import Question, Lesson, Module, Topic, PresentationAction
from django.core.management.base import BaseCommand
from django.core.files.storage import DefaultStorage, get_storage_class
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.base import ContentFile
from os import chmod, environ, path as os_path
from subprocess import call as call_subprocess
from tempfile import NamedTemporaryFile
import tempfile
import json
import os
import zipfile

class Command(BaseCommand):
    help = 'Publish to pdf'
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument('type',
                    type=str)
        parser.add_argument('id',
                    type=int)


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



    def handle(self, *args, **options):
        storage = get_storage_class(settings.STATICFILES_STORAGE)()
        ct = ContentType.objects.get(app_label="repo", model=options['type'])
        obj = ct.get_object_for_this_type(pk=options['id'])
        root = obj
        root_path = obj.get_absolute_url()
        path_set = set([])
        to_render = []
        end = False

        while not end and obj:
            new_path = obj.get_absolute_url()
            ancestors = frozenset([p.get_absolute_url() for p in obj.get_ancestors()])
            print root_path
            print ancestors
            if new_path in path_set or (new_path != root_path and root_path not in ancestors):
                # if we have a hit a circular route, or this is not a child of the root element
                end = True
            else:
                path_set.add(new_path)
                to_render.append(obj)
                obj = obj.get_next_object()



        html = render_to_string("pdf_template.html", {'objects': to_render})
        base_options = ["-s","A4",]

        letter_filename = "%s-letter.pdf" % root.slug
        a4_filename = "%s-a4.pdf" % root.slug
        
        a4_pdf = self.generate_pdf(html, options = base_options)

        american_options = ["-s","Letter"]

        letter_pdf = self.generate_pdf(html, options = american_options)

        pdf_path = "pdf/%d" % root.pk

        storage.save("%s/%s" % (pdf_path, letter_filename), letter_pdf)
        storage.save("%s/%s" % (pdf_path, a4_filename), a4_pdf)   
