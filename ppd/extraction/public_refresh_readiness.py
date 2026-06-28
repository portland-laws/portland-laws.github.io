"""Fixture-first public refresh readiness packet planning.

This module is intentionally side-effect free. It consumes only caller-provided
synthetic inactive preview rows and emits a deterministic readiness packet for
normalized document extraction planning.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Iterable, Mapping


SCHEMA_VERSION = "public-refresh-normalized-document-extraction-readiness-v1"
_ALLOWED_SOURCE_TYPES = {"public_html", "public_pdf", "public_form", "devhub_public"}
_ALLOWED_PREVIEW_STATES = {"inactive", "preview", "queued_preview"}
_ALLOWED_PATCH_OPERATIONS = {"add", "replace", "refresh"}
_ALLOWED_QUEUE_STATES = {"inactive", "preview", "queued_preview"}


@dataclass(frozen=True)
class ReadinessInputError(ValueError):
    """Raised when fixture rows are not safe offline readiness inputs."""

    message: str

    def __str__(self) -> str:
        return self.message


def build_readiness_packet(
    archive_patch_preview_rows: Iterable[Mapping[str, Any]],
    citation_impact_queue_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a normalized document extraction readiness packet.

    The packet plans placeholder IDs, extraction routes, citation-span checks,
    table and file-rule expectations, confidence placeholders, human-review
    routing, stale-source holds, rollback notes, and exact offline validation
    commands. It never opens URLs, downloads documents, persists raw output, or
    mutates active document records.
    """

    archive_rows = [_validate_archive_row(row, index) for index, row in enumerate(archive_patch_preview_rows)]
    citation_rows = [_validate_citation_row(row, index) for index, row in enumerate(citation_impact_queue_rows)]

    archive_by_source = {row["source_id"]: row for row in archive_rows}
    planned_documents = [_planned_document(row, citation_rows) for row in archive_rows]
    unmatched_citation_rows = [
        _citation_queue_summary(row, accepted=False, reason="source_not_in_inactive_archive_preview")
        for row in citation_rows
        if row["source_id"] not in archive_by_source
    ]

    stale_source_holds = [
        {
            "source_id": row["source_id"],
            "canonical_url": row["canonical_url"],
            "hold_reason": row.get("stale_reason") or "fixture_marked_stale",
            "release_condition": "fresh synthetic inactive preview row with reviewed source freshness metadata",
        }
        for row in archive_rows
        if bool(row.get("stale_source"))
    ]

    return {
        "schema_version": SCHEMA_VERSION,
        "input_policy": {
            "accepted_archive_rows": "synthetic inactive archive patch preview rows only",
            "accepted_citation_rows": "synthetic inactive citation impact queue rows only",
            "live_extraction": False,
            "live_crawling": False,
            "document_downloads": False,
            "raw_output_storage": False,
            "devhub_opened": False,
            "active_document_record_mutation": False,
            "official_actions": False,
        },
        "planned_documents": planned_documents,
        "unmatched_citation_queue_rows": unmatched_citation_rows,
        "stale_source_holds": stale_source_holds,
        "human_review_routing": _human_review_routing(planned_documents, unmatched_citation_rows, stale_source_holds),
        "rollback_notes": [
            "Discard this readiness packet and regenerate from fixtures if any source row is replaced.",
            "Do not promote placeholder normalized_document_id values into active DocumentRecord rows without a separately validated extraction run.",
            "If citation-span acceptance fails, keep impacted requirements in human review and leave existing guardrail bundles unchanged.",
        ],
        "offline_validation_commands": [
            ["python3", "-m", "py_compile", "ppd/extraction/public_refresh_readiness.py", "ppd/tests/test_public_refresh_readiness.py"],
            ["python3", "-m", "pytest", "ppd/tests/test_public_refresh_readiness.py"],
            ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
        ],
    }


def _validate_archive_row(row: Mapping[str, Any], index: int) -> dict[str, Any]:
    data = dict(row)
    _require(data, "source_id", "archive_patch_preview_rows", index)
    _require(data, "canonical_url", "archive_patch_preview_rows", index)
    _require(data, "source_type", "archive_patch_preview_rows", index)
    _require(data, "content_type", "archive_patch_preview_rows", index)
    _require(data, "title", "archive_patch_preview_rows", index)

    if data.get("synthetic") is not True:
        raise ReadinessInputError(f"archive row {index} is not marked synthetic")
    if data.get("archive_state") not in _ALLOWED_PREVIEW_STATES:
        raise ReadinessInputError(f"archive row {index} is not inactive preview state")
    if data.get("patch_operation") not in _ALLOWED_PATCH_OPERATIONS:
        raise ReadinessInputError(f"archive row {index} has unsupported patch operation")
    if data.get("source_type") not in _ALLOWED_SOURCE_TYPES:
        raise ReadinessInputError(f"archive row {index} has unsupported source_type")
    if data.get("raw_output_ref"):
        raise ReadinessInputError(f"archive row {index} includes raw_output_ref")
    if data.get("downloaded_document_ref"):
        raise ReadinessInputError(f"archive row {index} includes downloaded_document_ref")
    if data.get("active_document_record_id"):
        raise ReadinessInputError(f"archive row {index} targets an active DocumentRecord")

    data.setdefault("expected_tables", [])
    data.setdefault("expected_file_rules", [])
    data.setdefault("expected_form_fields", [])
    data.setdefault("expected_pdf_pages", None)
    data.setdefault("stale_source", False)
    return data


