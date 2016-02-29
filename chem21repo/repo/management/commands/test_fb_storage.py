from django.core.files.storage import DefaultStorage, default_storage
from filebrowser.sites import site
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Print nodes with text changes'

    def handle(self, *args, **options):
        print site.storage.__class__
        print default_storage.__class__
        print default_storage.isdir("uploads/")
        print site.storage.isdir("uploads/")
