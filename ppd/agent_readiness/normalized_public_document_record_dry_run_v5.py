"""Fixture-first normalized public document record dry-run v5.

This module consumes committed public metadata manifest fixtures only. It does
not crawl live sites, download documents, persist raw bodies, open DevHub, or
make legal or permitting guarantees.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

OFFLINE_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

ALLOWED_MANIFEST_DRY_RUN = "public_metadata_manifest_dry_run_v5"
CONFIDENCE_BY_KIND = {
    "public_html": "synthetic-metadata-high",
    "public_pdf": "synthetic-metadata-medium",
    "public_form": "synthetic-metadata-medium",
    "devhub_public": "synthetic-metadata-low",
}
REQUIRED_FALSE_FLAGS = (
    "live_crawl_performed",
    "raw_body_persisted",
    "devhub_opened",
    "legal_or_permitting_guarantee",
    "active_mutation_enabled",
    "mutation_performed",
    "document_downloaded",
    "downloaded_document_claim",
)
PRIVATE_ARTIFACT_KEYS = {
    "auth_state",
    "auth_storage",
    "browser_trace",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "devhub_session",
    "har",
    "har_path",
    "local_private_path",
    "mfa_secret",
    "password",
    "private_upload",
    "session",
    "session_file",
    "session_state",
    "screenshot",
    "screenshot_path",
    "token",
    "trace",
    "trace_path",
}
RAW_ARTIFACT_KEYS = {"raw_body", "raw_body_artifact", "raw_html", "raw_pdf", "body_text"}
LEGAL_GUARANTEE_KEYS = {"legal_guarantee", "permitting_guarantee", "approval_guarantee"}
ACTIVE_MUTATION_KEYS = {"active_mutation", "active_mutation_enabled", "mutation_enabled", "side_effects_permitted"}


@dataclass(frozen=True)
class NormalizedPublicDocumentRecordDryRunV5:
    """Synthetic DocumentRecord row assembled from metadata-only fixtures."""

    document_id: str
    source_id: str
    title: str
    document_type: str
    language: str
    sections: tuple[dict[str, Any], ...]
    tables: tuple[dict[str, Any], ...]
    links: tuple[dict[str, Any], ...]
    pdf_pages: tuple[dict[str, Any], ...]
    form_fields: tuple[dict[str, Any], ...]
    citation_spans: tuple[dict[str, Any], ...]
    content_hash: str
    extraction_confidence: str
    reviewer_holds: tuple[str, ...]
    rollback_notes: tuple[str, ...]
    validation_commands: tuple[tuple[str, ...], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "source_id": self.source_id,
            "title": self.title,
            "document_type": self.document_type,
            "language": self.language,
            "sections": list(self.sections),
            "tables": list(self.tables),
            "links": list(self.links),
            "pdf_pages": list(self.pdf_pages),
            "form_fields": list(self.form_fields),
            "citation_spans": list(self.citation_spans),
            "content_hash": self.content_hash,
            "extraction_confidence": self.extraction_confidence,
            "reviewer_holds": list(self.reviewer_holds),
            "rollback_notes": list(self.rollback_notes),
            "validation_commands": [list(command) for command in self.validation_commands],
        }


def load_manifest_fixture(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    validate_manifest_fixture(manifest)
    return manifest


def validate_manifest_fixture(manifest: dict[str, Any]) -> None:
    if manifest.get("dry_run") != ALLOWED_MANIFEST_DRY_RUN:
        raise ValueError(f"unsupported manifest dry_run: {manifest.get('dry_run')!r}")
    for flag in REQUIRED_FALSE_FLAGS:
        if manifest.get(flag) is not False:
            raise ValueError(f"manifest must declare {flag}=false")
    _reject_prohibited_artifacts(manifest, path="manifest")
    sources = manifest.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError("manifest must include synthetic public metadata sources")
    expected = manifest.get("expected_document_record_ids")
    if not isinstance(expected, list) or not expected:
        raise ValueError("manifest missing expected synthetic DocumentRecord rows")
    for source in sources:
        _validate_source_fixture(source)


def assemble_document_records(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    validate_manifest_fixture(manifest)
    records = [_record_from_source(source) for source in manifest["sources"]]
    record_dicts = [record.to_dict() for record in records]
    validate_document_records(manifest, record_dicts)
    return record_dicts


def assemble_document_records_from_fixture(path: Path) -> list[dict[str, Any]]:
    return assemble_document_records(load_manifest_fixture(path))


def validate_document_records(manifest: dict[str, Any], records: list[dict[str, Any]]) -> None:
    expected_ids = set(manifest["expected_document_record_ids"])
    actual_ids = {record.get("document_id") for record in records}
    if actual_ids != expected_ids:
        raise ValueError("missing synthetic DocumentRecord rows")
    by_source = {source["source_id"]: source for source in manifest["sources"]}
    for record in records:
        _reject_prohibited_artifacts(record, path=f"record:{record.get('document_id')}")
        source = by_source.get(record.get("source_id"))
        if source is None:
            raise ValueError("DocumentRecord source_id is not present in metadata manifest")
        _require_non_empty_list(record, "sections", "missing section placeholders")
        if int(source.get("metadata", {}).get("table_count", 0)) > 0:
            _require_non_empty_list(record, "tables", "missing table placeholders")
        if source["source_type"] == "public_pdf":
            _require_non_empty_list(record, "pdf_pages", "missing PDF page placeholders")
        else:
            _require_non_empty_list(record, "links", "missing link placeholders")
        if source["source_type"] == "public_form":
            _require_non_empty_list(record, "form_fields", "missing form-field placeholders")
        _require_non_empty_list(record, "citation_spans", "missing citation-span placeholders")
        _require_text(record, "extraction_confidence", "missing extraction confidence labels")
        _require_non_empty_list(record, "reviewer_holds", "missing reviewer holds")
        _require_non_empty_list(record, "rollback_notes", "missing rollback notes")
        commands = record.get("validation_commands")
        if commands != [list(command) for command in OFFLINE_VALIDATION_COMMANDS]:
            raise ValueError("missing validation commands")


def _validate_source_fixture(source: Any) -> None:
    if not isinstance(source, dict):
        raise ValueError("manifest sources must be objects")
    _reject_prohibited_artifacts(source, path=f"source:{source.get('source_id')}")
    for key in ("source_id", "source_type", "title", "content_hash", "canonical_url", "metadata_manifest_ref"):
        _required_text(source, key)
    if not source["metadata_manifest_ref"].startswith("metadata-manifest://public-dry-run-v5/"):
        raise ValueError("source missing metadata manifest reference")
    if source["source_type"] == "devhub_authenticated":
        raise ValueError("private/session/auth artifacts are not allowed in public dry-run v5")


def _record_from_source(source: dict[str, Any]) -> NormalizedPublicDocumentRecordDryRunV5:
    source_id = _required_text(source, "source_id")
    source_type = _required_text(source, "source_type")
    title = _required_text(source, "title")
    content_hash = _required_text(source, "content_hash")
    document_id = f"docrec-v5-{source_id}"
    reviewer_holds = tuple(source.get("reviewer_holds") or _default_reviewer_holds(source_type))
    rollback_notes = tuple(source.get("rollback_notes") or _default_rollback_notes(source_id))
    return NormalizedPublicDocumentRecordDryRunV5(
        document_id=document_id,
        source_id=source_id,
        title=title,
        document_type=_document_type(source),
        language=source.get("language", "en"),
        sections=_section_placeholders(source),
        tables=_table_placeholders(source),
        links=_link_references(source),
        pdf_pages=_pdf_page_placeholders(source),
        form_fields=_form_field_placeholders(source),
        citation_spans=_citation_span_placeholders(source, document_id),
        content_hash=content_hash,
        extraction_confidence=CONFIDENCE_BY_KIND.get(source_type, "synthetic-metadata-review-required"),
        reviewer_holds=reviewer_holds,
        rollback_notes=rollback_notes,
        validation_commands=OFFLINE_VALIDATION_COMMANDS,
    )


def _required_text(source: dict[str, Any], key: str) -> str:
    value = source.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"source fixture missing required text field: {key}")
    return value


def _require_text(record: dict[str, Any], key: str, message: str) -> None:
    value = record.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(message)


def _require_non_empty_list(record: dict[str, Any], key: str, message: str) -> None:
    value = record.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(message)


def _reject_prohibited_artifacts(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower()
            if normalized in PRIVATE_ARTIFACT_KEYS and nested:
                raise ValueError(f"private/session/auth artifacts are not allowed: {path}.{key}")
            if normalized in RAW_ARTIFACT_KEYS and nested:
                raise ValueError(f"raw body artifacts are not allowed: {path}.{key}")
            if normalized in LEGAL_GUARANTEE_KEYS and nested:
                raise ValueError(f"legal or permitting guarantees are not allowed: {path}.{key}")
            if normalized in ACTIVE_MUTATION_KEYS and nested:
                raise ValueError(f"active mutation flags are not allowed: {path}.{key}")
            if normalized in {"document_downloaded", "downloaded_document_claim", "pdf_downloaded"} and nested:
                raise ValueError(f"downloaded document claims are not allowed: {path}.{key}")
            _reject_prohibited_artifacts(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_prohibited_artifacts(nested, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if "live crawl performed" in lowered or "live_crawl_performed=true" in lowered:
            raise ValueError("live crawl claims are not allowed")
        if "legal guarantee" in lowered or "permit approval guaranteed" in lowered:
            raise ValueError("legal or permitting guarantees are not allowed")
        if "session cookie" in lowered or "auth token" in lowered:
            raise ValueError("private/session/auth artifacts are not allowed")
        if "raw body artifact" in lowered or "raw html artifact" in lowered:
            raise ValueError("raw body artifacts are not allowed")
        if "active mutation enabled" in lowered:
            raise ValueError("active mutation flags are not allowed")
        if "document downloaded" in lowered or "downloaded document claim" in lowered:
            raise ValueError("downloaded document claims are not allowed")


def _document_type(source: dict[str, Any]) -> str:
    if source.get("document_type"):
        return str(source["document_type"])
    source_type = source.get("source_type")
    if source_type == "public_pdf":
        return "public_pdf_placeholder"
    if source_type == "public_form":
        return "public_form_placeholder"
    if source_type == "devhub_public":
        return "devhub_public_help_placeholder"
    return "public_html_placeholder"


def _section_placeholders(source: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    headings = source.get("metadata", {}).get("headings") or [source["title"]]
    return tuple(
        {
            "section_id": f"{source['source_id']}-section-{index}",
            "heading": heading,
            "outline_status": "placeholder_from_public_metadata_only",
            "raw_body_stored": False,
        }
        for index, heading in enumerate(headings, start=1)
    )


def _table_placeholders(source: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    table_count = int(source.get("metadata", {}).get("table_count", 0))
    return tuple(
        {
            "table_id": f"{source['source_id']}-table-{index}",
            "status": "placeholder_pending_public_extraction",
            "raw_cells_stored": False,
        }
        for index in range(1, table_count + 1)
    )


def _link_references(source: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    links = source.get("metadata", {}).get("links", ())
    return tuple(
        {
            "link_id": f"{source['source_id']}-link-{index}",
            "href": link["href"],
            "label": link.get("label", "public metadata link"),
            "reference_only": True,
        }
        for index, link in enumerate(links, start=1)
    )


def _pdf_page_placeholders(source: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    page_count = int(source.get("metadata", {}).get("pdf_page_count", 0))
    return tuple(
        {
            "page_number": page_number,
            "status": "placeholder_no_pdf_downloaded",
            "text_stored": False,
        }
        for page_number in range(1, page_count + 1)
    )


def _form_field_placeholders(source: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    fields = source.get("metadata", {}).get("form_fields", ())
    return tuple(
        {
            "field_id": f"{source['source_id']}-field-{index}",
            "name": field["name"],
            "field_type": field.get("field_type", "unknown"),
            "status": "placeholder_no_form_document_downloaded",
        }
        for index, field in enumerate(fields, start=1)
    )


def _citation_span_placeholders(source: dict[str, Any], document_id: str) -> tuple[dict[str, Any], ...]:
    canonical_url = _required_text(source, "canonical_url")
    return (
        {
            "citation_id": f"{document_id}-citation-1",
            "source_id": source["source_id"],
            "canonical_url": canonical_url,
            "span_status": "placeholder_metadata_only_no_raw_body",
            "start_offset": None,
            "end_offset": None,
        },
    )


def _default_reviewer_holds(source_type: str) -> tuple[str, ...]:
    holds = [
        "human_review_required_before_promotion",
        "metadata_only_record_not_authoritative",
    ]
    if source_type in {"public_pdf", "public_form"}:
        holds.append("document_download_and_extraction_not_performed")
    return tuple(holds)


def _default_rollback_notes(source_id: str) -> tuple[str, ...]:
    return (
        f"Remove synthetic DocumentRecord rows derived from {source_id} if fixture inputs change.",
        "Rollback is offline-only and does not alter public sources, DevHub state, or downloaded documents.",
    )
