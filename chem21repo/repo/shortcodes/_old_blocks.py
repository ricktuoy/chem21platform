from .processors import *
from .errors import *
import re


class BaseShortcodeBlock(object):
    block_regex = re.compile((
        r"\<\!\-\-user_block\-\-\>"
        r"(?P<content>.*?)\<\!\-\-user_block\-\-\>"), re.DOTALL)
    question_blocks = {}

    @classmethod
    def block_is_shortcode(kls, match):
        return match.group("tag_atts").find("class=\"token") != -1

    @property
    def blocks(self):
        try:
            return BaseShortcodeBlock.question_blocks[self.question.pk]
        except KeyError:
            blocks = HTMLBlockProcessor(
                self.question.text)
            blocks_enum = []
            para_num = 0
            prev_was_shortcode = False
            for block in blocks:
                if self.block_is_shortcode(block):
                    if not prev_was_shortcode:
                        shortcode_num = 1
                    else:
                        shortcode_num += 1
                    prev_was_shortcode = True
                else:
                    para_num += 1
                blocks_enum.append(
                    (block, (para_num, shortcode_num)))
            return blocks_enum

    @property
    def id(self):
        self._id = "%d_%d_%d" % (self.question.pk, self.para, self.fig)

    @classmethod
    def get_match(kls, source, number):
        matches = list(kls.token_regex.finditer(source))
        try:
            return matches[number - 1]
        except IndexError:
            raise MatchError("No such shortcode block found")

    @property
    def start_index(self):
        offset = -1 if self.above else 0
        if self.para + offset == 0:
            start = 0
        else:
            para_match = self.blocks.get_match(
                self.para + offset)
            start = para_match.end()
        try:
            para_match_next = self.blocks.get_match(
                self.para + offset + 1)
            token_text = self.question.text[
                start:para_match_next.start()]
        except MatchError:
            token_text = self.question.text[
                start:]
        if not self.fig or not token_text:
            return start
        try:
            token_match = self.get_match(
                token_text, self.fig)
        except MatchError:
            return start
        return start + token_match.end()

    def insert(self):
        html = self.get_html()
        index = self.start_index
        self.question.text = self.question.text[:index] + \
            html + self.question.text[index:]

    def delete(self):
        offset = -1 if self.above else 0
        if self.para + offset == 0:
            start = 0
        else:
            pm = self.blocks.get_match(
                self.para + offset)
            start = pm.end()
        search_text = self.question.text[
            start:]
        tm = self.get_match(search_text, self.fig)

        self.question.text = self.question.text[
            0:start + tm.start()] + self.question.text[
            start + tm.end():]

    def get(self, para, question, order=1):
        p_match = self.blocks.get_match(para)
        return p_match

    def shortcode_html(inner_html):
        def wrap(self):
            out = "<div class=\"shortcode\"><!--shortcode-->"
            out += inner_html(self)
            out += "<!--end_shortcode--></div>"
            return out
        return wrap

    def shortcode_loader(load_from_shortcode):
        def wrap(self, html, *args, **kwargs):
            match = self.block_regex.search(html)
            try:
                content = match.group('content')
            except AttributeError:
                raise NotAShortcodeError('Not a shortcode.')

            return load_from_shortcode(
                self, content, *args, **kwargs)
        return wrap

    shortcode_html = staticmethod(shortcode_html)
    shortcode_loader = staticmethod(shortcode_loader)


class FigureGroupBlock(ContainerShortcodeBlock):
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

    def get_shortcode_params(self):
        params = [self.group_type, ]
        if self.styles:
            params.append(" ".join(self.styles))
        return params

    def children(self):
        for figure in figures:
            yield figure
        for caption in captions:
            yield caption

    def get_shortcode(self):
        ftype = self.data.get("figure_type", "figure")
        if not ftype:
            ftype = "figure"
        return "[figgroup:%s]%s%s[/figgroup]" % (
            self.id,
            ":".join(group_attrs),
            "".join([f.get_shortcode() for f in self.figure_blocks]))
    get_shortcode_html = BaseShortcodeBlock.shortcode_html(get_shortcode)

    def to_html(self):
        classes = " ".join(self.styles)
        out = "".join([figure.get_html() for figure in self.figures])
        out += "".join([caption.get_html() for caption in self.captions])
        out = "<figure class=\"%s\">%s</figure>" % (
            classes, out)
        if not self.is_hero() and "inline" in self.styles:
            return "<aside>%s</aside>" % out

    def is_hero(self):
        if "aside" not in self.styles and "inline" not in self.styles:
            return True
        return False


class TableBlock(ContainerShortcodeBlock):
    def __init__(
            self,
            question,
            caption="",
            html="",
            table_type="table"):
        super(TableBlock, self).__init__(question, caption)

        self.table_html = html
        self.table_type = table_type

    def form(self, *args, **kwargs):
        return TableGroupForm(self.question, *args, **kwargs)

    @property
    def caption_shortcode():
        if self.caption:
            return "<caption>%s</caption>" % self.caption
        return ""

    def get_shortcode(self):
        return "<table>%s%s</table>" % (
            self.caption_shortcode, self.table_html)

    get_shortcode_html = BaseShortcodeBlock.shortcode_html(get_shortcode)


class FigureBlock(BaseShortcodeBlock):
    def __init__(self, question, file_obj, alt="", title=""):
        self.file_obj = file_obj
        self.alt = alt
        self.title = title
        super(FigureBlock, self).__init__(question)

    def get_shortcode(self, txt=""):
        content = "[figure:local:%s]" % self.file_obj.pk
        return content

    get_shortcode_html = BaseShortcodeBlock.shortcode_html(get_shortcode)