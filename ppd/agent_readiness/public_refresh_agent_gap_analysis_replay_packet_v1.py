"""Fixture-first public refresh agent gap-analysis replay packet v1.

This module consumes only synthetic inactive ProcessModel delta plan rows and
inactive guardrail recompile plan rows. It plans UserGapAnalysis replay
expectations without live extraction, crawling, downloads, DevHub access, active
agent API or case-record mutation, or official actions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

PACKET_TYPE = "ppd.public_refresh_agent_gap_analysis_replay_packet.v1"
PACKET_VERSION = "v1"
EXECUTION_MODE = "offline_fixture_only"

EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/public_refresh_agent_gap_analysis_replay_packet_v1.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_refresh_agent_gap_analysis_replay_packet_v1.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

NON_MUTATION_FLAGS = {
    "fixture_first": True,
    "uses_synthetic_rows_only": True,
    "live_extraction_performed": False,
    "live_crawling_performed": False,
    "documents_downloaded": False,
    "devhub_opened": False,
    "active_agent_api_mutated": False,
    "active_case_records_mutated": False,
    "active_process_models_mutated": False,
    "active_guardrails_mutated": False,
    "official_actions_performed": False,
}

REQUIRED_BLOCKED_ACTION_CLASSES = {
    "upload",
    "submit",
    "certify",
    "pay",
    "schedule",
    "cancel",
    "official_record_change",
}

PRIVATE_KEY_MARKERS = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "devhub_session",
    "downloaded_artifact",
    "downloaded_document",
    "har",
    "local_private_path",
    "password",
    "private_artifact",
    "raw_body",
    "raw_crawl_output",
    "raw_download",
    "screenshot",
    "session_state",
    "storage_state",
    "trace",
)

PRIVATE_VALUE_MARKERS = (
    "/private/",
    "auth-state",
    "auth_state",
    "browser-trace",
    "browser_trace",
    "cookies.json",
    "downloaded-document",
    "downloaded_document",
    "har.zip",
    "raw-body",
    "raw_body",
    "raw-crawl-output",
    "raw_crawl_output",
    "session-state",
    "session_state",
    "storage_state",
    "trace.zip",
)

FORBIDDEN_TEXT_MARKERS = (
    "account created",
    "active agent api mutated",
    "active case record mutated",
    "application submitted",
    "approval guaranteed",
    "case record mutated",
    "certification completed",
    "certified the application",
    "devhub opened",
    "devhub session established",
    "devhub workflow completed",
    "document downloaded",
    "downloaded document",
    "fee paid",
    "guarantee approval",
    "guaranteed approval",
    "guaranteed permit",
    "inspection scheduled",
    "legal guarantee",
    "legally guaranteed",
    "live crawl completed",
    "live crawl executed",
    "live crawl performed",
    "live extraction completed",
    "live extraction executed",
    "live extraction performed",
    "official action completed",
    "official record changed",
    "payment submitted",
    "permit guaranteed",
    "permitting guarantee",
    "raw crawl output",
    "submitted permit",
    "upload completed",
)

ACTIVE_MUTATION_FLAG_KEYS = {
    "active_agent_api_mutated",
    "active_case_records_mutated",
    "active_process_models_mutated",
    "active_guardrails_mutated",
    "official_actions_performed",
    "crawler_mutation",
    "source_mutation",
    "archive_mutation",
    "document_mutation",
    "requirement_mutation",
    "guardrail_mutation",
    "prompt_mutation",
    "contract_mutation",
    "devhub_surface_mutation",
    "release_state_mutation",
}


def load_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed synthetic replay fixture."""

    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("public refresh agent gap-analysis replay fixture must be an object")
    return loaded


def build_public_refresh_agent_gap_analysis_replay_packet_v1_from_file(path: str | Path) -> dict[str, Any]:
    return build_public_refresh_agent_gap_analysis_replay_packet_v1(load_fixture(path))


