"""Text normalization helpers used by validators and the quote audit."""

from __future__ import annotations

import re
from html.parser import HTMLParser

_WS = re.compile(r"[\s\u00a0\u200b\u200c\u200d\ufeff]+")
_TAG_BLOCKS = {"script", "style", "noscript"}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in _TAG_BLOCKS:
            self._skip_depth += 1
        else:
            self._parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in _TAG_BLOCKS and self._skip_depth:
            self._skip_depth -= 1
        else:
            self._parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self._skip_depth:
            self._parts.append(data)


def strip_html(html: str) -> str:
    """Extract visible text from an HTML document."""
    parser = _TextExtractor()
    parser.feed(html)
    parser.close()
    return "".join(parser._parts)


def collapse_ws(text: str) -> str:
    """Remove all Unicode whitespace and zero-width characters.

    Quotes are checked after whitespace removal so that HTML line wrapping or
    inserted spaces do not cause false negatives. Punctuation is preserved.
    """
    return _WS.sub("", text or "")


def normalize_for_quote(text: str) -> str:
    return collapse_ws(text)


def quote_in_text(quote: str, text: str) -> bool:
    q = normalize_for_quote(quote)
    return bool(q) and q in normalize_for_quote(text)
