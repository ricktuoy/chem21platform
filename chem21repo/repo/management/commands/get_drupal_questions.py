import requests

from chem21repo.repo.models import Lesson
from chem21repo.repo.models import LessonsInModule
from chem21repo.repo.models import Module
from chem21repo.repo.models import Question
from chem21repo.repo.models import QuestionsInLesson
from chem21repo.api_clients import C21RESTRequests

from django.core.management.base import BaseCommand
from django.db import IntegrityError


class Command(BaseCommand):
    help = 'Import questions from the platform'

    def get_module_from_input(self):
        m_obj = None
        while True:
            code = raw_input("Enter module code (X to skip): ")
            if code == "X":
                break
            try:
                m_obj = Module.objects.get(code=code)
            except Module.DoesNotExist:
                continue
            break
        return m_obj

    def save_question(self, question):
        q_obj, created = \
            Question.objects.get_or_create(remote_id=question['nid'],
                                           defaults={'title':
                                                     question['title']})
        if not created:
            q_obj.title = question['title']
            q_obj.save()
        try:
            QuestionsInLesson.objects.create(
                question=q_obj,
                lesson=l_obj,
                order=question['number'])
        except IntegrityError:
            pass

    def save_lesson(self, lesson):
        l_obj, created = \
            Lesson.objects.get_or_create(remote_id=lesson['nid'],
                                         defaults={'title': lesson['title']})
        if not created:
            l_obj.title = lesson['title']
            l_obj.save()
        try:
            LessonsInModule.objects.create(
                lesson=l_obj, module=m_obj)
        except IntegrityError:
            print "Lesson %s not added to module" % l_obj.title
            pass
        for question in lesson['questions']:
            self.save_question(question)

    def handle(self, *args, **options):
        c21_requests = C21RESTRequests()
        courses_data = c21_requests.get_courses()
        for module in courses_data:
            print "Getting tree for %s" % module['title']
            tree_data = c21_requests.get_lesson_tree(cId=module['nid'])
            try:
                m_obj = Module.objects.get(remote_id=module['nid'])
            except Module.DoesNotExist:
                m_obj = self.get_module_from_input()
                if not m_obj:
                    continue
                m_obj.remote_id = module['nid']
                m_obj.save()

            for lesson in tree_data['lessons']:
                self.save_lesson(lesson)
