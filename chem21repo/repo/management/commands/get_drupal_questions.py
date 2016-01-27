from chem21repo.api_clients import C21RESTRequests
from chem21repo.drupal import DrupalQuestion
from chem21repo.repo.models import Lesson
from chem21repo.repo.models import Module
from chem21repo.repo.models import Question

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
            Question.objects.get_or_create(
                remote_id=question['nid'],
                defaults={'order': question['number'],
                          'title': question['title']})
        if not created:
            q_obj.title = question['title']
            q_obj.text = question['intro']
            q_obj.save()
        try:
            q_obj.lessons.add(lesson)
        except IntegrityError:
            pass
        return (q_obj, created)

    def save_lesson(self, lesson, module):
        l_obj, created = \
            Lesson.objects.get_or_create(remote_id=lesson['nid'],
                                         defaults={'title': lesson['title']})
        if not created:
            l_obj.title = lesson['title']
            l_obj.text = lesson['intro']
            l_obj.save()
        try:
            l_obj.modules.add(module)
        except IntegrityError:
            pass
        return (l_obj, created)

    def handle(self, *args, **options):
        c21_requests = C21RESTRequests()
        c21_requests.authenticate()
        courses_data = c21_requests.index_courses()
        for module in courses_data:
            print "Getting tree for %s" % module['title']

            tree_data = c21_requests.get("course", int(module['nid']))
            try:
                m_obj = Module.objects.get(remote_id=module['nid'])
            except Module.DoesNotExist:
                m_obj = self.get_module_from_input()
                if not m_obj:
                    continue
                m_obj.remote_id = module['nid']
                m_obj.save()
            m_obj.intro = tree_data['intro']

            for lesson in tree_data['lessons']:
                l_obj, l_created = self.save_lesson(lesson, m_obj)
                for question in lesson['questions']:
                    qnode = c21_requests.get("question", int(question['nid']))
                    qnode['number'] = question['number']
                    q_obj, q_created = self.save_question(qnode, l_obj)
                    """
                    node = DrupalQuestion(qnode)
                    print json.dumps(node, sort_keys=True,
                                     indent=4,
                                     separators=(',', ': '))
                    """
        #print json.dumps(DrupalQuestion(**c21_requests.get("question", 62)))
