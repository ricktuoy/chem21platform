from django.core.management import call_command
from django.core.management.base import BaseCommand

from chem21repo.repo.models import Question


class Command(BaseCommand):
    help = 'Initialise the database from fixture, if it is empty'

    def add_arguments(self, parser):
        parser.add_argument('filename')

    def handle(self, *args, **options):
        if self.is_database_empty():
            print("Database empty, loading data from fixture %s" % options['filename'])
            call_command('loaddata', options['filename'])
        else:
            print("Database not empty so will not touch data")

    @staticmethod
    def is_database_empty():
        return Question.objects.count() == 0
