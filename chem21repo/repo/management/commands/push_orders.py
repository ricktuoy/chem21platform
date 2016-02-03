
from chem21repo.repo.models import Lesson
from chem21repo.repo.models import Module
from chem21repo.repo.models import Question
from chem21repo.drupal import DrupalQuestion, DrupalLesson, DrupalCourse
from django.core.management.base import BaseCommand
from chem21repo.api_clients import C21RESTRequests


class Command(BaseCommand):
    help = 'Print nodes with text changes'

    def handle(self, *args, **options):
        api = C21RESTRequests()

        print "*** LESSONS"
        for lesson in Lesson.objects.all():
            try:
                node = DrupalLesson(
                    id=lesson.remote_id, question_orders=lesson.child_orders)

            except:
                print "No id"
                continue
            print api.push(node)
            
        print "*** MODULES"
        for module in Module.objects.all():
            print module.name
            try:
                node = DrupalCourse(
                    id=module.remote_id, lesson_orders=module.child_orders)
                print module.child_orders
                print node
            except:
                print "No id"
                continue
            try:
                print api.push(node)
                pass
            except:
                print "Error"
                pass
