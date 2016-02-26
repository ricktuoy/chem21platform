from chem21repo.repo.models import *
from chem21repo.repo.templatetags.tokens import SurroundFiguresTokenProcessor
from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify


class Command(BaseCommand):
    help = 'Print nodes with text changes'

    def handle(self, *args, **options):
        mods = [Topic, Module, Lesson, Question]
        proc = SurroundFiguresTokenProcessor()
        for model in mods:
            for obj in model.objects.all():
                if obj.text:
                    proc = SurroundFiguresTokenProcessor()
                    obj.text = proc.apply(obj.text)
                    if hasattr(proc, 'is_matched'):
                        try:
                            print obj.title
                        except UnicodeEncodeError:
                            print "SHITTY TITLE"
                    obj.save()
