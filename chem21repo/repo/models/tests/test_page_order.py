from django.test import TestCase

from .helpers import Initialiser
from .. import Module, Question, Lesson


class PageOrderTestCase(TestCase):

    def setUp(self):
        self.topic = Initialiser.create_base_topic()

    def test_that_saving_a_module_to_a_topic_adds_it_at_the_end(self):
        modules = []
        for i in range(0, 5):
            modules.append(Module(topic=self.topic, name='Module %s' % str(i), code='MOD %s' % str(i)))
            modules[i].save()

        self._assert_that_cms_order_matches_array_order([self.topic, ] + modules)

    def test_that_saving_a_lesson_to_a_module_adds_it_at_the_end(self):
        module = Module(topic=self.topic, name='Fake module', code='FAKE')
        module.save()

        lessons = Initialiser.add_lessons_to_module(module, range(0, 4))

        self._assert_that_cms_order_matches_array_order([module, ] + lessons)

    def test_that_saving_a_question_to_a_lesson_adds_it_at_the_end(self):
        lesson = Initialiser.create_base_lesson(self.topic)
        questions = Initialiser.add_questions_to_lesson(lesson, range(0, 4))

        self._assert_that_cms_order_matches_array_order([lesson, ] + questions)

    def test_that_moving_a_question_to_top_generates_the_right_ordering(self):
        lesson = Initialiser.create_base_lesson(self.topic)
        questions = Initialiser.add_questions_to_lesson(lesson, range(0, 10))

        Question.objects.move_to_top(questions[4])

        # reload objects from DB
        lesson = Lesson.objects.get(pk=lesson.pk)
        questions = [Question.objects.get(pk=q.pk) for q in questions]

        expected_order = [lesson, questions[4]] + questions[0:4] + questions[5:]
        self._assert_that_cms_order_matches_array_order(expected_order)

    def test_that_moving_a_question_up_generates_the_right_ordering(self):
        lesson = Initialiser.create_base_lesson(self.topic)
        questions = Initialiser.add_questions_to_lesson(lesson, range(0, 10))

        Question.objects.move(questions[6], questions[3])

        # reload objects from DB
        lesson = Lesson.objects.get(pk=lesson.pk)
        questions = [Question.objects.get(pk=q.pk) for q in questions]

        expected_order = [lesson, ] + questions[0:4] + [questions[6], ] + questions[4:6] + questions[7:]
        self._assert_that_cms_order_matches_array_order(expected_order)

    def test_that_moving_a_question_down_generates_the_right_ordering(self):
        lesson = Initialiser.create_base_lesson(self.topic)
        questions = Initialiser.add_questions_to_lesson(lesson, range(0, 10))

        Question.objects.move(questions[2], questions[9])

        # reload objects from DB
        lesson = Lesson.objects.get(pk=lesson.pk)
        questions = [Question.objects.get(pk=q.pk) for q in questions]

        expected_order = [lesson, ] + questions[0:2] + questions[3:10] + [questions[2],]
        self._assert_that_cms_order_matches_array_order(expected_order)


    def test_that_moving_a_lesson_to_top_generates_the_right_ordering(self):
        module = Initialiser.create_base_module(self.topic)
        lessons = Initialiser.add_lessons_to_module(module, range(0, 10))
        source_l = lessons[7]
        Lesson.objects.move_to_top(source_l)

        # reload objects from DB
        module = Module.objects.get(pk=module.pk)
        lessons = [Lesson.objects.get(pk=q.pk) for q in lessons]

        expected_order = [module, lessons[7]] + lessons[0:7] + lessons[8:]
        self._assert_that_cms_order_matches_array_order(expected_order)

    def _assert_that_cms_order_matches_array_order(self, objects):
        for i in range(1, len(objects)):
            self.assertEqual(objects[i - 1].get_next_object().title, objects[i].title)
            self.assertEqual(objects[i].get_previous_object().title, objects[i - 1].title)
