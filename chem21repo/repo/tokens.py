from django import forms
import re
from abc import ABCMeta
from abc import abstractproperty
from abc import abstractmethod
from chem21repo.repo.models import Question
from django.core.urlresolvers import reverse
import logging


class HTMLBlockProcessor(object):
    matches = []
    pattern = re.compile(
                r'(<p[^>]*>)(.*?)(</p>)',
                re.DOTALL)
    @classmethod
    def get_match(kls, source, number):
        if number < 1:
            raise ValueError("Blocks are numbered from 1 upwards")
        matches = list(kls.pattern.finditer(source))
        return matches[number - 1]

    @classmethod
    def get_block_ref(kls, match):
        return ""

    @classmethod
    def insert_rendered_after(kls, source, render, number):
        if number < 1:
            raise ValueError("Blocks are numbered from 1 upwards")
        i_match = kls.get_match(source, number)
        return source[:i_match.end()] + render + source[i_match.end():] 

    @classmethod
    def insert_rendered_before(kls, source, render, number):
        if number < 1:
            raise ValueError("Blocks are numbered from 1 upwards")
        if number == 1:
            i_match = kls.get_match(source, 1)
            return source[:i_match.start()] + render + source[i_match.start():]
        else:
            i_match = kls.get_match(source, number - 1)
            return source[:i_match.end()] + render + source[i_match.end():] 
            



    @classmethod
    def append_to_all(kls, source, render_fn):
        def sub_callback(match):
            out = "%s%s%s" % ( 
                match.group(1) + match.group(2),
                render_fn(sub_callback.count, ref = kls.get_block_ref(match)),
                match.group(3))
            sub_callback.count += 1
            return out
        sub_callback.count = 1
        return kls.pattern.sub(sub_callback, source)


class BaseProcessor:
    __metaclass__ = ABCMeta
    openchar = "\["
    closechar = "\]"
    blocks = HTMLBlockProcessor


    def __init__(self, *args, **kwargs):
        pass

    def match_as_token(self, match, para, token):
        return Token.from_match(question, para, match)

    @abstractproperty
    def pattern(self):
        return None

    @abstractmethod
    def repl_function(self, match):
        return None

    def apply(self, st):
        self.full_text = st
        return self.pattern.sub(self.repl_function, st)

    def _token_generator(self, seq):
        prev_end = 0
        para_count = 0
        for i,m in enumerate(seq):
            para_count = para_count + m.string.count("<p", prev_end, m.start())
            prev_end = m.end()
            yield (para, self.match_as_token(match = m, question = None, para=para_count))

    def tokens(self, st):
        try:
            return self._tokens
        except AttributeError:
            self.full_text = st
            self._tokens = dict(self._token_generator(self.pattern.finditer(st)))
            return self._tokens


class BlockToolMixin(object):
 
    def apply_block_tool(self, st):
        self.full_text = st
        try:
            obj = self.context['object']
        except KeyError:
            return st        
        def render_tool(count, ref):
            url = reverse("admin:repo_question_addtoken", 
                args = [obj.first_question.pk,
                        count,
                        self.block_tool_name
                       ])
            handle_html = self.block_tool_handle_html()
            return "<a href=\"%s\" class=\"para_token_tool\">%s</a>" % ( 
                url,
                handle_html)
        return self.blocks.append_to_all(st, render_tool)


class ContextProcessorMixin(object):

    def __init__(self, *args, **kwargs):
        self.context = kwargs.get("context", {})
        self.request = self.context.get("request", None)
        super(ContextProcessorMixin,self).__init__(*args, **kwargs)


class FigureTokenForm(forms.Form):
    figure_type = forms.CharField(label = "Type of figure", help_text="e.g. Figure/Scheme/Table (defaults to Figure)", required=False)
    caption = forms.CharField(label = "Caption", max_length = 200, required=False)
    media = forms.MultipleChoiceField(label = "Files", choices = []) # choices are defined on init
    layout = forms.ChoiceField(label="Layout", 
        choices = [("full_width", "Full width"), ("aside", "Inset (40% width")], initial="full_width")

    def __init__(self, question, *args, **kwargs):
        super(FigureTokenForm,self).__init__(*args, **kwargs)
        self.fields['media'].choices = [(f.pk, f.title) for f in question.files.filter(type="image")]


class BaseToken(object):

    def __init__(self, para, question, processor=None, above=False):
        self.para = para
        self.question = question
        self.data = {}
        self.above = above
        if not processor:
            processor = HTMLBlockProcessor
        self.processor = processor

    def update(self, **kwargs):
        self.data.update(kwargs)

    def render(self):
        html = self.get_html()
        para = self.para
        if self.above:
            fn = self.processor.insert_rendered_before
        else:
            fn = self.processor.insert_rendered_after
        self.question.text = fn(self.question.text, html, para)

    def get_html(self, txt):
        return "<div class=\"token\"><!--token-->" + txt + "<!--endtoken--></div>"


class FigureToken(BaseToken):

    def __init__(self, para, question, processor=None):
        super(FigureToken,self).__init__(para=para, 
            question=question, 
            processor=processor, 
            above=True)
    
    def form(self, *args, **kwargs):
        return FigureTokenForm(self.question, *args, **kwargs)

    def update(self, *args, **kwargs):
        super(FigureToken, self).update(*args, **kwargs)
        if 'layout' in kwargs and kwargs['layout'] == "full_width":
            self.above = False

    def get_html(self, txt=""):
        if not 'media' in self.data:
            return ""
        ftype = self.data.get("figure_type", "figure")
        if not ftype: 
            ftype = "figure"
        group_attrs = [ftype,]
        if 'layout' in self.data and self.data['layout']:
            style = self.data['layout']
            if style != "full_width":
                styles = set()
                styles.add("aside")
                styles.add("inline")
                styles.add(style)
                group_attrs.append(" ".join(styles) )
        group_content = ["[figure:local:%s]" % pk for pk in self.data['media']]
        if 'caption' in self.data and self.data['caption']:
            group_content.append(
                "[figcaption]%s[/figcaption]" % self.data['caption'])
        return super(FigureToken, self).get_html("[figgroup:%s]%s[/figgroup]" % (
            ":".join(group_attrs), 
            "".join(group_content) + txt))


class Token(object):

    @classmethod
    def processor_from_name(kls, nm):
        return eval(nm.capitalize() + "Processor")
    @classmethod
    def class_from_name(kls, nm):
        return eval(nm.capitalize() + "Token")

    @classmethod
    def create(kls, tp, para, question, *args, **kwargs):
        token_class = kls.class_from_name(tp)
        return token_class(para=para, question=question,
                           *args, **kwargs)