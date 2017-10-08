from chem21repo.repo.models import *
from django.core.management.base import BaseCommand
import re
from chem21repo.repo.shortcodes import HTMLShortcodeParser
from difflib import Differ
from pprint import pprint

class Command(BaseCommand):
    help = 'Surround figgroups with divs'

    def handle(self, *args, **options):
        mods =  [Topic, Module, Lesson, Question]
        i=0
        for model in mods:
            for obj in model.objects.all():
                if obj.text:
                    before = obj.text
                    html = re.sub(r"\[figgroup:table(.*?)\[\/figgroup\]", "[table\g<1>[/table]", obj.text, flags=re.DOTALL)
                    html = HTMLShortcodeParser(html).mark_up_block_shortcodes()
                    if html != obj.text:
                        d = Differ()
                        b = before.splitlines()
                        a = html.splitlines()
                        result = list(d.compare(a,b))
                        pprint(result)

                        i += 1

                        obj.text = html
                        obj.save()

