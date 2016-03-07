import re

import logging

from abc import ABCMeta
from abc import abstractproperty
from abc import abstractmethod
from chem21repo.repo.models import Biblio
from chem21repo.repo.models import Lesson
from chem21repo.repo.models import Module
from chem21repo.repo.models import Question
from chem21repo.repo.models import Topic
from chem21repo.repo.models import UniqueFile
from django import template

register = template.Library()


class BaseProcessor:
    __metaclass__ = ABCMeta
    openchar = "\["
    closechar = "\]"

    @abstractproperty
    def pattern(self):
        return None

    @abstractmethod
    def repl_function(self, match):
        return None

    def apply(self, st):
        self.full_text = st
        return self.pattern.sub(self.repl_function, st)


class TokenProcessor(BaseProcessor):
    __metaclass__ = ABCMeta

    @abstractproperty
    def token_name(self):
        return None

    @abstractmethod
    def token_function(*args):
        return None

    @property
    def pattern(self):
        try:
            return self._pattern
        except AttributeError:
            self._pattern = re.compile(
                r'%s%s(.*?)%s' % (self.openchar,
                                  self.token_name,
                                  self.closechar),
                re.DOTALL)
            return self._pattern

    def repl_function(self, match):
        args = match.group(1).split(":")
        return self.token_function(*args[1:])


class TagProcessor(BaseProcessor):
    __metaclass__ = ABCMeta

    @abstractproperty
    def tag_name(self):
        return None

    @property
    def pattern(self):
        try:
            return self._pattern
        except AttributeError:
            self._pattern = re.compile(
                r'%s%s[:]?(.*?)%s(.*?)%s\/%s%s' % (
                    self.openchar, self.tag_name, self.closechar,
                    self.openchar, self.tag_name, self.closechar),
                re.DOTALL)
            return self._pattern

    @abstractmethod
    def tag_function(self, st, *args):
        return None

    def repl_function(self, match):
        logging.debug("Tag match")
        args = match.group(1).split(":")
        return self.tag_function(match.group(2), *args)


class BiblioTagProcessor(TagProcessor):
    tag_name = "bib"

    def __init__(self, *args, **kwargs):
        self.bibs = []
        self.bibset = set([])
        return super(BiblioTagProcessor, self).__init__(*args, **kwargs)

    def tag_function(self, st, *args):
        try:
            bib = Biblio.objects.get(citekey=st)
        except Biblio.DoesNotExist:
            bib = Biblio(citekey=st)
            bib.save()
        if st not in self.bibset:
            self.bibs.append(bib)
            self.bibset.add(st)
        return "<a href=\"#citekey_%d\">[%d]</a>" % (
            len(self.bibs), len(self.bibs))

    def _get_footnote_html(self, bib, id):
        return "<li id=\"citekey_%d\">%s</li>" % (
            id, bib.get_footnote_html())

    def get_footnotes_html(self):
        return "\n".join(
            [self._get_footnote_html(bib, id)
             for id, bib in
             zip(
                range(1, len(self.bibs) + 1), self.bibs)])


class BiblioInlineTagProcessor(TagProcessor):
    tag_name = "ibib"

    def tag_function(self, st, *args):
        try:
            bib = Biblio.objects.get(citekey=st)
        except Biblio.DoesNotExist:
            bib = Biblio(citekey=st)
            bib.save()
        return bib.get_inline_html()

class GreenPrincipleTokenProcessor(TokenProcessor):
    token_name = "greenprinciple"
    principles = [
        {'title': 'Prevention',
         'description': ''
         },
        {'title': 'Atom economy',
         'description': ''
         },
        {'title': 'Less hazardous chemical syntheses',
         'description': ''
         },
        {'title': 'Designing safer chemicals',
         'description': ''
         },
        {'title': 'Safer solvents and auxiliaries',
         'description': ''
         },
        {'title': 'Design for energy efficiency',
         'description': ''
         },
        {'title': 'Use of renewable feedstocks',
         'description': ''
         },
        {'title': 'Reduce derivatives',
         'description': ''
         },
        {'title': 'Catalysis',
         'description': ''
         },
        {'title': 'Design for degradation',
         'description': ''
         },
        {'title': 'Real-time analysis for pollution prevention',
         'description': ''
         },
        {'title': 'Inherently safer chemistry for accident prevention',
         'description': ''
         },
    ]

    def build_html(self, num_list):
        out = "<ol class=\"green_principles\">"
        num = 1
        for principle in self.principles:
            active_cls = ""
            if num in num_list:
                active_cls = " active"
            out += "<li class=\"%s%s\">%s</li>" % (
                "p" + str(num), active_cls, principle['title'])
            num += 1
        out += "</ol>"
        return out

    def token_function(self, *args):
        num_list = []
        try:
            command = args[0]
        except IndexError:
            return
        if command == "show":
            try:
                num_list = [int(x) for x in args[1:]]
            except IndexError:
                num_list = range(1, 12)
        return self.build_html(num_list)


class FigCaptionTagProcessor(TagProcessor):
    tag_name = "figcaption"

    def tag_function(self, st, *args):
        return "<figcaption>%s</figcaption>" % st


