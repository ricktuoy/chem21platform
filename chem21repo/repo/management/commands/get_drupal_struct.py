from chem21repo.api_clients import C21RESTRequests, DrupalQuestion


from django.core.management.base import BaseCommand


import json


class Command(BaseCommand):
    help = 'Get Drupal structure'

    def handle(self, *args, **options):
        c21_requests = C21RESTRequests()
        c21_requests.authenticate()
        courses_data = c21_requests.index_courses()
        for module in courses_data:
            tree_data = c21_requests.get("course", int(module['nid']))
            print "%s: %s" % (tree_data['nid'], tree_data['title'])
            print "*******"
            for lesson in tree_data['lessons']:
                print "-- %s: %s" % (lesson['nid'], lesson['title'])
                for question in lesson['questions']:
                    node = DrupalQuestion(
                        **c21_requests.get("question", int(question['nid'])))
                    print "---- %s: %s" % (node.id, node.get('title'))
