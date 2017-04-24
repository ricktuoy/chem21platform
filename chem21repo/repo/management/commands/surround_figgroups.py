from chem21repo.repo.models import *
from chem21repo.repo.templatetags.tokens import SurroundFiguresTokenProcessor
from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify
import re


class Command(BaseCommand):
    help = 'Surround figgroups with divs'

    def handle(self, *args, **options):
        mods = [Topic, Module, Lesson, Question]
        regex_start = re.compile(r"(?<!\<\!\-\-token\-\-\>)\[figgroup")
        regex_end = re.compile(r"\[\/figgroup\](?!\<\!\-\-endtoken\-\-\>)")
        for model in mods:
            for obj in model.objects.all():
                if obj.text:
                    obj.text, n1 = regex_start.subn(
                        "<div class=\"token\"><!--token-->[figgroup", obj.text)
                    obj.text, n2 = regex_end.subn(
                        "[/figgroup]<!--endtoken--></div>", obj.text)

                    if n1:
                        print "%d:%s" % (n1, n2)
                        assert n1 == n2
                        print "%d figgroups surrounded." % n1
                        print obj.text
                        obj.save()
