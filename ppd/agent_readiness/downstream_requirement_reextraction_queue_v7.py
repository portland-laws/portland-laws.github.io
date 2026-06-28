"""Fixture-first downstream requirement re-extraction queue v7.

Consumes only source freshness diff intake v7 fixtures and assembles offline
source-to-extraction work rows, candidate RequirementNode packet placeholders,
source-evidence continuity checks, mapping placeholders, review flags, reviewer
owner placeholders, and exact validation commands. This module never performs a
live crawl, downloads artifacts, opens DevHub, reads private documents, uploads,
submits, certifies, pays, schedules, mutates active guardrails, completes
official actions, or makes legal or permitting guarantees.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Mapping

from ppd.source_freshness_diff_v7 import (
    build_source_freshness_diff_v7_from_paths,
    validate_source_freshness_diff_v7,
)

QUEUE_SCHEMA = "ppd.downstream_requirement_reextraction_queue.v7"
QUEUE_MODE = "fixture_first_downstream_reextraction_queue_v7"
CONSUMES_ONLY = {"source_freshness_diff_intake_v7_fixtures": True}

EXACT_OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/downstream_requirement_reextraction_queue_v7.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_downstream_requirement_reextraction_queue_v7.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_downstream_requirement_reextraction_queue_v7.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

BOUNDARIES = {
    "fixture_first": True,
    "source_freshness_diff_intake_v7_fixtures_only": True,
    "downstream_queue_only": True,
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

FORBIDDEN_TRUE_KEYS = frozenset(
    {
        "active_guardrail_mutation",
        "active_mutation",
        "active_mutation_allowed",
        "active_process_model_mutation",
        "active_requirement_mutation",
        "certifications_performed",
        "crawl_executed",
        "devhub_opened",
        "documents_downloaded",
        "downloaded_documents_persisted",
        "legal_or_permitting_guarantees_made",
        "live_crawl_executed",
        "official_action_completed",
        "payments_performed",
        "private_documents_read",
        "private_session_or_auth_artifacts_created",
        "raw_artifacts_downloaded",
        "requires_devhub",
        "requires_live_crawl",
        "requires_private_document_access",
        "scheduling_performed",
        "submissions_performed",
        "uploads_performed",
    }
)

FORBIDDEN_FIELD_TOKENS = (
    "auth",
    "cookie",
    "credential",
    "download",
    "har",
    "password",
    "payment",
    "private",
    "raw_body",
    "raw_html",
    "screenshot",
    "session",
    "storage_state",
    "token",
    "trace",
)

ALLOWED_FORBIDDEN_TOKEN_KEYS = frozenset(
    {
        "downloaded_documents_persisted",
        "private_documents_read",
        "private_session_or_auth_artifacts_created",
        "raw_artifacts_downloaded",
        "requires_private_document_access",
    }
)

REQUIREMENT_FAMILY_BY_SOURCE_HINT = {
    "devhub": "devhub_action_gate",
    "faq": "devhub_action_gate",
    "fee": "fee_trigger",
    "pay": "fee_trigger",
    "plans": "document_requirement",
    "submit": "document_requirement",
    "tools": "process_precondition",
}

REQUIRED_QUEUE_SECTIONS = (
    "work_packet_refs",
    "reextraction_queue_refs",
    "source_fixture_refs",
    "normalized_document_fixture_refs",
    "source_to_extraction_work_rows",
    "changed_section_placeholders",
    "extraction_prompt_rows",
    "source_evidence_anchor_placeholders",
    "source_evidence_continuity_checks",
    "citation_span_refresh_expectations",
    "requirement_family_hints",
    "candidate_requirement_node_placeholders",
    "candidate_requirement_add_rows",
    "candidate_requirement_update_rows",
    "candidate_requirement_deprecate_rows",
    "permit_type_mapping_placeholders",
    "process_stage_mapping_placeholders",
    "confidence_and_human_review_placeholders",
    "conflict_and_stale_evidence_review_flags",
    "unsupported_path_notes",
    "stale_citation_replacement_reminders",
    "stale_evidence_hold_carry_forward_rows",
    "reviewer_assignment_placeholders",
)

COVERAGE_SECTIONS = tuple(key for key in REQUIRED_QUEUE_SECTIONS if key != "source_fixture_refs")


def load_json(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("downstream requirement re-extraction fixture must be a JSON object")
    return payload


def build_downstream_requirement_reextraction_queue_v7_from_fixture(path: str | Path) -> dict[str, Any]:
    fixture_path = Path(path)
    fixture = load_json(fixture_path)
    refs = fixture.get("source_freshness_diff_fixture_refs")
    if not isinstance(refs, Mapping):
        raise ValueError("fixture must declare source_freshness_diff_fixture_refs")
    diff = build_source_freshness_diff_v7_from_paths(
        _resolve(fixture_path, _required_text(refs, "handoff_manifest")),
        _resolve(fixture_path, _required_text(refs, "prior_metadata")),
        _resolve(fixture_path, _required_text(refs, "current_metadata")),
    )
    return build_downstream_requirement_reextraction_queue_v7(diff, fixture_ref=str(fixture_path))


def build_downstream_requirement_reextraction_queue_v7(
    source_freshness_diff: Mapping[str, Any],
    *,
    fixture_ref: str = "fixture://source_freshness_diff_v7",
) -> dict[str, Any]:
    validate_source_freshness_diff_v7(source_freshness_diff)
    changed_rows = _mapping_list(source_freshness_diff.get("changed_source_rows"), "changed_source_rows")
    citation_rows = _by_source(source_freshness_diff.get("affected_citation_placeholders"), "affected_citation_placeholders")
    requirement_rows = _by_source(source_freshness_diff.get("affected_requirement_placeholders"), "affected_requirement_placeholders")
    stale_rows = _by_source(source_freshness_diff.get("stale_evidence_hold_updates"), "stale_evidence_hold_updates")
    reviewer_rows = _by_source(source_freshness_diff.get("reviewer_owner_placeholders"), "reviewer_owner_placeholders")

    queue = {
        "schema": QUEUE_SCHEMA,
        "mode": QUEUE_MODE,
        "consumes_only": copy.deepcopy(CONSUMES_ONLY),
        "work_packet_refs": [_work_packet_ref(row) for row in changed_rows],
        "reextraction_queue_refs": [_reextraction_queue_ref(row) for row in changed_rows],
        "source_fixture_refs": [_source_fixture_ref(source_freshness_diff, fixture_ref)],
        "normalized_document_fixture_refs": [_normalized_document_fixture_ref(row) for row in changed_rows],
        "boundaries": copy.deepcopy(BOUNDARIES),
        "source_to_extraction_work_rows": [_work_row(row, requirement_rows[_source_id(row)]) for row in changed_rows],
        "changed_section_placeholders": [_section_placeholder(row) for row in changed_rows],
        "extraction_prompt_rows": [_extraction_prompt_row(row) for row in changed_rows],
        "source_evidence_anchor_placeholders": [
            _source_evidence_anchor_placeholder(row, citation_rows[_source_id(row)]) for row in changed_rows
        ],
        "source_evidence_continuity_checks": [
            _source_evidence_continuity_check(row, citation_rows[_source_id(row)]) for row in changed_rows
        ],
        "citation_span_refresh_expectations": [
            _citation_expectation(row, citation_rows[_source_id(row)]) for row in changed_rows
        ],
        "requirement_family_hints": [_requirement_family_hint(row) for row in changed_rows],
        "candidate_requirement_node_placeholders": [
            _candidate_requirement_node_placeholder(row, requirement_rows[_source_id(row)]) for row in changed_rows
        ],
        "candidate_requirement_add_rows": [
            _candidate_requirement_change_row(row, requirement_rows[_source_id(row)], "add") for row in changed_rows
        ],
        "candidate_requirement_update_rows": [
            _candidate_requirement_change_row(row, requirement_rows[_source_id(row)], "update") for row in changed_rows
        ],
        "candidate_requirement_deprecate_rows": [
            _candidate_requirement_change_row(row, requirement_rows[_source_id(row)], "deprecate") for row in changed_rows
        ],
        "permit_type_mapping_placeholders": [_permit_type_mapping_placeholder(row) for row in changed_rows],
        "process_stage_mapping_placeholders": [_process_stage_mapping_placeholder(row) for row in changed_rows],
        "confidence_and_human_review_placeholders": [
            _confidence_and_human_review_placeholder(row, requirement_rows[_source_id(row)]) for row in changed_rows
        ],
        "conflict_and_stale_evidence_review_flags": [
            _conflict_and_stale_evidence_review_flag(row, stale_rows[_source_id(row)]) for row in changed_rows
        ],
        "unsupported_path_notes": [_unsupported_path_note(row) for row in changed_rows],
        "stale_citation_replacement_reminders": [
            _stale_citation_replacement_reminder(row, citation_rows[_source_id(row)]) for row in changed_rows
        ],
        "stale_evidence_hold_carry_forward_rows": [
            _stale_hold_carry_forward(row, stale_rows[_source_id(row)]) for row in changed_rows
        ],
        "reviewer_assignment_placeholders": [
            _reviewer_assignment(row, reviewer_rows[_source_id(row)]) for row in changed_rows
        ],
        "exact_offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
    }
    validate_downstream_requirement_reextraction_queue_v7(queue)
    return queue


def validate_downstream_requirement_reextraction_queue_v7(queue: Mapping[str, Any]) -> None:
    if queue.get("schema") != QUEUE_SCHEMA:
        raise ValueError("downstream requirement re-extraction queue must use v7 schema")
    if queue.get("mode") != QUEUE_MODE:
        raise ValueError("downstream requirement re-extraction queue must declare fixture-first mode")
    if queue.get("consumes_only") != CONSUMES_ONLY:
        raise ValueError("downstream requirement re-extraction queue must consume only source freshness diff intake v7 fixtures")
    if queue.get("boundaries") != BOUNDARIES:
        raise ValueError("downstream requirement re-extraction queue boundaries were changed")
    if queue.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        raise ValueError("downstream requirement re-extraction queue validation commands must match exactly")
    _reject_forbidden_content(queue, "queue")

    for key in REQUIRED_QUEUE_SECTIONS:
        if not _mapping_list(queue.get(key), key):
            raise ValueError(f"downstream requirement re-extraction queue missing {key}")

    work_ids = _source_ids(queue["source_to_extraction_work_rows"], "source_to_extraction_work_rows")
    for key in COVERAGE_SECTIONS:
        if _source_ids(queue[key], key) != work_ids:
            raise ValueError(f"{key} must cover every work-row source and only those sources")

    for index, row in enumerate(queue["work_packet_refs"]):
        if row.get("packet_status") != "work_packet_reference_required_before_extraction":
            raise ValueError(f"work_packet_refs[{index}] missing work packet reference status")
        _required_text(row, "work_packet_ref_id")
    for index, row in enumerate(queue["source_to_extraction_work_rows"]):
        if row.get("requires_live_crawl") is not False or row.get("requires_devhub") is not False:
            raise ValueError(f"source_to_extraction_work_rows[{index}] must remain offline-only")
        if row.get("work_status") != "queued_for_fixture_backed_reextraction_review":
            raise ValueError(f"source_to_extraction_work_rows[{index}] has unsupported work_status")
        _required_text(row, "normalized_document_id_placeholder")
        _required_text(row, "requirement_placeholder_id")
    for index, row in enumerate(queue["normalized_document_fixture_refs"]):
        if row.get("fixture_status") != "placeholder_required_before_extraction":
            raise ValueError(f"normalized_document_fixture_refs[{index}] must require fixture placeholders")
        _required_text(row, "normalized_document_id_placeholder")
    for index, row in enumerate(queue["extraction_prompt_rows"]):
        if row.get("prompt_status") != "placeholder_pending_reviewer_authored_prompt":
            raise ValueError(f"extraction_prompt_rows[{index}] must keep prompt placeholders")
        _required_text(row, "prompt_row_id")
        _required_text(row, "prompt_placeholder")
    for index, row in enumerate(queue["source_evidence_anchor_placeholders"]):
        if row.get("anchor_status") != "placeholder_until_fixture_span_reviewed":
            raise ValueError(f"source_evidence_anchor_placeholders[{index}] must keep source evidence anchors pending")
        _required_text(row, "source_evidence_anchor_placeholder_id")
    for index, row in enumerate(queue["source_evidence_continuity_checks"]):
        if row.get("continuity_check_required") is not True:
            raise ValueError(f"source_evidence_continuity_checks[{index}] must require continuity checks")
        if row.get("continuity_status") != "pending_reviewer_trace_from_prior_to_current_fixture":
            raise ValueError(f"source_evidence_continuity_checks[{index}] missing continuity status")
        _required_text(row, "prior_citation_placeholder_id")
        _required_text(row, "current_source_evidence_anchor_placeholder_id")
    for index, row in enumerate(queue["citation_span_refresh_expectations"]):
        if row.get("refresh_expected") is not True or row.get("refresh_source") != "normalized_document_fixture_only":
            raise ValueError(f"citation_span_refresh_expectations[{index}] must be fixture-only")
    for index, row in enumerate(queue["candidate_requirement_node_placeholders"]):
        if row.get("node_status") != "candidate_placeholder_pending_fixture_backed_extraction":
            raise ValueError(f"candidate_requirement_node_placeholders[{index}] must stay as candidate placeholders")
        if row.get("formalization_status_placeholder") != "not_formalized":
            raise ValueError(f"candidate_requirement_node_placeholders[{index}] missing formalization status placeholder")
        _required_text(row, "candidate_requirement_node_placeholder_id")
        _required_text(row, "requirement_placeholder_id")
    for section, expected_kind in (
        ("candidate_requirement_add_rows", "add"),
        ("candidate_requirement_update_rows", "update"),
        ("candidate_requirement_deprecate_rows", "deprecate"),
    ):
        for index, row in enumerate(queue[section]):
            if row.get("candidate_change_kind") != expected_kind:
                raise ValueError(f"{section}[{index}] missing {expected_kind} candidate row")
            if row.get("candidate_status") != "placeholder_pending_fixture_backed_reviewer_decision":
                raise ValueError(f"{section}[{index}] missing candidate status")
            _required_text(row, "candidate_row_id")
            _required_text(row, "requirement_placeholder_id")
    for index, row in enumerate(queue["permit_type_mapping_placeholders"]):
        if row.get("mapping_status") != "placeholder_pending_fixture_backed_permit_type_review":
            raise ValueError(f"permit_type_mapping_placeholders[{index}] missing mapping placeholder")
        _required_text(row, "permit_type_placeholder")
    for index, row in enumerate(queue["process_stage_mapping_placeholders"]):
        if row.get("mapping_status") != "placeholder_pending_fixture_backed_process_stage_review":
            raise ValueError(f"process_stage_mapping_placeholders[{index}] missing mapping placeholder")
        _required_text(row, "process_stage_placeholder")
    for index, row in enumerate(queue["confidence_and_human_review_placeholders"]):
        if row.get("confidence_placeholder") != "pending_fixture_backed_review":
            raise ValueError(f"confidence_and_human_review_placeholders[{index}] missing confidence placeholder")
        if row.get("human_review_status_placeholder") != "human_review_required_before_release":
            raise ValueError(f"confidence_and_human_review_placeholders[{index}] missing human-review placeholder")
    for index, row in enumerate(queue["conflict_and_stale_evidence_review_flags"]):
        if row.get("conflict_review_required") is not True:
            raise ValueError(f"conflict_and_stale_evidence_review_flags[{index}] missing conflict review flag")
        if row.get("stale_evidence_review_required") is not True:
            raise ValueError(f"conflict_and_stale_evidence_review_flags[{index}] missing stale-evidence review flag")
        if row.get("review_status") != "pending_reviewer_disposition_before_release":
            raise ValueError(f"conflict_and_stale_evidence_review_flags[{index}] missing review status")
    for index, row in enumerate(queue["unsupported_path_notes"]):
        if row.get("unsupported_path_status") != "notes_required_before_release":
            raise ValueError(f"unsupported_path_notes[{index}] must preserve unsupported-path notes")
        _required_text(row, "note_placeholder")
    for index, row in enumerate(queue["stale_citation_replacement_reminders"]):
        if row.get("replacement_required") is not True:
            raise ValueError(f"stale_citation_replacement_reminders[{index}] must require stale citation replacement")
        _required_text(row, "replacement_reminder")
    for index, row in enumerate(queue["stale_evidence_hold_carry_forward_rows"]):
        if row.get("carry_forward") is not True or row.get("release_requires_reviewer_disposition") is not True:
            raise ValueError(f"stale_evidence_hold_carry_forward_rows[{index}] must carry forward reviewer holds")
    for index, row in enumerate(queue["reviewer_assignment_placeholders"]):
        if row.get("assignment_status") != "placeholder_unassigned":
            raise ValueError(f"reviewer_assignment_placeholders[{index}] must stay unassigned placeholders")
        _required_text(row, "owner_placeholder")


def _work_packet_ref(changed: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "work_packet_ref_id": f"work-packet::{source_id}",
        "packet_status": "work_packet_reference_required_before_extraction",
        "packet_scope": "candidate_requirement_node_reextraction_v7",
    }


def _reextraction_queue_ref(changed: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "queue_ref_id": f"reextraction-queue-ref::{source_id}",
        "queue_schema": QUEUE_SCHEMA,
        "queue_status": "queued_for_fixture_backed_reextraction_review",
    }


def _source_fixture_ref(diff: Mapping[str, Any], fixture_ref: str) -> dict[str, Any]:
    source = diff.get("source")
    if not isinstance(source, Mapping):
        raise ValueError("source freshness diff missing source references")
    return {
        "source_id": "source_freshness_diff_intake_v7",
        "fixture_role": "source_freshness_diff_intake_v7",
        "fixture_ref": fixture_ref,
        "handoff_manifest_id": _required_text(source, "handoff_manifest_id"),
        "prior_metadata_id": _required_text(source, "prior_metadata_id"),
        "current_metadata_id": _required_text(source, "current_metadata_id"),
    }


def _normalized_document_fixture_ref(changed: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "normalized_document_fixture_ref_id": f"normalized-document-fixture::{source_id}",
        "normalized_document_id_placeholder": _required_text(changed, "current_normalized_document_id"),
        "fixture_status": "placeholder_required_before_extraction",
        "raw_artifact_ref": None,
    }


def _work_row(changed: Mapping[str, Any], requirement: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "work_row_id": f"source-to-extraction::{source_id}",
        "source_id": source_id,
        "canonical_url": _required_text(changed, "canonical_url"),
        "change_kind": _required_text(changed, "change_kind"),
        "normalized_document_id_placeholder": _required_text(changed, "current_normalized_document_id"),
        "requirement_placeholder_id": _required_text(requirement, "placeholder_id"),
        "work_status": "queued_for_fixture_backed_reextraction_review",
        "requires_live_crawl": False,
        "requires_devhub": False,
        "requires_private_document_access": False,
        "active_mutation_allowed": False,
        "official_action_completed": False,
    }


def _section_placeholder(changed: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "section_placeholder_id": f"changed-section::{source_id}",
        "expected_basis": "source_freshness_diff_v7_changed_source_row",
        "section_status": "placeholder_until_normalized_document_sections_reviewed",
        "changed_section_claim_made": False,
    }


def _extraction_prompt_row(changed: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "prompt_row_id": f"extraction-prompt::{source_id}",
        "prompt_placeholder": "reviewer must provide fixture-backed requirement extraction prompt before release",
        "prompt_status": "placeholder_pending_reviewer_authored_prompt",
    }


def _source_evidence_anchor_placeholder(changed: Mapping[str, Any], citation: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "source_evidence_anchor_placeholder_id": f"source-evidence-anchor::{source_id}",
        "citation_placeholder_id": _required_text(citation, "placeholder_id"),
        "normalized_document_id_placeholder": _required_text(changed, "current_normalized_document_id"),
        "anchor_status": "placeholder_until_fixture_span_reviewed",
    }


def _source_evidence_continuity_check(changed: Mapping[str, Any], citation: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "continuity_check_id": f"source-evidence-continuity::{source_id}",
        "prior_citation_placeholder_id": _required_text(citation, "placeholder_id"),
        "current_source_evidence_anchor_placeholder_id": f"source-evidence-anchor::{source_id}",
        "continuity_check_required": True,
        "continuity_status": "pending_reviewer_trace_from_prior_to_current_fixture",
    }


def _citation_expectation(changed: Mapping[str, Any], citation: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "citation_placeholder_id": _required_text(citation, "placeholder_id"),
        "refresh_expected": True,
        "refresh_source": "normalized_document_fixture_only",
        "span_status": "needs_fixture_backed_span_refresh",
        "carry_forward_reason": _required_text(citation, "reason"),
    }


def _requirement_family_hint(changed: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    haystack = f"{source_id} {_required_text(changed, 'canonical_url')} {changed.get('title', '')}".lower()
    family = "process_precondition"
    for token, candidate in REQUIREMENT_FAMILY_BY_SOURCE_HINT.items():
        if token in haystack:
            family = candidate
            break
    return {
        "source_id": source_id,
        "family_hint_id": f"requirement-family::{source_id}",
        "requirement_family_hint": family,
        "hint_status": "reviewer_must_confirm_from_fixture_evidence",
        "legal_or_permitting_guarantee": False,
    }


def _candidate_requirement_node_placeholder(changed: Mapping[str, Any], requirement: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "candidate_requirement_node_placeholder_id": f"candidate-requirement-node::{source_id}",
        "requirement_placeholder_id": _required_text(requirement, "placeholder_id"),
        "requirement_node_type": "RequirementNode",
        "node_status": "candidate_placeholder_pending_fixture_backed_extraction",
        "formalization_status_placeholder": "not_formalized",
    }


def _candidate_requirement_change_row(
    changed: Mapping[str, Any], requirement: Mapping[str, Any], candidate_change_kind: str
) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "candidate_row_id": f"candidate-requirement-{candidate_change_kind}::{source_id}",
        "candidate_change_kind": candidate_change_kind,
        "requirement_placeholder_id": _required_text(requirement, "placeholder_id"),
        "candidate_status": "placeholder_pending_fixture_backed_reviewer_decision",
        "active_mutation_allowed": False,
    }


def _permit_type_mapping_placeholder(changed: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "permit_type_mapping_id": f"permit-type-mapping::{source_id}",
        "permit_type_placeholder": "reviewer must map permit types from normalized fixture evidence before release",
        "mapping_status": "placeholder_pending_fixture_backed_permit_type_review",
    }


def _process_stage_mapping_placeholder(changed: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "process_stage_mapping_id": f"process-stage-mapping::{source_id}",
        "process_stage_placeholder": "reviewer must map process stage from normalized fixture evidence before release",
        "mapping_status": "placeholder_pending_fixture_backed_process_stage_review",
    }


def _confidence_and_human_review_placeholder(changed: Mapping[str, Any], requirement: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "requirement_placeholder_id": _required_text(requirement, "placeholder_id"),
        "confidence_placeholder": "pending_fixture_backed_review",
        "human_review_status_placeholder": "human_review_required_before_release",
    }


def _conflict_and_stale_evidence_review_flag(changed: Mapping[str, Any], stale: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "review_flag_id": f"conflict-stale-evidence-review::{source_id}",
        "prior_hold_status": _required_text(stale, "hold_status"),
        "conflict_review_required": True,
        "stale_evidence_review_required": True,
        "review_status": "pending_reviewer_disposition_before_release",
    }


def _unsupported_path_note(changed: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "unsupported_path_note_id": f"unsupported-path-note::{source_id}",
        "note_placeholder": "reviewer must record unsupported email/manual/non-DevHub paths observed in fixture evidence",
        "unsupported_path_status": "notes_required_before_release",
    }


def _stale_citation_replacement_reminder(changed: Mapping[str, Any], citation: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "stale_citation_replacement_reminder_id": f"stale-citation-replacement::{source_id}",
        "citation_placeholder_id": _required_text(citation, "placeholder_id"),
        "replacement_required": True,
        "replacement_reminder": "replace stale citation spans from normalized document fixtures before release",
    }


def _stale_hold_carry_forward(changed: Mapping[str, Any], stale: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "hold_id": f"stale-evidence-hold::{source_id}",
        "prior_hold_status": _required_text(stale, "hold_status"),
        "carry_forward": True,
        "release_condition": _required_text(stale, "release_condition"),
        "release_requires_reviewer_disposition": True,
    }


def _reviewer_assignment(changed: Mapping[str, Any], reviewer: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _source_id(changed)
    return {
        "source_id": source_id,
        "assignment_id": f"reviewer-assignment::{source_id}",
        "owner_placeholder": _required_text(reviewer, "owner_placeholder"),
        "review_stage": "downstream_requirement_reextraction_queue_v7",
        "assignment_status": "placeholder_unassigned",
        "human_reviewer_required": True,
    }


def _resolve(base_file: Path, relative_path: str) -> Path:
    path = Path(relative_path)
    if path.is_absolute():
        raise ValueError("fixture references must be relative paths")
    return (base_file.parent / path).resolve()


def _by_source(value: Any, label: str) -> dict[str, Mapping[str, Any]]:
    rows = _mapping_list(value, label)
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        source_id = _source_id(row)
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
        source_id = _source_id(row)
        if source_id in ids:
            raise ValueError(f"{label} contains duplicate source_id: {source_id}")
        ids.add(source_id)
    return ids


def _source_id(row: Mapping[str, Any]) -> str:
    return _required_text(row, "source_id")


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
            if key_text in FORBIDDEN_TRUE_KEYS and child is True:
                raise ValueError(f"forbidden live/private/mutating claim at {path}.{key_text}")
            if any(token in lower_key for token in FORBIDDEN_FIELD_TOKENS):
                if lower_key not in ALLOWED_FORBIDDEN_TOKEN_KEYS:
                    raise ValueError(f"forbidden artifact/private/session field at {path}.{key_text}")
            if key_text == "legal_or_permitting_guarantees" and child not in ([], None):
                raise ValueError("legal or permitting guarantees are not allowed")
            _reject_forbidden_content(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_content(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if "guaranteed permit" in lowered or "legal advice" in lowered or "live crawl completed" in lowered:
            raise ValueError(f"forbidden claim at {path}")
