from django.templatetags.static import static
from django.test import TestCase

from chem21repo.repo.shortcodes import HTMLShortcodeParser
from chem21repo.repo.shortcodes.processors import GHSStatementProcessor


class MiscInlineShortcodeTestCase(TestCase):
    input_html_template = "<p>This is a symbol [GHS_statement:{id}]</p>"
    expected_html_template = "<p>This is a symbol <img src=\"{url}\" alt=\"GHS symbol\" class=\"ghs_symbol\" /></p>"

    def test_that_ghs_statement_is_rendered_correctly(self):
        for n in range(1, 10):
            input_html = self.input_html_template.format(id=n)
            parser = HTMLShortcodeParser(input_html)
            parser.register_inline_shortcode(GHSStatementProcessor)
            output_html = parser.get_rendered_html()
            self.assertEqual(output_html,
                             self.expected_html_template.format(url=static("/static/img/ghs/symbol_{id}.png".format(id=n))))
