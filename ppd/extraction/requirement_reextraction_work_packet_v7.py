"""Fixture-first requirement re-extraction work packet v7.

Consumes only downstream requirement re-extraction queue v7 fixtures plus
synthetic normalized document fixtures. The packet assembles offline extraction
prompt rows, source evidence anchors, candidate RequirementNode placeholders,
confidence and human-review placeholders, unsupported-path notes, stale-citation
replacement reminders, and exact validation commands. It never crawls live
sites, downloads raw artifacts, opens DevHub, reads private documents, activates
guardrails, uploads, submits, certifies, pays, schedules, or makes legal or
permitting guarantees.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping

PACKET_SCHEMA = "ppd.requirement_reextraction_work_packet.v7"
PACKET_MODE = "fixture_first_requirement_reextraction_work_packet_v7"

CONSUMES_ONLY = {
    "downstream_requirement_reextraction_queue_v7_fixtures": True,
    "synthetic_normalized_document_fixtures": True,
}

SAFETY_BOUNDARIES = {
    "fixture_first": True,
    "live_crawl_executed": False,
    "raw_artifacts_downloaded": False,
    "devhub_opened": False,
    "private_documents_read": False,
    "guardrails_activated": False,
    "uploads_performed": False,
    "submissions_performed": False,
    "certifications_performed": False,
    "payments_performed": False,
    "scheduling_performed": False,
    "legal_or_permitting_guarantees_made": False,
    "active_requirement_mutation": False,
    "active_process_model_mutation": False,
    "active_guardrail_mutation": False,
}

EXACT_OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/extraction/requirement_reextraction_work_packet_v7.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_requirement_reextraction_work_packet_v7.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_requirement_reextraction_work_packet_v7.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_FORBIDDEN_TRUE_KEYS = frozenset(
    {
        "active_guardrail_mutation",
        "active_process_model_mutation",
        "active_requirement_mutation",
        "certifications_performed",
        "devhub_opened",
        "guardrails_activated",
        "legal_or_permitting_guarantees_made",
        "live_crawl_executed",
        "payments_performed",
        "private_documents_read",
        "raw_artifacts_downloaded",
        "scheduling_performed",
        "submissions_performed",
        "uploads_performed",
    }
)

_FORBIDDEN_FIELD_TOKENS = (
    "auth",
    "cookie",
    "credential",
    "har",
    "password",
    "raw_body",
    "raw_html",
    "screenshot",
    "session",
    "storage_state",
    "token",
    "trace",
)

_FORBIDDEN_TEXT = (
    "activated guardrail",
    "certified the application",
    "downloaded raw",
    "guaranteed permit",
    "legal advice",
    "live crawl completed",
    "opened devhub",
    "paid the fee",
    "private document",
    "scheduled inspection",
    "submitted the permit",
    "uploaded correction",
)


def load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("requirement re-extraction work packet v7 fixture must be a JSON object")
    return payload


def build_work_packet_v7_from_fixture(path: str | Path) -> dict[str, Any]:
    fixture_path = Path(path)
    manifest = load_json(fixture_path)
    refs = _required_mapping(manifest, "fixture_refs")
    queue = load_json(_resolve(fixture_path, _required_text(refs, "downstream_queue_v7")))
    normalized_documents = load_json(_resolve(fixture_path, _required_text(refs, "synthetic_normalized_documents")))
    return build_work_packet_v7(queue, normalized_documents, fixture_ref=str(fixture_path))


def build_work_packet_v7(
    downstream_queue: Mapping[str, Any],
    normalized_documents: Mapping[str, Any],
    *,
    fixture_ref: str = "fixture://requirement_reextraction_work_packet_v7",
) -> dict[str, Any]:
    _validate_downstream_queue_shape(downstream_queue)
    docs_by_id = _documents_by_id(normalized_documents)
    work_rows = _mapping_list(downstream_queue.get("source_to_extraction_work_rows"), "source_to_extraction_work_rows")
    citation_rows = _by_source(downstream_queue.get("citation_span_refresh_expectations"), "citation_span_refresh_expectations")
    family_rows = _by_source(downstream_queue.get("requirement_family_hints"), "requirement_family_hints")
    stale_rows = _by_source(downstream_queue.get("stale_evidence_hold_carry_forward_rows"), "stale_evidence_hold_carry_forward_rows")
    reviewer_rows = _by_source(downstream_queue.get("reviewer_assignment_placeholders"), "reviewer_assignment_placeholders")

    prompt_rows: list[dict[str, Any]] = []
    evidence_anchors: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    review_placeholders: list[dict[str, Any]] = []
    unsupported_notes: list[dict[str, Any]] = []
    stale_reminders: list[dict[str, Any]] = []

    for row in work_rows:
        source_id = _required_text(row, "source_id")
        doc_id = _required_text(row, "normalized_document_id_placeholder")
        document = docs_by_id.get(doc_id)
        if document is None:
            raise ValueError(f"missing synthetic normalized document fixture for {doc_id}")
        if _required_text(document, "source_id") != source_id:
            raise ValueError(f"normalized document {doc_id} source_id does not match work row")

        prompt_rows.append(_prompt_row(row, document))
        evidence_anchors.append(_evidence_anchor(row, document, citation_rows[source_id]))
        candidates.append(_candidate_requirement_node(row, family_rows[source_id]))
        review_placeholders.append(_review_placeholder(row, reviewer_rows[source_id]))
        unsupported_notes.append(_unsupported_note(row))
        stale_reminders.append(_stale_reminder(row, citation_rows[source_id], stale_rows[source_id]))

    packet = {
        "schema": PACKET_SCHEMA,
        "mode": PACKET_MODE,
        "consumes_only": copy.deepcopy(CONSUMES_ONLY),
        "source_fixture_refs": [
            {
                "fixture_role": "requirement_reextraction_work_packet_v7_input_manifest",
                "fixture_ref": fixture_ref,
                "downstream_queue_schema": _required_text(downstream_queue, "schema"),
                "normalized_document_fixture_id": _required_text(normalized_documents, "fixture_id"),
            }
        ],
        "safety_boundaries": copy.deepcopy(SAFETY_BOUNDARIES),
        "extraction_prompt_rows": prompt_rows,
        "source_evidence_anchors": evidence_anchors,
        "candidate_requirement_node_placeholders": candidates,
        "confidence_and_human_review_placeholders": review_placeholders,
        "unsupported_path_notes": unsupported_notes,
        "stale_citation_replacement_reminders": stale_reminders,
        "exact_offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
    }
    validate_work_packet_v7(packet)
    return packet


def validate_work_packet_v7(packet: Mapping[str, Any]) -> None:
    if packet.get("schema") != PACKET_SCHEMA:
        raise ValueError("requirement re-extraction work packet v7 must use the v7 schema")
    if packet.get("mode") != PACKET_MODE:
        raise ValueError("requirement re-extraction work packet v7 must declare fixture-first mode")
    if packet.get("consumes_only") != CONSUMES_ONLY:
        raise ValueError("requirement re-extraction work packet v7 must consume only downstream queue v7 and synthetic normalized document fixtures")
    if packet.get("safety_boundaries") != SAFETY_BOUNDARIES:
        raise ValueError("requirement re-extraction work packet v7 safety boundaries were changed")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        raise ValueError("requirement re-extraction work packet v7 validation commands must match exactly")
    _reject_forbidden_content(packet, "packet")

    required_sections = (
        "source_fixture_refs",
        "extraction_prompt_rows",
        "source_evidence_anchors",
        "candidate_requirement_node_placeholders",
        "confidence_and_human_review_placeholders",
        "unsupported_path_notes",
        "stale_citation_replacement_reminders",
    )
    for key in required_sections:
        if not _mapping_list(packet.get(key), key):
            raise ValueError(f"requirement re-extraction work packet v7 missing {key}")

    prompt_ids = _source_ids(packet["extraction_prompt_rows"], "extraction_prompt_rows")
    for key in required_sections[2:]:
        if _source_ids(packet[key], key) != prompt_ids:
            raise ValueError(f"{key} must cover every prompt-row source and only those sources")

    for index, row in enumerate(packet["extraction_prompt_rows"]):
        if row.get("requires_live_access") is not False:
            raise ValueError(f"extraction_prompt_rows[{index}] must remain offline-only")
        if row.get("raw_document_ref") is not None:
            raise ValueError(f"extraction_prompt_rows[{index}] must not reference raw documents")
        _required_text(row, "extraction_prompt")

    for index, row in enumerate(packet["source_evidence_anchors"]):
        if row.get("anchor_source") != "synthetic_normalized_document_fixture":
            raise ValueError(f"source_evidence_anchors[{index}] must use synthetic normalized document fixtures")
        if row.get("requires_live_access") is not False:
            raise ValueError(f"source_evidence_anchors[{index}] must remain offline-only")

    for index, row in enumerate(packet["candidate_requirement_node_placeholders"]):
        if row.get("formalization_status") != "inactive_placeholder_only":
            raise ValueError(f"candidate_requirement_node_placeholders[{index}] must remain inactive")
        if row.get("source_evidence_ids") == []:
            raise ValueError(f"candidate_requirement_node_placeholders[{index}] must cite placeholder evidence")

    for index, row in enumerate(packet["confidence_and_human_review_placeholders"]):
        if row.get("confidence") is not None:
            raise ValueError(f"confidence_and_human_review_placeholders[{index}] must not assert confidence")
        if row.get("human_review_status") != "pending_fixture_review":
            raise ValueError(f"confidence_and_human_review_placeholders[{index}] must remain pending fixture review")

    for index, row in enumerate(packet["unsupported_path_notes"]):
        if row.get("unsupported_path_status") != "not_supported_by_this_offline_packet":
            raise ValueError(f"unsupported_path_notes[{index}] must stay unsupported")
    for index, row in enumerate(packet["stale_citation_replacement_reminders"]):
        if row.get("replacement_status") != "reminder_only_pending_human_review":
            raise ValueError(f"stale_citation_replacement_reminders[{index}] must remain reminder-only")


def _prompt_row(work_row: Mapping[str, Any], document: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _required_text(work_row, "source_id")
    document_id = _required_text(document, "document_id")
    title = _required_text(document, "title")
    section_ids = [_required_text(section, "section_id") for section in _mapping_list(document.get("sections"), "sections")]
    return {
        "source_id": source_id,
        "prompt_row_id": f"extraction-prompt::{source_id}",
        "normalized_document_id": document_id,
        "source_title": title,
        "section_ids": section_ids,
        "extraction_prompt": (
            f"Use only synthetic normalized document fixture {document_id} ({title}) and downstream queue v7 row "
            f"{_required_text(work_row, 'work_row_id')} to draft candidate RequirementNode placeholders. "
            "Anchor every candidate to fixture section ids; leave confidence blank; route uncertain or consequential paths to human review."
        ),
        "raw_document_ref": None,
        "requires_live_access": False,
    }


def _evidence_anchor(
    work_row: Mapping[str, Any],
    document: Mapping[str, Any],
    citation_row: Mapping[str, Any],
) -> dict[str, Any]:
    source_id = _required_text(work_row, "source_id")
    section = _mapping_list(document.get("sections"), "sections")[0]
    return {
        "source_id": source_id,
        "source_evidence_id": f"source-evidence::{source_id}",
        "citation_placeholder_id": _required_text(citation_row, "citation_placeholder_id"),
        "normalized_document_id": _required_text(document, "document_id"),
        "section_id": _required_text(section, "section_id"),
        "anchor_text": _required_text(section, "text"),
        "anchor_source": "synthetic_normalized_document_fixture",
        "requires_live_access": False,
    }


def _candidate_requirement_node(work_row: Mapping[str, Any], family_row: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _required_text(work_row, "source_id")
    requirement_id = _required_text(work_row, "requirement_placeholder_id")
    family = _required_text(family_row, "requirement_family_hint")
    return {
        "source_id": source_id,
        "requirement_id": requirement_id,
        "source_evidence_ids": [f"source-evidence::{source_id}"],
        "requirement_type": family,
        "subject": "CANDIDATE_PLACEHOLDER: reviewer must extract subject from fixture evidence",
        "action": "CANDIDATE_PLACEHOLDER: reviewer must extract action from fixture evidence",
        "object": "CANDIDATE_PLACEHOLDER: reviewer must extract object from fixture evidence",
        "conditions": ["CANDIDATE_PLACEHOLDER: fixture-backed conditions only"],
        "deadline_or_temporal_scope": "CANDIDATE_PLACEHOLDER: fixture-backed temporal scope only",
        "permit_types": ["CANDIDATE_PLACEHOLDER: reviewer must confirm permit type"],
        "process_stage": "CANDIDATE_PLACEHOLDER: reviewer must confirm process stage",
        "confidence": None,
        "human_review_status": "pending_fixture_review",
        "formalization_status": "inactive_placeholder_only",
    }


def _review_placeholder(work_row: Mapping[str, Any], reviewer_row: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _required_text(work_row, "source_id")
    return {
        "source_id": source_id,
        "requirement_id": _required_text(work_row, "requirement_placeholder_id"),
        "confidence": None,
        "confidence_basis": "placeholder_until_fixture_evidence_reviewed",
        "human_review_status": "pending_fixture_review",
        "owner_placeholder": _required_text(reviewer_row, "owner_placeholder"),
        "review_note": "Reviewer must compare fixture evidence before assigning confidence or formalizing a requirement.",
    }


def _unsupported_note(work_row: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _required_text(work_row, "source_id")
    return {
        "source_id": source_id,
        "note_id": f"unsupported-path::{source_id}",
        "unsupported_path_status": "not_supported_by_this_offline_packet",
        "unsupported_actions": [
            "live public crawl",
            "raw artifact download",
            "DevHub access",
            "guardrail activation",
            "official upload, submission, certification, payment, or scheduling action",
        ],
        "note": "This packet is offline planning evidence only and cannot replace reviewer disposition or official PP&D guidance.",
    }


def _stale_reminder(
    work_row: Mapping[str, Any],
    citation_row: Mapping[str, Any],
    stale_row: Mapping[str, Any],
) -> dict[str, Any]:
    source_id = _required_text(work_row, "source_id")
    return {
        "source_id": source_id,
        "reminder_id": f"stale-citation-replacement::{source_id}",
        "citation_placeholder_id": _required_text(citation_row, "citation_placeholder_id"),
        "hold_id": _required_text(stale_row, "hold_id"),
        "replacement_status": "reminder_only_pending_human_review",
        "replacement_instruction": "Replace stale citation spans only after reviewer confirms fixture-backed source evidence anchors.",
    }


def _validate_downstream_queue_shape(queue: Mapping[str, Any]) -> None:
    if queue.get("schema") != "ppd.downstream_requirement_reextraction_queue.v7":
        raise ValueError("work packet v7 must consume a downstream requirement re-extraction queue v7 fixture")
    if queue.get("consumes_only") != {"source_freshness_diff_intake_v7_fixtures": True}:
        raise ValueError("downstream queue fixture must consume only source freshness diff intake v7 fixtures")
    if queue.get("exact_offline_validation_commands") in (None, []):
        raise ValueError("downstream queue fixture must declare exact offline validation commands")
    _reject_forbidden_content(queue, "downstream_queue")
    required = (
        "source_to_extraction_work_rows",
        "citation_span_refresh_expectations",
        "requirement_family_hints",
        "stale_evidence_hold_carry_forward_rows",
        "reviewer_assignment_placeholders",
    )
    for key in required:
        _mapping_list(queue.get(key), key)
    source_ids = _source_ids(queue["source_to_extraction_work_rows"], "source_to_extraction_work_rows")
    for key in required[1:]:
        if _source_ids(queue[key], key) != source_ids:
            raise ValueError(f"downstream queue {key} must cover every work-row source")
    for row in queue["source_to_extraction_work_rows"]:
        if row.get("requires_live_crawl") is not False or row.get("requires_devhub") is not False:
            raise ValueError("downstream queue work rows must remain offline-only")


def _documents_by_id(documents_fixture: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    if documents_fixture.get("fixture_kind") != "synthetic_normalized_documents_v7":
        raise ValueError("normalized document fixture must be synthetic_normalized_documents_v7")
    rows = _mapping_list(documents_fixture.get("documents"), "documents")
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        document_id = _required_text(row, "document_id")
        if document_id in result:
            raise ValueError(f"duplicate normalized document fixture: {document_id}")
        _mapping_list(row.get("sections"), "sections")
        result[document_id] = row
    return result


def _resolve(base_file: Path, relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        raise ValueError("fixture references must be relative paths")
    return (base_file.parent / path).resolve()


def _by_source(value: Any, label: str) -> dict[str, Mapping[str, Any]]:
    rows = _mapping_list(value, label)
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        source_id = _required_text(row, "source_id")
        if source_id in result:
            raise ValueError(f"{label} contains duplicate source_id: {source_id}")
        result[source_id] = row
    return result


def _mapping_list(value: Any, label: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    rows: list[Mapping[str, Any]] = []
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            raise ValueError(f"{label}[{index}] must be an object")
        rows.append(row)
    return rows


def _source_ids(rows: Any, label: str) -> set[str]:
    ids: set[str] = set()
    for row in _mapping_list(rows, label):
        source_id = _required_text(row, "source_id")
        if source_id in ids:
            raise ValueError(f"{label} contains duplicate source_id: {source_id}")
        ids.add(source_id)
    return ids


def _required_mapping(row: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = row.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"missing required object field: {key}")
    return value


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required text field: {key}")
    return value.strip()


def _reject_forbidden_content(value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            lower_key = key_text.lower()
            if key_text in _FORBIDDEN_TRUE_KEYS and child is True:
                raise ValueError(f"forbidden live/private/mutating claim at {path}.{key_text}")
            if any(token in lower_key for token in _FORBIDDEN_FIELD_TOKENS):
                raise ValueError(f"forbidden artifact/session field at {path}.{key_text}")
            if key_text == "legal_or_permitting_guarantees" and child not in ([], None):
                raise ValueError("legal or permitting guarantees are not allowed")
            _reject_forbidden_content(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_content(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(token in lowered for token in _FORBIDDEN_TEXT):
            raise ValueError(f"forbidden claim at {path}")
