from abc import ABCMeta
from abc import abstractproperty
from abc import abstractmethod
from .errors import *
from .renderers import FigureGroupRenderer, TableRenderer
import re


class ContextProcessorMixin(object):
    """ Mixin adding Django context and request objects to the
    Processor class on init """

    def __init__(self, *args, **kwargs):
        self.context = kwargs.get("context", {})
        self.request = self.context.get("request", None)
        super(ContextProcessorMixin, self).__init__(
            *args, **kwargs)


class HTMLShortcodeProcessor(ContextProcessorMixin):
    """ An object of this class accept source text HTML on instantiation.
    Public methods process shortcodes within the HTML as described.
    These shortcodes are defined by ShortcodeProcessor classes (below)
    that are registered to the HTMLShortcodeProcessor class using
    the .register_block_processor,.register_inline_processor class methods. """
    pattern = re.compile((
        r'<(?P<tag>\w*)\s*(?P<tag_atts>[^<>]*)>',
        r'(?P<content>.*?(?:<(?P=tag).*?>.*?<\/(?P=tag)>)',
        r'*[^<>]*)<\/(?P=tag)>'),
        re.DOTALL)
    block_processors = {}
    inline_processors = {}

    def __init__(self, html, *args, **kwargs):
        self.raw_html = html
        return super(HTMLProcessor, self).__init__(*args, **kwargs)

    @classmethod
    def register_block_shortcode(kls, ShortcodeProcessor):
        """ Registers a ShortcodeProcessor that matches to a specific
        block shortcode type in the source text."""
        kls.block_processors[Shortcode.__name__] = ShortcodeProcessor

    @classmethod
    def register_inline_shortcode(kls, Shortcode):
        """ Registers a ShortcodeProcessor that matches to a specific
        inline shortcode type in the source text. """
        kls.inline_processors[Shortcode.__name__] = Shortcode

    def remove_block_shortcodes(self):
        """ returns HTML with all block shortcodes
        from the source HTML removed """
        out = ""
        for match in self.matches:
            try:
                self._get_renderers_for_shortcode(match.group(0))
            except ShortcodeLoadError:
                out += match.group(0)
        return out

    def replace_shortcodes_with_html(self):
        """ returns HTML with all shortcodes from the source replaced
        by their HTML """
        out = ""
        for match in self.matches:
            try:
                shortcode_name, renderers = self._get_renderers_for_shortcode(
                    match.group(0))
            except ShortcodeLoadError:
                out += match.group(0)
                continue
            for renderer in renderers:
                out += renderer.to_html()
        return out

    def insert_shortcode(self, block_id, renderer, after=True):
        """ returns source HTML with new shortcode added
        after (or before if after=False) block specified by block_id """
        try:
            match = self._matches[block_id]
        except KeyError:
            raise BlockNotFoundError
        index = match.end() if after else match.start()
        return self.raw_html[:index] + renderer.to_shortcode() \
            + self.raw_html[index:]

    def remove_shortcode(self, block_id):
        """ returns source HTML with shortcode specified
        by block_id removed """
        try:
            match = self._matches[block_id]
        except KeyError:
            raise BlockNotFoundError
        # next line raises ShortcodeLoadError if not a shortcode
        self._get_renderers_for_shortcode(match.group(0))
        return self.raw_html[:match.start()] + self.raw_html[match.end():]

    def get_renderers(self, block_id):
        """ returns the renderer(s) for the shortcode specified by
        block_id as a list """
        try:
            match = self._matches[block_id]
        except KeyError:
            raise BlockNotFoundError
        # next line raises ShortcodeLoadError if not a shortcode
        return self._get_renderers_for_shortcode(match.group(0))

    def update_context(self):
        """ Iterates source blocks and updates the context object with any additional
        data provided by shortcode renderers.  Returns updated context """
        context = self.context
        for match in self.matches:
            try:
                shortcode_name, renderers = self._get_renderers_for_shortcode(
                    match.group(0))
            except ShortcodeLoadError:
                continue
            for renderer in renderers:
                try:
                    context = renderer.update_context(
                        context=self.context, request=self.request)
                except AttributeError:
                    continue
        return context

    @_add_attr_to_each_block(["data-admin-index", "data-shortcode"])
    def get_admin_html(self, match):
        """ adds HTML attributes to each block of the source html.
        They give each block a unique id and, if a shortcode block,
        the name of the relevant processor class. These can then be
        selected by front end JS and passed back via AJAX to select blocks. """
        return [
            self._get_id_of_match(match),
            self._get_shortcode_type(match)]

    def _replace_inline_shortcodes(self):
        """  preprocess HTML with all inline shortcodes substituted
        with HTML
        """
        try:
            return self._source
        except AttributeError:
            pass
        self._source = self.raw_html
        for name, ShortcodeProcessor in kls.inline_processors.iteritems():
            self._source = ShortcodeProcessor(self._source).replace_with_html()
        return self._source

    @property
    def _matches(self):
        """  returns a dict of all HTML blocks as regex Match objects,
        with keys given by the start index of each Match in the source text.
        Inline shortcodes are substituted, block codes are not."""
        try:
            return self._c_matches
        except AttributeError:
            pass
        self._c_matches = dict([
            (match.start(), match)
            for match in self.pattern.finditer(
                self.replace_inline_shortcodes)])
        return self._c_matches

    def _get_match(self, block_id):
        """ returns regex Match object at of HTML block with given ID """
        try:
            self.match = self._matches[block_id]
        except IndexError:
            raise MatchError("No match found.")
        return self.match

    def _get_renderers_for_shortcode(self, shortcode_html):
        """ returns a (name, renderer_list) pair for the first
        registered shortcode processor that matches the shortcode_html arg.
        Raises ShortcodeLoadError if no registered processors match
        (i.e. shortcode_html is not a recognised shortcode) """
        for name, ShortcodeProcessor in self.block_processors.iteritems():
            try:
                return (name, ShortcodeProcessor(shortcode_html).renderers())
            except ShortcodeLoadError:
                continue
        raise ShortcodeLoadError

    def _add_attr_to_each_block(attr_names):
        """ helper decorator that iterates through source blocks and
        adds html attributes to each, returning the result as HTML string.
        Attribute names are passed in as an iterable to the decorator itself,
        corresponding values are returned as tuples by the decorated
        function. """
        def the_decorator(attr_method):
            def the_wrapper(self):
                out = ""
                for match in self.matches:
                    attr_vals = attr_method(self, match)

                    def gen_attr(acc, pair):
                        if pair[1] is None:
                            return acc
                        attr = " %s=\"%s\"" % pair
                        return acc + attr
                    try:
                        replacement_attrs = reduce(
                            gen_attr,
                            zip(attr_names, attr_vals),
                            match.group("tag_attrs"))
                    except TypeError:
                        replacement_attrs = gen_attr(
                            match.group("tag_attrs"),
                            (attr_names, attr_vals))
                    out += "<%s %s>%s</%s>" % (
                        match.group('tag'),
                        replacement_attrs,
                        match.group('content'),
                        match.group('tag'))
                return out

    def _get_id_of_match(self, match):
        """ Returns the unique ID of a matched block """
        return str(match.start())

    def _get_shortcode_type(self, match):
        """ Returns the name of the processor for a matched shortcode block,
        or raises ShortcodeLoadError if the block
        is not a recognised shortcode """
        try:
            shortcode_name, shortcode = self._get_renderers_for_shortcode(
                match.group(0))
            return shortcode_name
        except ShortcodeLoadError:
            return None


