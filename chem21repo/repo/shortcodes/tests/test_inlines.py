from django.test import TestCase

from chem21repo.repo.models.tests.helpers import Initialiser
from chem21repo.repo.shortcodes import HTMLShortcodeParser, InternalLinkProcessor


class InlineShortcodeTestCase(TestCase):
    noop_html = "<p>Pellentesque habitant morbi tristique " + \
                "senectus et netus et malesuada fames ac turpis egestas.</p>"
    input_html_template = "<p>Pellentesque habitant [inlink:{page_ids}]morbi tristique[/inlink] senectus et netus " + \
                          "et malesuada fames ac turpis egestas.</p>"
    expected_html_template = "<p>Pellentesque habitant <a class=\"internal\" href=\"{url}\">morbi tristique</a> " + \
                             "senectus et netus et malesuada fames ac turpis egestas.</p>"

    def test_that_inline_link_to_topic_is_rendered(self):
        topic = Initialiser.create_base_topic()
        input_html = self.input_html_template.format(page_ids=topic.pk)

        parser = HTMLShortcodeParser(input_html)
        parser.register_inline_shortcode(InternalLinkProcessor)
        output_html = parser.get_rendered_html()

        expected_html = self.expected_html_template.format(url=topic.get_absolute_url())

        self.assertEqual(output_html, expected_html)

    def test_that_inline_link_to_module_is_rendered(self):
        topic = Initialiser.create_base_topic()
        module = Initialiser.create_base_module(topic)

        input_html = self.input_html_template.format(page_ids="{0}:{1}".format(topic.pk, module.pk))

        parser = HTMLShortcodeParser(input_html)
        parser.register_inline_shortcode(InternalLinkProcessor)
        output_html = parser.get_rendered_html()

        expected_html = self.expected_html_template.format(url=module.get_absolute_url())

        self.assertEqual(output_html, expected_html)

    def test_that_inline_link_with_unknown_page_ids_passes_thru_contents(self):
        input_html = self.input_html_template.format(page_ids="78:12:99")
        parser = HTMLShortcodeParser(input_html)
        parser.register_inline_shortcode(InternalLinkProcessor)
        output_html = parser.get_rendered_html()
        self.assertEqual(output_html, self.noop_html)

    def test_that_inline_link_with_bad_params_passes_thru_contents(self):
        input_html = self.input_html_template.format(page_ids="  abc d &* fg")
        parser = HTMLShortcodeParser(input_html)
        parser.register_inline_shortcode(InternalLinkProcessor)
        output_html = parser.get_rendered_html()
        self.assertEqual(output_html, self.noop_html)