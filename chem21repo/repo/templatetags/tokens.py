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
from chem21repo.repo.tokens import *
from django import template
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.template.defaultfilters import striptags

register = template.Library()


class FigureRefProcessor(ContextProcessorMixin, BaseProcessor):
    @property
    def pattern(self):
        try:
            return self._pattern
        except AttributeError:
            self._pattern = re.compile(
                r'(example|Example|figure|Figure|scheme|Scheme|table|Table)\s+[0-9]+',
                re.DOTALL)
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
                r'%s%s(?P<%s_args>.*?)%s' % (self.openchar,
                                  self.token_name,
                                  self.name,
                                  self.closechar),
                re.DOTALL)
            return self._pattern

    def repl_function(self, match):
        args = match.group(self.name+"_args").split(":")
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

    def get_complex_tag_pattern(self):
        return None

    def create_token(self, question, para=None):
        name = self.tag_name
        return Token.create(name, question, para)
        
    def create_token_from_match(self, question, match, para=None):
        token = self.create_token(self, question, para)
        token.update(content = match.group('content'))

    @property
    def pattern(self):
        try:
            return self._simple_pattern
        except AttributeError:
            self._simple_pattern = re.compile(self.get_simple_tag_pattern(),
                re.DOTALL)
            return self._simple_pattern

    @property
    def complex_pattern(self):
        try:
            return self._complex_pattern
        except AttributeError:
            self._complex_pattern = re.compile(self.get_complex_tag_pattern(),
                re.DOTALL)
            return self._complex_pattern
    

    @abstractmethod
    def tag_function(self, st, *args):
        return None

    def repl_function(self, match):
        args = match.group(self.name+"_args").split(":")
        return self.tag_function(match.group('content'), *args)

class AttributionProcessor(ContextProcessorMixin, TagProcessor):
    tag_name="attrib"
    def tag_function(self, st, *args):
        html = "<p class=\"attrib\">%s</p>" % st
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
        if re.match(r"\s*<.*?p>", match.string[:match.start][::-1]):
            return "[ibib]%s[/ibib]" % bib.citekey
        else:
            return "[bib]%s[/bib]" % bib.citekey

class RSCRightsProcessor(ContextProcessorMixin, TagProcessor):
    tag_name="rsc"
    def tag_function(self, st, *args):
        rsc_template = template.loader.get_template("chem21/include/rsc_statement.html")
        cxt = {'content': st}
        cxt['tools'] = not self.context.get('staticgenerator', False)
        html = rsc_template.render(cxt)
        return html

class BiblioTagProcessor(ContextProcessorMixin, TagProcessor):
    tag_name = "bib"

    def __init__(self, request=None, *args, **kwargs):
        self.bibs = []
        self.bibset = {}
        return super(BiblioTagProcessor, self).__init__(*args, **kwargs)

    def tag_function(self, st, *args):
        try:
            bib = Biblio.objects.get(citekey=st)
        except Biblio.DoesNotExist:
            bib = Biblio(citekey=st)
            bib.save()
        if st not in self.bibset:
            self.bibs.append(bib)
            self.bibset[st] = len(self.bibs)
        return "<a href=\"#citekey_%d\">[%d]</a>" % (
            self.bibset[st], self.bibset[st])

    def _get_footnote_html(self, bib, id):
        html = bib.get_footnote_html()
        if html == False:
            try:
                messages.add_message(self.request, 
                    messages.ERROR, 
                    "Could not find reference on this page with citekey '%s'." % bib.citekey)
            except AttributeError:
                pass
            html = "Unknown reference."
        if self.context['user'].is_authenticated() and ('staticgenerator' not in self.context or not self.context['staticgenerator']):
            url = reverse("admin:repo_biblio-power_change", 
                args = [bib.pk,])
            html += "<a href=\"%s\">%s</a>" % (url, "[edit]")
        return "<li id=\"citekey_%d\">%s</li>" % (
            id, html)

    def get_footnotes_html(self):
        return "\n".join(
            [self._get_footnote_html(bib, id)
             for id, bib in
             zip(
                range(1, len(self.bibs) + 1), self.bibs)])


class BiblioInlineTagProcessor(ContextProcessorMixin, TagProcessor):
    tag_name = "ibib"

    def tag_function(self, st, *args):
        try:
            bib = Biblio.objects.get(citekey=st)
        except Biblio.DoesNotExist:
            bib = Biblio(citekey=st)
            bib.save()
        html = bib.get_inline_html()
        if html == False:
            try:
                messages.add_message(self.request, 
                    messages.ERROR, 
                    "Could not find reference on this page with citekey '%s'." % bib.citekey)
            except AttributeError:
                pass
            html = "Unknown reference."
        return html

class GreenPrincipleTokenProcessor(ContextProcessorMixin, TokenProcessor):
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
        return ""
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
        self.context['pre_content'] = self.context.get('pre_content', "") + self.build_html(num_list)
        return ""

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

    def tag_function(self, st, *args):
        return "<figcaption>%s</figcaption>" % st