def _validate_citation_row(row: Mapping[str, Any], index: int) -> dict[str, Any]:
    data = dict(row)
    _require(data, "source_id", "citation_impact_queue_rows", index)
    _require(data, "impacted_requirement_id", "citation_impact_queue_rows", index)
    _require(data, "citation_span_hint", "citation_impact_queue_rows", index)

    if data.get("synthetic") is not True:
        raise ReadinessInputError(f"citation row {index} is not marked synthetic")
    if data.get("queue_state") not in _ALLOWED_QUEUE_STATES:
        raise ReadinessInputError(f"citation row {index} is not inactive queue state")
    if data.get("raw_output_ref"):
        raise ReadinessInputError(f"citation row {index} includes raw_output_ref")
    if data.get("official_action_ref"):
        raise ReadinessInputError(f"citation row {index} includes official_action_ref")

    return data


def _planned_document(row: Mapping[str, Any], citation_rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    matching_citations = [item for item in citation_rows if item["source_id"] == row["source_id"]]
    route = _route_for(row)
    citation_checks = [_citation_acceptance_check(row, item) for item in matching_citations]
    has_hold = bool(row.get("stale_source"))
    review_status = "hold_for_stale_source" if has_hold else "human_review_required"

    return {
        "normalized_document_placeholder_id": _placeholder_id(row),
        "source_id": row["source_id"],
        "canonical_url": row["canonical_url"],
        "title": row["title"],
        "document_type": row["source_type"],
        "patch_operation": row["patch_operation"],
        "extraction_route": route,
        "citation_span_acceptance_checks": citation_checks,
        "table_extraction_expectations": [
            {
                "label": str(item.get("label", "unnamed_table")),
                "required_columns": list(item.get("required_columns", [])),
                "acceptance": "table structure detected with source-order-preserved cells",
            }
            for item in row.get("expected_tables", [])
        ],
        "file_rule_extraction_expectations": [
            {
                "rule_id": str(item.get("rule_id", "unnamed_file_rule")),
                "expectation": str(item.get("expectation", "extract file preparation rule text")),
                "acceptance": "rule text has citation span and normalized process-stage candidate",
            }
            for item in row.get("expected_file_rules", [])
        ],
        "confidence_placeholders": {
            "document_parse_confidence": "pending_offline_extraction",
            "citation_span_confidence": "pending_fixture_span_check",
            "table_confidence": "pending_table_extraction",
            "file_rule_confidence": "pending_file_rule_extraction",
        },
        "human_review_status": review_status,
        "review_queue": "source_freshness" if has_hold else "normalized_document_extraction",
        "stale_source_hold": has_hold,
        "mutation_policy": "plan_only_no_active_document_record_mutation",
    }


def _route_for(row: Mapping[str, Any]) -> dict[str, Any]:
    content_type = str(row["content_type"]).lower()
    source_type = row["source_type"]
    if source_type == "public_pdf" or "pdf" in content_type:
        route_name = "pdf_text_tables_and_fields"
    elif source_type == "public_form":
        route_name = "form_fields_and_instructions"
    else:
        route_name = "html_structure_and_links"

    return {
        "route_name": route_name,
        "source_type": source_type,
        "content_type": row["content_type"],
        "allowed_inputs": "normalized fixture metadata only until a separate extraction run is approved",
        "live_fetch_allowed": False,
        "raw_body_persistence_allowed": False,
    }


def _citation_acceptance_check(source_row: Mapping[str, Any], citation_row: Mapping[str, Any]) -> dict[str, Any]:
    hint = str(citation_row.get("citation_span_hint", "")).strip()
    accepted = bool(hint) and citation_row["source_id"] == source_row["source_id"]
    return {
        "impacted_requirement_id": citation_row["impacted_requirement_id"],
        "citation_span_hint": hint,
        "acceptance_check": "non-empty fixture span hint tied to matching inactive preview source_id",
        "accepted_for_planning": accepted,
        "failure_routing": None if accepted else "human_review_required",
    }


def _citation_queue_summary(row: Mapping[str, Any], accepted: bool, reason: str) -> dict[str, Any]:
    return {
        "source_id": row["source_id"],
        "impacted_requirement_id": row["impacted_requirement_id"],
        "accepted_for_planning": accepted,
        "reason": reason,
        "routing": "human_review_required",
    }


def _human_review_routing(
    planned_documents: list[Mapping[str, Any]],
    unmatched_citation_rows: list[Mapping[str, Any]],
    stale_source_holds: list[Mapping[str, Any]],
) -> dict[str, Any]:
    return {
        "normalized_document_extraction": [
            item["normalized_document_placeholder_id"]
            for item in planned_documents
            if item["human_review_status"] == "human_review_required"
        ],
        "source_freshness": [item["source_id"] for item in stale_source_holds],
        "citation_queue_triage": [item["impacted_requirement_id"] for item in unmatched_citation_rows],
    }


def _placeholder_id(row: Mapping[str, Any]) -> str:
    digest = sha256(f"{row['source_id']}|{row['canonical_url']}".encode("utf-8")).hexdigest()[:16]
    return f"normdoc-placeholder-v1-{digest}"


def _require(data: Mapping[str, Any], field: str, collection: str, index: int) -> None:
    if field not in data or data[field] in (None, ""):
        raise ReadinessInputError(f"{collection} row {index} missing {field}")
