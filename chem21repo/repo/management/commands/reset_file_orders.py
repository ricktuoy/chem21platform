from chem21repo.repo.models import *
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Push object'

    def handle(self, *args, **options):
    	UniqueFilesofModule.objects._current_element = UniqueFilesofModule.objects.get(pk=476)
        UniqueFilesofModule.objects._reset_order()
