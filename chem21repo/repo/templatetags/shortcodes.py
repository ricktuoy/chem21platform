import re

from ..shortcodes import HTMLShortcodeParser
from django import template
import logging

register = template.Library()


class FigureRefProcessor(object):
    @property
    def pattern(self):
        p = r'(example|Example|figure|Figure|' + \
            r'scheme|Scheme|table|Table)\s+[0-9]+'
        try:
            return self._pattern
        except AttributeError:
            self._pattern = re.compile(p, re.DOTALL)
            return self._pattern

    def repl_function(self, match):
        return "<span class=\"figure_ref\">%s</span>" % match.group()


class ReplaceShortcodesNode(template.Node):
    def __init__(self, text_field):
        self.text = template.Variable(text_field)

    def render(self, context):
        html = self.text.resolve(context)
        if not html:
            context['footnotes_html'] = ''
            context['pre_content'] = ''
            context['tokens_replaced'] = ''
            return ""
        parser = HTMLShortcodeParser(html)
        context['shortcodes_replaced'] = parser.get_rendered_html()
        logging.debug(parser.get_rendered_html())
        context.update(parser.get_extra_html_snippets())
        logging.debug(context)
        return ""


@register.tag(name="replace_shortcodes")
def do_replace_shortcode(parser, token):
    try:
        tag_name, text_field = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly one argument" % token.contents.split()[
                0]
        )
    return ReplaceShortcodesNode(text_field)
