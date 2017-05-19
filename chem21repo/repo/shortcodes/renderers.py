from .errors import *
from abc import ABCMeta
from abc import abstractmethod


class BaseShortcodeRenderer(object):
    openchar = "["
    closechar = "]"

    __metaclass__ = ABCMeta

    @abstractmethod
    def to_html(self, obj):
        """ returns rendered HTML """
        pass

    @abstractmethod
    def to_shortcode(self):
        """ returns rendered shortcode text """
        pass

    def shortcode_html(inner_html):
        """ decorator that wraps shortcodes in placeholder html """
        def wrap(self):
            out = "<div class=\"shortcode\"><!--shortcode-->"
            out += inner_html(self)
            out += "<!--end_shortcode--></div>"
            return out
        return wrap
    shortcode_html = staticmethod(shortcode_html)


class TagShortcodeRenderer(object):

    __metaclass__ = ABCMeta

    @BaseShortcodeRenderer.shortcode_html
    def to_shortcode(self):
        """ returns string of complete shortcode block"""
        args = self._arg_list()
        return "%s%s%s%s%s%s%s%s/%s" % (
            self.openchar,
            self.name,
            ":" if len(args > 0) else "",
            ":".join(self._to_arg_list()),
            self.closechar,
            self._content(),
            self.openchar,
            self.name,
            self.closechar)

    @abstractmethod
    def _to_arg_list(self):
        """ returns ordered list of properties
        to be output in shortcode tag """
        pass

    @abstractmethod
    def _content():
        """ returns text to display between opening and closing
        tags of shortcode """
        pass


class TokenShortcodeRenderer(object):

    __metaclass__ = ABCMeta

    @BaseShortcodeRenderer.shortcode_html
    def to_shortcode(self):
        """ returns string of complete shortcode block"""
        args = self.renderer_to_arg_list(obj)
        return "%s%s%s%s%s" % (
            self.openchar,
            self.name,
            ":" if len(args > 0) else "",
            ":".join(self._to_arg_list()),
            self.closechar)

    @abstractmethod
    def _to_arg_list(self):
        """ returns ordered list of properties
        to be output in shortcode tag """
        pass


class FigureGroupRenderer(BaseShortcodeRenderer):
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

    def form(self, question, *args, **kwargs):
        return FigureGroupForm(question, *args, **kwargs)

    def get_html(self):
        classes = " ".join(self.styles)
        out = "".join(self._children_html())
        out += "<figure class=\"%s\">%s</figure>" % (
            classes, out)
        if not self._is_hero() and "inline" in self.styles:
            return "<aside>%s</aside>" % out

    def to_html(self):
        if self.is_hero():
            return ""
        return self.get_html()

    def update_context(self, context):
        if not self._is_hero():
            return context
        try:
            context['pre_content'] += self.get_html()
        except KeyError:
            context['pre_content'] = self.get_html()
        return context

    def _is_hero(self):
        if "aside" not in self.styles and "inline" not in self.styles:
            return True
        return False

    def _children_html(self):
        for figure in self.figures:
            yield figure.get_html()
        for caption in self.captions:
            yield "<figcaption>%s</figcaption>" % caption

    def _to_arg_list(self):
        """ Returns ordered list of FigureGroupRenderer properties """
        layout = " ".join(self.layout)
        group_type = self.group_type
        return [group_type, layout]

    @classmethod
    def _content(self):
        """ Returns text content of the figgroup shortcode, made up of
        figure and caption shortcodes """
        figure_content = "".join(
            [f.to_shortcode() for f in self.figures])
        caption_content = "".join(
            [c.to_shortcode() for c in self.captions])
        return "%s%s" % (figure_content, caption_content)


class TableRenderer(ContainerShortcodeBlock):
    def __init__(
            self,
            caption="",
            html="",
            table_type="table"):
        super(TableBlock, self).__init__(question, caption)

        self.table_html = html
        self.table_type = table_type

    def form(self, question, *args, **kwargs):
        return TableGroupForm(question, *args, **kwargs)

    def get_html(self):
        caps = "".join(
            ["<caption>%s</caption>" % c for c in self.captions])
        return caps + self.table_html

    def to_html(self):
        return self.get_html()

    @classmethod
    def _to_arg_list(self):
        """ Returns ordered list of TableRenderer properties """
        layout = " ".join(obj.layout)
        group_type = obj.group_type
        return [group_type, layout]

    @classmethod
    def _to_content(self):
        """ Returns text content of the table shortcode, made up of
        caption shortcodes and the table html """
        caption_content = "".join(
            [c.to_shortcode() for c in obj.captions])
        return "%s%s" % (caption_content, self.html)


class FigureRenderer(BaseShortcodeBlock):
    def __init__(self, question, file_obj, alt="", title=""):
        self.alt = alt
        self.title = title
        self.url = file_obj.get_absolute_url()
        super(FigureBlock, self).__init__(question)

    def _to_arg_list(self):
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
