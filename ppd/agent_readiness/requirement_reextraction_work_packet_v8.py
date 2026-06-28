"""Fixture-first requirement re-extraction work packet v8.

Consumes only downstream requirement re-extraction queue v8 fixtures and
normalized public document record fixtures. It assembles source-scoped offline
work items for reviewer-facing requirement re-extraction planning. It never
performs live crawling, downloads raw artifacts, opens DevHub, reads private
documents, uploads, submits, certifies, pays, schedules, mutates active models,
or makes legal or permitting guarantees.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from ppd.agent_readiness.normalized_public_document_record_dry_run_v5 import (
    assemble_document_records_from_fixture,
)

PACKET_SCHEMA = "ppd.requirement_reextraction_work_packet.v8"
PACKET_MODE = "fixture_first_requirement_reextraction_work_packet_v8"
DOWNSTREAM_QUEUE_SCHEMA = "ppd.downstream_requirement_reextraction_queue.v8"
NORMALIZED_RECORD_FIXTURE_KIND = "normalized_public_document_record_fixture"

EXACT_OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/requirement_reextraction_work_packet_v8.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_requirement_reextraction_work_packet_v8.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_requirement_reextraction_work_packet_v8.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

BOUNDARIES: dict[str, bool] = {
    "fixture_first": True,
    "downstream_requirement_reextraction_queue_v8_fixtures_only": True,
    "normalized_public_document_record_fixtures_only": True,
    "live_crawl_executed": False,
    "raw_artifacts_downloaded": False,
    "downloaded_documents_persisted": False,
    "devhub_opened": False,
    "private_documents_read": False,
    "private_session_or_auth_artifacts_created": False,
    "uploads_performed": False,
    "submissions_performed": False,
    "certifications_performed": False,
    "payments_performed": False,
    "scheduling_performed": False,
    "official_action_completed": False,
    "legal_or_permitting_guarantees_made": False,
    "active_requirement_mutation": False,
    "active_process_model_mutation": False,
    "active_guardrail_mutation": False,
    "active_mutation": False,
}

REQUIRED_FALSE_FLAGS = tuple(key for key, value in BOUNDARIES.items() if value is False)
FORBIDDEN_TRUE_KEYS = frozenset(REQUIRED_FALSE_FLAGS) | frozenset(
    {
        "requires_live_crawl",
        "requires_devhub",
        "requires_private_document_access",
        "active_mutation_allowed",
        "legal_or_permitting_guarantee",
        "official_action_completed",
    }
)
PROHIBITED_KEYS = frozenset(
    {
        "auth_state",
        "browser_trace",
        "cookie",
        "credential",
        "credentials",
        "devhub_session",
        "har",
        "password",
        "private_document",
        "private_upload",
        "raw_body",
        "raw_html",
        "raw_pdf",
        "session_state",
        "screenshot",
        "storage_state",
        "token",
        "trace",
    }
)
PROHIBITED_PHRASES = (
    "devhub opened",
    "document downloaded",
    "downloaded raw artifact",
    "guaranteed approval",
    "legal advice",
    "live crawl completed",
    "permit guaranteed",
    "private document read",
    "raw artifact downloaded",
    "session cookie",
    "submitted application",
    "uploaded document",
)

ALLOWED_REQUIREMENT_TYPES = frozenset(
    {
        "obligation",
        "prohibition",
        "permission",
        "precondition",
        "exception",
        "deadline",
        "fee_trigger",
        "license_requirement",
        "document_requirement",
        "action_gate",
    }
)


def build_requirement_reextraction_work_packet_v8_from_fixture(path: str | Path) -> dict[str, Any]:
    fixture_path = Path(path)
    fixture = _load_json(fixture_path)
    refs = fixture.get("fixture_refs")
    if not isinstance(refs, Mapping):
        raise ValueError("fixture must declare fixture_refs")
    queue = _load_json(_resolve(fixture_path, _required_text(refs, "downstream_queue_v8")))
    record_refs = refs.get("normalized_public_document_records")
    if not isinstance(record_refs, list) or not record_refs:
        raise ValueError("fixture_refs.normalized_public_document_records must be a non-empty list")
    records: list[dict[str, Any]] = []
    for ref in record_refs:
        if not isinstance(ref, str) or not ref:
            raise ValueError("normalized document record fixture refs must be non-empty strings")
        records.extend(assemble_document_records_from_fixture(_resolve(fixture_path, ref)))
    return build_requirement_reextraction_work_packet_v8(queue, records, fixture_ref=str(fixture_path))


def build_requirement_reextraction_work_packet_v8(
    downstream_queue: Mapping[str, Any],
    normalized_document_records: Iterable[Mapping[str, Any]],
    *,
    fixture_ref: str = "fixture://requirement-reextraction-work-packet-v8",
) -> dict[str, Any]:
    validate_downstream_requirement_reextraction_queue_v8_fixture(downstream_queue)
    records = tuple(normalized_document_records)
    if not records:
        raise ValueError("at least one normalized public document record fixture is required")
    _reject_prohibited_content(records, "normalized_document_records")
    record_by_source = _records_by_source(records)

    candidates = _mapping_list(downstream_queue.get("candidate_rows"), "candidate_rows")
    work_items: list[dict[str, Any]] = []
    skipped_rows: list[dict[str, Any]] = []
    for candidate in candidates:
        source_id = _required_text(candidate, "source_id")
        record = record_by_source.get(source_id)
        if record is None:
            skipped_rows.append(_skipped_candidate_row(candidate, "missing_normalized_public_document_record_fixture"))
            continue
        if candidate.get("unsupported_path") is True:
            skipped_rows.append(_skipped_candidate_row(candidate, "unsupported_path_requires_reviewer_note_only"))
            continue
        work_items.append(_work_item(candidate, record))

    if not work_items:
        raise ValueError("at least one source-scoped extraction work item is required")

    packet = {
        "schema": PACKET_SCHEMA,
        "mode": PACKET_MODE,
        "fixture_ref": fixture_ref,
        "consumes_only": {
            "downstream_requirement_reextraction_queue_v8_fixtures": True,
            "normalized_public_document_record_fixtures": True,
        },
        "boundaries": dict(BOUNDARIES),
        "source_scoped_extraction_work_items": work_items,
        "citation_span_inputs": [_citation_span_input(item) for item in work_items],
        "requirement_type_expectations": [_requirement_type_expectation(item) for item in work_items],
        "confidence_and_human_review_placeholders": [
            _confidence_and_human_review_placeholder(item) for item in work_items
        ],
        "unsupported_path_notes": [_unsupported_path_note(row) for row in _mapping_list(downstream_queue.get("unsupported_path_notes"), "unsupported_path_notes")],
        "skipped_candidate_rows": skipped_rows,
        "exact_offline_validation_commands": [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS],
    }
    validate_requirement_reextraction_work_packet_v8(packet)
    return packet


def validate_downstream_requirement_reextraction_queue_v8_fixture(queue: Mapping[str, Any]) -> None:
    _reject_prohibited_content(queue, "downstream_queue")
    if queue.get("schema") != DOWNSTREAM_QUEUE_SCHEMA:
        raise ValueError("downstream queue fixture must use v8 schema")
    if queue.get("fixture_first") is not True:
        raise ValueError("downstream queue fixture must declare fixture_first true")
    boundaries = queue.get("boundaries")
    if not isinstance(boundaries, Mapping):
        raise ValueError("downstream queue fixture must declare boundaries")
    for flag in REQUIRED_FALSE_FLAGS:
        if boundaries.get(flag) is not False:
            raise ValueError(f"downstream queue boundary must declare {flag}=false")
    candidate_rows = _mapping_list(queue.get("candidate_rows"), "candidate_rows")
    for row in candidate_rows:
        if _required_text(row, "expected_requirement_type") not in ALLOWED_REQUIREMENT_TYPES:
            raise ValueError("candidate row has unsupported expected_requirement_type")
        if row.get("requires_live_crawl") is not False:
            raise ValueError("candidate rows must remain offline-only")
        if row.get("requires_devhub") is not False:
            raise ValueError("candidate rows must not require DevHub")
    _mapping_list(queue.get("unsupported_path_notes"), "unsupported_path_notes")


def validate_requirement_reextraction_work_packet_v8(packet: Mapping[str, Any]) -> None:
    _reject_prohibited_content(packet, "packet")
    if packet.get("schema") != PACKET_SCHEMA:
        raise ValueError("work packet must use v8 schema")
    if packet.get("mode") != PACKET_MODE:
        raise ValueError("work packet must declare fixture-first v8 mode")
    if packet.get("boundaries") != BOUNDARIES:
        raise ValueError("work packet boundaries changed")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        raise ValueError("exact offline validation commands changed")
    consumes_only = packet.get("consumes_only")
    if consumes_only != {
        "downstream_requirement_reextraction_queue_v8_fixtures": True,
        "normalized_public_document_record_fixtures": True,
    }:
        raise ValueError("work packet must consume only committed fixtures")

    work_items = _mapping_list(packet.get("source_scoped_extraction_work_items"), "source_scoped_extraction_work_items")
    work_ids = {_required_text(row, "work_item_id") for row in work_items}
    for row in work_items:
        if row.get("work_status") != "assembled_from_fixtures_pending_human_review":
            raise ValueError("work item must remain pending human review")
        for flag in ("requires_live_crawl", "requires_devhub", "requires_private_document_access", "active_mutation_allowed"):
            if row.get(flag) is not False:
                raise ValueError(f"work item must declare {flag}=false")
        if _required_text(row, "expected_requirement_type") not in ALLOWED_REQUIREMENT_TYPES:
            raise ValueError("work item has unsupported expected requirement type")
        _mapping_list(row.get("citation_span_inputs"), "work_item.citation_span_inputs")

    for section in (
        "citation_span_inputs",
        "requirement_type_expectations",
        "confidence_and_human_review_placeholders",
    ):
        rows = _mapping_list(packet.get(section), section)
        if {_required_text(row, "work_item_id") for row in rows} != work_ids:
            raise ValueError(f"{section} must cover every work item exactly")

    for row in _mapping_list(packet.get("confidence_and_human_review_placeholders"), "confidence_and_human_review_placeholders"):
        if row.get("confidence_placeholder") != "pending_fixture_backed_extraction_review":
            raise ValueError("missing confidence placeholder")
        if row.get("human_review_status_placeholder") != "human_review_required_before_release":
            raise ValueError("missing human-review placeholder")

    for row in _mapping_list(packet.get("unsupported_path_notes"), "unsupported_path_notes"):
        if row.get("unsupported_path_status") != "note_only_no_extraction_work_item":
            raise ValueError("unsupported paths must remain note-only")

    skipped = packet.get("skipped_candidate_rows")
    if not isinstance(skipped, list):
        raise ValueError("skipped_candidate_rows must be a list")
    for row in skipped:
        if not isinstance(row, Mapping):
            raise ValueError("skipped candidate rows must be objects")
        _required_text(row, "candidate_row_id")
        _required_text(row, "skip_reason")
        if row.get("active_mutation_allowed") is not False:
            raise ValueError("skipped rows must not allow active mutation")


def _work_item(candidate: Mapping[str, Any], record: Mapping[str, Any]) -> dict[str, Any]:
    candidate_id = _required_text(candidate, "candidate_row_id")
    source_id = _required_text(candidate, "source_id")
    citation_inputs = _record_citation_inputs(record)
    return {
        "work_item_id": f"work-packet-v8::{candidate_id}",
        "candidate_row_id": candidate_id,
        "source_id": source_id,
        "canonical_url": _required_text(candidate, "canonical_url"),
        "normalized_document_id": _required_text(record, "document_id"),
        "document_title": _required_text(record, "title"),
        "expected_requirement_type": _required_text(candidate, "expected_requirement_type"),
        "requirement_expectation_note": _required_text(candidate, "expectation_note"),
        "source_scope": "single_normalized_public_document_record_fixture",
        "citation_span_inputs": citation_inputs,
        "work_status": "assembled_from_fixtures_pending_human_review",
        "requires_live_crawl": False,
        "requires_devhub": False,
        "requires_private_document_access": False,
        "active_mutation_allowed": False,
        "official_action_completed": False,
    }


def _record_citation_inputs(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    spans = _mapping_list(record.get("citation_spans"), "citation_spans")
    inputs: list[dict[str, Any]] = []
    for span in spans:
        inputs.append(
            {
                "source_id": _required_text(record, "source_id"),
                "document_id": _required_text(record, "document_id"),
                "citation_span_id": _required_text(span, "span_id"),
                "anchor": _required_text(span, "anchor"),
                "quoted_text_placeholder": "placeholder:quoted-text-not-stored-fixture-only",
                "normalized_text_placeholder": "placeholder:normalized-text-pending-requirement-extraction",
            }
        )
    return inputs


def _citation_span_input(work_item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "work_item_id": _required_text(work_item, "work_item_id"),
        "source_id": _required_text(work_item, "source_id"),
        "normalized_document_id": _required_text(work_item, "normalized_document_id"),
        "citation_span_inputs": list(_mapping_list(work_item.get("citation_span_inputs"), "citation_span_inputs")),
    }


def _requirement_type_expectation(work_item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "work_item_id": _required_text(work_item, "work_item_id"),
        "source_id": _required_text(work_item, "source_id"),
        "expected_requirement_type": _required_text(work_item, "expected_requirement_type"),
        "expectation_status": "reviewer_must_confirm_from_fixture_citation_spans",
    }


def _confidence_and_human_review_placeholder(work_item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "work_item_id": _required_text(work_item, "work_item_id"),
        "source_id": _required_text(work_item, "source_id"),
        "confidence_placeholder": "pending_fixture_backed_extraction_review",
        "human_review_status_placeholder": "human_review_required_before_release",
        "formalization_status_placeholder": "not_formalized",
    }


def _unsupported_path_note(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": _required_text(row, "source_id"),
        "note_id": _required_text(row, "note_id"),
        "note_placeholder": _required_text(row, "note_placeholder"),
        "unsupported_path_status": "note_only_no_extraction_work_item",
    }


def _skipped_candidate_row(candidate: Mapping[str, Any], reason: str) -> dict[str, Any]:
    return {
        "candidate_row_id": _required_text(candidate, "candidate_row_id"),
        "source_id": _required_text(candidate, "source_id"),
        "skip_reason": reason,
        "active_mutation_allowed": False,
        "official_action_completed": False,
    }


def _records_by_source(records: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for record in records:
        source_id = _required_text(record, "source_id")
        if source_id in result:
            raise ValueError(f"duplicate normalized public document record source_id: {source_id}")
        _required_text(record, "document_id")
        _required_text(record, "title")
        _mapping_list(record.get("citation_spans"), "record.citation_spans")
        result[source_id] = record
    return result


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fixture must be a JSON object")
    return payload


def _resolve(base_file: Path, relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        raise ValueError("fixture references must be relative paths")
    return (base_file.parent / path).resolve()


def _mapping_list(value: Any, label: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    rows: list[Mapping[str, Any]] = []
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            raise ValueError(f"{label}[{index}] must be an object")
        rows.append(row)
    return rows


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required text field: {key}")
    return value.strip()


def _reject_prohibited_content(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in FORBIDDEN_TRUE_KEYS and child is True:
                raise ValueError(f"forbidden live/private/mutating claim at {path}.{key_text}")
            if key_text in PROHIBITED_KEYS and child:
                raise ValueError(f"prohibited artifact key at {path}.{key_text}")
            _reject_prohibited_content(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_prohibited_content(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        for phrase in PROHIBITED_PHRASES:
            if phrase in lowered:
                raise ValueError(f"prohibited claim phrase at {path}")
