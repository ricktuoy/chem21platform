import re

from django import template
from django.template.defaultfilters import stringfilter
from abc import ABCMeta, abstractproperty, abstractmethod
from chem21repo.repo.models import Biblio, UniqueFile

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
        return re.sub(self.pattern, self.repl_function, st)


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
        return r'%s%s(.*?)%s' % (self.openchar,
                                 self.token_name, self.closechar)

    def repl_function(self, match):
        return None
        args = match.group(1).split(":")
        return self.token_function(*args[1:])


class TagProcessor(BaseProcessor):
    __metaclass__ = ABCMeta

    @abstractproperty
    def tag_name(self):
        return None

    @property
    def pattern(self):
        return r'%s%s%s(.*?)%s\/%s%s' % (self.openchar, self.tag_name, self.closechar,
                                         self.openchar, self.tag_name, self.closechar)

    @abstractmethod
    def tag_function(self, st):
        return None

    def repl_function(self, match):
        return self.tag_function(match.group(1))


class BiblioTagProcessor(TagProcessor):
    tag_name = "bib"

    def __init__(self):
        self.bibs = []
        return super(BiblioTagProcessor, self).__init__()

    def tag_function(self, st):
        try:
            bib = Biblio.objects.get(citekey=st)
        except Biblio.DoesNotExist:
            bib = Biblio(citekey=st)
            bib.save()
        self.bibs.append(bib)
        return "<a href=\"#citekey_%s\">[%d]</a>" % (st, len(self.bibs))

    def _get_footnote_html(self, bib):
        return "<li id=\"#citekey_%s\">%s</li>" % (
            bib.citekey, bib.get_footnote_html())

    def get_footnotes_html(self):
        return "<ol class=\"footnotes\">%s</ol>" % "\n".join(
            [self._get_footnote_html(bib) for bib in self.bibs])

    def apply(self, st):
        st = super(BiblioTagProcessor, self).apply(st)
        return st + "<hr />" + self.get_footnotes_html()


class BiblioInlineTagProcessor(TagProcessor):
    tag_name = "ibib"

    def tag_function(self, st):
        try:
            bib = Biblio.objects.get(citekey=st)
        except Biblio.DoesNotExist:
            bib = Biblio(citekey=st)
        return bib.get_inline_html()

class FigureTokenProcessor(TokenProcessor):
    token_name = "figure"

    def token_function(self, command, *args):
        if command == "show":
            fle = UniqueFile.objects.get(remote_id=args[0])
            try:
                alt = args[1]
            except IndexError:
                alt = ""
            return "<img src=\"%s\" alt=\"%s\" />" % (fle.url, alt)


@register.filter
@stringfilter
def replace_tokens(st):
    _registered_processors = [
        BiblioTagProcessor, BiblioInlineTagProcessor, FigureTokenProcessor]
    for processor in _registered_processors:
        st = processor().apply(st)
    return st
