"""Synthetic file-preparation compliance checks for PP&D workflows.

This module intentionally works from metadata dictionaries only. It does not read
private files, fetch documents, persist PDFs, or prepare upload staging areas.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ComplianceFinding:
    """A single deterministic compliance finding."""

    code: str
    message: str


@dataclass(frozen=True)
class SyntheticDocumentMetadata:
    """Metadata-only representation of a document fixture."""

    document_id: str
    title: str
    media_type: str
    synthetic: bool
    downloaded: bool = False
    private: bool = False
    upload_staging: bool = False
    raw_pdf_persisted: bool = False

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SyntheticDocumentMetadata":
        return cls(
            document_id=str(value.get("document_id", "")),
            title=str(value.get("title", "")),
            media_type=str(value.get("media_type", "")),
            synthetic=bool(value.get("synthetic", False)),
            downloaded=bool(value.get("downloaded", False)),
            private=bool(value.get("private", False)),
            upload_staging=bool(value.get("upload_staging", False)),
            raw_pdf_persisted=bool(value.get("raw_pdf_persisted", False)),
        )


def load_metadata_fixture(path: Path) -> list[SyntheticDocumentMetadata]:
    """Load synthetic metadata records from a JSON fixture file."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("documents", payload)
    if not isinstance(records, list):
        raise ValueError("metadata fixture must be a list or contain a documents list")
    return [SyntheticDocumentMetadata.from_mapping(record) for record in records]


def evaluate_metadata(records: Iterable[SyntheticDocumentMetadata]) -> list[ComplianceFinding]:
    """Return compliance findings for metadata-only document preparation."""

    findings: list[ComplianceFinding] = []
    seen_ids: set[str] = set()

    for index, record in enumerate(records):
        label = record.document_id or f"record[{index}]"

        if not record.document_id:
            findings.append(ComplianceFinding("missing_document_id", f"{label} has no document_id"))
        elif record.document_id in seen_ids:
            findings.append(ComplianceFinding("duplicate_document_id", f"{label} is duplicated"))
        else:
            seen_ids.add(record.document_id)

        if not record.title:
            findings.append(ComplianceFinding("missing_title", f"{label} has no title"))
        if not record.media_type:
            findings.append(ComplianceFinding("missing_media_type", f"{label} has no media_type"))
        if not record.synthetic:
            findings.append(ComplianceFinding("not_synthetic", f"{label} is not marked synthetic"))
        if record.private:
            findings.append(ComplianceFinding("private_metadata", f"{label} is marked private"))
        if record.downloaded:
            findings.append(ComplianceFinding("downloaded_document", f"{label} indicates a downloaded document"))
        if record.raw_pdf_persisted:
            findings.append(ComplianceFinding("raw_pdf_persisted", f"{label} indicates raw PDF persistence"))
        if record.upload_staging:
            findings.append(ComplianceFinding("upload_staging", f"{label} indicates upload staging"))

    return findings


def assert_metadata_compliant(records: Iterable[SyntheticDocumentMetadata]) -> None:
    """Raise ValueError when synthetic metadata violates preparation rules."""

    findings = evaluate_metadata(records)
    if findings:
        detail = "; ".join(f"{finding.code}: {finding.message}" for finding in findings)
        raise ValueError(detail)
