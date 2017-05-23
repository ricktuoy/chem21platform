from chem21repo.repo.models import *
from chem21repo.repo.templatetags.tokens import SurroundFiguresTokenProcessor
from django.core.management.base import BaseCommand
from django.template.defaultfilters import slugify
import re
from chem21repo.repo.shortcodes import HTMLShortcodeParser

class Command(BaseCommand):
    help = 'Surround figgroups with divs'

    def handle(self, *args, **options):
        mods = [Topic, Module, Lesson, Question]
        i=0
        for model in mods:
            for obj in model.objects.all():
                if obj.text:
                    html = re.sub(r"\[figgroup:table(.*?)\[\/figgroup\]", "[table\g<1>[/table]", obj.text, flags=re.DOTALL)
                    html = HTMLShortcodeParser(html).mark_up_block_shortcodes()
                    if html != obj.text and ("[table" in html):
                        print html.encode("utf-8")
                        print "----------------------"
                        i += 1
                        if i == 5:
                            die() 
                        # obj.text = html
                        # obj.save()

