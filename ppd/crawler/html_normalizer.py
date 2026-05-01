"""Fixture-only HTML to normalized PP&D document conversion.

This module intentionally accepts caller-provided HTML strings and never fetches
URLs, opens browser sessions, stores auth state, or writes crawl output. It is
for deterministic fixture validation of public PP&D-style guidance pages.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Any, Optional
from urllib.parse import urljoin

MODIFIED_RE = re.compile(
    r"(?:last\s+)?(?:updated|modified|reviewed)\s*:?\s*([A-Z][a-z]+\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2})",
    re.IGNORECASE,
)
SPACE_RE = re.compile(r"\s+")


@dataclass
class _TextFrame:
    tag: str
    attrs: dict[str, str]
    parts: list[str] = field(default_factory=list)


@dataclass
class _TableFrame:
    attrs: dict[str, str]
    caption: str = ""
    headers: list[str] = field(default_factory=list)
    rows: list[list[str]] = field(default_factory=list)
    current_row: Optional[list[str]] = None
    current_cell_tag: Optional[str] = None
    current_cell_parts: list[str] = field(default_factory=list)


class _PpdHtmlParser(HTMLParser):
    def __init__(self, source_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.source_url = source_url
        self.title = ""
        self.headings: list[dict[str, Any]] = []
        self.paragraphs: list[str] = []
        self.links: list[dict[str, Any]] = []
        self.ordered_steps: list[dict[str, Any]] = []
        self.tables: list[dict[str, Any]] = []
        self.modified_date_evidence: list[dict[str, str]] = []
        self._frames: list[_TextFrame] = []
        self._ol_stack: list[dict[str, Any]] = []
        self._table_stack: list[_TableFrame] = []
        self._capturing_table_caption = False

    def handle_starttag(self, tag: str, attrs_list: list[tuple[str, Optional[str]]]) -> None:
        tag = tag.lower()
        attrs = {name.lower(): value or "" for name, value in attrs_list}
        if tag in {"title", "h1", "h2", "h3", "h4", "h5", "h6", "p", "a", "li", "caption"}:
            self._frames.append(_TextFrame(tag=tag, attrs=attrs))
        if tag == "ol":
            self._ol_stack.append({"index": 0, "attrs": attrs})
        elif tag == "table":
            self._table_stack.append(_TableFrame(attrs=attrs))
        elif tag == "tr" and self._table_stack:
            self._table_stack[-1].current_row = []
        elif tag in {"th", "td"} and self._table_stack:
            table = self._table_stack[-1]
            table.current_cell_tag = tag
            table.current_cell_parts = []
        elif tag == "caption" and self._table_stack:
            self._capturing_table_caption = True

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"th", "td"} and self._table_stack:
            table = self._table_stack[-1]
            cell_text = _clean_text(" ".join(table.current_cell_parts))
            if table.current_cell_tag == "th":
                table.headers.append(cell_text)
            if table.current_row is not None:
                table.current_row.append(cell_text)
            table.current_cell_tag = None
            table.current_cell_parts = []
            return
        if tag == "tr" and self._table_stack:
            table = self._table_stack[-1]
            if table.current_row:
                if table.headers and table.current_row == table.headers:
                    pass
                else:
                    table.rows.append(table.current_row)
            table.current_row = None
            return
        if tag == "table" and self._table_stack:
            table = self._table_stack.pop()
            table_id = _slug_or_fallback(table.attrs.get("id"), f"table-{len(self.tables) + 1}")
            self.tables.append(
                {
                    "id": table_id,
                    "caption": table.caption or None,
                    "headers": table.headers,
                    "rows": table.rows,
                    "anchorId": table_id,
                }
            )
            return
        if tag == "ol" and self._ol_stack:
            self._ol_stack.pop()
            return
        if tag == "caption":
            self._capturing_table_caption = False
        frame = self._pop_frame(tag)
        if frame is None:
            return
        text = _clean_text(" ".join(frame.parts))
        if not text:
            return
        if tag == "title":
            self.title = text
        elif tag.startswith("h") and len(tag) == 2 and tag[1].isdigit():
            level = int(tag[1])
            anchor_id = _slug_or_fallback(frame.attrs.get("id"), f"section-{len(self.headings) + 1}")
            self.headings.append({"id": anchor_id, "heading": text, "level": level, "text": "", "anchorId": anchor_id})
        elif tag == "p":
            self.paragraphs.append(text)
            self._record_modified_date(text, "p")
        elif tag == "a":
            href = frame.attrs.get("href", "").strip()
            if href:
                self.links.append(
                    {
                        "url": urljoin(self.source_url, href),
                        "label": text,
                        "relation": _classify_link_relation(href),
                        "contentTypeHint": _classify_content_type_hint(href),
                    }
                )
        elif tag == "li" and self._ol_stack:
            current = self._ol_stack[-1]
            current["index"] += 1
            step_id = _slug_or_fallback(frame.attrs.get("id"), f"step-{len(self.ordered_steps) + 1}")
            self.ordered_steps.append(
                {
                    "id": step_id,
                    "sequence": current["index"],
                    "text": text,
                    "anchorId": step_id,
                    "evidenceSelector": f"ol li:nth-of-type({current['index']})",
                }
            )
        elif tag == "caption" and self._table_stack:
            self._table_stack[-1].caption = text

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        for frame in self._frames:
            frame.parts.append(data)
        if self._table_stack and self._table_stack[-1].current_cell_tag:
            self._table_stack[-1].current_cell_parts.append(data)

    def _pop_frame(self, tag: str) -> Optional[_TextFrame]:
        for index in range(len(self._frames) - 1, -1, -1):
            if self._frames[index].tag == tag:
                return self._frames.pop(index)
        return None

    def _record_modified_date(self, text: str, selector: str) -> None:
        match = MODIFIED_RE.search(text)
        if not match:
            return
        self.modified_date_evidence.append(
            {
                "dateText": match.group(1),
                "evidenceText": text,
                "evidenceSelector": selector,
            }
        )


def normalize_html_fixture(
    *,
    document_id: str,
    source_url: str,
    html: str,
    fetched_at: str,
    normalized_at: str,
    canonical_url: Optional[str] = None,
    document_role: str = "guidance",
    source_family: str = "portland_gov_ppd",
) -> dict[str, Any]:
    """Convert a supplied HTML fixture into a normalized-document dictionary."""
    parser = _PpdHtmlParser(source_url=source_url)
    parser.feed(html)
    parser.close()

    title = parser.title or (parser.headings[0]["heading"] if parser.headings else document_id)
    text_parts = [heading["heading"] for heading in parser.headings] + parser.paragraphs + [step["text"] for step in parser.ordered_steps]
    text = _clean_text("\n".join(text_parts))
    sections = _sections_with_body_text(parser.headings, parser.paragraphs)

    return {
        "id": document_id,
        "sourceUrl": source_url,
        "canonicalUrl": canonical_url or source_url,
        "contentType": "html",
        "title": title,
        "fetchedAt": fetched_at,
        "contentHash": "sha256:" + hashlib.sha256(html.encode("utf-8")).hexdigest(),
        "text": text,
        "links": parser.links,
        "pageAnchors": [{"id": section["anchorId"], "label": section["heading"], "selector": f"#{section['anchorId']}"} for section in sections],
        "documentRole": document_role,
        "normalizedAt": normalized_at,
        "sourceFamily": source_family,
        "sections": sections,
        "orderedSteps": parser.ordered_steps,
        "tables": parser.tables,
        "modifiedDateEvidence": parser.modified_date_evidence,
        "warnings": [],
    }


def _sections_with_body_text(headings: list[dict[str, Any]], paragraphs: list[str]) -> list[dict[str, Any]]:
    if not headings:
        return []
    sections: list[dict[str, Any]] = []
    for index, heading in enumerate(headings):
        section = dict(heading)
        if index == len(headings) - 1:
            section["text"] = "\n".join(paragraphs)
        sections.append(section)
    return sections


def _clean_text(value: str) -> str:
    return SPACE_RE.sub(" ", value).strip()


def _slug_or_fallback(value: Optional[str], fallback: str) -> str:
    if value and value.strip():
        return value.strip()
    slug = re.sub(r"[^a-z0-9]+", "-", fallback.lower()).strip("-")
    return slug or fallback


def _classify_link_relation(href: str) -> str:
    lower = href.lower()
    if lower.startswith("mailto:") or lower.startswith("tel:"):
        return "contact"
    if lower.endswith(".pdf"):
        return "download"
    if lower.startswith("https://devhub.portlandoregon.gov"):
        return "portal_action"
    if lower.startswith("http") and "portland.gov" not in lower:
        return "external_reference"
    return "same_site"


def _classify_content_type_hint(href: str) -> str:
    lower = href.lower()
    if lower.endswith(".pdf"):
        return "pdf"
    if lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        return "image"
    return "html"
