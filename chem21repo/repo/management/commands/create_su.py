from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    def handle(self, *args, **options):
        if User.objects.count() == 0:
            try:
                users = settings.SUPERUSERS_BOOTSTRAP
            except AttributeError:
                users = []
            for username, email in users.iteritems():
                User.objects.create_superuser(username, email, None)