class TableCaptionTagProcessor(ContextProcessorMixin, TagProcessor):
    tag_name = "tabcaption"

    def tag_function(self, st, *args):
        return "<caption>%s</caption>" % st

class FigureGroupTagProcessor(ContextProcessorMixin, BlockToolMixin, TagProcessor):
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

    def block_tool_handle_html(self):
        return "[+Fig]"

    @property
    def block_tool_name(self):
        return "figure"

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

    def delete_tool(self):
        if self.context['user'].is_authenticated() and 'staticgenerator' not in self.context:
            return "<a data-fig-num=\"%s\" class=\"btn btn-success admin-delete delete-figure\">Delete figure</a>" % str(self.total_count)
        return "" 

    def tag_function(self, st, *args):
        self.inner_text = st
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
            self.inner_text = "<figure class=\"%s\">%s%s</figure>" % (
                classes, self.inner_text, self.delete_tool())
            if "aside" in class_set:
                if not "inline" in class_set:
                    self.asides.append(self.inner_text)
                    return ""
                else:
                    self.inner_text = "<aside>%s</aside>" % self.inner_text    
        return self.inner_text

    def get_asides_html(self):
        return "".join(map(lambda x: "<aside>%s</aside>" % x, self.asides))  


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

    def tag_function(self, st, *args):
        obj = ILinkTagProcessor.get_object(*[int(x) for x in args])
        if not obj:
            messages.add_message(self.request, 
                    messages.ERROR, 
                    "[ilink:%s] token not valid: cannot find object with this reference." % ":".join(args))
            return ""
        return "<a class=\"internal\" href=\"%s\">%s</a>" % (
            obj.get_absolute_url(), st)

class HideTagProcessor(ContextProcessorMixin, TagProcessor):
    tag_name = "hide"

    def get_simple_tag_pattern(self):
        return "<p>\s*%s\s*</p>" % super(HideTagProcessor, self).get_simple_tag_pattern()
    def tag_function(self, st, *args):
        return "<div class=\"hide_solution\"><p>%s</p></div>" % st


class FigureTokenProcessor(ContextProcessorMixin, TokenProcessor):
    token_name = "figure"

    def token_function(self, command, *args):
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
            title = ":".join(args[2:])
            if not fle:
                messages.add_message(self.request, 
                    messages.ERROR, 
                    "[figure] token not valid: cannot find file object with this %s id: %s" % (where, args[0]) )
                return ""
            title = striptags(title)
            logging.debug("Here is title %s" % title)
            return "<a href=\"%s\" title=\"%s\"><img src=\"%s\" alt=\"%s\" /></a>" % (fle.url, title, fle.url, alt)
        messages.add_message(self.request, 
                messages.ERROR, 
                "[figure] token not valid: must be either [figure:show:xx] or [figure:local:xx]" % (where, args[0]))
        return ""


class ReplaceTokensNode(template.Node):
    def __init__(self, text_field):
        self.text = template.Variable(text_field)

    def render(self, context):
        txt = self.text.resolve(context)
        request = context['request']
        processors = {
            'bibtex':BibTeXCiteProcessor(context=context),
            'ibib':BiblioInlineTagProcessor(context=context),
            'bib':BiblioTagProcessor(context=context),
            'ilink':ILinkTagProcessor(context=context),
            'cta':CTATokenProcessor(context=context),
            'rsc':RSCRightsProcessor(context=context),
            'attrib': AttributionProcessor(context=context),
            'green':GreenPrincipleTokenProcessor(context=context),
            'figref':FigureRefProcessor(context=context),
            'figure':FigureTokenProcessor(context=context),
            'figgroup':FigureGroupTagProcessor(context=context),
            'figcaption':FigCaptionTagProcessor(context=context),
            'tabcaption':TableCaptionTagProcessor(context=context),
            'hide':HideTagProcessor(context=context),
            'GHS_statement':GHSStatementProcessor(context=context)
            }
        decruft = re.compile(
                r'<div class="token"><!--token-->(.*?)<!--endtoken--></div>',
                re.DOTALL)



        txt = decruft.sub(lambda match: match.group(1), txt)
        proc_order = ['hide','bibtex','ibib','bib','ilink','rsc','attrib','cta','green',
                      'figref','figure','figgroup','figcaption','tabcaption','GHS_statement']
        for key in proc_order:
            txt = processors[key].apply(txt)
            if context['user'].is_authenticated() and ('staticgenerator' not in context or not context['staticgenerator']):
                try:
                    txt = processors[key].apply_block_tool(txt)
                except AttributeError, e:
                    pass
        sidebyside = re.compile(
            r'<figure class="stacked2.*?<figure class="stacked2.*?</figure>',
            re.DOTALL)

        txt = sidebyside.sub(lambda match: "<div class=\"sidebyside_figures\"%s<div class=\"clear\">&nbsp;</div></div>" % match.group(0), txt)
        context['footnotes_html'] = processors['bib'].get_footnotes_html()
        asides_html = processors['figgroup'].get_asides_html()
        asides_html = processors['figcaption'].apply(asides_html)
        context['pre_content'] = context.get('pre_content',"") + asides_html 
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
