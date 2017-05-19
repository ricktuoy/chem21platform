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
from chem21repo.repo.shortcodes.processors import HTMLShortcodeProcessor

from django import template
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.template.defaultfilters import striptags


from ..tokens import Token

register = template.Library()


class FigureRefProcessor(ContextProcessorMixin, BaseProcessor):
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


class TokenProcessor(BaseProcessor):
    __metaclass__ = ABCMeta

    @abstractproperty
    def token_name(self):
        return None

    @property
    def name(self):
        return self.token_name

    @abstractmethod
    def token_function(*args):
        return None

    @property
    def pattern(self):
        try:
            return self._pattern
        except AttributeError:
            self._pattern = re.compile(
                r'(?<!\<\!\-\-token\-\-\>)%s%s(?P<%s_args>.*?)%s' %
                (self.openchar,
                    self.token_name,
                    self.name,
                    self.closechar),
                re.DOTALL)
            return self._pattern

    def repl_function(self, match):
        args = match.group(self.name + "_args").split(":")
        return self.token_function(*args[1:])


class TagProcessor(BaseProcessor):
    __metaclass__ = ABCMeta

    @abstractproperty
    def tag_name(self):
        return None

    @property
    def name(self):
        return self.tag_name

    def get_simple_tag_pattern(self):
        return self.get_inner_tag_pattern(self.name, '(?P<content>.*?)')

    @property
    def pattern(self):
        try:
            return self._simple_pattern
        except AttributeError:
            self._simple_pattern = re.compile(
                self.get_simple_tag_pattern(),
                re.DOTALL)
            return self._simple_pattern

    @abstractmethod
    def tag_function(self, content, *args):
        return None

    

    def repl_function(self, match):
        args = match.group(self.name + "_args").split(":")
        return self.tag_function(match.group('content'), *args)


class AttributionProcessor(ContextProcessorMixin, TagProcessor):
    tag_name="attrib"
    def tag_function(self, content, *args):
        html = "<p class=\"attrib\">%s</p>" % content
        return html

class BibTeXCiteProcessor(ContextProcessorMixin, BaseProcessor):
    openchar = r"\\cite\{"
    closechar = r"\}"
    name = u"bibcite"
    @property
    def pattern(self):
        try:
            return self._pattern
        except AttributeError:
            self._pattern = re.compile(
                r'%s(?P<bibkey>.*?)%s' % (self.openchar,
                                  self.closechar),
                re.DOTALL)
            return self._pattern

    def repl_function(self, match):
        bibkey = match.group('bibkey').lower()
        try:
            bib = Biblio.objects.get(bibkey=bibkey)
        except Biblio.DoesNotExist:
            try:
                bib = Biblio(bibkey=bibkey, citekey=bibkey)
                bib.save()
            except IntegrityError:
                bib = Biblio.objects.get(citekey=bibkey)
                bib.bibkey = bibkey
                bib.save()
        
        if re.match(r"\s*>.*?p<", match.string[:match.start()][::-1]):
            return "[ibib]%s[/ibib]" % bib.citekey
        else:
            return "[bib]%s[/bib]" % bib.citekey


class RSCRightsProcessor(ContextProcessorMixin, TagProcessor):
    tag_name="rsc"
    def tag_function(self, content, *args):
        rsc_template = template.loader.get_template("chem21/include/rsc_statement.html")
        cxt = {'content': content}
        cxt['tools'] = not self.context.get('staticgenerator', False)
        html = rsc_template.render(cxt)
        return html


class BiblioTagProcessor(
        ContextProcessorMixin,
        TagProcessor):
    tag_name = "bib"

    def __init__(self, request=None, *args, **kwargs):
        self.bibs = []
        self.bibset = {}
        return super(BiblioTagProcessor, self).__init__(*args, **kwargs)

    def tag_function(self, content, *args):
        try:
            bib = Biblio.objects.get(citekey=content)
        except Biblio.DoesNotExist:
            bib = Biblio(citekey=content)
            bib.save()
        if content not in self.bibset:
            self.bibs.append(bib)
            self.bibset[content] = len(self.bibs)
        return "<a href=\"#citekey_%s_%d\">[%d]</a>" % (
            content, self.bibset[content], self.bibset[content])

    def _get_footnote_html(self, bib, id):
        html = bib.get_footnote_html()
        if html is False:
            try:
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    "Could not find reference on this page with citekey '%s'."
                    % bib.citekey)
            except AttributeError:
                pass
            html = "Unknown reference."
        if self.context['user'].is_authenticated() and (
                'staticgenerator' not in self.context or not
                self.context['staticgenerator']):
            url = reverse(
                "admin:repo_biblio-power_change",
                args=[bib.pk, ])
            html += "<a href=\"%s\">%s</a>" % (url, "[edit]")
        return "<li id=\"citekey_%s_%d\">%s</li>" % (
            bib.citekey, self.bibset[bib.citekey], html)

    def get_footnotes_html(self):
        return "\n".join(
            [self._get_footnote_html(bib, id)
             for id, bib in
             zip(
                range(1, len(self.bibs) + 1), self.bibs)])


