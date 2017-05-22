import re

from chem21repo.repo.shortcodes import HTMLShortcodeProcessor
from django import template

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
        processor = HTMLShortcodeProcessor(html)
        context['tokens_replaced'] = processor.replace_shortcodes_with_html()
        context += processor.get_extra_html_snippets()
        return ""


@register.tag(name="replace_shortcode")
def do_replace_shortcode(parser, token):
    try:
        tag_name, text_field = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly one argument" % token.contents.split()[
                0]
        )
    return ReplaceShortcodesNode(text_field)

