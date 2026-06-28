"""Fixture-first process model refresh impact queue v7.

Consumes only committed re-extracted RequirementNode candidate set v7 fixtures
and assembles inactive ProcessModel impact rows. The queue is offline-only and
must not activate guardrails, crawl live sources, open DevHub, read private
documents, upload, submit, certify, pay, schedule, or make legal/permitting
guarantees.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

QUEUE_TYPE = "ppd.process_model_refresh_impact_queue.v7"
QUEUE_VERSION = "v7"
QUEUE_MODE = "fixture_first_offline_process_model_refresh_impact_queue_v7"
CANDIDATE_SET_TYPE = "ppd.reextracted_requirement_node_candidate_set.v7"
CANDIDATE_SET_VERSION = "v7"
CANDIDATE_SET_MODE = "fixture_first_reextracted_requirement_node_candidates_v7_only"

EXACT_OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/process_model_refresh_impact_queue_v7.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_process_model_refresh_impact_queue_v7.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_process_model_refresh_impact_queue_v7.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

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

REQUIRED_FALSE_FLAGS = (
    "live_crawl_executed",
    "live_extraction_executed",
    "document_downloaded",
    "raw_body_stored",
    "devhub_opened",
    "private_document_read",
    "upload_attempted",
    "submission_attempted",
    "certification_attempted",
    "payment_attempted",
    "inspection_scheduling_attempted",
    "official_action_completed",
    "legal_or_permitting_guarantee",
    "active_process_model_mutation",
    "active_guardrail_mutation",
    "active_requirement_mutation",
    "guardrail_activation_attempted",
)

PROHIBITED_KEYS = frozenset(
    {
        "access_token",
        "auth_artifact",
        "auth_state",
        "browser_trace",
        "cookie",
        "credential",
        "devhub_session",
        "downloaded_artifact",
        "downloaded_document",
        "har",
        "html_body",
        "local_private_path",
        "password",
        "payment_detail",
        "private_artifact",
        "private_document",
        "raw_artifact",
        "raw_body",
        "raw_crawl_artifact",
        "raw_crawl_output",
        "raw_html",
        "raw_pdf",
        "raw_text",
        "screenshot",
        "session_artifact",
        "session_state",
        "storage_state",
        "trace",
    }
)

PROHIBITED_PHRASES = tuple(
    sorted(
        {
            "active guardrail activated",
            "active mutation enabled",
            "application submitted",
            "approval guaranteed",
            "certification completed",
            "crawled live",
            "devhub opened",
            "document downloaded",
            "guaranteed approval",
            "guaranteed permit",
            "inspection scheduled",
            "legal advice",
            "legal guarantee",
            "live crawl completed",
            "official action completed",
            "payment completed",
            "permit guaranteed",
            "permitting guarantee",
            "private document read",
            "raw body stored",
            "submission completed",
            "upload completed",
        }
    )
)

CANDIDATE_REF_FIELDS = (
    "eligibility_impact_placeholder_refs",
    "document_impact_placeholder_refs",
    "fee_impact_placeholder_refs",
    "deadline_impact_placeholder_refs",
    "stage_impact_placeholder_refs",
    "unsupported_path_carry_forward_note_refs",
    "guardrail_bundle_recompile_suggestion_refs",
    "stale_evidence_hold_refs",
    "reviewer_signoff_placeholder_refs",
)

ROW_REF_FIELDS = {
    "eligibility_impact_placeholder_refs": "eligibility_impact_placeholders",
    "document_impact_placeholder_refs": "document_impact_placeholders",
    "fee_impact_placeholder_refs": "fee_impact_placeholders",
    "deadline_impact_placeholder_refs": "deadline_impact_placeholders",
    "stage_impact_placeholder_refs": "stage_impact_placeholders",
    "unsupported_path_carry_forward_note_refs": "unsupported_path_carry_forward_notes",
    "guardrail_bundle_recompile_suggestion_refs": "guardrail_bundle_recompile_suggestions",
    "stale_evidence_hold_refs": "stale_evidence_holds",
    "reviewer_signoff_placeholder_refs": "reviewer_signoff_placeholders",
}


@dataclass(frozen=True)
class RequirementNodeCandidateV7:
    candidate_id: str
    requirement_node_id: str
    requirement_type: str
    affected_process_model_ids: tuple[str, ...]
    permit_type_placeholders: tuple[str, ...]
    process_stage_placeholders: tuple[str, ...]
    eligibility_impact_placeholder_refs: tuple[str, ...]
    document_impact_placeholder_refs: tuple[str, ...]
    fee_impact_placeholder_refs: tuple[str, ...]
    deadline_impact_placeholder_refs: tuple[str, ...]
    stage_impact_placeholder_refs: tuple[str, ...]
    unsupported_path_carry_forward_note_refs: tuple[str, ...]
    guardrail_bundle_recompile_suggestion_refs: tuple[str, ...]
    stale_evidence_hold_refs: tuple[str, ...]
    reviewer_signoff_placeholder_refs: tuple[str, ...]

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "RequirementNodeCandidateV7":
        _reject_prohibited_content(row)
        for flag in REQUIRED_FALSE_FLAGS:
            if row.get(flag) is not False:
                raise ValueError(f"requirement node candidate must declare {flag} false")
        requirement_type = _required_text(row, "requirement_type")
        if requirement_type not in ALLOWED_REQUIREMENT_TYPES:
            raise ValueError(f"unsupported requirement_type: {requirement_type}")
        _require_exact_validation_commands(row.get("exact_offline_validation_commands"), "requirement node candidate")
        return cls(
            candidate_id=_required_text(row, "candidate_id"),
            requirement_node_id=_required_text(row, "requirement_node_id"),
            requirement_type=requirement_type,
            affected_process_model_ids=_required_text_tuple(row, "affected_process_model_ids"),
            permit_type_placeholders=_required_text_tuple(row, "permit_type_placeholders"),
            process_stage_placeholders=_required_text_tuple(row, "process_stage_placeholders"),
            eligibility_impact_placeholder_refs=_required_text_tuple(row, "eligibility_impact_placeholder_refs"),
            document_impact_placeholder_refs=_required_text_tuple(row, "document_impact_placeholder_refs"),
            fee_impact_placeholder_refs=_required_text_tuple(row, "fee_impact_placeholder_refs"),
            deadline_impact_placeholder_refs=_required_text_tuple(row, "deadline_impact_placeholder_refs"),
            stage_impact_placeholder_refs=_required_text_tuple(row, "stage_impact_placeholder_refs"),
            unsupported_path_carry_forward_note_refs=_required_text_tuple(row, "unsupported_path_carry_forward_note_refs"),
            guardrail_bundle_recompile_suggestion_refs=_required_text_tuple(
                row, "guardrail_bundle_recompile_suggestion_refs"
            ),
            stale_evidence_hold_refs=_required_text_tuple(row, "stale_evidence_hold_refs"),
            reviewer_signoff_placeholder_refs=_required_text_tuple(row, "reviewer_signoff_placeholder_refs"),
        )


def load_reextracted_requirement_node_candidate_set_v7(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("re-extracted RequirementNode candidate set v7 fixture must be an object")
    validate_reextracted_requirement_node_candidate_set_v7(payload)
    return payload


def validate_reextracted_requirement_node_candidate_set_v7(candidate_set: Mapping[str, Any]) -> None:
    _reject_prohibited_content(candidate_set)
    if candidate_set.get("candidate_set_type") != CANDIDATE_SET_TYPE:
        raise ValueError(f"candidate_set_type must be {CANDIDATE_SET_TYPE}")
    if candidate_set.get("candidate_set_version") != CANDIDATE_SET_VERSION:
        raise ValueError("candidate_set_version must be v7")
    if candidate_set.get("mode") != CANDIDATE_SET_MODE:
        raise ValueError(f"mode must be {CANDIDATE_SET_MODE}")
    _required_text(candidate_set, "candidate_set_id")
    if candidate_set.get("fixture_first") is not True:
        raise ValueError("fixture_first must be true")
    if candidate_set.get("consumes_only_reextracted_requirement_node_candidate_set_v7_fixtures") is not True:
        raise ValueError("candidate set must declare v7 RequirementNode fixture-only consumption")
    _require_exact_validation_commands(candidate_set.get("exact_offline_validation_commands"), "candidate set")
    for flag in REQUIRED_FALSE_FLAGS:
        if candidate_set.get(flag) is not False:
            raise ValueError(f"candidate set must declare {flag} false")
    candidates = candidate_set.get("requirement_node_candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidate set must include non-empty requirement_node_candidates")
    for row in candidates:
        if not isinstance(row, Mapping):
            raise ValueError("requirement_node_candidates must contain objects")
        RequirementNodeCandidateV7.from_mapping(row)


def build_process_model_refresh_impact_queue_v7_from_fixture(path: str | Path) -> dict[str, Any]:
    candidate_set = load_reextracted_requirement_node_candidate_set_v7(path)
    candidates = tuple(RequirementNodeCandidateV7.from_mapping(row) for row in candidate_set["requirement_node_candidates"])
    return build_process_model_refresh_impact_queue_v7(_required_text(candidate_set, "candidate_set_id"), candidates)


def build_process_model_refresh_impact_queue_v7(
    candidate_set_id: str,
    candidates: Sequence[RequirementNodeCandidateV7],
) -> dict[str, Any]:
    if not candidates:
        raise ValueError("at least one re-extracted RequirementNode candidate is required")

    process_ids = sorted({process_id for candidate in candidates for process_id in candidate.affected_process_model_ids})
    rows = []
    for process_id in process_ids:
        scoped = [candidate for candidate in candidates if process_id in candidate.affected_process_model_ids]
        rows.append(
            {
                "process_model_id": process_id,
                "candidate_refs": sorted(candidate.candidate_id for candidate in scoped),
                "requirement_node_refs": sorted(candidate.requirement_node_id for candidate in scoped),
                "permit_type_placeholders": _sorted_unique(
                    value for candidate in scoped for value in candidate.permit_type_placeholders
                ),
                "process_stage_placeholders": _sorted_unique(
                    value for candidate in scoped for value in candidate.process_stage_placeholders
                ),
                "eligibility_impact_placeholders": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.eligibility_impact_placeholder_refs
                ),
                "document_impact_placeholders": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.document_impact_placeholder_refs
                ),
                "fee_impact_placeholders": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.fee_impact_placeholder_refs
                ),
                "deadline_impact_placeholders": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.deadline_impact_placeholder_refs
                ),
                "stage_impact_placeholders": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.stage_impact_placeholder_refs
                ),
                "unsupported_path_carry_forward_notes": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.unsupported_path_carry_forward_note_refs
                ),
                "guardrail_bundle_recompile_suggestions": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.guardrail_bundle_recompile_suggestion_refs
                ),
                "stale_evidence_holds": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.stale_evidence_hold_refs
                ),
                "reviewer_signoff_placeholders": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.reviewer_signoff_placeholder_refs
                ),
                "process_model_mutation_allowed": False,
                "guardrail_activation_allowed": False,
                "legal_or_permitting_guarantee": False,
                "exact_offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
            }
        )

    queue = {
        "queue_type": QUEUE_TYPE,
        "queue_version": QUEUE_VERSION,
        "mode": QUEUE_MODE,
        "fixture_first": True,
        "consumes_only": {"reextracted_requirement_node_candidate_set_v7_fixtures": True},
        "source_candidate_set_ref": candidate_set_id,
        "row_count": len(rows),
        "affected_process_models": process_ids,
        "affected_process_model_rows": rows,
        "unsupported_path_carry_forward_notes": _reference_rows(
            candidates,
            "unsupported_path_carry_forward_note_refs",
            "unsupported_path_note_ref",
            "carry_forward_pending_reviewer_disposition",
        ),
        "guardrail_bundle_recompile_suggestions": _reference_rows(
            candidates,
            "guardrail_bundle_recompile_suggestion_refs",
            "guardrail_recompile_suggestion_ref",
            "inactive_recompile_suggestion_only",
        ),
        "stale_evidence_hold_rows": _reference_rows(
            candidates,
            "stale_evidence_hold_refs",
            "stale_evidence_hold_ref",
            "hold_pending_reviewer_disposition",
        ),
        "reviewer_signoff_placeholders": _reference_rows(
            candidates,
            "reviewer_signoff_placeholder_refs",
            "reviewer_signoff_placeholder_ref",
            "placeholder_unassigned",
        ),
        "exact_offline_validation_commands": copy.deepcopy(EXACT_OFFLINE_VALIDATION_COMMANDS),
        "attestations": {flag: False for flag in REQUIRED_FALSE_FLAGS},
    }
    validate_process_model_refresh_impact_queue_v7(queue)
    return queue


def validate_process_model_refresh_impact_queue_v7(queue: Mapping[str, Any]) -> None:
    _reject_prohibited_content(queue)
    if queue.get("queue_type") != QUEUE_TYPE:
        raise ValueError(f"queue_type must be {QUEUE_TYPE}")
    if queue.get("queue_version") != QUEUE_VERSION:
        raise ValueError("queue_version must be v7")
    if queue.get("mode") != QUEUE_MODE:
        raise ValueError(f"mode must be {QUEUE_MODE}")
    if queue.get("fixture_first") is not True:
        raise ValueError("fixture_first must be true")
    if queue.get("consumes_only") != {"reextracted_requirement_node_candidate_set_v7_fixtures": True}:
        raise ValueError("queue must consume only re-extracted RequirementNode candidate set v7 fixtures")
    _required_text(queue, "source_candidate_set_ref")
    _require_exact_validation_commands(queue.get("exact_offline_validation_commands"), "queue")

    attestations = queue.get("attestations")
    if not isinstance(attestations, Mapping):
        raise ValueError("queue must include attestations")
    for flag in REQUIRED_FALSE_FLAGS:
        if attestations.get(flag) is not False:
            raise ValueError(f"queue attestation {flag} must be false")

    affected_process_models = queue.get("affected_process_models")
    if not _non_empty_text_list(affected_process_models):
        raise ValueError("affected_process_models must be a non-empty list of strings")
    affected_process_model_set = set(affected_process_models)

    rows = queue.get("affected_process_model_rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("affected_process_model_rows must be a non-empty list")
    process_ids_from_rows = set()
    for row in rows:
        process_ids_from_rows.add(_validate_process_model_row(row))
    if queue.get("row_count") != len(rows):
        raise ValueError("row_count must match affected_process_model_rows length")
    if process_ids_from_rows != affected_process_model_set:
        raise ValueError("affected_process_models must match affected_process_model_rows")

    _validate_reference_section(
        queue.get("unsupported_path_carry_forward_notes"),
        "unsupported_path_note_ref",
        "carry_forward_pending_reviewer_disposition",
        _collect_row_refs(rows, "unsupported_path_carry_forward_notes"),
    )
    _validate_reference_section(
        queue.get("guardrail_bundle_recompile_suggestions"),
        "guardrail_recompile_suggestion_ref",
        "inactive_recompile_suggestion_only",
        _collect_row_refs(rows, "guardrail_bundle_recompile_suggestions"),
    )
    _validate_reference_section(
        queue.get("stale_evidence_hold_rows"),
        "stale_evidence_hold_ref",
        "hold_pending_reviewer_disposition",
        _collect_row_refs(rows, "stale_evidence_holds"),
    )
    _validate_reference_section(
        queue.get("reviewer_signoff_placeholders"),
        "reviewer_signoff_placeholder_ref",
        "placeholder_unassigned",
        _collect_row_refs(rows, "reviewer_signoff_placeholders"),
    )


def _validate_process_model_row(row: Any) -> str:
    if not isinstance(row, Mapping):
        raise ValueError("affected process model row must be an object")
    process_model_id = _required_text(row, "process_model_id")
    for field in (
        "candidate_refs",
        "requirement_node_refs",
        "permit_type_placeholders",
        "process_stage_placeholders",
        *ROW_REF_FIELDS.values(),
    ):
        if not _non_empty_text_list(row.get(field)):
            raise ValueError(f"affected process model row {field} must be non-empty")
    if row.get("process_model_mutation_allowed") is not False:
        raise ValueError("process_model_mutation_allowed must be false")
    if row.get("guardrail_activation_allowed") is not False:
        raise ValueError("guardrail_activation_allowed must be false")
    if row.get("legal_or_permitting_guarantee") is not False:
        raise ValueError("legal_or_permitting_guarantee must be false")
    _require_exact_validation_commands(row.get("exact_offline_validation_commands"), "affected process model row")
    return process_model_id


def _reference_rows(
    candidates: Sequence[RequirementNodeCandidateV7], source_field: str, ref_field: str, status: str
) -> list[dict[str, Any]]:
    refs = []
    for candidate in candidates:
        refs.extend(getattr(candidate, source_field))
    return [
        {
            ref_field: ref,
            "status": status,
            "activation_allowed": False,
            "official_action_completed": False,
            "reviewer_disposition_required": True,
        }
        for ref in sorted(set(refs))
    ]


def _validate_reference_section(rows: Any, ref_field: str, status: str, expected_refs: set[str]) -> None:
    if not expected_refs:
        raise ValueError(f"{ref_field} expected references must be non-empty")
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{ref_field} rows must be non-empty")
    seen_refs = set()
    for row in rows:
        if not isinstance(row, Mapping):
            raise ValueError(f"{ref_field} row must be an object")
        ref = _required_text(row, ref_field)
        if ref in seen_refs:
            raise ValueError(f"duplicate {ref_field} row: {ref}")
        seen_refs.add(ref)
        if row.get("status") != status:
            raise ValueError(f"{ref_field} row status must be {status}")
        if row.get("activation_allowed") is not False:
            raise ValueError(f"{ref_field} row activation_allowed must be false")
        if row.get("official_action_completed") is not False:
            raise ValueError(f"{ref_field} row official_action_completed must be false")
        if row.get("reviewer_disposition_required") is not True:
            raise ValueError(f"{ref_field} row reviewer_disposition_required must be true")
    if seen_refs != expected_refs:
        raise ValueError(f"{ref_field} rows must match process model row references")


def _collect_row_refs(rows: Sequence[Any], field: str) -> set[str]:
    refs = set()
    for row in rows:
        if isinstance(row, Mapping):
            value = row.get(field)
            if isinstance(value, list):
                refs.update(item for item in value if isinstance(item, str) and item.strip())
    return refs


def _reject_prohibited_content(value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            if key_text in PROHIBITED_KEYS:
                raise ValueError(f"{path} contains prohibited key: {key}")
            if key_text in REQUIRED_FALSE_FLAGS and child is not False:
                raise ValueError(f"{path}.{key} must be false")
            if key_text.endswith("_allowed") and "activation" in key_text and child is not False:
                raise ValueError(f"{path}.{key} activation must not be allowed")
            _reject_prohibited_content(child, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _reject_prohibited_content(child, f"{path}[{index}]")
    elif isinstance(value, str):
        normalized = _normalize_text(value)
        for phrase in PROHIBITED_PHRASES:
            if phrase in normalized:
                raise ValueError(f"{path} contains prohibited claim phrase: {phrase}")


def _require_exact_validation_commands(value: Any, label: str) -> None:
    if value != EXACT_OFFLINE_VALIDATION_COMMANDS:
        raise ValueError(f"{label} must contain only exact offline validation commands")


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _required_text_tuple(row: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = row.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)) or not value:
        raise ValueError(f"{key} must be a non-empty list of strings")
    output = tuple(item for item in value if isinstance(item, str) and item.strip())
    if len(output) != len(value):
        raise ValueError(f"{key} must contain only non-empty strings")
    return output


def _non_empty_text_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def _sorted_unique(values: Any) -> list[str]:
    return sorted({value for value in values if isinstance(value, str) and value.strip()})


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().replace("_", " ").replace("-", " ").split())
