from chem21repo.api_clients import C21RESTRequests, RESTError
from chem21repo.drupal import drupal_node_factory
from chem21repo.repo.models import UniqueFile, Question, Module, Path

from django.core.management.base import BaseCommand

import os


class Command(BaseCommand):
    help = 'Download all drupal files'

    def handle(self, *args, **options):
        modules = set()
        for m in Module.objects.all():
            try:
                paths = Path.objects.filter(module = m)
                path = paths[0]
            except IndexError:
                modules.add(m)
        print [module.topic.title+": "+module.title for module in modules]
