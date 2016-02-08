from chem21repo.api_clients import C21RESTRequests, RESTError
from chem21repo.drupal import drupal_node_factory
from chem21repo.repo.models import Question

from django.core.management.base import BaseCommand
import json


class Command(BaseCommand):
    help = 'Download all drupal files'

    def add_arguments(self, parser):
        parser.add_argument('filename', type=str)

    def handle(self, *args, **options):
    	with open(options['filename'], 'r') as f:
            fixture = json.loads(f.read())
        for entry in fixture:
            q = Question.objects.get(pk=entry['pk'])
            q.files.clear()
            for fid in entry['fields']['files']:
                q.files.add(int(fid))
                pass
