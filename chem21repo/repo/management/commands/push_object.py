from chem21repo.repo.models import *
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Push object'

    def add_arguments(self, parser):
        parser.add_argument('type', type=str)
        parser.add_argument('id', type=int)

    def handle(self, *args, **options):
        ct = ContentType.objects.get(app_label="repo", model=options['type'])
        obj = ct.get_object_for_this_type(pk=options['id'])
        obj.drupal.push()