class BiblioInlineTagProcessor(ContextProcessorMixin, TagProcessor):
    tag_name = "ibib"

    def tag_function(self, content, *args):
        try:
            bib = Biblio.objects.get(citekey=content)
        except Biblio.DoesNotExist:
            bib = Biblio(citekey=content)
            bib.save()
        html = bib.get_inline_html()
        if html is False:
            try:
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    "Could not find reference on this page with citekey '%s'."
                    % bib.citekey)
            except AttributeError:
                pass
            html = "Unknown reference."
        return html

class GHSStatementProcessor(ContextProcessorMixin, TokenProcessor):
    token_name = "GHS_statement"
    def token_function(self, *args):
        try:
            num = args[0]
        except IndexError:
            return
        symbol_name = "symbol"
        url = static("img/ghs/symbol_%s.png" % num)
        return "<img src=\"%s\" alt=\"GHS symbol: %s\" class=\"ghs_symbol\" />" % (
            url, symbol_name)


class FigCaptionTagProcessor(ContextProcessorMixin, TagProcessor):
    tag_name = "figcaption"

    def tag_function(self, content, *args):
        return "<figcaption>%s</figcaption>" % content

class TableCaptionTagProcessor(ContextProcessorMixin, TagProcessor):
    tag_name = "tabcaption"

    def tag_function(self, content, *args):
        return "<caption>%s</caption>" % content

class FigureGroupProcessor(ContextProcessorMixin, TagProcessor):
    tag_name = "figgroup"

    def __init__(self, *args, **kwargs):
        self.count = {}
        self.asides = []
        self.total_count = 0
        return super(
            FigureGroupTagProcessor, self).__init__(
                *args, **kwargs)

    def inc_count(self, t):
        try:
            self.count[t] += 1
        except KeyError:
            self.count[t] = 1
        self.total_count += 1

    def get_count(self, t):
        try:
            return self.count[t]
        except KeyError:
            self.count[t] = 1
            return 1

    def get_type(self):
        t = "figure"
        return t

    @property
    def caption_regex(self):
        return r"\[figcaption\](.*?)\[\/figcaption\]"

    def get_name(self, t):
        return "%s %d" % (t.capitalize(), self.get_count(t))

    def replace_caption_html(self, t):
        matches = []
        a_title = None
        title_regex = r'(<a[^>]*?)title=\".*?\"'
        figtitle = "<span class=\"figure_name\">%s</span>" % self.get_name(t)
        for match in re.finditer(self.caption_regex, self.inner_text):
            self.inner_text = self.inner_text.replace(match.group(0), "")
            if not a_title:
                a_title = "%s: %s" % (self.get_name(t), match.group(1))
            matches.append("%s%s: %s%s" % 
                (self.start_caption_tag, figtitle, match.group(1), self.end_caption_tag))
        a_title = striptags(a_title)
        self.inner_text = re.sub(title_regex, "\g<1>title=\"%s\"" % a_title, self.inner_text)
        if len(matches):
            repl = "".join(matches)
        else:
            repl = "%s%s%s" % (self.start_caption_tag, figtitle, self.end_caption_tag)
        if t == "table":
            self.inner_text = re.sub(r"<table(.*?)>", "\g<0>%s" % repl, self.inner_text)
        else:
            self.inner_text += repl


    def tag_function(self, content, *args):
        self.inner_text = content
        try:
            t = args[0]
        except IndexError:
            t = "figure"
        if not t:
            t = "figure"
        try:
            class_set = frozenset(args[1].split(" "))
        except IndexError:
            class_set = frozenset([])
        if t != "table":
            self.start_caption_tag = "[figcaption]"
            self.end_caption_tag = "[/figcaption]"
        else:
            self.start_caption_tag = "<caption>"
            self.end_caption_tag = "</caption>"
        class_set = class_set | frozenset(["inline"])
        classes = " ".join(class_set)
        self.replace_caption_html(t)
        self.inc_count(t)

        if t != "table":
            self.inner_text = "<figure class=\"%s\">%s</figure>" % (
                classes, self.inner_text)
            if "aside" in class_set:
                if not "inline" in class_set:
                    self.asides.append(self.inner_text)
                    return ""
                else:
                    self.inner_text = "<aside>%s</aside>" % self.inner_text
        return self.inner_text

    def get_asides_html(self):
        return "".join(
            map(lambda x: "<aside>%s</aside>" % x, self.asides))


