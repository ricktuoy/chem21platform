from datetime import datetime
from datetime import timedelta
from chem21repo.repo.models import TextVersion, Module, Lesson, Question
from django.contrib.auth.models import User

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Adds an original version'

    def handle(self, *args, **options):
        now = datetime.now() - timedelta(days=150)
        models = [Module, Lesson, Question]
        su = User.objects.filter(is_superuser=True).first()
        for md in models:
            for obj in md.objects.filter(text_versions=None):
                obj.user = su
                try:
                    name = obj.name
                except AttributeError:
                    name = obj.title
                print "Creating a text version for %s" % name
                TextVersion.objects.create_for_object(obj, time=now)
