from ..models import Guide
from ..models import Quiz
from ..models import ToolNotFoundError
from django import template
from django.template.loader import get_template
from django.utils.html import format_html
from django.utils.html import mark_safe


register = template.Library()


class RenderToolNode(template.Node):
    def __init__(self, text_field):
        self.text = template.Variable(text_field)
        super(RenderToolNode, self).__init__()

    def get_element_context(self, element):
        pass

    def render_element(self, element):
        pass

    @property
    def iter_elements():
        pass

    def get_wrapper_context(self, context):
        content_html = mark_safe("\n".join([
            self.render_element(el)
            for i, el in self.iter_elements()]))
        return {
            'content': content_html,
            'tool_id': self.tool['id']
        }

    def render(self, context):
        self.tool_name = self.text.resolve(context)
        try:
            self.tool = self.tool_class.load(self.tool_name)
        except ToolNotFoundError:
            return ""
        w_context = self.get_wrapper_context(context)
        context['rendered_tool'] = format_html(
            self.tool_html_wrapper, **w_context)
        return ""


class ElTemplateMixin(object):
    templates = {}

    @classmethod
    def template_dispatch(cls, name="default"):
        if name == "default":
            name = cls.default_template_name
        if name not in cls.templates:
            cls.templates[name] = get_template(
                cls.question_template_path + name + ".html")
        return cls.templates[name]

    def render_element(self, element):
        return self.template_dispatch(
            element.get("type", "default")
        ).render(self.get_element_context(element))


class ElInlineMixin(object):
    def render_element(self, element):
        return format_html(
            self.formats[element.get("type", "default")],
            **self.get_element_context(element))


class QuestionToolMixin(object):
    @property
    def iter_elements(self):
        return self.tool.iter_questions


class AnswerToolMixin(object):
    @property
    def iter_elements(self):
        return self.tool.iter_answers


class RenderQuizNode(
        QuestionToolMixin, ElTemplateMixin, RenderToolNode):
    question_template_path = "quiz/questions/"
    default_template_name = "single"
    tool_class = Quiz
    tool_html_wrapper = (
        u"<div class=\"quiz_questions\" data-id=\"{tool_id}\""
        u"data-answers-json-url=\"{json_url}\">{content}</div>")
    submit_html = (
        u"<a class=\"submit\" href=\"#\" style=\"display:none;\">"
        u"View all scores</a>")

    def get_element_context(self, question):
        return {
            'question': question,
            'submit': mark_safe(self.submit_html)}

    def get_wrapper_context(self, context):
        ctx = super(
            RenderQuizNode, self).get_wrapper_context(context)
        ctx.update({
            'json_url': self.tool.answer_file_url
        })
        return ctx


class RenderPDFQuizNode(
        QuestionToolMixin, ElInlineMixin, RenderToolNode):
    default_f = (
        u"<li class=\"question\">{text}"
        u"<ul class=\"choices\">{choices}</ul></li>")
    formats = {
        'single': default_f,
        'multi': default_f,
        'numeric': u"<li class=\"question\">{text}</li>}"}
    tool_class = Quiz
    tool_html_wrapper = (
        u"<ol id=\"{tool_id}\" class=\"quiz_questions\">{content}</ol>")

    def render_choices(self, element):
        return mark_safe("\n".join([
            format_html(
                u"<li>{}</li>",
                mark_safe(choice['text'])) for choice in element['responses']
        ]))

    def get_element_context(self, question):
        ctx = {
            'text': question['text']
        }
        """
        if question['type'] == "numeric":
            return ctx
        """
        ctx['choices'] = self.render_choices(question)
        return ctx


class RenderGuideNode(RenderQuizNode):
    tool_class = Guide
    tool_html_wrapper = (
        u"<div class=\"guide\" data-id=\"{tool_id}\" "
        u"data-answers-json-url=\"{json_url}\">"
        u"<form>{content}</form><div id=\"she_scores\"></div></div>")
    submit_html = u"<a href=\"#she_scores\" class=\"submit\">Show scores</a>"


"""
class RenderPDFGuideNode(RenderQuestionsToolNode):
    question_template_path = "quiz/pdf_questions/"
    default_template_name = "single"
    tool_class = Guide
    tool_html_wrapper = (
        u"<div class=\"guide\">{content}</div>")
"""


class RenderPDFAnswersNode(
        AnswerToolMixin, ElInlineMixin, RenderToolNode):
    default_f = (
        u"<li class=\"answer\"><div class=\"question\">{text}</div>"
        u"<div class=\"answers\"><span class=\"label\">Correct answer</span>:"
        u" {answer}</div></div>")
    multi_f = (
        u"<li class=\"answer\"><div class=\"question\">{text}</div>"
        u"<div class=\"answers\"><span class=\"label\">Correct answers</span>:"
        u"<ul class=\"answers\">{answers}</ul></div></li>")
    formats = {
        'single': default_f,
        'multi': multi_f,
        'numeric': default_f}
    tool_class = Quiz
    tool_html_wrapper = (
        u"<ol id=\"answers_{tool_id}\""
        u" class=\"quiz_questions\">{content}</ol>")

    def render_answers(self, answer):
        return mark_safe("\n".join([
            format_html(
                u"<li>{}</li>",
                (mark_safe(
                    answer_t),)) for answer_t in answer['correct_texts']
        ]))

    def get_element_context(self, answer):
        question = answer['question']
        ctx = {
            'text': question['text']
        }
        if question['type'] != "multi":
            ctx['answer'] = answer['correct_texts'][0]
        else:
            ctx['answers'] = self.render_answers(answer)
        return ctx


@register.tag(name="render_quiz")
def do_render_quiz(parser, token):
    try:
        tag_name, text_field = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly one argument" % token.contents.split()[
                0]
        )
    return RenderQuizNode(text_field)


@register.tag(name="render_pdf_quiz")
def do_render_pdf_quiz(parser, token):
    try:
        tag_name, text_field = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly one argument" % token.contents.split()[
                0]
        )
    return RenderPDFQuizNode(text_field)


@register.tag(name="render_pdf_answers")
def do_render_pdf_answers(parser, token):
    try:
        tag_name, text_field = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly one argument" % token.contents.split()[
                0]
        )
    return RenderPDFAnswersNode(text_field)


@register.tag(name="render_guide_tool")
def do_render_guide_tool(parser, token):
    try:
        tag_name, text_field = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly one argument" % token.contents.split()[
                0]
        )
    return RenderGuideNode(text_field)




"""
@register.tag(name="render_pdf_guide_tool")
def do_render_pdf_guide_tool(parser, token):
    try:
        tag_name, text_field = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly one argument" % token.contents.split()[
                0]
        )
    return RenderPDFGuideNode(text_field)
"""