class SurroundFiguresTokenProcessor(ContextProcessorMixin, TokenProcessor):
    token_name = "figure"

    def token_function(self, *args):
        joinargs = ("figure", ) + args
        return "[figgroup][figure%s][/figgroup]" % ":".join(joinargs)

    def repl_function(self, match):
        _super = super(SurroundFiguresTokenProcessor, self).repl_function
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


class CTATokenProcessor(ContextProcessorMixin, LinkMixin, TokenProcessor):
    token_name = "cta"

    def token_function(self, *args):
        if not args:
            messages.add_message(self.request, 
                    messages.ERROR, 
                    "[cta] token not valid: needs object reference (e.g. [cta:1:2:3] ).")
            return ""
        obj = CTATokenProcessor.get_object(*[int(x) for x in args])
        if not obj:
            messages.add_message(self.request, 
                    messages.ERROR, 
                    "[cta:%s] token not valid: cannot find object with this reference." % ":".join(args))
            return ""
        return "<p class=\"cta\">To study this area in more depth, see <a href=\"%s\"><span class=\"subject_title\">%s</span></a></p>" % (
                obj.get_absolute_url(), obj.title)


class ILinkTagProcessor(ContextProcessorMixin, LinkMixin, TagProcessor):
    tag_name = "inlink"

    def tag_function(self, content, *args):
        obj = ILinkTagProcessor.get_object(*[int(x) for x in args])
        if not obj:
            messages.add_message(
                self.request,
                messages.ERROR,
                "[ilink:%s] token not valid: cannot find object with this reference." % ":".join(args))
            return ""
        return "<a class=\"internal\" href=\"%s\">%s</a>" % (
            obj.get_absolute_url(), content)

class HideTagProcessor(ContextProcessorMixin, TagProcessor):
    tag_name = "hide"

    def get_simple_tag_pattern(self):
        return "<p>\s*%s\s*</p>" % super(
            HideTagProcessor, self).get_simple_tag_pattern()

    def tag_function(self, content, *args):
        return "<div class=\"hide_solution\"><p>%s</p></div>" % content


class FigureTokenProcessor(ContextProcessorMixin, TokenProcessor):
    token_name = "figure"

    @staticmethod
    def get_token(self, command, pk, alt="", *args):
        if command == "show":
            fle = UniqueFile.objects.get(remote_id=args[0])
            where = "remote"
        elif command == "local":
            fle = UniqueFile.objects.get(pk=args[0])
            where = "local"
        else:
            raise TokenValidationError(
                "Format must be either [figure:show:xx] or [figure:local:xx]")
        if not fle:
            raise TokenValidationError(
                "Cannot find %s file object with id %s" % (
                    where, args[0]))

        token = FigureToken(
            file_obj=fle,
            alt=alt,
            title=striptags(":".join(args)))
        return token

    @staticmethod
    def get_html(self, token):
        return "<a href=\"%s\" title=\"%s\"><img src=\"%s\" alt=\"%s\" /></a>" % (
            token.url,
            token.title,
            token.url,
            token.alt)

    def token_function(self, command, id, alt="", *args):
        if command == "show" or command == "local":
            if command == "show":
                fle = UniqueFile.objects.get(remote_id=args[0])
                where = "remote"
            else:
                fle = UniqueFile.objects.get(pk=args[0])
                where = "local"
            try:
                alt = args[1]
            except IndexError:
                alt = ""
            title = striptags(":".join(args))
            if not fle:
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    "[figure] token not valid: cannot find file object with this %s id: %s" % (
                        where, args[0]))
                return ""

        messages.add_message(
            self.request,
            messages.ERROR,
            "[figure] token not valid: " % (
                where, args[0]))
        return ""

class ReplaceShortcodesNode(template.Node):
    def __init__(self, text_field):
        self.text = template.Variable(text_field)

    def render(self, context):
        txt = self.text.resolve(context)
        if not txt:
            context['footnotes_html'] = ''
            context['pre_content'] = ''
            context['tokens_replaced'] = ''
            return ""
        processor = HTMLShortcodeProcessor(txt, context=context)
        context['tokens_replaced'] = processor.replace_shortcodes_with_html()
        context = processor.update_context()
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
