from chem21repo.api_clients import C21RESTRequests, RESTError
from chem21repo.drupal import drupal_node_factory
from chem21repo.repo.models import Question

from django.core.management.base import BaseCommand
import json


class Command(BaseCommand):
    help = 'Download all drupal files'

    def handle(self, *args, **options):
        fixture = []
        for q in Question.objects.all():
            files = list(q.files.all())
            if files:
                fixture.append(
                    {"pk": q.pk,
                     "model": "repo.question",
                     "fields": {
                         "files": [f.pk for f in files],
                     }}
                )
        print json.dumps(fixture)
