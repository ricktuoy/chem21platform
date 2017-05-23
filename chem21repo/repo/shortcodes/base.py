"""Summary
"""
from abc import ABCMeta
from abc import abstractmethod, abstractproperty
import re
import logging


class BaseShortcodeProcessor(object):
    """Abstract base class for shortcode processor

    Subclasses match to specific shortcodes.
    Then map to renderers and thereby HTML

    Attributes:
        closechar (str): closing char(s) of tag
        openchar (str): open char(s) of tag

    """
    __metaclass__ = ABCMeta
    openchar = "\["
    closechar = "\]"

    def __init__(self, html):
        """Summary

        Args:
            html (str): Description

        """
        self._html = html

    @abstractproperty
    def pattern(self):
        """defines shortcode structure

        Returns:
            :obj:`re.RegexObject`: shortcode structure
        """
        return None

    def renderers(self):
        """
        Returns:
            :obj: `list` of :obj:`BaseShortcodeRenderer`: list of renderer objects for each
                matching shortcode
        """
        return [
            self._shortcode_to_renderer(match)
            for match in self.pattern.finditer(self._html)]

    def renderers_and_matches(self):
        return [
            (self._shortcode_to_renderer(match), match)
            for match in self.pattern.finditer(self._html)]

    def get_rendered_html(self, extra_html_snippets):
        """substitutes each matched shortcode with the
        appropriate HTML

        Args:
            extra_html_snippets (dict): extra named HTML snippets,
                which can be adjusted by the processor

        Returns:
            TYPE: Description
        """
        self._extra_snippets = extra_html_snippets
        return self.pattern.sub(self._shortcode_to_rendered_html, self._html)

    def _shortcode_to_rendered_html(self, match):
        """
        Args:
            match (:obj:`re.MatchObject`): shortcode  

        Returns:
            str: rendered HTML
        """
        renderer = self._shortcode_to_renderer(match)
        try:
            renderer.update_extra_html_snippets(self._extra_snippets)
        except AttributeError:
            pass
        return renderer.get_html()

    @abstractmethod
    def _shortcode_to_renderer(self, match):
        """
        Args:
            match (:obj:`re.MatchObject`): shortcode

        Returns:
            :obj:`BaseShortcodeRenderer`: Renderer object for shortcode
        """
        return None


