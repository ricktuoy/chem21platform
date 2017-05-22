from ..models.biblio import Biblio
from ..models.scos import Lesson
from ..models.scos import Module
from ..models.scos import Question
from ..models.scos import Topic
from .base import TagShortcodeProcessor
from .base import TokenShortcodeProcessor
from .errors import ShortcodeValidationError
from .parser import HTMLShortcodeParser
from .renderers import AttributionRenderer
from .renderers import BlockReferenceRenderer
from .renderers import CTARenderer
from .renderers import FigureGroupRenderer
from .renderers import FigureRenderer
from .renderers import FootnoteReferenceRenderer
from .renderers import InternalLinkRenderer
from .renderers import TableRenderer
from .renderers import RSCRightsRenderer
from .renderers import GHSStatementRenderer
from ..models.base import UniqueFile
from django.utils.html import strip_tags


class FigureProcessor(TokenShortcodeProcessor):
    name = "figure"
    renderer = FigureRenderer

    def renderer_args(self, command, pk, alt="", *args):
        if command == "show":
            fle = UniqueFile.objects.get(remote_id=args[0])
            where = "remote"
        elif command == "local":
            fle = UniqueFile.objects.get(pk=args[0])
            where = "local"
        else:
            raise ShortcodeValidationError(
                "Format must be either [figure:show:xx] or [figure:local:xx]")
        if not fle:
            raise ShortcodeValidationError(
                "Cannot find %s file object with id %s" % (
                    where, pk))

        return [], {
            'file_obj': fle,
            'alt': alt,
            'title': strip_tags(":".join(args))}


class CaptionProcessor(TagShortcodeProcessor):
    name = "caption"
    renderer = lambda caption: caption 

    def renderer_args(self, caption):
        return [caption, ], {}


class FigureGroupProcessor(TagShortcodeProcessor):
    name = "figgroup"
    renderer = FigureGroupRenderer

    def renderer_args(self, content, group_type="figure", layout=""):
        figures = FigureProcessor(content).renderers()
        captions = CaptionProcessor(content).renderers()
        layouts_set = frozenset(layout.split(" "))
        return [], {
            'figures': figures,
            'captions': captions,
            'group_type': group_type,
            'layout': list(layouts_set)}


class TableProcessor(TagShortcodeProcessor):
    name = "table"
    renderer = TableRenderer

    def renderer_args(self, content, container_type, layout=""):
        captions = CaptionProcessor(content).renderers()
        html = HTMLShortcodeParser(content).remove_block_shortcodes()
        layouts_set = frozenset(layout.split(" "))
        return [], {
            'layout': list(layouts_set),
            'captions': captions,
            'html': html}


class BiblioFootnoteProcessor(TagShortcodeProcessor):
    name = "bib"
    renderer = FootnoteReferenceRenderer

    def __init__(self):
        self.bibs = []
        self.bibset = {}
        return super(BiblioFootnoteProcessor, self).__init__()

    def renderer_args(self, content):
        try:
            bib = Biblio.objects.get(citekey=content)
        except Biblio.DoesNotExist:
            bib = Biblio(citekey=content)
            bib.save()
        if content not in self.bibset:
            self.bibs.append(bib)
            self.bibset[content] = len(self.bibs)

        return [], {
            'bib': bib,
            'position': self.bibset[content]}


class BiblioBlockProcessor(TagShortcodeProcessor):
    name = "ibib"
    renderer = BlockReferenceRenderer

    def renderer_args(self, content):
        try:
            bib = Biblio.objects.get(citekey=content)
        except Biblio.DoesNotExist:
            bib = Biblio(citekey=content)
            bib.save()
        return [], {'bib': bib}


class PageMixin(object):
    def _get_page(self, *pks):
        obj = None
        try:
            topic = Topic.objects.get(pk=pks[0])
            obj = topic
        except IndexError:
            pass
        try:
            module = Module.objects.get(pk=pks[1])
            obj = module
        except IndexError:
            pass
        try:
            lesson = Lesson.objects.get(pk=pks[2])
            obj = lesson
            obj.current_module = module
        except IndexError:
            pass
        try:
            question = Question.objects.get(pk=pks[3])
            obj = question
            obj.current_lesson = lesson
            obj.current_module = module
        except IndexError:
            pass
        return obj


class InternalLinkProcessor(PageMixin, TagShortcodeProcessor):
    name = "ilink"
    renderer = InternalLinkRenderer

    def renderer_args(self, content, *page_pks):
        return [], {
            'page': self._get_page(*[int(x) for x in page_pks]),
            'inner_html': content}


class CTAProcessor(TokenShortcodeProcessor):
    name = "cta"
    renderer = CTARenderer

    def renderer_args(self, *page_pks):
        return [], {
            'page': self._get_page(*[int(x) for x in page_pks])
        }


class AttributionProcessor(TagShortcodeProcessor):
    tag_name = "attrib"
    renderer = AttributionRenderer

    def renderer_args(self, content):
        return [], {
            'inner_html': content
        }


class GHSStatementProcessor(TokenShortcodeProcessor):
    name = "GHS_statement"
    renderer = GHSStatementRenderer

    def renderer_args(self, num):
        return [], {
            'num': num
        }


class RSCRightsProcessor(TagShortcodeProcessor):
    name = "rsc"
    renderer = RSCRightsRenderer

    def renderer_args(self, content, *args):
        return [], {
            'inner_html': content
        }