class BaseShortcodeProcessor:
    __metaclass__ = ABCMeta
    openchar = "\["
    closechar = "\]"

    def __init__(self, text, *args, **kwargs):
        self.text = text

    @abstractproperty
    def pattern(self):
        return None

    def renderers(self):
        """ returns a list of renderer objects for each matching
        shortcode """
        return [
            self._match_to_renderer(match)
            for match in self.pattern.finditer()]

    def replace_with_html(self):
        """ substitutes each matched shortcode with the
        appropriate HTML """
        return self.pattern.sub(self._match_to_html, self.text)

    @classmethod
    def _match_to_html(kls, match):
        """ helper for replace_with_html that
        returns HTML for a given shortcode match object """
        return kls.match_to_renderer(match).to_html()

    @abstractmethod
    def _match_to_renderer(kls, match):
        """ This should be implemented with @classmethod """
        return None


class TokenShortcodeProcessor(BaseShortcodeProcessor):
    __metaclass__ = ABCMeta

    @property
    def pattern(self):
        try:
            return self._pattern
        except AttributeError:
            self._pattern = re.compile(
                r'(%s%s(?P<%s_args>.*?)%s' %
                (self.openchar,
                    self.name,
                    self.name,
                    self.closechar),
                re.DOTALL)
            return self._pattern

    def _match_to_renderer(self, match):
        """ Returns the Renderer for the given shortcode
        Match object """
        return self.to_renderer(
            *match.group(self.name + "_args").split(":"))

    @abstractmethod
    def _to_renderer(self, *args):
        """ Takes list of properties easily obtainable from
        shortcode and returns the resulting Renderer
        This should be implemented with @classmethod """
        return None


