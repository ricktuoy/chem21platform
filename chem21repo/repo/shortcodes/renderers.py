from .base import BaseShortcodeRenderer
from .base import TagShortcodeRenderer
from .base import TokenShortcodeRenderer
from .forms import FigureGroupForm
from .forms import TableForm
from django.core.urlresolvers import reverse
from django.contrib.staticfiles.templatetags.staticfiles import static
from django import template


class FigureGroupRenderer(TagShortcodeRenderer):
    name = "figgroup"

    def __init__(
            self,
            figures=[],
            captions=[],
            layout=set(),
            group_type="figure"):
        self.figures = figures
        self.styles = set(layout)
        if layout:
            if "stacked2" not in layout:
                self.styles.add("inline")
            if "full_width" in layout:
                self.styles.remove("full_width")
        self.group_type = group_type

    def get_form(self, question, *args, **kwargs):
        return FigureGroupForm(question, *args, **kwargs)

    def get_html(self):
        if self._is_hero():
            return ""
        classes = " ".join(self.styles)
        out = "".join(self._children_html())
        out += "<figure class=\"%s\">%s</figure>" % (
            classes, out)
        if not self._is_hero() and "inline" in self.styles:
            return "<aside>%s</aside>" % out

    def update_extra_html_snippets(self, html_snippets):
        if not self._is_hero():
            return
        try:
            html_snippets['pre_content'] += self.get_html()
        except KeyError:
            html_snippets['pre_content'] = self.get_html()

    def shortcode_args(self):
        layout = " ".join(self.layout)
        group_type = self.group_type
        return [group_type, layout]

    def shortcode_content(self):
        figure_content = "".join(
            [f.get_shortcode() for f in self.figures])
        caption_content = "".join(
            [c.get_shortcode() for c in self.captions])
        return "%s%s" % (figure_content, caption_content)

    def _is_hero(self):
        if "aside" not in self.styles and "inline" not in self.styles:
            return True
        return False

    def _children_html(self):
        for figure in self.figures:
            yield figure.get_html()
        for caption in self.captions:
            yield "<figcaption>%s</figcaption>" % caption


class TableRenderer(TagShortcodeRenderer):
    name = "table"

    def __init__(
            self,
            caption="",
            html="",
            table_type="table"):
        super(TableRenderer, self).__init__(caption)

        self.table_html = html
        self.table_type = table_type

    def get_form(self, question, *args, **kwargs):
        return TableForm(question, *args, **kwargs)

    def get_html(self):
        caps = "".join(
            ["<caption>%s</caption>" % c for c in self.captions])
        return caps + self.table_html

    def shortcode_args(self):
        layout = " ".join(self.layout)
        group_type = self.group_type
        return [group_type, layout]

    def shortcode_content(self):
        """ Returns text content of the table shortcode, made up of
        caption shortcodes and the table html """
        caption_content = "".join(
            [c.get_shortcode() for c in self.captions])
        return "%s%s" % (caption_content, self.html)


class FigureRenderer(TokenShortcodeRenderer):
    name = "figure"

    def __init__(self, file_obj, alt="", title=""):
        self.alt = alt
        self.title = title
        self.url = file_obj.get_absolute_url()

    def shortcode_args(self):
        command = "local"
        pk = self.file_obj.pk
        alt = self.alt
        title = self.title
        return [command, pk, alt, title]

    def get_html(self):
        return "<a href=\"%s\" title=\"%s\"><img src=\"%s\" alt=\"%s\" /></a>" % (
            self.url,
            self.title,
            self.url,
            self.alt)


class BiblioMixin(object):

    def _reference_html(self):
        html = self.bib.get_footnote_html()
        if html is False:
            html = "Unknown reference with citekey %s" % self.bib.citekey

        if self.edit:
            url = reverse(
                "admin:repo_biblio-power_change",
                args=[bib.pk, ])
            html += "<a href=\"%s\">%s</a>" % (url, "[edit]")
        return html


class FootnoteReferenceRenderer(BiblioMixin, BaseShortcodeRenderer):
    name = "bib"
    positions = {}

    def __init__(self, bib, position, edit=False):
        self.bib = bib
        try:
            self.position = self.positions[self.bib.citekey]
        except KeyError:
            self.positions[self.bib.citekey] = self.position = \
                len(self.positions) + 1
        self.edit = edit

    def get_html(self):
        return "<a href=\"#citekey_%s_%d\">[%d]</a>" % (
            self.bib.citekey, self.position, self.position)

    def update_extra_html_snippets(self, html_snippets):
        html_snippets['footnotes'] += "<li id=\"citekey_%s_%s\">%s</li>" % (
            self.bib.citekey, self.position, self._reference_html())


class BlockReferenceRenderer(BiblioMixin, BaseShortcodeRenderer):
    name = "ibib"

    def __init__(self, bib, edit=False):
        self.bib = bib
        self.edit = edit

    def get_html(self):
        return self._reference_html()


class InternalLinkRenderer(BaseShortcodeRenderer):
    name = "ilink"

    def __init__(self, inner_html, page):
        self.page = page
        self.inner_html = inner_html

    def get_html(self):
        return "<a class=\"internal\" href=\"%s\">%s</a>" % (
            self.page.get_absolute_url(), self.inner_html)


class CTARenderer(BaseShortcodeRenderer):
    name = "cta"

    def __init__(self, page):
        self.page = page

    def get_html(self):

        return "<p class=\"cta\">To study this area in more depth, see <a href=\"%s\"><span class=\"subject_title\">%s</span></a></p>" % (
            self.page.get_absolute_url(), self.page.title)


class AttributionRenderer(BaseShortcodeRenderer):
    name = "attrib"

    def get_html(self, inner_html):
        html = "<p class=\"attrib\">%s</p>" % inner_html
        return html


class GHSStatementRenderer(BaseShortcodeRenderer):
    name = "GHS_statement"

    def get_html(self, num):
        url = static("img/ghs/symbol_%s.png" % num)
        return "<img src=\"%s\" alt=\"GHS symbol\" class=\"ghs_symbol\" />" %  url


class RHSRightsRenderer(BaseShortcodeRenderer):
    name = "rsc"

    def get_html(self, content):
        rsc_template = template.loader.get_template(
            "chem21/include/rsc_statement.html")
        cxt = {'content': content}
        cxt['tools'] = False
        html = rsc_template.render(cxt)
        return html