class TokenShortcodeProcessor(BaseShortcodeProcessor):
    """Abstract class for token processors

    Examples:
        Tokens have no closing tag:
        [cta:1:4:8:12]
        [figure:local:936]
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def renderer(self):
        """
        Returns:
            :class:`BaseShortcodeRenderer`: Renderer class for this shortcode
        """
        return None

    @abstractproperty
    def name(self):
        """
        Returns:
            str: machine name of this shortcode
        """
        return ""

    @property
    def pattern(self):
        try:
            return self._pattern
        except AttributeError:
            self._pattern = re.compile(
                r'%s%s:(?P<%s_attrs>.*?)%s' %
                (self.openchar,
                    self.name,
                    self.name,
                    self.closechar),
                re.DOTALL)
            return self._pattern

    def _shortcode_to_renderer(self, match):
        args, kwargs = self.renderer_args(
            *match.group(self.name + "_attrs").split(":"))
        return self.renderer(*args, **kwargs)

    @abstractmethod
    def renderer_args(self, *args):
        """
        Args:
            *args: list of properties from shortcode

        Returns:
            list, dict: args and kwargs to instantiate a renderer
        """
        return [], {}


class TagShortcodeProcessor(BaseShortcodeProcessor):
    """Abstract class for token processors.

    Examples:
        Tag shortcodes have closing markup:
        [bib]taylor-2014[/bib]

        Here `figgroup` and `caption` are tag shortcodes whereas
            `figure` is a token shortcode:
        [figgroup:figure:aside][caption]A caption[/caption]
            [figure:local:10][/figgroup]
    """
    __metaclass__ = ABCMeta

    @abstractproperty
    def renderer(self):
        """
        Returns:
            :class:`BaseShortcodeRenderer`: Renderer class for this shortcode
        """
        return None

    @abstractproperty
    def name(self):
        """
        Returns:
            str: machine name of this shortcode
        """
        pass

    @property
    def pattern(self):
        try:
            return self._simple_pattern
        except AttributeError:
            regstr = r'%s%s[:]?(?P<%s_attrs>.*?)%s%s%s\/%s%s' % (
                self.openchar, self.name, self.name,
                self.closechar, '(?P<content>.*?)',
                self.openchar, self.name, self.closechar)
            self._simple_pattern = re.compile(regstr, re.DOTALL)
            return self._simple_pattern

    def _shortcode_to_renderer(self, match):
        attr_str = match.group(self.name + "_attrs")
        props = [match.group('content'), ]
        if attr_str:
            props += attr_str.split(":")
        args, kwargs = self.renderer_args(*props)
        return self.renderer(*args, **kwargs)

    @abstractmethod
    def renderer_args(self, *args):
        """
        Args:
            *args: list of properties from shortcode

        Returns:
            list, dict: args and kwargs to instantiate a renderer
        """
        return [], {}


class BaseShortcodeRenderer(object):
    """Abstract class for shortcode renderers
    
    Generate HTML from supplied semantic args

    Attributes:
        closechar (str): Description
        openchar (str): Description
    """
    openchar = "["
    closechar = "]"

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_html(self):
        """returns rendered HTML
        """
        pass

    @staticmethod
    def _shortcode_html(inner_html):
        """decorator that wraps shortcodes in placeholder html 

        Args:
            inner_html (func): function to decorate

        Returns:
            func: decorated function
        """

        def wrap(self):
            """Body of decorator

            Returns:
                str: wrapped HTML
            """
            out = "<div class=\"shortcode\"><!-- shortcode -->"
            out += inner_html(self)
            out += "<!-- end_shortcode --></div>"
            return out
        return wrap


class TagShortcodeRenderer(BaseShortcodeRenderer):
    """Abstract class for tag-style renderers

    Can also generate shortcode from args
    """
    __metaclass__ = ABCMeta

    def get_shortcode(self):
        """returns string of complete shortcode block

        Returns:
            str: shortcode block HTML
        """
        args = self.shortcode_args()
        return "%s%s%s%s%s%s%s/%s%s" % (
            self.openchar,
            self.name,
            ":" if len(args) > 0 else "",
            ":".join(args),
            self.closechar,
            self.shortcode_content(),
            self.openchar,
            self.name,
            self.closechar)

    get_wrapped_shortcode = BaseShortcodeRenderer._shortcode_html(
        get_shortcode)

    @abstractmethod
    def shortcode_args(self):
        """ordered properties to be output in shortcode tag 

        Returns:
            :obj:`list` of :obj:`str`: shortcode properties
        """
        return []

    @abstractmethod
    def shortcode_content():
        """what to display between opening and closing
        tags of shortcode 

        Returns:
            str: HTML/shortcode content
        """
        return ''


class TokenShortcodeRenderer(BaseShortcodeRenderer):
    """Abstract class for token-style renderers

    Can also generate shortcode from args
    """
    __metaclass__ = ABCMeta

    def get_shortcode(self):
        """returns string of complete shortcode block

        Returns:
            str: shortcode block HTML
        """
        args = self.shortcode_args()
        print self.name
        print args
        return "%s%s%s%s%s" % (
            self.openchar,
            self.name,
            ":" if len(args) > 0 else "",
            ":".join(args),
            self.closechar)

    get_wrapped_shortcode = BaseShortcodeRenderer._shortcode_html(
        get_shortcode)

    @abstractmethod
    def shortcode_args(self):
        """ordered properties to be output in shortcode tag 

        Returns:
            :obj:`list` of :obj:`str`: shortcode properties
        """
        pass
