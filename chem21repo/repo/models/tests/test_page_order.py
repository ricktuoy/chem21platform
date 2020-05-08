from django.test import TestCase

from .helpers import Initialiser
from .. import Module


class PageOrderTestCase(TestCase):

    def setUp(self):
        self.topic = Initialiser.create_base_topic()

    def test_that_saving_a_module_to_a_topic_adds_it_at_the_end(self):
        modules = []
        for i in range(0, 5):
            modules.append(Module(topic=self.topic, name='Module %s' % str(i), code='MOD %s' % str(i)))
            modules[i].save()

        self.assertEqual(self.topic.get_next_object().name, modules[0].name)
        self.assertEqual(modules[0].get_previous_object().name, self.topic.name)
        for i in range(1, 5):
            self.assertEqual(modules[i - 1].get_next_object().name, modules[i].name)
            self.assertEqual(modules[i].get_previous_object().name, modules[i - 1].name)

    def test_that_saving_a_lesson_to_a_module_adds_it_at_the_end(self):
        module = Module(topic=self.topic, name='Fake module', code='FAKE')
        module.save()

        lessons = Initialiser.add_lessons_to_module(module, range(0, 4))

        self.assertEqual(module.get_next_object().title, lessons[0].title)
        self.assertEqual(lessons[0].get_previous_object().title, module.title)

        for i in range(1, 4):
            self.assertEqual(lessons[i - 1].get_next_object().title, lessons[i].title)
            self.assertEqual(lessons[i].get_previous_object().title, lessons[i - 1].title)

    def test_that_saving_a_question_to_a_lesson_adds_it_at_the_end(self):
        lesson = Initialiser.create_base_lesson(self.topic)
        questions = Initialiser.add_questions_to_lesson(lesson, range(0, 4))

        self.assertEqual(lesson.get_next_object().title, questions[0].title)
        self.assertEqual(questions[0].get_previous_object().title, lesson.title)
        for i in range(1, 4):
            self.assertEqual(questions[i - 1].get_next_object().title, questions[i].title)
            self.assertEqual(questions[i].get_previous_object().title, questions[i - 1].title)

    def test_that_moving_a_question_up_generates_the_right_ordering(self):
        lesson = Initialiser.create_base_lesson(self.topic)
        questions = Initialiser.add_questions_to_lesson(lesson, range(0, 10))
