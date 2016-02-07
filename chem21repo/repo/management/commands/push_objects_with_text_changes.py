
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

        print "*** QUESTIONS"
        for question in Question.objects.all():
            if question.has_text_changes():
                try:
                    node = DrupalQuestion(
                        id=question.remote_id, intro=question.text)
                except:
                    print "No id"
                    continue
                print node.id
                print node
                api.push(node)
                """
                for lesson in question.lessons.all():
                    node = DrupalLesson(
                        id=lesson.remote_id, question_orders=lesson.child_orders)
                    print "LESS:" + lesson.title
                    print node
                    api.push(node)
                    for module in lesson.modules.all():
                        node = DrupalCourse(
                            id=module.remote_id, lesson_orders=module.child_orders)
                        print "MOD: " + module.name
                        print node
                        api.push(node)
                """

        print "*** LESSONS"
        for lesson in Lesson.objects.all():
            if lesson.has_text_changes():
                try:
                    node = DrupalLesson(
                        id=lesson.remote_id, intro=question.text)
                except:
                    print "No id"
                    continue
                print lesson.title
                api.push(node)
                for module in lesson.modules.all():
                    node = DrupalCourse(
                        id=module.remote_id, lesson_orders=module.child_orders)
                    print "MOD" + module.name
                    print node
                    api.push(node)
        print "*** MODULES"
        for module in Module.objects.all():
            if module.has_text_changes():
                print module.name
                try:
                    node = DrupalCourse(id=module.remote_id, intro=module.text)
                except:
                    print "No id"
                    continue

