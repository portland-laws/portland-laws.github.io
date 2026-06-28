"""Fixture-first public refresh requirement re-extraction queue v2.

Consumes only synthetic normalized document extraction readiness rows and builds
an offline reviewer queue for candidate RequirementNode update planning. This
module does not perform live extraction, live crawling, document downloads,
DevHub access, raw output storage, active requirement/process/guardrail
mutation, or official actions.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

QUEUE_VERSION = "public-refresh-requirement-reextraction-queue-v2"
MODE = "fixture_first_offline_review_only"
INPUT_CONTRACT = "synthetic_normalized_document_extraction_readiness_rows_only"

EXACT_OFFLINE_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "-m", "py_compile", "ppd/agent_readiness/public_refresh_requirement_reextraction_queue_v2.py"),
    ("python3", "-m", "pytest", "ppd/tests/test_public_refresh_requirement_reextraction_queue_v2.py"),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

ALLOWED_HUMAN_REVIEW_STATUSES = frozenset(
    {
        "needs_human_review",
        "blocked_by_stale_source",
        "blocked_by_conflicting_evidence",
        "ready_for_reviewer_triage",
    }
)

ALLOWED_FORMALIZATION_HOLDS = frozenset(
    {
        "hold_until_source_evidence_reviewed",
        "hold_until_conflict_resolved",
        "hold_until_stale_source_cleared",
        "hold_until_requirement_owner_approves",
    }
)

PROHIBITED_ACTIONS: tuple[str, ...] = (
    "live_extraction",
    "live_crawling",
    "document_download",
    "raw_output_storage",
    "devhub_access",
    "active_requirement_mutation",
    "active_process_model_mutation",
    "active_guardrail_mutation",
    "official_action",
    "submission",
    "certification",
    "upload",
    "payment",
    "inspection_scheduling",
)

REQUIRED_FALSE_FLAGS = (
    "live_extraction",
    "live_crawl",
    "document_download",
    "raw_output_stored",
    "devhub_opened",
    "active_requirement_mutation",
    "active_process_model_mutation",
    "active_guardrail_mutation",
    "active_mutation",
    "official_action_completed",
    "legal_or_permitting_guarantee",
)

SENSITIVE_OR_RUNTIME_KEYS = frozenset(
    {
        "auth_state",
        "browser_trace",
        "cookie",
        "credential",
        "devhub_session",
        "downloaded_artifact",
        "downloaded_document",
        "downloaded_pdf",
        "har",
        "html_body",
        "local_path",
        "password",
        "private_artifact",
        "raw_artifact",
        "raw_body",
        "raw_crawl_output",
        "raw_download",
        "raw_html",
        "raw_output",
        "raw_pdf",
        "screenshot",
        "session_state",
        "trace",
        "warc_path",
    }
)

PROHIBITED_CLAIM_PHRASES = frozenset(
    {
        "active guardrail mutation",
        "active process model mutation",
        "active requirement mutation",
        "certification completed",
        "devhub opened",
        "downloaded artifact",
        "downloaded document",
        "guaranteed approval",
        "guaranteed permit",
        "legal advice",
        "live crawl completed",
        "live extraction completed",
        "official action completed",
        "payment completed",
        "permit guaranteed",
        "raw artifact stored",
        "raw output stored",
        "submission completed",
        "upload completed",
    }
)


@dataclass(frozen=True)
class SyntheticNormalizedDocumentExtractionReadinessRow:
    row_id: str
    readiness_packet_ref: str
    normalized_document_id_placeholder: str
    source_id: str
    canonical_url: str
    candidate_requirement_id: str
    candidate_requirement_type: str
    candidate_requirement_action: str
    candidate_requirement_object: str
    affected_process_model_ids: tuple[str, ...]
    affected_guardrail_bundle_ids: tuple[str, ...]
    source_evidence_placeholder_mappings: tuple[Mapping[str, Any], ...]
    human_review_status: str
    formalization_hold: str
    stale_evidence: bool
    conflicting_evidence: bool
    rollback_note: str
    reviewer_note: str

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "SyntheticNormalizedDocumentExtractionReadinessRow":
        _reject_runtime_or_private_content(row)
        if row.get("synthetic_normalized_document_extraction_readiness_row") is not True:
            raise ValueError("row must declare synthetic_normalized_document_extraction_readiness_row true")
        for flag in REQUIRED_FALSE_FLAGS:
            if row.get(flag) is not False:
                raise ValueError(f"row must declare {flag} false")

        human_review_status = _required_text(row, "human_review_status")
        if human_review_status not in ALLOWED_HUMAN_REVIEW_STATUSES:
            raise ValueError(f"unsupported human_review_status: {human_review_status}")

        formalization_hold = _required_text(row, "formalization_hold")
        if formalization_hold not in ALLOWED_FORMALIZATION_HOLDS:
            raise ValueError(f"unsupported formalization_hold: {formalization_hold}")

        source_evidence_mappings = _required_mapping_tuple(row, "source_evidence_placeholder_mappings")
        for mapping in source_evidence_mappings:
            _require_source_evidence_mapping(mapping)

        return cls(
            row_id=_required_text(row, "row_id"),
            readiness_packet_ref=_required_text(row, "readiness_packet_ref"),
            normalized_document_id_placeholder=_required_placeholder_text(row, "normalized_document_id_placeholder"),
            source_id=_required_text(row, "source_id"),
            canonical_url=_required_text(row, "canonical_url"),
            candidate_requirement_id=_required_placeholder_text(row, "candidate_requirement_id"),
            candidate_requirement_type=_required_text(row, "candidate_requirement_type"),
            candidate_requirement_action=_required_text(row, "candidate_requirement_action"),
            candidate_requirement_object=_required_text(row, "candidate_requirement_object"),
            affected_process_model_ids=_required_text_tuple(row, "affected_process_model_ids"),
            affected_guardrail_bundle_ids=_required_text_tuple(row, "affected_guardrail_bundle_ids"),
            source_evidence_placeholder_mappings=source_evidence_mappings,
            human_review_status=human_review_status,
            formalization_hold=formalization_hold,
            stale_evidence=_required_bool(row, "stale_evidence"),
            conflicting_evidence=_required_bool(row, "conflicting_evidence"),
            rollback_note=_required_text(row, "rollback_note"),
            reviewer_note=_required_text(row, "reviewer_note"),
        )


def build_public_refresh_requirement_reextraction_queue_v2(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalized_rows = tuple(SyntheticNormalizedDocumentExtractionReadinessRow.from_mapping(row) for row in rows)
    if not normalized_rows:
        raise ValueError("at least one requirement re-extraction readiness row is required")

    candidates = sorted((_candidate_from_row(row) for row in normalized_rows), key=lambda item: item["candidate_id"])
    queue = {
        "queue_version": QUEUE_VERSION,
        "mode": MODE,
        "input_contract": INPUT_CONTRACT,
        "input_row_count": len(normalized_rows),
        "candidate_count": len(candidates),
        "readiness_packet_refs": _sorted_unique(row.readiness_packet_ref for row in normalized_rows),
        "affected_requirement_ids": _sorted_unique(row.candidate_requirement_id for row in normalized_rows),
        "affected_process_model_ids": _sorted_unique(_flatten(row.affected_process_model_ids for row in normalized_rows)),
        "affected_guardrail_bundle_ids": _sorted_unique(_flatten(row.affected_guardrail_bundle_ids for row in normalized_rows)),
        "requirement_reextraction_candidates": candidates,
        "source_evidence_placeholder_mappings": _source_evidence_placeholder_mappings(normalized_rows),
        "human_review_statuses": _human_review_statuses(normalized_rows),
        "formalization_holds": _formalization_holds(normalized_rows),
        "stale_or_conflicting_evidence_flags": _evidence_flags(normalized_rows),
        "rollback_notes": _rollback_notes(normalized_rows),
        "exact_offline_validation_commands": [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS],
        "prohibited_actions": list(PROHIBITED_ACTIONS),
        "attestations": {
            "fixture_first": True,
            "synthetic_normalized_document_extraction_readiness_rows_only": True,
            "no_live_extraction": True,
            "no_live_crawling": True,
            "no_document_downloads": True,
            "no_raw_output_storage": True,
            "no_devhub_access": True,
            "no_active_requirement_mutation": True,
            "no_active_process_model_mutation": True,
            "no_active_guardrail_mutation": True,
            "no_official_actions": True,
            "no_legal_or_permitting_guarantees": True,
        },
    }
    validate_public_refresh_requirement_reextraction_queue_v2(queue)
    return queue


def validate_public_refresh_requirement_reextraction_queue_v2(queue: Mapping[str, Any]) -> None:
    _reject_runtime_or_private_content(queue)
    if queue.get("queue_version") != QUEUE_VERSION:
        raise ValueError(f"queue_version must be {QUEUE_VERSION}")
    if queue.get("mode") != MODE:
        raise ValueError(f"mode must be {MODE}")
    if queue.get("input_contract") != INPUT_CONTRACT:
        raise ValueError(f"input_contract must be {INPUT_CONTRACT}")

    for key in (
        "readiness_packet_refs",
        "affected_requirement_ids",
        "affected_process_model_ids",
        "affected_guardrail_bundle_ids",
    ):
        if not _non_empty_list_of_strings(queue.get(key)):
            raise ValueError(f"queue must include non-empty {key}")
    for key in (
        "requirement_reextraction_candidates",
        "source_evidence_placeholder_mappings",
        "human_review_statuses",
        "formalization_holds",
        "stale_or_conflicting_evidence_flags",
        "rollback_notes",
    ):
        if not _non_empty_list_of_mappings(queue.get(key)):
            raise ValueError(f"queue must include non-empty {key}")
    if queue.get("exact_offline_validation_commands") != [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]:
        raise ValueError("queue must include exact offline validation commands")

    for candidate in queue["requirement_reextraction_candidates"]:
        _require_candidate_controls(candidate)
    for mapping in queue["source_evidence_placeholder_mappings"]:
        _require_source_evidence_mapping(mapping)
        _required_text(mapping, "mapping_id")
        _required_text(mapping, "candidate_id")
        _required_placeholder_text(mapping, "requirement_id")
        _required_placeholder_text(mapping, "normalized_document_id_placeholder")
        if mapping.get("activation_allowed") is not False:
            raise ValueError("source_evidence_placeholder_mappings activation_allowed must be false")
    for review in queue["human_review_statuses"]:
        _required_text(review, "review_id")
        _required_text(review, "candidate_id")
        status = _required_text(review, "human_review_status")
        if status not in ALLOWED_HUMAN_REVIEW_STATUSES:
            raise ValueError(f"unsupported human_review_status: {status}")
        _required_text(review, "required_review_decision")
    for hold in queue["formalization_holds"]:
        _required_text(hold, "hold_id")
        _required_text(hold, "candidate_id")
        formalization_hold = _required_text(hold, "formalization_hold")
        if formalization_hold not in ALLOWED_FORMALIZATION_HOLDS:
            raise ValueError(f"unsupported formalization_hold: {formalization_hold}")
        if hold.get("formalization_allowed") is not False:
            raise ValueError("formalization_holds formalization_allowed must be false")
    for flags in queue["stale_or_conflicting_evidence_flags"]:
        _required_text(flags, "flag_id")
        _required_text(flags, "candidate_id")
        _required_bool(flags, "stale_evidence")
        _required_bool(flags, "conflicting_evidence")
        if flags.get("agent_may_treat_source_as_current") is not False:
            raise ValueError("stale_or_conflicting_evidence_flags agent_may_treat_source_as_current must be false")
    for note in queue["rollback_notes"]:
        _required_text(note, "rollback_id")
        _required_text(note, "candidate_id")
        _required_text(note, "rollback_note")
        if note.get("active_state_changed") is not False:
            raise ValueError("rollback_notes active_state_changed must be false")

    attestations = queue.get("attestations")
    if not isinstance(attestations, Mapping):
        raise ValueError("queue must include attestations")
    for key in (
        "fixture_first",
        "synthetic_normalized_document_extraction_readiness_rows_only",
        "no_live_extraction",
        "no_live_crawling",
        "no_document_downloads",
        "no_raw_output_storage",
        "no_devhub_access",
        "no_active_requirement_mutation",
        "no_active_process_model_mutation",
        "no_active_guardrail_mutation",
        "no_official_actions",
        "no_legal_or_permitting_guarantees",
    ):
        if attestations.get(key) is not True:
            raise ValueError(f"queue attestation {key} must be true")


def load_synthetic_normalized_document_extraction_readiness_rows(path: Path) -> tuple[dict[str, Any], ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fixture must be a JSON object")
    _reject_runtime_or_private_content(payload)
    rows = payload.get("synthetic_normalized_document_extraction_readiness_rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("fixture must contain non-empty synthetic_normalized_document_extraction_readiness_rows list")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("each synthetic normalized document extraction readiness row must be an object")
    return tuple(rows)


def build_queue_from_fixture(path: Path) -> dict[str, Any]:
    return build_public_refresh_requirement_reextraction_queue_v2(
        load_synthetic_normalized_document_extraction_readiness_rows(path)
    )


def _candidate_from_row(row: SyntheticNormalizedDocumentExtractionReadinessRow) -> dict[str, Any]:
    return {
        "candidate_id": f"requirement-reextraction::{row.row_id}",
        "readiness_packet_ref": row.readiness_packet_ref,
        "normalized_document_id_placeholder": row.normalized_document_id_placeholder,
        "source_id": row.source_id,
        "canonical_url": row.canonical_url,
        "candidate_requirement_update": {
            "requirement_node_update_placeholder": True,
            "requirement_id": row.candidate_requirement_id,
            "requirement_type": row.candidate_requirement_type,
            "action": row.candidate_requirement_action,
            "object": row.candidate_requirement_object,
            "activation_allowed": False,
            "active_requirement_mutation": False,
        },
        "affected_process_model_ids": list(row.affected_process_model_ids),
        "affected_guardrail_bundle_ids": list(row.affected_guardrail_bundle_ids),
        "source_evidence_placeholder_mappings": [dict(mapping) for mapping in row.source_evidence_placeholder_mappings],
        "human_review_status": row.human_review_status,
        "formalization_hold": row.formalization_hold,
        "stale_evidence": row.stale_evidence,
        "conflicting_evidence": row.conflicting_evidence,
        "rollback_note": row.rollback_note,
        "reviewer_note": row.reviewer_note,
        "allowed_next_action": "human_review_of_fixture_requirement_reextraction_queue_only",
        "requires_live_extraction": False,
        "requires_live_crawl": False,
        "requires_document_download": False,
        "stores_raw_output": False,
        "opens_devhub": False,
        "mutates_active_requirements": False,
        "mutates_active_process_models": False,
        "mutates_active_guardrails": False,
        "active_mutation": False,
        "official_action_completed": False,
        "legal_or_permitting_guarantee": False,
    }


def _source_evidence_placeholder_mappings(rows: Sequence[SyntheticNormalizedDocumentExtractionReadinessRow]) -> list[dict[str, Any]]:
    mappings: list[dict[str, Any]] = []
    for row in rows:
        for index, mapping in enumerate(row.source_evidence_placeholder_mappings):
            placeholder = _required_placeholder_text(mapping, "source_evidence_id_placeholder")
            mappings.append(
                {
                    "mapping_id": f"source-evidence-placeholder::{row.row_id}::{index + 1}",
                    "candidate_id": f"requirement-reextraction::{row.row_id}",
                    "requirement_id": row.candidate_requirement_id,
                    "source_evidence_id_placeholder": placeholder,
                    "normalized_document_id_placeholder": row.normalized_document_id_placeholder,
                    "citation_span_placeholder": _required_placeholder_text(mapping, "citation_span_placeholder"),
                    "activation_allowed": False,
                }
            )
    return sorted(mappings, key=lambda item: item["mapping_id"])


def _human_review_statuses(rows: Sequence[SyntheticNormalizedDocumentExtractionReadinessRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "review_id": f"human-review::{row.row_id}",
                "candidate_id": f"requirement-reextraction::{row.row_id}",
                "human_review_status": row.human_review_status,
                "required_review_decision": "approve_candidate_update_or_keep_hold",
            }
            for row in rows
        ),
        key=lambda item: item["review_id"],
    )


def _formalization_holds(rows: Sequence[SyntheticNormalizedDocumentExtractionReadinessRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "hold_id": f"formalization-hold::{row.row_id}",
                "candidate_id": f"requirement-reextraction::{row.row_id}",
                "formalization_hold": row.formalization_hold,
                "formalization_allowed": False,
            }
            for row in rows
        ),
        key=lambda item: item["hold_id"],
    )


def _evidence_flags(rows: Sequence[SyntheticNormalizedDocumentExtractionReadinessRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "flag_id": f"evidence-flags::{row.row_id}",
                "candidate_id": f"requirement-reextraction::{row.row_id}",
                "stale_evidence": row.stale_evidence,
                "conflicting_evidence": row.conflicting_evidence,
                "agent_may_treat_source_as_current": False,
            }
            for row in rows
        ),
        key=lambda item: item["flag_id"],
    )


def _rollback_notes(rows: Sequence[SyntheticNormalizedDocumentExtractionReadinessRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "rollback_id": f"rollback-note::{row.row_id}",
                "candidate_id": f"requirement-reextraction::{row.row_id}",
                "rollback_note": row.rollback_note,
                "active_state_changed": False,
            }
            for row in rows
        ),
        key=lambda item: item["rollback_id"],
    )


def _require_candidate_controls(candidate: Mapping[str, Any]) -> None:
    for key in (
        "candidate_id",
        "readiness_packet_ref",
        "normalized_document_id_placeholder",
        "source_id",
        "canonical_url",
        "human_review_status",
        "formalization_hold",
        "rollback_note",
        "reviewer_note",
    ):
        _required_text(candidate, key)
    _required_placeholder_text(candidate, "normalized_document_id_placeholder")
    for key in ("affected_process_model_ids", "affected_guardrail_bundle_ids"):
        _required_text_tuple(candidate, key)
    mappings = candidate.get("source_evidence_placeholder_mappings")
    if not _non_empty_list_of_mappings(mappings):
        raise ValueError("candidate must include source_evidence_placeholder_mappings")
    for mapping in mappings:
        _require_source_evidence_mapping(mapping)
    update = candidate.get("candidate_requirement_update")
    if not isinstance(update, Mapping):
        raise ValueError("candidate must include candidate_requirement_update")
    if update.get("requirement_node_update_placeholder") is not True:
        raise ValueError("candidate_requirement_update must declare requirement_node_update_placeholder true")
    _required_placeholder_text(update, "requirement_id")
    for key in ("requirement_type", "action", "object"):
        _required_text(update, key)
    if update.get("activation_allowed") is not False:
        raise ValueError("candidate_requirement_update activation_allowed must be false")
    if update.get("active_requirement_mutation") is not False:
        raise ValueError("candidate_requirement_update active_requirement_mutation must be false")
    status = _required_text(candidate, "human_review_status")
    if status not in ALLOWED_HUMAN_REVIEW_STATUSES:
        raise ValueError(f"unsupported human_review_status: {status}")
    formalization_hold = _required_text(candidate, "formalization_hold")
    if formalization_hold not in ALLOWED_FORMALIZATION_HOLDS:
        raise ValueError(f"unsupported formalization_hold: {formalization_hold}")
    _required_bool(candidate, "stale_evidence")
    _required_bool(candidate, "conflicting_evidence")
    for key in (
        "requires_live_extraction",
        "requires_live_crawl",
        "requires_document_download",
        "stores_raw_output",
        "opens_devhub",
        "mutates_active_requirements",
        "mutates_active_process_models",
        "mutates_active_guardrails",
        "active_mutation",
        "official_action_completed",
        "legal_or_permitting_guarantee",
    ):
        if candidate.get(key) is not False:
            raise ValueError(f"candidate must declare {key} false")


def _require_source_evidence_mapping(mapping: Mapping[str, Any]) -> None:
    _required_placeholder_text(mapping, "source_evidence_id_placeholder")
    _required_placeholder_text(mapping, "citation_span_placeholder")


def _reject_runtime_or_private_content(value: Any, path: str = "row") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key).lower()
            if key_text in SENSITIVE_OR_RUNTIME_KEYS:
                raise ValueError(f"{path} contains runtime, raw-output, downloaded, or private key: {key}")
            _reject_runtime_or_private_content(nested, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_runtime_or_private_content(nested, f"{path}[{index}]")
    elif isinstance(value, str):
        normalized = " ".join(value.lower().replace("_", " ").replace("-", " ").split())
        for phrase in PROHIBITED_CLAIM_PHRASES:
            if phrase in normalized:
                raise ValueError(f"{path} contains prohibited claim phrase: {phrase}")


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _required_placeholder_text(row: Mapping[str, Any], key: str) -> str:
    value = _required_text(row, key)
    if not (value.startswith("placeholder:") or value.startswith("pending-")):
        raise ValueError(f"{key} must remain a placeholder")
    return value


def _required_bool(row: Mapping[str, Any], key: str) -> bool:
    value = row.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _required_text_tuple(row: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = row.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        raise ValueError(f"{key} must be a non-empty list of strings")
    output = tuple(item for item in value if isinstance(item, str) and item.strip())
    if len(output) != len(value):
        raise ValueError(f"{key} must contain only non-empty strings")
    return output


def _required_mapping_tuple(row: Mapping[str, Any], key: str) -> tuple[Mapping[str, Any], ...]:
    value = row.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        raise ValueError(f"{key} must be a non-empty list of mappings")
    output = tuple(item for item in value if isinstance(item, Mapping))
    if len(output) != len(value):
        raise ValueError(f"{key} must contain only mappings")
    return output


def _non_empty_list_of_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def _non_empty_list_of_mappings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, Mapping) for item in value)


def _flatten(groups: Iterable[Iterable[str]]) -> tuple[str, ...]:
    return tuple(item for group in groups for item in group)


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted(set(values))
