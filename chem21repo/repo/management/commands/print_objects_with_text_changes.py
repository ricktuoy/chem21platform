
from chem21repo.repo.models import Lesson
from chem21repo.repo.models import Module
from chem21repo.repo.models import Question

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Print nodes with text changes'

    def handle(self, *args, **options):
        print "*** MODULES"
        for module in Module.objects.all():
            if module.has_text_changes():
                print module.title
        print "*** LESSONS"
        for lesson in Lesson.objects.all():
            if lesson.has_text_changes():
                print lesson.title
        print "*** QUESTIONS"
        for question in Question.objects.all():
            if question.has_text_changes():
                print question.title
