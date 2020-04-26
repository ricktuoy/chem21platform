from django.test import TestCase

from .. import Lesson

class SCOBaseTestCase(TestCase):
    fixtures = ['fixtures/init_data.json']

    def test_that_all_lesson_objects_only_have_one_parent_module(self):
        all_lessons = Lesson.objects.all().exclude(archived=True)
        for lesson in all_lessons:
            parents = lesson.modules.all()
            self.assertFalse(len(parents) > 1)
