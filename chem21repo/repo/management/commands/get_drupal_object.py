from chem21repo.api_clients import C21RESTRequests
from chem21repo.drupal import drupal_node_factory


from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Get Drupal object'

    def add_arguments(self, parser):
        parser.add_argument('type', type=str)
        parser.add_argument('node_id', type=int)

    def handle(self, *args, **options):
        c21_requests = C21RESTRequests()
        c21_requests.authenticate()
        raw = c21_requests.get(options['type'], options['node_id'])
        node = drupal_node_factory(options['type'])(**raw)
        print node
