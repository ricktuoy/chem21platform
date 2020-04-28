from django.test import TestCase

from .. import Lesson


class LessonTestCase(TestCase):
    fixtures = ['fixtures/init_data.json']

    def test_that_all_lesson_objects_only_have_one_parent_module(self):
        all_lessons = Lesson.objects.all().exclude(archived=True)
        for lesson in all_lessons:
            parents = lesson.modules.all()
            self.assertFalse(len(parents) > 1)

    def test_that_all_lesson_objects_with_question_attr_have_page_attr(self):
        pss = True
        all_lessons = Lesson.objects.all().exclude(archived=True)
        for lesson in all_lessons:
            if lesson.is_question:
                if not lesson.page:
                    print [lesson.title, lesson.pk, lesson.first_question.title, lesson.first_question.pk]
                    try:
                        print lesson.get_absolute_url()
                    except AttributeError:
                        print "Orphan"
                    pss = False
        self.assertTrue(pss)
