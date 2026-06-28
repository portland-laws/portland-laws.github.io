"""Fixture-first public citation span inventory v5.

This module consumes only normalized public document record dry-run v5
fixtures. It does not crawl live sites, download documents, persist raw bodies,
open DevHub, or make legal or permitting guarantees.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from ppd.agent_readiness.normalized_public_document_record_dry_run_v5 import (
    assemble_document_records_from_fixture,
)

INVENTORY_VERSION = "public-citation-span-inventory-v5"
MODE = "fixture_first_normalized_public_document_records_only"
DOCUMENT_RECORD_REF_PREFIX = "document-record://public-dry-run-v5/"
EXPECTED_STALE_SOURCE_HOLD = "hold_until_public_source_freshness_reviewed"
EXPECTED_QUOTED_TEXT_PLACEHOLDER = "placeholder:quoted-text-not-stored-fixture-only"
EXPECTED_NORMALIZED_TEXT_PLACEHOLDER = "placeholder:normalized-text-pending-requirement-extraction"

EXPECTED_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "-m", "py_compile", "ppd/agent_readiness/public_citation_span_inventory_v5.py"),
    ("python3", "-m", "pytest", "ppd/tests/test_public_citation_span_inventory_v5.py"),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

ALLOWED_CONFIDENCE_LABELS = frozenset(
    {
        "synthetic-metadata-high",
        "synthetic-metadata-medium",
        "synthetic-metadata-low",
        "synthetic-metadata-review-required",
    }
)

REQUIRED_REVIEWER_ROUTES = frozenset(
    {
        "public_citation_span_reviewer",
        "requirement_extraction_reviewer",
    }
)

REQUIRED_FALSE_FLAGS = (
    "live_crawl_performed",
    "document_downloaded",
    "raw_body_persisted",
    "devhub_opened",
    "legal_or_permitting_guarantee",
    "active_mutation_enabled",
)

PROHIBITED_KEYS = frozenset(
    {
        "access_token",
        "auth_state",
        "body_text",
        "browser_trace",
        "cookie",
        "credentials",
        "devhub_session",
        "downloaded_document",
        "downloaded_document_claim",
        "har",
        "html_body",
        "legal_guarantee",
        "local_private_path",
        "password",
        "permitting_guarantee",
        "raw_body",
        "raw_body_artifact",
        "raw_crawl_output",
        "raw_html",
        "raw_pdf",
        "raw_text",
        "session_file",
        "session_state",
        "screenshot",
        "trace",
    }
)

PROHIBITED_PHRASES = frozenset(
    {
        "auth token",
        "devhub opened",
        "document downloaded",
        "downloaded document claim",
        "guaranteed approval",
        "legal advice",
        "legal guarantee",
        "live crawl performed",
        "permit approval guaranteed",
        "permit guaranteed",
        "raw body artifact",
        "raw html artifact",
        "session cookie",
    }
)


@dataclass(frozen=True)
class PublicCitationSpanInventoryRowV5:
    inventory_id: str
    source_id: str
    document_id: str
    document_record_ref: str
    page_or_section_anchor: str
    quoted_text_placeholder: str
    normalized_text_placeholder: str
    extraction_confidence: str
    stale_source_hold: str
    reviewer_routing: tuple[str, ...]
    rollback_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "inventory_id": self.inventory_id,
            "source_id": self.source_id,
            "document_id": self.document_id,
            "document_record_ref": self.document_record_ref,
            "page_or_section_anchor": self.page_or_section_anchor,
            "quoted_text_placeholder": self.quoted_text_placeholder,
            "normalized_text_placeholder": self.normalized_text_placeholder,
            "extraction_confidence": self.extraction_confidence,
            "stale_source_hold": self.stale_source_hold,
            "reviewer_routing": list(self.reviewer_routing),
            "rollback_notes": list(self.rollback_notes),
            "live_crawl_performed": False,
            "document_downloaded": False,
            "raw_body_persisted": False,
            "devhub_opened": False,
            "legal_or_permitting_guarantee": False,
            "active_mutation_enabled": False,
        }


def build_public_citation_span_inventory_v5_from_normalized_fixture(path: Path) -> dict[str, Any]:
    """Build the inventory from the normalized document dry-run v5 fixture path."""

    records = assemble_document_records_from_fixture(path)
    return build_public_citation_span_inventory_v5(records)


def build_public_citation_span_inventory_v5(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalized_records = tuple(records)
    if not normalized_records:
        raise ValueError("at least one normalized public document record is required")
    rows = tuple(_rows_from_record(record) for record in normalized_records)
    flat_rows = tuple(row for record_rows in rows for row in record_rows)
    if not flat_rows:
        raise ValueError("at least one citation span inventory row is required")
    inventory = {
        "inventory_version": INVENTORY_VERSION,
        "mode": MODE,
        "source_ids": _sorted_unique(row.source_id for row in flat_rows),
        "document_ids": _sorted_unique(row.document_id for row in flat_rows),
        "document_record_refs": _sorted_unique(row.document_record_ref for row in flat_rows),
        "row_count": len(flat_rows),
        "spans_by_source_id": _spans_by_source(flat_rows),
        "validation_commands": [list(command) for command in EXPECTED_VALIDATION_COMMANDS],
        "attestations": {flag: False for flag in REQUIRED_FALSE_FLAGS},
    }
    validate_public_citation_span_inventory_v5(inventory)
    return inventory


def validate_public_citation_span_inventory_v5(inventory: Mapping[str, Any]) -> None:
    _reject_prohibited_content(inventory)
    if inventory.get("inventory_version") != INVENTORY_VERSION:
        raise ValueError(f"inventory_version must be {INVENTORY_VERSION}")
    if inventory.get("mode") != MODE:
        raise ValueError(f"mode must be {MODE}")
    for key in ("source_ids", "document_ids", "document_record_refs"):
        values = inventory.get(key)
        if not isinstance(values, list) or not values:
            raise ValueError(f"{key} must be a non-empty list")
        if not all(isinstance(value, str) and value for value in values):
            raise ValueError(f"{key} must contain only non-empty strings")
    if inventory.get("validation_commands") != [list(command) for command in EXPECTED_VALIDATION_COMMANDS]:
        raise ValueError("validation_commands must match exact offline commands")
    attestations = inventory.get("attestations")
    if not isinstance(attestations, Mapping):
        raise ValueError("attestations must be present")
    for flag in REQUIRED_FALSE_FLAGS:
        if attestations.get(flag) is not False:
            raise ValueError(f"attestations.{flag} must be false")
    spans_by_source = inventory.get("spans_by_source_id")
    if not isinstance(spans_by_source, Mapping) or not spans_by_source:
        raise ValueError("spans_by_source_id must be a non-empty mapping")
    row_total = 0
    seen_sources: set[str] = set()
    seen_documents: set[str] = set()
    seen_document_refs: set[str] = set()
    for source_id, by_document in spans_by_source.items():
        if not isinstance(source_id, str) or not source_id:
            raise ValueError("source id keys must be non-empty strings")
        seen_sources.add(source_id)
        if not isinstance(by_document, Mapping) or not by_document:
            raise ValueError("each source must map at least one document")
        for document_id, rows in by_document.items():
            if not isinstance(document_id, str) or not document_id:
                raise ValueError("document id keys must be non-empty strings")
            seen_documents.add(document_id)
            if not isinstance(rows, list) or not rows:
                raise ValueError("each document must include citation span rows")
            for row in rows:
                document_ref = _validate_span_row(row, source_id, document_id)
                seen_document_refs.add(document_ref)
                row_total += 1
    if inventory.get("row_count") != row_total:
        raise ValueError("row_count must equal citation span rows")
    if sorted(seen_sources) != sorted(inventory["source_ids"]):
        raise ValueError("source_ids must match citation span row sources")
    if sorted(seen_documents) != sorted(inventory["document_ids"]):
        raise ValueError("document_ids must match citation span row documents")
    if sorted(seen_document_refs) != sorted(inventory["document_record_refs"]):
        raise ValueError("document_record_refs must match citation span row document references")


def _rows_from_record(record: Mapping[str, Any]) -> tuple[PublicCitationSpanInventoryRowV5, ...]:
    _reject_prohibited_content(record)
    source_id = _required_text(record, "source_id")
    document_id = _required_text(record, "document_id")
    document_record_ref = _document_record_ref(document_id)
    confidence = _required_confidence(record.get("extraction_confidence"))
    citation_spans = record.get("citation_spans")
    if not isinstance(citation_spans, list) or not citation_spans:
        raise ValueError("citation_spans must be present on normalized document records")
    anchors = _anchors_for_record(record)
    if not anchors:
        raise ValueError("normalized document record must expose section or page anchors")
    rollback_notes = _required_text_tuple(record, "rollback_notes")
    rows = []
    for index, _span in enumerate(citation_spans, start=1):
        anchor = anchors[min(index - 1, len(anchors) - 1)]
        rows.append(
            PublicCitationSpanInventoryRowV5(
                inventory_id=f"citation-inventory-v5-{source_id}-{index}",
                source_id=source_id,
                document_id=document_id,
                document_record_ref=document_record_ref,
                page_or_section_anchor=anchor,
                quoted_text_placeholder=EXPECTED_QUOTED_TEXT_PLACEHOLDER,
                normalized_text_placeholder=EXPECTED_NORMALIZED_TEXT_PLACEHOLDER,
                extraction_confidence=confidence,
                stale_source_hold=EXPECTED_STALE_SOURCE_HOLD,
                reviewer_routing=_reviewer_routing(record),
                rollback_notes=rollback_notes,
            )
        )
    return tuple(rows)


def _anchors_for_record(record: Mapping[str, Any]) -> tuple[str, ...]:
    pdf_pages = record.get("pdf_pages")
    if isinstance(pdf_pages, list) and pdf_pages:
        return tuple(f"page:{page['page_number']}" for page in pdf_pages if isinstance(page, Mapping) and page.get("page_number"))
    sections = record.get("sections")
    if isinstance(sections, list) and sections:
        return tuple(
            f"section:{section['section_id']}"
            for section in sections
            if isinstance(section, Mapping) and section.get("section_id")
        )
    return ()


def _reviewer_routing(record: Mapping[str, Any]) -> tuple[str, ...]:
    routes = ["public_citation_span_reviewer", "requirement_extraction_reviewer"]
    reviewer_holds = record.get("reviewer_holds")
    if isinstance(reviewer_holds, list) and "document_download_and_extraction_not_performed" in reviewer_holds:
        routes.append("pdf_or_form_extraction_reviewer")
    return tuple(routes)


def _spans_by_source(rows: Iterable[PublicCitationSpanInventoryRowV5]) -> dict[str, dict[str, list[dict[str, Any]]]]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for row in sorted(rows, key=lambda item: (item.source_id, item.document_id, item.inventory_id)):
        grouped.setdefault(row.source_id, {}).setdefault(row.document_id, []).append(row.to_dict())
    return grouped


def _validate_span_row(row: Any, expected_source_id: str, expected_document_id: str) -> str:
    if not isinstance(row, Mapping):
        raise ValueError("citation span inventory rows must be objects")
    for flag in REQUIRED_FALSE_FLAGS:
        if row.get(flag) is not False:
            raise ValueError(f"{flag} must be false")
    if row.get("source_id") != expected_source_id:
        raise ValueError("row source_id must match source grouping")
    if row.get("document_id") != expected_document_id:
        raise ValueError("row document_id must match document grouping")
    document_record_ref = _required_text(row, "document_record_ref")
    if document_record_ref != _document_record_ref(expected_document_id):
        raise ValueError("document_record_ref must match grouped document_id")
    for key in ("inventory_id", "page_or_section_anchor"):
        _required_text(row, key)
    if not str(row["page_or_section_anchor"]).startswith(("page:", "section:")):
        raise ValueError("page_or_section_anchor must be a page or section anchor")
    if row.get("quoted_text_placeholder") != EXPECTED_QUOTED_TEXT_PLACEHOLDER:
        raise ValueError("quoted_text_placeholder must remain the approved placeholder")
    if row.get("normalized_text_placeholder") != EXPECTED_NORMALIZED_TEXT_PLACEHOLDER:
        raise ValueError("normalized_text_placeholder must remain the approved placeholder")
    _required_confidence(row.get("extraction_confidence"))
    if row.get("stale_source_hold") != EXPECTED_STALE_SOURCE_HOLD:
        raise ValueError("stale_source_hold must require freshness review")
    routes = set(_required_text_tuple(row, "reviewer_routing"))
    if not REQUIRED_REVIEWER_ROUTES.issubset(routes):
        raise ValueError("reviewer_routing must include public citation and requirement reviewers")
    _required_text_tuple(row, "rollback_notes")
    return document_record_ref


def _reject_prohibited_content(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized_key = str(key).lower()
            if normalized_key in PROHIBITED_KEYS and nested:
                raise ValueError(f"prohibited artifact key: {key}")
            _reject_prohibited_content(nested)
    elif isinstance(value, list):
        for nested in value:
            _reject_prohibited_content(nested)
    elif isinstance(value, str):
        lowered = value.lower()
        for phrase in PROHIBITED_PHRASES:
            if phrase in lowered:
                raise ValueError(f"prohibited claim phrase: {phrase}")


def _document_record_ref(document_id: str) -> str:
    if not isinstance(document_id, str) or not document_id:
        raise ValueError("document_id must be a non-empty string")
    return f"{DOCUMENT_RECORD_REF_PREFIX}{document_id}"


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _required_confidence(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("extraction_confidence must be a non-empty string")
    if value not in ALLOWED_CONFIDENCE_LABELS:
        raise ValueError("extraction_confidence must be an approved label")
    return value


def _required_text_tuple(mapping: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = mapping.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) and item for item in value):
        raise ValueError(f"{key} must be a non-empty string list")
    return tuple(value)


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted(set(values))
