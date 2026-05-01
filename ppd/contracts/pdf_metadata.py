"""Fixture-only PDF normalized-document metadata contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PdfFieldKind(str, Enum):
    TEXT = "text"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SELECT = "select"
    SIGNATURE = "signature"
    DATE = "date"
    MONEY = "money"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PdfPageText:
    id: str
    page_number: int
    text: str
    text_hash: str

    def validate(self, *, page_count: int) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("page text id is required")
        if self.page_number < 1 or self.page_number > page_count:
            errors.append(f"page text {self.id} page_number is out of range")
        if not self.text.strip():
            errors.append(f"page text {self.id} text is required")
        if not self.text_hash.startswith("sha256:"):
            errors.append(f"page text {self.id} requires sha256 text_hash")
        return errors


@dataclass(frozen=True)
class PdfFormField:
    id: str
    label: str
    kind: PdfFieldKind
    page_number: int
    required: bool
    evidence_text: str
    options: tuple[str, ...] = field(default_factory=tuple)

    def validate(self, *, page_count: int) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("form field id is required")
        if not self.label.strip():
            errors.append(f"form field {self.id} label is required")
        if self.page_number < 1 or self.page_number > page_count:
            errors.append(f"form field {self.id} page_number is out of range")
        if not self.evidence_text.strip():
            errors.append(f"form field {self.id} evidence_text is required")
        if self.kind in {PdfFieldKind.RADIO, PdfFieldKind.SELECT} and not self.options:
            errors.append(f"form field {self.id} requires options")
        return errors


@dataclass(frozen=True)
class PdfCheckboxHint:
    id: str
    label: str
    page_number: int
    checked_by_default: bool = False
    evidence_text: str = ""

    def validate(self, *, page_count: int) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("checkbox hint id is required")
        if not self.label.strip():
            errors.append(f"checkbox hint {self.id} label is required")
        if self.page_number < 1 or self.page_number > page_count:
            errors.append(f"checkbox hint {self.id} page_number is out of range")
        if not self.evidence_text.strip():
            errors.append(f"checkbox hint {self.id} evidence_text is required")
        return errors


@dataclass(frozen=True)
class PdfSignatureHint:
    id: str
    label: str
    page_number: int
    required: bool
    signer_role: str
    evidence_text: str

    def validate(self, *, page_count: int) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("signature hint id is required")
        if not self.label.strip():
            errors.append(f"signature hint {self.id} label is required")
        if self.page_number < 1 or self.page_number > page_count:
            errors.append(f"signature hint {self.id} page_number is out of range")
        if not self.signer_role.strip():
            errors.append(f"signature hint {self.id} signer_role is required")
        if not self.evidence_text.strip():
            errors.append(f"signature hint {self.id} evidence_text is required")
        return errors


@dataclass(frozen=True)
class PdfFeeTableHint:
    id: str
    page_number: int
    caption: str
    headers: tuple[str, ...]
    row_count: int
    evidence_text: str

    def validate(self, *, page_count: int) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("fee table hint id is required")
        if self.page_number < 1 or self.page_number > page_count:
            errors.append(f"fee table hint {self.id} page_number is out of range")
        if not self.caption.strip():
            errors.append(f"fee table hint {self.id} caption is required")
        if not self.headers:
            errors.append(f"fee table hint {self.id} headers are required")
        if self.row_count < 1:
            errors.append(f"fee table hint {self.id} row_count must be positive")
        if not self.evidence_text.strip():
            errors.append(f"fee table hint {self.id} evidence_text is required")
        return errors


@dataclass(frozen=True)
class PdfNormalizedDocumentMetadata:
    document_id: str
    source_url: str
    canonical_url: str
    title: str
    page_count: int
    captured_at: str
    extraction_mode: str
    page_text: tuple[PdfPageText, ...] = field(default_factory=tuple)
    form_fields: tuple[PdfFormField, ...] = field(default_factory=tuple)
    checkbox_hints: tuple[PdfCheckboxHint, ...] = field(default_factory=tuple)
    signature_hints: tuple[PdfSignatureHint, ...] = field(default_factory=tuple)
    fee_table_hints: tuple[PdfFeeTableHint, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    live_download_performed: bool = False

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.document_id.strip():
            errors.append("document_id is required")
        if not self.source_url.startswith("https://"):
            errors.append("source_url must be HTTPS")
        if not self.canonical_url.startswith("https://"):
            errors.append("canonical_url must be HTTPS")
        if not self.title.strip():
            errors.append("title is required")
        if self.page_count < 1:
            errors.append("page_count must be positive")
        if not self.captured_at.endswith("Z"):
            errors.append("captured_at must end in Z")
        if self.extraction_mode != "fixture_only":
            errors.append("extraction_mode must be fixture_only")
        if self.live_download_performed:
            errors.append("fixture metadata must not perform live downloads")

        for item in self.page_text:
            errors.extend(item.validate(page_count=self.page_count))
        for item in self.form_fields:
            errors.extend(item.validate(page_count=self.page_count))
        for item in self.checkbox_hints:
            errors.extend(item.validate(page_count=self.page_count))
        for item in self.signature_hints:
            errors.extend(item.validate(page_count=self.page_count))
        for item in self.fee_table_hints:
            errors.extend(item.validate(page_count=self.page_count))
        return errors