def build_public_refresh_agent_gap_analysis_replay_packet_v1(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic offline UserGapAnalysis replay packet."""

    process_rows = _validated_rows(
        fixture.get("inactive_process_model_delta_plan_rows"),
        "inactive_process_model_delta_plan_rows",
        "inactive_process_model_delta_plan_row",
    )
    guardrail_rows = _validated_rows(
        fixture.get("inactive_guardrail_recompile_plan_rows"),
        "inactive_guardrail_recompile_plan_rows",
        "inactive_guardrail_recompile_plan_row",
    )
    _reject_private_or_live_claims(fixture)

    replay_cases = []
    for index, process_row in enumerate(process_rows, start=1):
        guardrail_row = _matching_guardrail_row(process_row, guardrail_rows)
        replay_cases.append(_replay_case(index, process_row, guardrail_row))

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "public-refresh-agent-gap-analysis-replay-packet-v1",
        "execution_mode": EXECUTION_MODE,
        "non_mutation_flags": dict(NON_MUTATION_FLAGS),
        "source_row_refs": {
            "inactive_process_model_delta_plan_row_ids": [str(row["row_id"]) for row in process_rows],
            "inactive_guardrail_recompile_plan_row_ids": [str(row["row_id"]) for row in guardrail_rows],
        },
        "user_gap_analysis_replay_expectations": replay_cases,
        "source_evidence_placeholder_summary": _source_evidence_summary(replay_cases),
        "reviewer_holds": _reviewer_holds(replay_cases),
        "rollback_notes": [
            {
                "rollback_id": "discard-public-refresh-gap-analysis-replay-packet-v1",
                "note": "Discard this synthetic replay packet and its inactive fixture rows; no active agent API, case record, ProcessModel, GuardrailBundle, source corpus, DevHub state, or official record was changed.",
            }
        ],
        "exact_offline_validation_commands": [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS],
    }
    assert_valid_public_refresh_agent_gap_analysis_replay_packet_v1(packet)
    return packet


def assert_valid_public_refresh_agent_gap_analysis_replay_packet_v1(packet: Mapping[str, Any]) -> None:
    problems = validate_public_refresh_agent_gap_analysis_replay_packet_v1(packet)
    if problems:
        raise ValueError("invalid public refresh agent gap-analysis replay packet v1: " + "; ".join(problems))


def validate_public_refresh_agent_gap_analysis_replay_packet_v1(packet: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v1")
    if packet.get("execution_mode") != EXECUTION_MODE:
        problems.append(f"execution_mode must be {EXECUTION_MODE}")
    if packet.get("non_mutation_flags") != NON_MUTATION_FLAGS:
        problems.append("non_mutation_flags must preserve offline fixture-only boundaries")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("exact_offline_validation_commands must match the offline validation command list")

    _validate_source_row_refs(packet, problems)
    _validate_top_level_support_sections(packet, problems)

    cases = packet.get("user_gap_analysis_replay_expectations")
    if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes, bytearray)) or not cases:
        problems.append("user_gap_analysis_replay_expectations must be a non-empty list")
    else:
        for index, case in enumerate(cases):
            if not isinstance(case, Mapping):
                problems.append(f"user_gap_analysis_replay_expectations[{index}] must be an object")
                continue
            _validate_case(case, index, problems)

    try:
        _reject_private_or_live_claims(packet)
    except ValueError as exc:
        problems.append(str(exc))
    return problems


def _validated_rows(value: Any, label: str, expected_row_type: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)) or not value:
        raise ValueError(f"{label} must be a non-empty list")
    rows: list[Mapping[str, Any]] = []
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            raise ValueError(f"{label}[{index}] must be an object")
        if row.get("row_type") != expected_row_type:
            raise ValueError(f"{label}[{index}].row_type must be {expected_row_type}")
        if row.get("synthetic") is not True:
            raise ValueError(f"{label}[{index}] must be synthetic")
        if row.get("state") != "inactive":
            raise ValueError(f"{label}[{index}].state must be inactive")
        if not _text(row.get("row_id")):
            raise ValueError(f"{label}[{index}].row_id is required")
        if not _text(row.get("process_model_id")):
            raise ValueError(f"{label}[{index}].process_model_id is required")
        if not _string_list(row.get("source_evidence_placeholder_ids")):
            raise ValueError(f"{label}[{index}].source_evidence_placeholder_ids is required")
        rows.append(row)
    return sorted(rows, key=lambda row: str(row["row_id"]))


def _matching_guardrail_row(process_row: Mapping[str, Any], guardrail_rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
    process_model_id = str(process_row["process_model_id"])
    for row in guardrail_rows:
        if row.get("process_model_id") == process_model_id:
            return row
    raise ValueError(f"missing inactive guardrail recompile row for process_model_id {process_model_id}")


def _replay_case(sequence: int, process_row: Mapping[str, Any], guardrail_row: Mapping[str, Any]) -> dict[str, Any]:
    process_row_id = str(process_row["row_id"])
    guardrail_row_id = str(guardrail_row["row_id"])
    process_model_id = str(process_row["process_model_id"])
    citation_ids = sorted(
        set(_string_list(process_row.get("source_evidence_placeholder_ids")))
        | set(_string_list(guardrail_row.get("source_evidence_placeholder_ids")))
    )
    stale_ids = _string_list(process_row.get("stale_evidence_ids")) or [f"{process_row_id}-stale-placeholder"]
    conflict_ids = _string_list(process_row.get("conflicting_evidence_ids")) or [f"{guardrail_row_id}-conflict-placeholder"]

    return {
        "case_sequence": sequence,
        "case_id": f"{process_model_id}-user-gap-analysis-replay",
        "source_rows": {
            "inactive_process_model_delta_plan_row_id": process_row_id,
            "inactive_guardrail_recompile_plan_row_id": guardrail_row_id,
        },
        "process_id": process_model_id,
        "user_gap_analysis_expectation": {
            "expected_status": "held_for_reviewer_gap_analysis_replay",
            "known_facts_policy": "use_synthetic_inactive_fixture_facts_only",
            "matched_documents_policy": "use_synthetic_inactive_fixture_document_refs_only",
        },
        "missing_fact_deltas": _delta_rows(
            process_row,
            "missing_fact_ids",
            "missing_fact_delta",
            f"{process_row_id}-missing-fact-placeholder",
            citation_ids,
        ),
        "missing_document_deltas": _delta_rows(
            process_row,
            "missing_document_ids",
            "missing_document_delta",
            f"{process_row_id}-missing-document-placeholder",
            citation_ids,
        ),
        "stale_evidence_outcomes": [
            {
                "evidence_id": evidence_id,
                "outcome": "flag_stale_for_user_gap_analysis_review",
                "source_evidence_placeholder_ids": citation_ids,
            }
            for evidence_id in stale_ids
        ],
        "conflicting_evidence_outcomes": [
            {
                "evidence_id": evidence_id,
                "outcome": "flag_conflict_for_reviewer_resolution",
                "source_evidence_placeholder_ids": citation_ids,
            }
            for evidence_id in conflict_ids
        ],
        "blocked_action_checks": [
            {
                "check_id": f"{guardrail_row_id}-block-consequential-action",
                "blocked_action_classes": sorted(REQUIRED_BLOCKED_ACTION_CLASSES),
                "expected_decision": "blocked",
                "reason": "Inactive public-refresh replay cannot perform consequential or official actions.",
                "source_evidence_placeholder_ids": citation_ids,
            }
        ],
        "next_safe_action_deltas": [
            {
                "next_safe_action_id": f"{process_row_id}-ask-for-missing-inputs",
                "action": "ask_user_for_missing_or_conflicting_synthetic_inputs",
                "allowed": True,
                "limits": "No DevHub access, upload, submission, payment, scheduling, certification, cancellation, active API mutation, or active case-record mutation.",
                "source_evidence_placeholder_ids": citation_ids,
            },
            {
                "next_safe_action_id": f"{guardrail_row_id}-prepare-reviewer-handoff",
                "action": "prepare_reviewer_handoff_note_from_fixture_placeholders",
                "allowed": True,
                "limits": "Reviewer handoff remains an offline note and does not change active records.",
                "source_evidence_placeholder_ids": citation_ids,
            },
        ],
        "source_evidence_placeholders": [
            {"placeholder_id": placeholder_id, "status": "placeholder_pending_public_source_replacement"}
            for placeholder_id in citation_ids
        ],
        "reviewer_hold": {
            "hold_id": f"{process_model_id}-gap-analysis-reviewer-hold",
            "status": "held_for_manual_review",
            "reason": "Synthetic inactive public-refresh replay expectations require reviewer disposition before promotion.",
        },
        "rollback_note": {
            "rollback_id": f"{process_model_id}-gap-analysis-replay-rollback",
            "note": "Discard this replay case; no active agent API, case record, ProcessModel, GuardrailBundle, DevHub, source corpus, or official record was changed.",
        },
    }


def _delta_rows(
    source_row: Mapping[str, Any],
    source_key: str,
    delta_kind: str,
    fallback_id: str,
    citation_ids: Sequence[str],
) -> list[dict[str, Any]]:
    ids = _string_list(source_row.get(source_key)) or [fallback_id]
    return [
        {
            "delta_id": value,
            "delta_kind": delta_kind,
            "expected_user_gap_analysis_change": "add_or_refresh_offline_gap_placeholder",
            "source_evidence_placeholder_ids": list(citation_ids),
        }
        for value in ids
    ]


def _source_evidence_summary(replay_cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    placeholder_ids = sorted(
        {
            str(row["placeholder_id"])
            for case in replay_cases
            for row in _mapping_list(case.get("source_evidence_placeholders"))
            if _text(row.get("placeholder_id"))
        }
    )
    return {
        "all_replay_cases_have_source_evidence_placeholders": bool(placeholder_ids),
        "placeholder_ids": placeholder_ids,
        "replacement_policy": "replace placeholders only through future validated public-source refresh review, not during this replay packet",
    }


def _reviewer_holds(replay_cases: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [dict(case["reviewer_hold"]) for case in replay_cases if isinstance(case.get("reviewer_hold"), Mapping)]


def _validate_source_row_refs(packet: Mapping[str, Any], problems: list[str]) -> None:
    refs = packet.get("source_row_refs")
    if not isinstance(refs, Mapping):
        problems.append("source_row_refs must be an object with process-model and guardrail references")
        return
    if not _string_list(refs.get("inactive_process_model_delta_plan_row_ids")):
        problems.append("source_row_refs.inactive_process_model_delta_plan_row_ids must be a non-empty list")
    if not _string_list(refs.get("inactive_guardrail_recompile_plan_row_ids")):
        problems.append("source_row_refs.inactive_guardrail_recompile_plan_row_ids must be a non-empty list")


def _validate_top_level_support_sections(packet: Mapping[str, Any], problems: list[str]) -> None:
    summary = packet.get("source_evidence_placeholder_summary")
    if not isinstance(summary, Mapping) or not _string_list(summary.get("placeholder_ids")):
        problems.append("source_evidence_placeholder_summary.placeholder_ids must be a non-empty list")
    if not _non_empty_sequence(packet.get("reviewer_holds")):
        problems.append("reviewer_holds must be a non-empty list")
    if not _non_empty_sequence(packet.get("rollback_notes")):
        problems.append("rollback_notes must be a non-empty list")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("exact_offline_validation_commands must include the required offline validation commands")


def _validate_case(case: Mapping[str, Any], index: int, problems: list[str]) -> None:
    required = (
        "case_id",
        "source_rows",
        "user_gap_analysis_expectation",
        "missing_fact_deltas",
        "missing_document_deltas",
        "stale_evidence_outcomes",
        "conflicting_evidence_outcomes",
        "blocked_action_checks",
        "next_safe_action_deltas",
        "source_evidence_placeholders",
        "reviewer_hold",
        "rollback_note",
    )
    for key in required:
        if key not in case:
            problems.append(f"user_gap_analysis_replay_expectations[{index}].{key} is required")

    source_rows = case.get("source_rows")
    if not isinstance(source_rows, Mapping):
        problems.append(f"user_gap_analysis_replay_expectations[{index}].source_rows must be an object")
    else:
        if not _text(source_rows.get("inactive_process_model_delta_plan_row_id")):
            problems.append(
                f"user_gap_analysis_replay_expectations[{index}].source_rows.inactive_process_model_delta_plan_row_id is required"
            )
        if not _text(source_rows.get("inactive_guardrail_recompile_plan_row_id")):
            problems.append(
                f"user_gap_analysis_replay_expectations[{index}].source_rows.inactive_guardrail_recompile_plan_row_id is required"
            )

    expectation = case.get("user_gap_analysis_expectation")
    if not isinstance(expectation, Mapping) or expectation.get("expected_status") != "held_for_reviewer_gap_analysis_replay":
        problems.append(
            f"user_gap_analysis_replay_expectations[{index}].user_gap_analysis_expectation must preserve held replay expectations"
        )

    _validate_non_empty_object_list(case, index, "missing_fact_deltas", "delta_id", problems)
    _validate_non_empty_object_list(case, index, "missing_document_deltas", "delta_id", problems)
    _validate_non_empty_object_list(case, index, "stale_evidence_outcomes", "evidence_id", problems)
    _validate_non_empty_object_list(case, index, "conflicting_evidence_outcomes", "evidence_id", problems)
    _validate_non_empty_object_list(case, index, "next_safe_action_deltas", "next_safe_action_id", problems)
    _validate_non_empty_object_list(case, index, "source_evidence_placeholders", "placeholder_id", problems)
    _validate_blocked_action_checks(case, index, problems)

    reviewer_hold = case.get("reviewer_hold")
    if not isinstance(reviewer_hold, Mapping) or reviewer_hold.get("status") != "held_for_manual_review":
        problems.append(f"user_gap_analysis_replay_expectations[{index}].reviewer_hold must be held_for_manual_review")
    rollback_note = case.get("rollback_note")
    if not isinstance(rollback_note, Mapping) or not _text(rollback_note.get("note")):
        problems.append(f"user_gap_analysis_replay_expectations[{index}].rollback_note.note is required")


def _validate_non_empty_object_list(
    case: Mapping[str, Any],
    case_index: int,
    key: str,
    required_id_key: str,
    problems: list[str],
) -> None:
    rows = case.get(key)
    if not _non_empty_sequence(rows):
        problems.append(f"user_gap_analysis_replay_expectations[{case_index}].{key} must be a non-empty list")
        return
    for row_index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            problems.append(f"user_gap_analysis_replay_expectations[{case_index}].{key}[{row_index}] must be an object")
            continue
        if not _text(row.get(required_id_key)):
            problems.append(
                f"user_gap_analysis_replay_expectations[{case_index}].{key}[{row_index}].{required_id_key} is required"
            )
        if not _string_list(row.get("source_evidence_placeholder_ids")) and key != "source_evidence_placeholders":
            problems.append(
                f"user_gap_analysis_replay_expectations[{case_index}].{key}[{row_index}].source_evidence_placeholder_ids is required"
            )


def _validate_blocked_action_checks(case: Mapping[str, Any], index: int, problems: list[str]) -> None:
    checks = case.get("blocked_action_checks")
    if not _non_empty_sequence(checks):
        problems.append(f"user_gap_analysis_replay_expectations[{index}].blocked_action_checks must be a non-empty list")
        return
    covered: set[str] = set()
    for check_index, check in enumerate(checks):
        if not isinstance(check, Mapping):
            problems.append(f"user_gap_analysis_replay_expectations[{index}].blocked_action_checks[{check_index}] must be an object")
            continue
        if check.get("expected_decision") != "blocked":
            problems.append(
                f"user_gap_analysis_replay_expectations[{index}].blocked_action_checks[{check_index}].expected_decision must be blocked"
            )
        covered.update(_string_list(check.get("blocked_action_classes")))
        if not _string_list(check.get("source_evidence_placeholder_ids")):
            problems.append(
                f"user_gap_analysis_replay_expectations[{index}].blocked_action_checks[{check_index}].source_evidence_placeholder_ids is required"
            )
    missing = sorted(REQUIRED_BLOCKED_ACTION_CLASSES - covered)
    if missing:
        problems.append(
            f"user_gap_analysis_replay_expectations[{index}].blocked_action_checks must cover blocked action classes: {', '.join(missing)}"
        )


def _reject_private_or_live_claims(value: Any, path: str = "packet") -> None:
    for child_path, key, child in _walk(value, path):
        lowered_key = key.lower() if key else ""
        if any(marker in lowered_key for marker in PRIVATE_KEY_MARKERS):
            raise ValueError(f"{child_path} must not contain private, raw, downloaded, or runtime artifacts")
        if lowered_key in ACTIVE_MUTATION_FLAG_KEYS and child is True:
            raise ValueError(f"{child_path} must not enable active mutation flags")
        if isinstance(child, str):
            lowered = child.lower()
            if any(marker in lowered for marker in PRIVATE_VALUE_MARKERS):
                raise ValueError(f"{child_path} must not contain private, raw, downloaded, or runtime artifacts")
            if any(marker in lowered for marker in FORBIDDEN_TEXT_MARKERS):
                raise ValueError(
                    f"{child_path} must not contain live extraction/crawl, DevHub access, download, active mutation, official-action, or guarantee claims"
                )


def _walk(value: Any, path: str = "packet", key: str | None = None) -> list[tuple[str, str | None, Any]]:
    rows = [(path, key, value)]
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            child_key_text = str(child_key)
            rows.extend(_walk(child, f"{path}.{child_key_text}", child_key_text))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            rows.extend(_walk(child, f"{path}[{index}]", None))
    return rows


def _mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [row for row in value if isinstance(row, Mapping)]


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and bool(value)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


__all__ = [
    "EXACT_OFFLINE_VALIDATION_COMMANDS",
    "build_public_refresh_agent_gap_analysis_replay_packet_v1",
    "build_public_refresh_agent_gap_analysis_replay_packet_v1_from_file",
    "assert_valid_public_refresh_agent_gap_analysis_replay_packet_v1",
    "validate_public_refresh_agent_gap_analysis_replay_packet_v1",
]
