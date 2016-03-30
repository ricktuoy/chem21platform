#
from chem21repo.repo.models import Lesson
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Print nodes with text changes'

    def handle(self, *args, **options):
        print "*** LESSONS"
        for lesson in Lesson.objects.all():
            if lesson.text:
                continue
            q = lesson.first_question
            if not q:
                continue
            if q.dummy:
                lesson.is_question = True
                lesson.save()
