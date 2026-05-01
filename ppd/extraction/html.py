"""Deterministic HTML extraction helpers for PP&D public fixtures.

This module is intentionally small and side-effect free. It parses already
captured public HTML snippets and never fetches pages, opens browser sessions,
or reads authenticated DevHub state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urljoin


@dataclass(frozen=True)
class HtmlLink:
    url: str
    label: str


@dataclass(frozen=True)
class HtmlImage:
    src: str
    alt: str


@dataclass(frozen=True)
class HtmlTable:
    headers: tuple[str, ...] = field(default_factory=tuple)
    rows: tuple[tuple[str, ...], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class HtmlExtraction:
    title: str
    headings: tuple[str, ...] = field(default_factory=tuple)
    list_items: tuple[str, ...] = field(default_factory=tuple)
    links: tuple[HtmlLink, ...] = field(default_factory=tuple)
    images: tuple[HtmlImage, ...] = field(default_factory=tuple)
    tables: tuple[HtmlTable, ...] = field(default_factory=tuple)
    modified_date: Optional[str] = None


class PublicGuidanceHtmlParser(HTMLParser):
    def __init__(self, *, base_url: str = "") -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.title = ""
        self.headings: list[str] = []
        self.list_items: list[str] = []
        self.links: list[HtmlLink] = []
        self.images: list[HtmlImage] = []
        self.tables: list[HtmlTable] = []
        self.modified_date: Optional[str] = None

        self._capture: Optional[str] = None
        self._buffer: list[str] = []
        self._link_href: Optional[str] = None
        self._table_rows: list[list[str]] = []
        self._current_row: Optional[list[str]] = None
        self._current_cell: Optional[list[str]] = None
        self._current_cell_tag: Optional[str] = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attrs_dict = {name.lower(): value or "" for name, value in attrs}
        tag = tag.lower()

        if tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "").strip()
            if content and name in {"modified", "last-modified", "dcterms.modified"}:
                self.modified_date = content
            if content and prop in {"article:modified_time"}:
                self.modified_date = content
            return

        if tag in {"title", "h1", "h2", "h3", "h4", "h5", "h6", "li", "time"}:
            self._capture = tag
            self._buffer = []
            return

        if tag == "a":
            self._link_href = attrs_dict.get("href") or ""
            self._capture = "a"
            self._buffer = []
            return

        if tag == "img":
            src = attrs_dict.get("src", "").strip()
            alt = attrs_dict.get("alt", "").strip()
            if src or alt:
                self.images.append(HtmlImage(src=urljoin(self.base_url, src), alt=alt))
            return

        if tag == "tr":
            self._current_row = []
            return

        if tag in {"td", "th"} and self._current_row is not None:
            self._current_cell = []
            self._current_cell_tag = tag
            return

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)
        if self._capture is not None:
            self._buffer.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self._current_cell is not None and tag == self._current_cell_tag:
            text = normalize_text("".join(self._current_cell))
            self._current_row.append(text)
            self._current_cell = None
            self._current_cell_tag = None
            return

        if tag == "tr" and self._current_row is not None:
            if any(cell for cell in self._current_row):
                self._table_rows.append(self._current_row)
            self._current_row = None
            return

        if tag == "table":
            if self._table_rows:
                headers = tuple(self._table_rows[0])
                rows = tuple(tuple(row) for row in self._table_rows[1:])
                self.tables.append(HtmlTable(headers=headers, rows=rows))
            self._table_rows = []
            return

        if self._capture != tag:
            return

        text = normalize_text("".join(self._buffer))
        if tag == "title" and text:
            self.title = text
        elif tag.startswith("h") and text:
            self.headings.append(text)
        elif tag == "li" and text:
            self.list_items.append(text)
        elif tag == "a" and self._link_href:
            self.links.append(HtmlLink(url=urljoin(self.base_url, self._link_href), label=text))
        elif tag == "time" and text and self.modified_date is None:
            self.modified_date = text

        self._capture = None
        self._buffer = []
        if tag == "a":
            self._link_href = None


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def extract_public_guidance_html(html: str, *, base_url: str = "") -> HtmlExtraction:
    parser = PublicGuidanceHtmlParser(base_url=base_url)
    parser.feed(html)
    parser.close()
    return HtmlExtraction(
        title=parser.title,
        headings=tuple(parser.headings),
        list_items=tuple(parser.list_items),
        links=tuple(parser.links),
        images=tuple(parser.images),
        tables=tuple(parser.tables),
        modified_date=parser.modified_date,
    )
