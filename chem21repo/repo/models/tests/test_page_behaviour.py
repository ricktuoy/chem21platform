from django.test import TestCase

from .. import Lesson, Module, Topic


class PageSaveTestCase(TestCase):

    def setUp(self):
        self.topic = Topic(name="fake topic")
        self.topic.save()

        self.module = Module(topic=self.topic, text="Fake module", name="Fake module", code="FAKE")
        self.module.save()

    def test_that_creating_a_module_saves_an_associated_page(self):
        # given some fake lesson
        body_text = "<p>Some test module</p>"
        name = "Test module"

        # when we make a new lesson
        self.module = Module(topic=self.topic, text=body_text, name=name, code="TEST")
        self.module.save()

        # then a question is also saved as its associated page
        page = self.module.page
        self.assertEqual(body_text, page.text)
        self.assertEqual(name, page.title)

        # and the question's canonical url is the same as its parent
        self.assertTrue(page.get_canonical_page().get_absolute_url())
        self.assertEqual(page.get_canonical_page().get_absolute_url(), self.module.get_absolute_url())

    def test_that_creating_a_lesson_saves_an_associated_page(self):
        # given some fake lesson
        body_text = "<p>Some test lesson</p>"
        name = "Test lesson"

        # when we make a new lesson
        test_lesson = Lesson(text=body_text, title=name)
        test_lesson.save()
        test_lesson.modules.add(self.module)

        # then a question is also saved as its associated page
        page = test_lesson.page
        self.assertEqual(body_text, page.text)
        self.assertEqual(name, page.title)

        # and the question's canonical url is the same as its parent
        self.assertTrue(page.get_canonical_page().get_absolute_url())
        self.assertEqual(page.get_canonical_page().get_absolute_url(), test_lesson.get_absolute_url())
