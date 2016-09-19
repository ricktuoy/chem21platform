from django import template
from django.core.files.storage import default_storage
from abc import ABCMeta
from abc import abstractmethod
from .tokens import GHSStatementProcessor
import json

register = template.Library()

class QuestionNotFoundError(Exception):
    pass

class QuestionRender:
    __metaclass__ = ABCMeta

    @abstractmethod
    def render(self):
        pass

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
                               "Skip question &raquo;")
        except QuestionNotFoundError:
            next_html = tpl % ("skip",
                               "final",
                               "Skip question &raquo;")

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
        if self.get_help_text():
            return "<legend class=\"help\">%s</legend>" % self.get_help_text()
        else:
            return ""

    def get_help_text(self):
        return self.help_text

    def render_score(self):
        return "<p class=\"final_score\"></p>"

class NumericQuestionRender(QuestionRender):
    def __init__(self, *args, **kwargs):
        question = kwargs['question']
        self.id = question['id']
        self.text = question['text']
        self.questions = kwargs['questions']
        self.help_text = kwargs.get('help_text', "")
        self.num = kwargs['num']
        self.question_type = "numeric"

    def render(self):
        return "<div class=\"question\" id=\"question_%s\" " % self.id + \
            "data-id=\"%s\" data-type=\"%s\">%s%s<fieldset data-role=\"controlgroup\">\n<input type=\"number\" name=\"%s\" />" % (
                self.id, self.question_type, self.render_question_text(), self.render_score(), self.id) + \
            self.render_help_text() + \
            "</fieldset>" + \
            self.render_navigation() + \
            self.render_submit() + \
            "<div class=\"clear\">&nbsp;</div>" + \
            "</div>"

class ChoiceQuestionRender(QuestionRender):
    __metaclass__ = ABCMeta

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
        self.help_text = kwargs.get('help_text', "")

    @abstractmethod
    def render_choice(self, choice):
        pass

    def render_choices(self):
        return "\n".join(
            [self.render_choice(choice)
             for choice in self.choices])



    def render(self):
        return "<div data-enhance=\"true\" class=\"question ui-field-contain\" id=\"question_%s\" " % self.id + \
            "data-id=\"%s\" data-type=\"%s\">%s%s<fieldset data-role=\"controlgroup\">\n" % (
                self.id, self.question_type, self.render_question_text(), self.render_score()) + \
            self.render_help_text() + \
            self.render_choices() + \
            "</fieldset>" + \
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
        ref = "q%sr%s" % (self.id, choice['id'])
        return "<input type=\"%s\" value=\"%s\" data-id=\"%s\" name=\"%s\" id=\"%s\" class=\"choice\"><label for=\"%s\">%s</label>" % (
            self.widget_type, choice['id'], choice['id'], self.id, ref, ref, choice['text']
        )

    def render_choices(self):
        return super(TextChoiceQuestionRender, self).render_choices() +"\n"



class MultiChoiceQuestionRender(TextChoiceQuestionRender):
    #help_text = "Select all that apply"
    widget_type = "checkbox"

    def get_help_text(self):
        if not self.help_text:
            return "Select all that apply"
        else:
            return self.help_text


class SingleChoiceQuestionRender(TextChoiceQuestionRender):
    widget_type = "radio"


QuestionRenderDispatch = {
    'default': SingleChoiceQuestionRender,
    'multi': MultiChoiceQuestionRender,
    'single': SingleChoiceQuestionRender,
    'numeric': NumericQuestionRender
}


class RenderQuizNode(template.Node):
    def __init__(self, text_field):
        self.text = template.Variable(text_field)

    @classmethod
    def question_file_path(cls, n):
        return "quiz/" + n + "_questions.json"

    @classmethod
    def answer_file_path(cls, n):
        return "quiz/" + n + "_answers.json"

    def render(self, context):
        quiz_name = self.text.resolve(context)
        try:
            with default_storage.open(self.question_file_path(quiz_name),"r") as f:    
                quiz = json.load(f)
        except IOError:
            return "<p>Quiz file not found.</p>"
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

class RenderGuideToolNode(template.Node):
    def __init__(self, text_field):
        self.text = template.Variable(text_field)
    
    @classmethod
    def guide_file_path(cls, n):
        return "guides/" + n + ".json"


    def render(self, context):
        guide_name = self.text.resolve(context)
        try:
            with default_storage.open(
                self.guide_file_path(guide_name),
                "r") as f:
                guide = json.load(f)
        except IOError:
            return "Tool file not found: %s" % self.guide_file_path(guide_name)

        def alt_render_nav(self):
            tpl = "<a class=\"%s\" href=\"#%s\">%s</a>"
            try:
                previous_html = tpl % ("prev",
                                       self.get_question_html_id(self.num - 2),
                                       "Previous")
            except QuestionNotFoundError:
                previous_html = ""

            try:
                next_html = tpl % ("next",
                                   self.get_question_html_id(self.num),
                                   "Next question &raquo;")
            except QuestionNotFoundError:
                next_html = ""

            if previous_html or next_html:
                return "<nav class=\"controls\">%s%s</nav>" % (
                    previous_html, next_html)
            else:
                return ""

        def alt_render_submit(self): 
            if self.is_final_question():
                return "<a href=\"#she_scores\" class=\"submit\">Show scores</a>"
            else:
                return ""

        html = ""

        for i, question in zip(range(1, len(guide['data']) + 1), guide['data']):
            cls = QuestionRenderDispatch[question.get("type", "default")]
            cls.render_navigation = alt_render_nav
            cls.render_submit = alt_render_submit
            html += cls(question=question,
                        questions=guide['data'],
                        num=i).render() + "\n"
            html += "<div class=\"error\"></div>"

        html += "<div id=\"she_scores\"> </div>"
        html = GHSStatementProcessor(context=context).apply(html)
        return "<div class=\"guide\" data-id=\"%s\"" % guide['id'] + \
            "><form>%s</form></div>" % html




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

@register.tag(name="render_guide_tool")
def do_render_guide_tool(parser, token):
    try:
        tag_name, text_field = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly one argument" % token.contents.split()[
                0]
        )
    return RenderGuideToolNode(text_field)   
