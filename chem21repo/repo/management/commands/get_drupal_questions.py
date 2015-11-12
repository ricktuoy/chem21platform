from chem21repo.api_clients import C21RESTRequests, DrupalNode
from chem21repo.repo.models import Lesson
from chem21repo.repo.models import LessonsInModule
from chem21repo.repo.models import Module
from chem21repo.repo.models import Question
from chem21repo.repo.models import QuestionsInLesson

from django.core.management.base import BaseCommand
from django.db import IntegrityError

import json


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

    def save_question(self, question, lesson):
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
                lesson=lesson,
                order=question['number'])
        except IntegrityError:
            pass
        return (q_obj, created)

    def save_lesson(self, lesson, module):
        l_obj, created = \
            Lesson.objects.get_or_create(remote_id=lesson['nid'],
                                         defaults={'title': lesson['title']})
        if not created:
            l_obj.title = lesson['title']
            l_obj.save()
        try:
            LessonsInModule.objects.create(
                lesson=l_obj, module=module)
        except IntegrityError:
            pass
        return (l_obj, created)

    def handle(self, *args, **options):
        c21_requests = C21RESTRequests()
        c21_requests.authenticate()
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

            for lesson in tree_data['lessons'][0:1]:
                l_obj, l_created = self.save_lesson(lesson, m_obj)
                for question in lesson['questions']:
                    q_obj, q_created = self.save_question(question, l_obj)
                    node = DrupalNode(
                        c21_requests.get_node(int(question['nid'])))
                    h5p = node.h5p_data
                    try:
                        node.json['filtered'] = json.loads(
                            node.json['filtered'])
                        node.json['json_content'] = json.loads(
                            node.json['json_content'])
                    except KeyError:
                        pass
                    print json.dumps(node.json, sort_keys=True,
                                     indent=4,
                                     separators=(',', ': '))
