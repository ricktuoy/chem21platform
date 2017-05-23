from .parser import HTMLShortcodeParser
from .processors import FigureGroupProcessor
from .processors import TableProcessor
from .processors import BiblioFootnoteProcessor
from .processors import BiblioInlineProcessor
from .processors import InternalLinkProcessor
from .processors import CTAProcessor
from .processors import AttributionProcessor
from .processors import RSCRightsProcessor

# a bit like dependency injection
HTMLShortcodeParser.register_block_shortcode(FigureGroupProcessor)
HTMLShortcodeParser.register_block_shortcode(TableProcessor)
HTMLShortcodeParser.register_inline_shortcode(BiblioInlineProcessor)
HTMLShortcodeParser.register_block_shortcode(CTAProcessor)
HTMLShortcodeParser.register_inline_shortcode(BiblioFootnoteProcessor)
HTMLShortcodeParser.register_inline_shortcode(InternalLinkProcessor)
HTMLShortcodeParser.register_inline_shortcode(RSCRightsProcessor)
HTMLShortcodeParser.register_block_shortcode(AttributionProcessor)
