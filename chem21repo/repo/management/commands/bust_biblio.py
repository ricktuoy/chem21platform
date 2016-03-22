from chem21repo.repo.models import *
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Busts the biblio cache for ref(s)'

    def add_arguments(self, parser):
        parser.add_argument('citekey',
                            type=str,
                            help="Citekey(s)")

    def handle(self, *args, **options):
        ckey = options['citekey']
        bib = Biblio.objects.get(citekey=ckey)
        bib.bust()
        bib.save()
