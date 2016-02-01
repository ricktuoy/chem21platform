from datetime import datetime
from datetime import timedelta
from chem21repo.repo.models import TextVersion

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Set missing version times as now'

    def handle(self, *args, **options):
        now = datetime.now() - timedelta(days=100)
        i = 1
        for obj in TextVersion.objects.filter(
                modified_time__isnull=True):
            obj.modified_time = now + timedelta(seconds=5*i)
            i += 1
            obj.save()
