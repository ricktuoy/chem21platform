import requests

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from repo.models import Lesson
from repo.models import Question


class Command(BaseCommand):
    help = 'Import questions from the platform'

    def add_arguments(self, parser):
        parser.add_argument('poll_id', nargs='+', type=int)

    def handle(self, *args, **options):
        rest_url = lambda x: settings.CHEM21_PLATFORM_BASE_URL+settings.CHEM21_PLATFORM_REST_URL+x
        courses_endpoint = { 'url':rest_url("node"), 'params':{'parameters[type]':'course'} }
        question_tree_endpoint = lambda x: { 'url': rest_url("question_tree/retrieve" % x), 'params':{'course':x} }
        node_endpoint = lambda x: {'url': rest_url("node/%d" % x) }
        courses = requests.get(**courses_endpoint).json()
        print courses

