from chem21repo.repo.models import *
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create pages for all topic/module/lessons'

    def handle(self, *args, **options):
        mods = [Topic, Module, Lesson]
        for model in mods:
            for obj in model.objects.all():
                if not obj.is_question:
                    # create orphan question
                    print "Creating new question for %s: %s" % (
                        model.__name__, obj.title)
                    qn = Question(title=obj.title, text=obj.text)
                    qn.save()
                else:
                    print "Found dummy question for %s: %s" % (
                        model.__name__, obj.title)
                    qn = obj.first_question
                obj.page = qn
                obj.save()