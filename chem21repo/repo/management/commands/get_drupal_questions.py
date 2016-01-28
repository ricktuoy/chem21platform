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

    def add_arguments(self, parser):
        parser.add_argument('--dry',
                            action="store_true",
                            dest="dry",
                            default=False,
                            help="Dry run: don't save anything")

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

    def save_question(self, question, lesson, dry=False):

        try:
            q_obj = Question.objects.get(remote_id=question['nid'])
            if q_obj.has_text_changes():
                self.print_obj(
                    "Question %s has text changes: ignoring", question)
                return
            q_obj.title = question['title']
            q_obj.text = question['intro']
            if not dry:
                q_obj.save()
        except Question.DoesNotExist:
            if not dry:
                q_obj = Question.objects.create(
                    remote_id=question['nid'],
                    order=question['number'],
                    title=question['title'], text=question['intro'])
        if dry:
            self.print_obj("Dry run: question %s", question)
            return
        try:
            q_obj.lessons.add(lesson)
        except IntegrityError:
            pass
        return q_obj

    def save_lesson(self, lesson, module, dry=False):
        try:
            l_obj = Lesson.objects.get(remote_id=lesson['nid'])
            if l_obj.has_text_changes():
                self.print_obj("Lesson %s has text changes: ignoring", lesson)
                return
            l_obj.title = lesson['title']
            l_obj.text = lesson['intro']
            if not dry:
                l_obj.save()
        except Lesson.DoesNotExist:
            if not dry:
                l_obj = Lesson.objects.create(
                    remote_id=lesson['nid'],
                    title=lesson['title'], text=lesson['intro'])
        if dry:
            self.print_obj("Dry run: ignoring lesson %s", lesson)
            return
        try:
            l_obj.modules.add(module)
        except IntegrityError:
            pass
        return l_obj

    def print_obj(self, text, obj):
        try:
            print text % obj['title']
        except UnicodeError:
            print text % obj['nid']

    def save_module(self, module, dry=False):
        try:
            m_obj = Module.objects.get(remote_id=module['nid'])
            if m_obj.has_text_changes():
                self.print_obj("Module %s has text changes: ignoring", module)
                return
        except Module.DoesNotExist:
            m_obj = self.get_module_from_input()
            if not m_obj:
                return
            m_obj.remote_id = module['nid']
        m_obj.intro = module['intro']
        if not dry:
            m_obj.save()
            return m_obj
        else:
            self.print_obj("Dry run: ignoring module %s", module)

    def handle(self, *args, **options):
        c21_requests = C21RESTRequests()
        c21_requests.authenticate()
        courses_data = c21_requests.index_courses()
        dry = options['dry']
        for module in courses_data:
            tree_data = c21_requests.get("course", int(module['nid']))
            tree_data['nid'] = module['nid']
            m_obj = self.save_module(tree_data, dry)

            for lesson in tree_data['lessons']:
                l_obj = self.save_lesson(lesson, m_obj, dry=dry)

                for question in lesson['questions']:
                    qnode = c21_requests.get("question", int(question['nid']))
                    qnode['number'] = question['number']
                    self.save_question(
                        qnode, l_obj, dry=dry)
                    """
                    node = DrupalQuestion(qnode)
                    print json.dumps(node, sort_keys=True,
                                     indent=4,
                                     separators=(',', ': '))
                    """
        # print json.dumps(DrupalQuestion(**c21_requests.get("question", 62)))