class FigureGroupTagProcessor(TagProcessor):
    tag_name = "figgroup"

    def __init__(self, *args, **kwargs):
        self.count = {}
        return super(
            FigureGroupTagProcessor, self).__init__(
                *args, **kwargs)

    def inc_count(self, t):
        try:
            self.count[t] += 1
        except KeyError:
            self.count[t] = 1

    def get_count(self, t):
        try:
            return self.count[t]
        except KeyError:
            self.count[t] = 1
            return 1

    def get_type(self):
        t = "figure"
        return t

    def replace_caption_html(self, t):
        out = "<span class=\"figure_name\">%s %d</span>" % (
            t.capitalize(), self.get_count(t))
        (self.full_text, nsubs) = re.subn(
            r"\[figcaption\](.*?)\[\/figcaption\]",
            lambda m: "[figcaption]%s: %s[/figcaption]" % (out, m.group(1)),
            self.full_text
        )
        if not nsubs:
            self.full_text += "[figcaption]%s[/figcaption]" % out
        return out

    def tag_function(self, st, *args):
        self.full_text = st
        try:
            t = args[0]
        except IndexError:
            t = "figure"
        if not t:
            t = "figure"
        try:
            classes = " " + args[1]
        except IndexError:
            classes = ""
        if not classes:
            classes = ""
        self.replace_caption_html(t)
        self.inc_count(t)
        return "<figure class=\"inline%s\">%s</figure>" % (
            classes, self.full_text)


class SurroundFiguresTokenProcessor(TokenProcessor):
    token_name = "figure"

    def token_function(self, *args):
        joinargs = ("figure", ) + args
        return "[figgroup][figure%s][/figgroup]" % ":".join(joinargs)

    def repl_function(self, match):
        _super = super(SurroundFiguresTokenProcessor, self).repl_function
        print match.group(0)
        self.is_matched = 1
        remainder = self.full_text[match.end():]
        endfiggroup = re.search("\[\/figgroup\]", remainder)
        if endfiggroup:
            startfiggroup = re.search("\[figgroup\]", remainder)
            try:
                if startfiggroup.start() < endfiggroup.start():
                    return _super(match)
                else:
                    # leave alone
                    return match.group(0)
            except AttributeError:
                # leave alone
                return match.group(0)
        return _super(match)


class LinkMixin:
    @classmethod
    def get_object(cls, *args):
        try:
            topic = Topic.objects.get(pk=args[0])
            obj = topic
        except IndexError:
            pass
        try:
            module = Module.objects.get(pk=args[1])
            obj = module
        except IndexError:
            pass
        try:
            lesson = Lesson.objects.get(pk=args[2])
            obj = lesson
            obj.current_module = module
        except IndexError:
            pass
        try:
            question = Question.objects.get(pk=args[3])
            obj = question
            obj.current_lesson = lesson
            obj.current_module = module
        except IndexError:
            pass
        return obj


class CTATokenProcessor(LinkMixin, TokenProcessor):
    token_name = "cta"

    def token_function(self, *args):
        obj = CTATokenProcessor.get_object(*[int(x) for x in args])
        return "<p class=\"cta\">To study this area in more depth, see <a href=\"%s\"><span class=\"subject_title\">%s</span></a></p>" % (
                obj.get_absolute_url(), obj.title)


class ILinkTagProcessor(LinkMixin, TagProcessor):
    tag_name = "inlink"

    def tag_function(self, st, *args):
        obj = ILinkTagProcessor.get_object(*[int(x) for x in args])
        return "<a class=\"internal\" href=\"%s\">%s</a>" % (
            obj.get_absolute_url(), st)


class FigureTokenProcessor(TokenProcessor):
    token_name = "figure"

    def token_function(self, command, *args):
        if command == "show" or command == "local":
            if command == "show":
                fle = UniqueFile.objects.get(remote_id=args[0])
            else:
                fle = UniqueFile.objects.get(pk=args[0])
            try:
                alt = args[1]
            except IndexError:
                alt = ""
            return "<img src=\"%s\" alt=\"%s\" />" % (fle.url, alt)


class ReplaceTokensNode(template.Node):
    def __init__(self, text_field):
        self.text = template.Variable(text_field)

    def render(self, context):
        txt = self.text.resolve(context)
        simple_processors = [
            FigureTokenProcessor(), FigureGroupTagProcessor(
            ), FigCaptionTagProcessor(),
            BiblioInlineTagProcessor(),
            ILinkTagProcessor(),
            CTATokenProcessor(),
            GreenPrincipleTokenProcessor()]
        for proc in simple_processors:
            txt = proc.apply(txt)
        btag_proc = BiblioTagProcessor()
        txt = btag_proc.apply(txt)
        context['footnotes_html'] = btag_proc.get_footnotes_html()
        context['tokens_replaced'] = txt
        return ""


@register.tag(name="replace_tokens")
def do_replace_tokens(parser, token):
    try:
        tag_name, text_field = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly one argument" % token.contents.split()[
                0]
        )
    return ReplaceTokensNode(text_field)