class TagShortcodeProcessor(BaseShortcodeProcessor):
    __metaclass__ = ABCMeta

    @property
    def pattern(self):
        """ Returns regex pattern to match tag-style shortcode """
        try:
            return self._simple_pattern
        except AttributeError:
            self._simple_pattern = re.compile(
                r'%s%s[:]?(?P<%s_args>.*?)%s%s%s\/%s%s' % (
                    self.openchar, self.name, self.name,
                    self.closechar, '(?P<content>.*?)',
                    self.openchar, self.name, self.closechar),
                re.DOTALL)
            return self._simple_pattern

    def _match_to_renderer(self, match):
        """ Takes a regex match and returns a Renderer object from it """
        return self._to_renderer(
            match.group('content'),
            *match.group(self.name + "_args").split(":"))

    @abstractmethod
    def _to_renderer(self, *args):
        """ Returns a Renderer object from params easily obtainable
        from shortcode text.
        This should be implemented with @classmethod """
        return None

    @abstractmethod
    def _renderer_to_arg_list(kls, obj):
        """ Takes a Renderer object and returns ordered list of its properties
        to be ouput in shortcode open tag
        This should be implemented with @classmethod """
        pass

    @abstractmethod
    def _renderer_to_content(kls, obj):
        """ Takes a Renderer object and returns text of content to appear within
        the open / close tags of its shortcode
        This should be implemented with @classmethod """
        pass


class FigureProcessor(TokenShortcodeProcessor):

    @classmethod
    def _renderer_to_arg_list(kls, obj):
        """ Returns ordered list of FigureRenderer properties """
        command = "local"
        pk = obj.file_obj.pk
        alt = obj.alt
        title = obj.title
        return [command, pk, alt, title]

    @classmethod
    def _to_renderer(kls, command, pk, alt="", *args):
        """ Returns a FigureRenderer from params easily obtainable
        from shortcode text """
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

        return FigureRenderer(
            file_obj=fle,
            alt=alt,
            title=striptags(":".join(args)))


class CaptionProcessor(TagShortcodeProcessor):
    name = "caption"

    def _to_renderer(self, caption, *args):
        """ String suffices as renderer """
        return caption

    def renderer_to_arg_list(kls, obj):
        """ Returns empty list as no properties """
        return []

    def _renderer_to_content(kls, caption):
        """ Inner content of the tag is just text """
        return caption


class FigureGroupProcessor(ContextProcessorMixin, TagShortcodeProcessor):
    name = "figgroup"

    def _to_renderer(self, content, group_type="figure", layout=""):
        """ Returns a FigureGroupRenderer from params easily obtainable
        from shortcode text """
        figures = FigureProcessor(content).renderers()
        captions = CaptionProcessor(content).renderers()
        layouts_set = frozenset(layout.split(" "))
        return FigureGroupRenderer(
            figures=figures,
            captions=captions,
            group_type=group_type,
            layout=list(layouts_set))

    @classmethod
    def renderer_to_arg_list(kls, obj):
        """ Returns ordered list of FigureGroupRenderer properties """
        layout = " ".join(obj.layout)
        group_type = obj.group_type
        return [group_type, layout]

    @classmethod
    def _renderer_to_content(kls, obj):
        """ Returns text content of the figgroup shortcode, made up of
        figure and caption shortcodes """
        figure_content = "".join(
            [FigureProcessor._renderer_to_shortcode(f) for f in obj.figures])
        caption_content = "".join(
            [CaptionProcessor._renderer_to_shortcode(c) for c in obj.captions])
        return "%s%s" % (figure_content, caption_content)


class TableProcessor(ContextProcessorMixin, TagShortcodeProcessor):
    name = "table"

    def _to_renderer(self, content, container_type, layout=""):
        """ Returns a TableRenderer from params easily obtainable
        from shortcode text """
        captions = CaptionProcessor(content).renderers()
        html = HTMLProcessor(content).remove_block_shortcodes()
        layouts_set = frozenset(layout.split(" "))
        return TableRenderer(
            layout=list(layouts_set),
            captions=captions,
            html=html)

    @classmethod
    def _renderer_to_arg_list(kls, obj):
        """ Returns ordered list of TableRenderer properties """
        layout = " ".join(obj.layout)
        group_type = obj.group_type
        return [group_type, layout]

    @classmethod
    def _renderer_to_content(kls, obj):
        """ Returns text content of the table shortcode, made up of
        caption shortcodes and the table html """
        caption_content = "".join(
            [CaptionProcessor._renderer_to_shortcode(c) for c in obj.captions])
        return "%s%s" % (caption_content, obj.html)
