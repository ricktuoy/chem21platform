from django.test import TestCase

from .. import Question, Topic, Lesson
from ...object_loaders import PageLoader


class QuestionTestCase(TestCase):
    fixtures = ['fixtures/init_data.json']

    def test_that_question_objects_know_their_canonical_page(self):
        solvent_selection_need = Question.objects.get(pk=40)
        solvent_selection_criteria = Question.objects.get(pk=41)
        solvent_selection_criteria_quiz = Question.objects.get(pk=305)

        # should be assigned to the associated lesson
        self.assertEqual(solvent_selection_need.get_canonical_page().id, 114)
        self.assertEqual(solvent_selection_need.get_canonical_page().get_absolute_url(),
                         "/methods-of-facilitating-change/tools-and-guides/the-need-fo-solvent-selection-guides/")
        # should be assigned to the associated lesson
        self.assertEqual(solvent_selection_criteria.get_canonical_page().id, 115)
        # should just be assigned to itself
        self.assertEqual(solvent_selection_criteria_quiz.get_canonical_page().id, 305)

    def test_that_all_question_objects_only_have_one_parent_lesson(self):
        all_questions = Question.objects.all().exclude(archived=True)
        for question in all_questions:
            parents = question.lessons.all()
            self.assertFalse(len(parents) > 1)

    def test_that_all_question_objects_only_have_one_parent_module(self):
        all_questions = Question.objects.all().exclude(archived=True)
        for question in all_questions:
            parents = question.modules
            self.assertFalse(len(parents) > 1)

    def test_that_all_navigable_object_have_a_topic(self):
        pss = True
        all_objects = PageLoader().get_list()
        all_non_topics = [obj for obj in all_objects if type(obj) != Topic]
        for obj in all_non_topics:
            try:
                topic = obj.current_topic
            except AttributeError:
                topic = None
            if not topic:
                print("Object {pk} {name} is an orphan".format(pk=obj.pk, name=obj.title))
                pss = False
        self.assertTrue(pss)

    def test_that_all_navigable_lessons_and_questions_have_a_module(self):
        pss = True
        all_objects = PageLoader().get_list()
        all_lessons = [obj for obj in all_objects if type(obj) in (Lesson, Question)]
        for obj in all_lessons:
            try:
                module = obj.current_module
            except AttributeError:
                module = None
            if not module:
                print("Lesson {pk} {name} is an orphan".format(pk=obj.pk, name=obj.title))
                pss = False
        self.assertTrue(pss)

    def test_that_all_navigable_questions_have_a_lesson(self):
        pss = True
        all_objects = PageLoader().get_list()
        all_questions = [obj for obj in all_objects if type(obj) == Question]
        for obj in all_questions:
            try:
                lesson = obj.current_lesson
            except AttributeError:
                lesson = None
            if not lesson:
                print("Question {pk} {name} is an orphan".format(pk=obj.pk, name=obj.title))
                pss = False
        self.assertTrue(pss)
