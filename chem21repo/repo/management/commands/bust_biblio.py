from chem21repo.repo.models import *
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Busts the biblio cache for ref(s)'

    def add_arguments(self, parser):
        parser.add_argument('citekeys',
                            nargs='*',
                            type=str,
                            help="Citekey(s)")

    def handle(self, *args, **options):
        ckeys = options['citekeys']
        if len(ckeys):
            bibs = Biblio.objects.filter(citekey__in=ckeys)
        else:
            bibs = Biblio.objects.all()
        for bib in bibs:
            try:
                bib.bust()
                bib.save()
            except Biblio.DoesNotExist:
                print "No ref found for this citekey"