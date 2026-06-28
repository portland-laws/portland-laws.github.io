"""Fixture-first process model refresh impact queue v6.

This module consumes only committed re-extracted requirement candidate set v6
fixtures and groups their inactive impact placeholders by affected process model.
It is intentionally offline-only: no live crawl, document download, DevHub access,
private artifact handling, official action, or legal/permitting guarantee is
represented or allowed in accepted packets.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

QUEUE_TYPE = "ppd.process_model_refresh_impact_queue.v6"
QUEUE_VERSION = "v6"
QUEUE_MODE = "fixture_first_offline_process_model_refresh_impact_queue_only"
CANDIDATE_SET_TYPE = "ppd.reextracted_requirement_candidate_set.v6"
CANDIDATE_SET_VERSION = "v6"
CANDIDATE_SET_MODE = "fixture_first_reextracted_requirement_candidates_v6_only"
EXPECTED_VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

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
    "live_crawl",
    "live_extraction",
    "document_download",
    "raw_body_storage",
    "devhub_opened",
    "private_document_read",
    "upload_attempted",
    "submission_attempted",
    "certification_attempted",
    "payment_attempted",
    "inspection_scheduling_attempted",
    "legal_or_permitting_guarantee",
    "active_process_model_mutation",
    "active_guardrail_mutation",
    "active_requirement_mutation",
)

ACTIVE_MUTATION_FLAG_KEYS = frozenset(
    {
        "active_mutation",
        "active_mutation_enabled",
        "mutation_enabled",
        "write_mode_enabled",
        "live_mutation",
        "active_refresh",
        "active_crawl",
        "active_process_model_refresh",
    }
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
        "trace",
    }
)

PROHIBITED_PHRASES = tuple(
    sorted(
        {
            "active mutation enabled",
            "application submitted",
            "approval guaranteed",
            "auth artifact",
            "certification completed",
            "crawled live",
            "devhub opened",
            "document downloaded",
            "downloaded artifact",
            "downloaded document",
            "guaranteed approval",
            "guaranteed permit",
            "inspection scheduled",
            "legal advice",
            "legal guarantee",
            "live crawl completed",
            "live crawl executed",
            "live crawl execution",
            "live extraction completed",
            "official action complete",
            "official action completed",
            "official action has completed",
            "payment completed",
            "permit guaranteed",
            "permitting guarantee",
            "private document read",
            "private session artifact",
            "raw artifact",
            "raw body stored",
            "raw crawl artifact",
            "raw crawl output",
            "session artifact",
            "submission completed",
            "upload completed",
        }
    )
)

REQUIRED_REF_FIELDS = (
    "required_user_fact_change_refs",
    "document_requirement_change_refs",
    "fee_change_placeholder_refs",
    "deadline_change_placeholder_refs",
    "action_gate_change_placeholder_refs",
    "unsupported_path_reminder_refs",
    "reviewer_hold_refs",
    "inactive_guardrail_dependency_note_refs",
)

IMPACT_GROUP_FIELDS = {
    "required_user_fact_change_refs": "required_user_fact_changes",
    "document_requirement_change_refs": "document_requirement_changes",
    "fee_change_placeholder_refs": "fee_change_placeholders",
    "deadline_change_placeholder_refs": "deadline_change_placeholders",
    "action_gate_change_placeholder_refs": "action_gate_change_placeholders",
    "unsupported_path_reminder_refs": "unsupported_path_reminders",
    "reviewer_hold_refs": "reviewer_hold_refs",
    "inactive_guardrail_dependency_note_refs": "inactive_guardrail_dependency_note_refs",
}


@dataclass(frozen=True)
class RequirementCandidateV6:
    candidate_id: str
    requirement_type: str
    affected_process_model_ids: tuple[str, ...]
    required_user_fact_change_refs: tuple[str, ...]
    document_requirement_change_refs: tuple[str, ...]
    fee_change_placeholder_refs: tuple[str, ...]
    deadline_change_placeholder_refs: tuple[str, ...]
    action_gate_change_placeholder_refs: tuple[str, ...]
    unsupported_path_reminder_refs: tuple[str, ...]
    reviewer_hold_refs: tuple[str, ...]
    inactive_guardrail_dependency_note_refs: tuple[str, ...]

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "RequirementCandidateV6":
        _reject_prohibited_content(row)
        for flag in REQUIRED_FALSE_FLAGS:
            if row.get(flag) is not False:
                raise ValueError(f"requirement candidate must declare {flag} false")
        requirement_type = _required_text(row, "requirement_type")
        if requirement_type not in ALLOWED_REQUIREMENT_TYPES:
            raise ValueError(f"unsupported requirement_type: {requirement_type}")
        _require_exact_validation_commands(row.get("validation_commands"), "requirement candidate")
        return cls(
            candidate_id=_required_text(row, "candidate_id"),
            requirement_type=requirement_type,
            affected_process_model_ids=_required_text_tuple(row, "affected_process_model_ids"),
            required_user_fact_change_refs=_required_text_tuple(row, "required_user_fact_change_refs"),
            document_requirement_change_refs=_required_text_tuple(row, "document_requirement_change_refs"),
            fee_change_placeholder_refs=_required_text_tuple(row, "fee_change_placeholder_refs"),
            deadline_change_placeholder_refs=_required_text_tuple(row, "deadline_change_placeholder_refs"),
            action_gate_change_placeholder_refs=_required_text_tuple(row, "action_gate_change_placeholder_refs"),
            unsupported_path_reminder_refs=_required_text_tuple(row, "unsupported_path_reminder_refs"),
            reviewer_hold_refs=_required_text_tuple(row, "reviewer_hold_refs"),
            inactive_guardrail_dependency_note_refs=_required_text_tuple(row, "inactive_guardrail_dependency_note_refs"),
        )


def load_reextracted_requirement_candidate_set_v6(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("re-extracted requirement candidate set v6 fixture must be an object")
    validate_reextracted_requirement_candidate_set_v6(payload)
    return payload


def validate_reextracted_requirement_candidate_set_v6(candidate_set: Mapping[str, Any]) -> None:
    _reject_prohibited_content(candidate_set)
    if candidate_set.get("candidate_set_type") != CANDIDATE_SET_TYPE:
        raise ValueError(f"candidate_set_type must be {CANDIDATE_SET_TYPE}")
    if candidate_set.get("candidate_set_version") != CANDIDATE_SET_VERSION:
        raise ValueError("candidate_set_version must be v6")
    _required_text(candidate_set, "candidate_set_id")
    if candidate_set.get("mode") != CANDIDATE_SET_MODE:
        raise ValueError(f"mode must be {CANDIDATE_SET_MODE}")
    if candidate_set.get("fixture_first") is not True:
        raise ValueError("fixture_first must be true")
    _require_exact_validation_commands(candidate_set.get("validation_commands"), "candidate set")
    for flag in REQUIRED_FALSE_FLAGS:
        if candidate_set.get(flag) is not False:
            raise ValueError(f"candidate set must declare {flag} false")
    candidates = candidate_set.get("requirement_candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidate set must include non-empty requirement_candidates")
    for row in candidates:
        if not isinstance(row, Mapping):
            raise ValueError("requirement_candidates must contain objects")
        RequirementCandidateV6.from_mapping(row)


def build_process_model_refresh_impact_queue_v6_from_fixture(path: str | Path) -> dict[str, Any]:
    candidate_set = load_reextracted_requirement_candidate_set_v6(path)
    candidates = tuple(RequirementCandidateV6.from_mapping(row) for row in candidate_set["requirement_candidates"])
    return build_process_model_refresh_impact_queue_v6(_required_text(candidate_set, "candidate_set_id"), candidates)


def build_process_model_refresh_impact_queue_v6(
    candidate_set_id: str,
    candidates: Sequence[RequirementCandidateV6],
) -> dict[str, Any]:
    if not candidates:
        raise ValueError("at least one re-extracted requirement candidate is required")

    process_ids = sorted({process_id for candidate in candidates for process_id in candidate.affected_process_model_ids})
    impact_groups = []
    for process_id in process_ids:
        scoped = [candidate for candidate in candidates if process_id in candidate.affected_process_model_ids]
        impact_groups.append(
            {
                "process_model_id": process_id,
                "candidate_refs": sorted(candidate.candidate_id for candidate in scoped),
                "required_user_fact_changes": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.required_user_fact_change_refs
                ),
                "document_requirement_changes": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.document_requirement_change_refs
                ),
                "fee_change_placeholders": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.fee_change_placeholder_refs
                ),
                "deadline_change_placeholders": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.deadline_change_placeholder_refs
                ),
                "action_gate_change_placeholders": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.action_gate_change_placeholder_refs
                ),
                "unsupported_path_reminders": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.unsupported_path_reminder_refs
                ),
                "reviewer_hold_refs": _sorted_unique(ref for candidate in scoped for ref in candidate.reviewer_hold_refs),
                "inactive_guardrail_dependency_note_refs": _sorted_unique(
                    ref for candidate in scoped for ref in candidate.inactive_guardrail_dependency_note_refs
                ),
                "activation_allowed": False,
                "validation_commands": EXPECTED_VALIDATION_COMMANDS,
            }
        )

    queue = {
        "queue_type": QUEUE_TYPE,
        "queue_version": QUEUE_VERSION,
        "mode": QUEUE_MODE,
        "fixture_first": True,
        "consumes_only_reextracted_requirement_candidate_set_v6_fixtures": True,
        "source_candidate_set_ref": candidate_set_id,
        "row_count": len(impact_groups),
        "affected_process_models": process_ids,
        "impact_groups": impact_groups,
        "reviewer_hold_rows": [
            {"reviewer_hold_ref": ref, "status": "inactive_reviewer_hold_placeholder", "activation_allowed": False}
            for ref in _sorted_unique(ref for candidate in candidates for ref in candidate.reviewer_hold_refs)
        ],
        "inactive_guardrail_dependency_notes": [
            {"dependency_note_ref": ref, "status": "inactive_guardrail_dependency_note", "activation_allowed": False}
            for ref in _sorted_unique(
                ref for candidate in candidates for ref in candidate.inactive_guardrail_dependency_note_refs
            )
        ],
        "validation_commands": EXPECTED_VALIDATION_COMMANDS,
        "attestations": {flag: False for flag in REQUIRED_FALSE_FLAGS},
    }
    validate_process_model_refresh_impact_queue_v6(queue)
    return queue


def validate_process_model_refresh_impact_queue_v6(queue: Mapping[str, Any]) -> None:
    _reject_prohibited_content(queue)
    if queue.get("queue_type") != QUEUE_TYPE:
        raise ValueError(f"queue_type must be {QUEUE_TYPE}")
    if queue.get("queue_version") != QUEUE_VERSION:
        raise ValueError("queue_version must be v6")
    if queue.get("mode") != QUEUE_MODE:
        raise ValueError(f"mode must be {QUEUE_MODE}")
    if queue.get("fixture_first") is not True:
        raise ValueError("fixture_first must be true")
    if queue.get("consumes_only_reextracted_requirement_candidate_set_v6_fixtures") is not True:
        raise ValueError("queue must consume only re-extracted requirement candidate set v6 fixtures")
    _required_text(queue, "source_candidate_set_ref")
    _require_exact_validation_commands(queue.get("validation_commands"), "queue")

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

    groups = queue.get("impact_groups")
    if not isinstance(groups, list) or not groups:
        raise ValueError("impact_groups must be a non-empty list")
    process_ids_from_groups = set()
    for group in groups:
        process_ids_from_groups.add(_validate_impact_group(group))
    if queue.get("row_count") != len(groups):
        raise ValueError("row_count must match impact_groups length")
    if process_ids_from_groups != affected_process_model_set:
        missing = sorted(affected_process_model_set - process_ids_from_groups)
        extra = sorted(process_ids_from_groups - affected_process_model_set)
        detail = []
        if missing:
            detail.append("missing impact groups for affected process models: " + ", ".join(missing))
        if extra:
            detail.append("unexpected impact groups for process models: " + ", ".join(extra))
        raise ValueError("; ".join(detail))

    reviewer_hold_refs = _collect_group_refs(groups, "reviewer_hold_refs")
    inactive_guardrail_refs = _collect_group_refs(groups, "inactive_guardrail_dependency_note_refs")
    _validate_reference_rows(
        queue.get("reviewer_hold_rows"),
        "reviewer_hold_ref",
        "inactive_reviewer_hold_placeholder",
        reviewer_hold_refs,
    )
    _validate_reference_rows(
        queue.get("inactive_guardrail_dependency_notes"),
        "dependency_note_ref",
        "inactive_guardrail_dependency_note",
        inactive_guardrail_refs,
    )


def _validate_impact_group(group: Any) -> str:
    if not isinstance(group, Mapping):
        raise ValueError("impact group must be an object")
    process_model_id = _required_text(group, "process_model_id")
    if group.get("activation_allowed") is not False:
        raise ValueError("impact group activation_allowed must be false")
    _require_exact_validation_commands(group.get("validation_commands"), "impact group")
    if not _non_empty_text_list(group.get("candidate_refs")):
        raise ValueError("impact group candidate_refs must be non-empty")
    for queue_field in IMPACT_GROUP_FIELDS.values():
        if not _non_empty_text_list(group.get(queue_field)):
            raise ValueError(f"impact group {queue_field} must be non-empty")
    return process_model_id


def _validate_reference_rows(rows: Any, ref_field: str, status: str, expected_refs: set[str]) -> None:
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
    if seen_refs != expected_refs:
        missing = sorted(expected_refs - seen_refs)
        extra = sorted(seen_refs - expected_refs)
        detail = []
        if missing:
            detail.append(f"missing {ref_field} rows: " + ", ".join(missing))
        if extra:
            detail.append(f"unexpected {ref_field} rows: " + ", ".join(extra))
        raise ValueError("; ".join(detail))


def _collect_group_refs(groups: Sequence[Any], field: str) -> set[str]:
    refs = set()
    for group in groups:
        if isinstance(group, Mapping):
            value = group.get(field)
            if isinstance(value, list):
                refs.update(item for item in value if isinstance(item, str) and item.strip())
    return refs


def _reject_prohibited_content(value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            normalized_key = _normalize_text(key_text)
            if key_text in PROHIBITED_KEYS:
                raise ValueError(f"{path} contains prohibited key: {key}")
            if key_text in REQUIRED_FALSE_FLAGS and child is not False:
                raise ValueError(f"{path}.{key} must be false")
            if key_text in ACTIVE_MUTATION_FLAG_KEYS and child not in (False, None, ""):
                raise ValueError(f"{path}.{key} active mutation flag is not allowed")
            if "active mutation" in normalized_key and child not in (False, None, ""):
                raise ValueError(f"{path}.{key} active mutation flag is not allowed")
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
    if value != EXPECTED_VALIDATION_COMMANDS:
        raise ValueError(f"{label} must contain only exact offline validation_commands")


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
