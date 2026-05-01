"""Normalized PP&D public document data contracts.

These contracts are side-effect free. They describe public-source crawler and
extractor outputs without fetching URLs, reading browser state, or storing
private DevHub artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PpdContentType(str, Enum):
    HTML = "html"
    PDF = "pdf"
    IMAGE = "image"
    FORM = "form"
    OTHER = "other"


class PpdDocumentRole(str, Enum):
    GUIDANCE = "guidance"
    APPLICATION = "application"
    CHECKLIST = "checklist"
    HANDOUT = "handout"
    FAQ = "faq"
    PORTAL_REFERENCE = "portal_reference"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SourceLink:
    url: str
    label: str
    relation: str = "unknown"
    content_type_hint: Optional[PpdContentType] = None


@dataclass(frozen=True)
class ExtractedField:
    id: str
    label: str
    field_type: str
    required: bool
    options: tuple[str, ...] = field(default_factory=tuple)
    page_number: Optional[int] = None
    evidence_text: Optional[str] = None


@dataclass(frozen=True)
class PageAnchor:
    id: str
    label: str
    page_number: Optional[int] = None
    selector: Optional[str] = None
    text_offset: Optional[int] = None


@dataclass(frozen=True)
class DocumentSection:
    id: str
    heading: str
    level: int
    text: str
    page_number: Optional[int] = None
    anchor_id: Optional[str] = None


@dataclass(frozen=True)
class DocumentTable:
    id: str
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    caption: Optional[str] = None
    page_number: Optional[int] = None
    anchor_id: Optional[str] = None


@dataclass(frozen=True)
class ScrapedDocument:
    id: str
    source_url: str
    canonical_url: str
    content_type: PpdContentType
    title: str
    fetched_at: str
    content_hash: str
    text: str
    links: tuple[SourceLink, ...] = field(default_factory=tuple)
    extracted_fields: tuple[ExtractedField, ...] = field(default_factory=tuple)
    page_anchors: tuple[PageAnchor, ...] = field(default_factory=tuple)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("id is required")
        if not self.source_url.startswith("https://"):
            errors.append("source_url must be HTTPS")
        if not self.canonical_url.startswith("https://"):
            errors.append("canonical_url must be HTTPS")
        if not self.title.strip():
            errors.append("title is required")
        if not self.fetched_at.strip():
            errors.append("fetched_at is required")
        if not self.content_hash.strip():
            errors.append("content_hash is required")
        return errors


@dataclass(frozen=True)
class NormalizedDocument(ScrapedDocument):
    document_role: PpdDocumentRole = PpdDocumentRole.UNKNOWN
    normalized_at: str = ""
    source_family: str = "unknown"
    sections: tuple[DocumentSection, ...] = field(default_factory=tuple)
    tables: tuple[DocumentTable, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> list[str]:
        errors = super().validate()
        if not self.normalized_at.strip():
            errors.append("normalized_at is required")
        for section in self.sections:
            if section.level < 1:
                errors.append(f"section {section.id} level must be positive")
        return errors
