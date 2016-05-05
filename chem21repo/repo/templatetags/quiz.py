from django import template
from django.core.files.storage import default_storage
from abc import ABCMeta
from abc import abstractmethod
import json

register = template.Library()


class QuestionRender:
    __metaclass__ = ABCMeta

    @abstractmethod
    def render(self):
        pass


class QuestionNotFoundError(Exception):
    pass


class ChoiceQuestionRender(QuestionRender):
    __metaclass__ = ABCMeta

    @property
    def help_text(self):
        return ""

    @property
    def question_type(self):
        return self.type

    def __init__(self, *args, **kwargs):
        question = kwargs['question']
        self.choices = question['responses']
        self.id = question['id']
        self.text = question['text']
        self.type = question['type']
        self.questions = kwargs['questions']
        self.num = kwargs['num']

    @abstractmethod
    def render_choice(self, choice):
        pass

    def render_choices(self):
        return "\n".join(
            [self.render_choice(choice)
             for choice in self.choices])

    def render_question_text(self):
        return "<h3>%s</h3>\n" % self.text

    def get_question_html_id(self, num):
        try:
            if num >= 0:
                return "question_" + self.questions[num]['id']
        except IndexError:
            pass
        raise QuestionNotFoundError("No question number %s" % num)

    def is_final_question(self):
        if(self.num == len(self.questions)):
            return True
        return False

    def render_navigation(self):
        tpl = "<a class=\"%s\" href=\"#%s\">%s</a>"

        try:
            previous_html = tpl % ("previous",
                                   self.get_question_html_id(self.num - 2),
                                   "Previous")
        except QuestionNotFoundError:
            previous_html = ""

        try:
            next_html = tpl % ("skip",
                               self.get_question_html_id(self.num),
                               "Skip question")
        except QuestionNotFoundError:
            next_html = tpl % ("skip",
                               "final",
                               "Skip question")

        if previous_html or next_html:
            return "<nav class=\"controls\">%s%s</nav>" % (
                previous_html, next_html)
        else:
            return ""

    def render_submit(self):
        if self.is_final_question():
            return "<a href=\"#\" class=\"submit\">View all scores</a>"
        else:
            return ""

    def render_help_text(self):
        if self.help_text:
            return "<p class=\"help\">%s</p>" % self.help_text
        else:
            return ""

    def render_score(self):
        return "<p class=\"final_score\"></p>"

    def render(self):
        return "<div class=\"question\" id=\"question_%s\"" % self.id + \
            "data-id=\"%s\" data-type=\"%s\">\n" % (
                self.id, self.question_type) + \
            self.render_question_text() + \
            self.render_help_text() + \
            self.render_score() + \
            self.render_choices() + \
            self.render_navigation() + \
            self.render_submit() + \
            "<div class=\"clear\">&nbsp;</div>" + \
            "</div>"


class DragChoiceQuestionRender(ChoiceQuestionRender):
    def render_choice_image(self, choice):
        return "<img src=\"%s\" alt=\"%s\" />" % (
            choice['url'], choice['text'])

    def render_choice(self, choice):
        return "<li data-id=\"%s\" class=\"choice drag\">%s</li>" % (
            choice['id'], self.render_choice_image(choice)
        )

    def render_target(self):
        return "<div class=\"answer\"><h3>Your answer</h3>" + \
            "<div class=\"drop-target\"></div></div>"

    def render_choices(self):
        return "<ul>%s%s</ul>" % (
            super(DragChoiceQuestionRender, self).render_choices(),
            self.render_target())


class TextChoiceQuestionRender(ChoiceQuestionRender):
    def render_choice(self, choice):
        return "<li data-id=\"%s\" class=\"choice\">%s</li>" % (
            choice['id'], choice['text']
        )

    def render_choices(self):
        return "<ul>\n" + \
            super(TextChoiceQuestionRender, self).render_choices() + \
            "</ul>\n"


class MultiChoiceQuestionRender(TextChoiceQuestionRender):
    help_text = "Select all that apply"


class SingleChoiceQuestionRender(TextChoiceQuestionRender):
    pass


QuestionRenderDispatch = {
    'default': SingleChoiceQuestionRender,
    'multi': MultiChoiceQuestionRender,
    'single': SingleChoiceQuestionRender
}


class RenderQuizNode(template.Node):
    def __init__(self, text_field):
        self.text = template.Variable(text_field)

    @classmethod
    def question_file_path(cls, n):
        return "quiz/" + n + "_questions.json"

    def answer_file_path(cls, n):
        return "quiz/" + n + "_answers.json"

    def render(self, context):
        quiz_name = self.text.resolve(context)
        with default_storage.open(
                self.question_file_path(quiz_name),
                "r") as f:
            quiz = json.load(f)
        json_url = default_storage.url(self.answer_file_path(quiz_name))
        return "<div class=\"quiz_questions\" data-id=\"%s\"" % quiz['id'] + \
            " data-answers-json-url=\"%s\">%s</div>" % (
                json_url,
                "\n".join(
                    [QuestionRenderDispatch[question.get("type", "default")]
                        (question=question,
                            questions=quiz['data'],
                            num=i).render()
                        for i, question in
                        zip(range(1, len(quiz['data']) + 1), quiz['data'])]
                )
        )


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
