from django.core.management import call_command
from django.test import TestCase

from chem21repo.repo.models import Question
from chem21repo.repo.models.tests.helpers import Initialiser


class InitDataTestCase(TestCase):

    def test_that_fixture_loaded_when_database_empty(self):
        self.assertEqual(Question.objects.count(), 0)
        call_command('initialise_data', 'fixtures/init_data.json')
        self.assertGreater(Question.objects.count(), 0)

    def test_that_fixture_not_loaded_when_database_not_empty(self):
        lesson = Initialiser.create_base_lesson(Initialiser.create_base_topic())
        Initialiser.add_questions_to_lesson(lesson, range(0, 3))
        question_count = Question.objects.count()
        self.assertGreater(question_count, 0)
        call_command('initialise_data', 'fixtures/init_data.json')
        self.assertEqual(Question.objects.count(), question_count)

