from .parser import HTMLShortcodeParser
from .processors import FigureGroupProcessor
from .processors import TableProcessor
from .processors import BiblioFootnoteProcessor
from .processors import BiblioBlockProcessor
from .processors import InternalLinkProcessor
from .processors import CTAProcessor
from .processors import AttributionProcessor

HTMLShortcodeParser.register_block_shortcode(FigureGroupProcessor)
HTMLShortcodeParser.register_block_shortcode(TableProcessor)
HTMLShortcodeParser.register_block_shortcode(BiblioBlockProcessor)
HTMLShortcodeParser.register_block_shortcode(CTAProcessor)
HTMLShortcodeParser.register_inline_shortcode(BiblioFootnoteProcessor)
HTMLShortcodeParser.register_inline_shortcode(InternalLinkProcessor)
HTMLShortcodeParser.register_block_shortcode(AttributionProcessor)
