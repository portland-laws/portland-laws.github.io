from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ALLOWED_PACKET_TYPES = {
    "agent_guardrail_api_compatibility_packet_v6",
    "guarded_draft_preview_handoff_packet_v6",
    "local_pdf_draft_preview_packet_v6",
}

OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
    ["python3", "-m", "pytest", "ppd/tests/test_user_gap_analysis_packet_v6.py"],
]

PROHIBITED_ACTIONS = [
    "read_private_documents",
    "open_devhub",
    "upload",
    "submit",
    "certify",
    "pay",
    "schedule",
    "legal_or_permitting_guarantee",
]

SAFE_REVERSIBLE_ACTIONS = [
    "review_synthetic_case_fact_inventory",
    "fill_missing_fact_rows_from_user_memory",
    "label_missing_documents_without_uploading",
    "compare_fixture_citation_payloads",
    "prepare_manual_handoff_notes",
    "run_offline_validation_commands",
]

REQUIRED_SOURCE_PACKET_TYPES = [
    "agent_guardrail_api_compatibility_packet_v6",
    "guarded_draft_preview_handoff_packet_v6",
    "local_pdf_draft_preview_packet_v6",
]

REQUIRED_LIST_FIELDS = {
    "synthetic_case_fact_inventory": "synthetic case fact inventories are required",
    "missing_fact_rows": "missing-fact rows are required",
    "missing_document_labels": "missing-document rows are required",
    "stale_or_conflicting_evidence_rows": "stale or conflicting evidence rows are required",
    "blocked_action_rows": "blocked action rows are required",
    "next_safe_reversible_actions": "reversible next-safe-action rows are required",
    "citation_payloads": "citation payloads are required",
    "manual_handoff_notes": "manual handoff notes are required",
    "offline_validation_commands": "validation commands are required",
}

PRIVATE_VALUE_KEYS = {
    "auth_state",
    "browser_state",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "downloaded_document_path",
    "downloaded_document_values",
    "local_private_path",
    "password",
    "private_document_value",
    "private_document_values",
    "private_file_path",
    "raw_authenticated_value",
    "raw_document_value",
    "raw_document_values",
    "session_state",
    "token",
    "trace_path",
}

FORBIDDEN_TEXT_PATTERNS = {
    "private document values": re.compile(
        r"\b(?:private document value|private document values|raw private document|downloaded private document|/users/[^\s]+|c:\\\\users\\\\[^\s]+|cookie=|auth state|session state)\b",
        re.IGNORECASE,
    ),
    "live DevHub access claims": re.compile(
        r"\b(?:live devhub access|opened devhub|logged into devhub|authenticated devhub|devhub session captured|devhub was accessed)\b",
        re.IGNORECASE,
    ),
    "official-action completion claims": re.compile(
        r"\b(?:submitted permit request|submitted the permit|uploaded to official record|certified acknowledgement|paid fees|scheduled inspection|official action completed|permit was approved)\b",
        re.IGNORECASE,
    ),
    "legal or permitting guarantees": re.compile(
        r"\b(?:guarantee(?:d|s)? permit|guarantee(?:d|s)? approval|will be approved|legal advice|legally compliant|permitting outcome is guaranteed)\b",
        re.IGNORECASE,
    ),
    "active mutation claims": re.compile(
        r"\b(?:active mutation|mutated live state|mutates live systems|live mutation enabled|mutation flag enabled)\b",
        re.IGNORECASE,
    ),
}


def load_json(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object fixture: {path}")
    return value


def _require_packet(packet: dict[str, Any], packet_type: str) -> None:
    actual = packet.get("packet_type")
    if actual != packet_type or actual not in ALLOWED_PACKET_TYPES:
        raise ValueError(f"Unexpected packet type: {actual!r}")


def _list(packet: dict[str, Any], key: str) -> list[Any]:
    value = packet.get(key, [])
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"Expected list for {key}")
    return value


def _facts_from_handoff(handoff: dict[str, Any]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for item in _list(handoff, "draft_case_facts"):
        if not isinstance(item, dict):
            continue
        facts.append(
            {
                "fact_id": str(item.get("fact_id", "")),
                "label": str(item.get("label", "")),
                "value": item.get("value"),
                "source_packet": handoff["packet_type"],
                "citation_ids": list(item.get("citation_ids", [])),
            }
        )
    return facts


def _missing_fact_rows(handoff: dict[str, Any], local_pdf: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _list(handoff, "required_facts"):
        if not isinstance(item, dict) or item.get("present") is True:
            continue
        rows.append(
            {
                "fact_id": str(item.get("fact_id", "")),
                "label": str(item.get("label", "")),
                "reason": str(item.get("reason", "missing_from_guarded_draft_preview")),
                "safe_collection_method": "ask_user_or_review_local_fixture_summary_only",
            }
        )
    for item in _list(local_pdf, "unresolved_fields"):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "fact_id": str(item.get("field_id", "")),
                "label": str(item.get("label", "")),
                "reason": "unresolved_in_local_pdf_draft_preview_fixture",
                "safe_collection_method": "ask_user_or_review_local_fixture_summary_only",
            }
        )
    return rows


def assemble_user_gap_analysis_packet_v6(
    guardrail: dict[str, Any],
    handoff: dict[str, Any],
    local_pdf: dict[str, Any],
) -> dict[str, Any]:
    _require_packet(guardrail, "agent_guardrail_api_compatibility_packet_v6")
    _require_packet(handoff, "guarded_draft_preview_handoff_packet_v6")
    _require_packet(local_pdf, "local_pdf_draft_preview_packet_v6")

    allowed_actions = set(guardrail.get("allowed_actions", []))
    blocked_action_rows = [
        {
            "action": action,
            "status": "blocked",
            "reason": "outside_fixture_first_user_gap_analysis_scope",
        }
        for action in PROHIBITED_ACTIONS
    ]

    next_safe_reversible_actions = [
        action for action in SAFE_REVERSIBLE_ACTIONS if action in allowed_actions
    ]

    return {
        "packet_type": "fixture_first_user_gap_analysis_packet_v6",
        "version": 6,
        "source_packet_types": list(REQUIRED_SOURCE_PACKET_TYPES),
        "scope": {
            "fixture_first": True,
            "private_documents_read": False,
            "devhub_opened": False,
            "uploads_or_submissions_performed": False,
            "payments_or_scheduling_performed": False,
            "legal_or_permitting_guarantees": False,
        },
        "synthetic_case_fact_inventory": _facts_from_handoff(handoff),
        "missing_fact_rows": _missing_fact_rows(handoff, local_pdf),
        "missing_document_labels": _list(handoff, "missing_document_labels") + _list(local_pdf, "missing_document_labels"),
        "stale_or_conflicting_evidence_rows": _list(handoff, "stale_or_conflicting_evidence_rows") + _list(local_pdf, "stale_or_conflicting_evidence_rows"),
        "blocked_action_rows": blocked_action_rows,
        "next_safe_reversible_actions": next_safe_reversible_actions,
        "citation_payloads": _list(handoff, "citation_payloads") + _list(local_pdf, "citation_payloads"),
        "manual_handoff_notes": _list(handoff, "manual_handoff_notes") + _list(local_pdf, "manual_handoff_notes"),
        "offline_validation_commands": OFFLINE_VALIDATION_COMMANDS,
    }


def assemble_from_fixture_paths(
    guardrail_path: str | Path,
    handoff_path: str | Path,
    local_pdf_path: str | Path,
) -> dict[str, Any]:
    return assemble_user_gap_analysis_packet_v6(
        load_json(guardrail_path),
        load_json(handoff_path),
        load_json(local_pdf_path),
    )


def validate_user_gap_analysis_packet_v6(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("packet_type") != "fixture_first_user_gap_analysis_packet_v6":
        errors.append("packet_type must be fixture_first_user_gap_analysis_packet_v6")
    if packet.get("version") != 6:
        errors.append("version must be 6")

    source_packet_types = packet.get("source_packet_types")
    if not isinstance(source_packet_types, list):
        errors.append("source_packet_types must include compatibility, guarded handoff, and local PDF preview references")
    else:
        for packet_type in REQUIRED_SOURCE_PACKET_TYPES:
            if packet_type not in source_packet_types:
                errors.append(f"missing required source packet reference: {packet_type}")

    _validate_scope(packet.get("scope"), errors)
    _validate_required_lists(packet, errors)
    _validate_fact_rows(packet.get("synthetic_case_fact_inventory"), errors)
    _validate_missing_fact_rows(packet.get("missing_fact_rows"), errors)
    _validate_missing_document_rows(packet.get("missing_document_labels"), errors)
    _validate_stale_or_conflicting_rows(packet.get("stale_or_conflicting_evidence_rows"), errors)
    _validate_blocked_actions(packet.get("blocked_action_rows"), errors)
    _validate_next_safe_actions(packet.get("next_safe_reversible_actions"), errors)
    _validate_citation_payloads(packet.get("citation_payloads"), errors)
    _validate_manual_handoff_notes(packet.get("manual_handoff_notes"), errors)
    _validate_validation_commands(packet.get("offline_validation_commands"), errors)
    _scan_for_forbidden_values(packet, errors)
    return errors


def assert_valid_user_gap_analysis_packet_v6(packet: dict[str, Any]) -> None:
    errors = validate_user_gap_analysis_packet_v6(packet)
    if errors:
        raise ValueError("; ".join(errors))


def _validate_scope(scope: Any, errors: list[str]) -> None:
    if not isinstance(scope, dict):
        errors.append("scope must be an object")
        return
    expected = {
        "fixture_first": True,
        "private_documents_read": False,
        "devhub_opened": False,
        "uploads_or_submissions_performed": False,
        "payments_or_scheduling_performed": False,
        "legal_or_permitting_guarantees": False,
    }
    for key, expected_value in expected.items():
        if scope.get(key) is not expected_value:
            errors.append(f"scope.{key} must be {expected_value!r}")


def _validate_required_lists(packet: dict[str, Any], errors: list[str]) -> None:
    for field, message in REQUIRED_LIST_FIELDS.items():
        value = packet.get(field)
        if not isinstance(value, list) or not value:
            errors.append(message)


def _validate_fact_rows(rows: Any, errors: list[str]) -> None:
    if not isinstance(rows, list):
        return
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"synthetic_case_fact_inventory[{index}] must be an object")
            continue
        for field in ("fact_id", "label", "source_packet", "citation_ids"):
            if field not in row or row.get(field) in (None, "", []):
                errors.append(f"synthetic_case_fact_inventory[{index}].{field} is required")


def _validate_missing_fact_rows(rows: Any, errors: list[str]) -> None:
    if not isinstance(rows, list):
        return
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"missing_fact_rows[{index}] must be an object")
            continue
        for field in ("fact_id", "label", "reason", "safe_collection_method"):
            if not row.get(field):
                errors.append(f"missing_fact_rows[{index}].{field} is required")


def _validate_missing_document_rows(rows: Any, errors: list[str]) -> None:
    if not isinstance(rows, list):
        return
    for index, row in enumerate(rows):
        if not isinstance(row, str) or not row.strip():
            errors.append(f"missing_document_labels[{index}] must be a non-empty label")


def _validate_stale_or_conflicting_rows(rows: Any, errors: list[str]) -> None:
    if not isinstance(rows, list):
        return
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"stale_or_conflicting_evidence_rows[{index}] must be an object")
            continue
        for field in ("evidence_id", "issue", "safe_resolution"):
            if not row.get(field):
                errors.append(f"stale_or_conflicting_evidence_rows[{index}].{field} is required")


def _validate_blocked_actions(rows: Any, errors: list[str]) -> None:
    if not isinstance(rows, list):
        return
    blocked = {row.get("action"): row for row in rows if isinstance(row, dict)}
    for action in PROHIBITED_ACTIONS:
        row = blocked.get(action)
        if not row:
            errors.append(f"blocked action row missing: {action}")
            continue
        if row.get("status") != "blocked" or not row.get("reason"):
            errors.append(f"blocked action row for {action} must include blocked status and reason")


def _validate_next_safe_actions(rows: Any, errors: list[str]) -> None:
    if not isinstance(rows, list):
        return
    allowed = set(SAFE_REVERSIBLE_ACTIONS)
    for index, action in enumerate(rows):
        if action not in allowed:
            errors.append(f"next_safe_reversible_actions[{index}] is not an allowed reversible fixture action")
    for action in SAFE_REVERSIBLE_ACTIONS:
        if action not in rows:
            errors.append(f"reversible next-safe-action row missing: {action}")


def _validate_citation_payloads(rows: Any, errors: list[str]) -> None:
    if not isinstance(rows, list):
        return
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"citation_payloads[{index}] must be an object")
            continue
        for field in ("citation_id", "source", "label"):
            if not row.get(field):
                errors.append(f"citation_payloads[{index}].{field} is required")


def _validate_manual_handoff_notes(rows: Any, errors: list[str]) -> None:
    if not isinstance(rows, list):
        return
    for index, note in enumerate(rows):
        if not isinstance(note, str) or not note.strip():
            errors.append(f"manual_handoff_notes[{index}] must be non-empty text")


def _validate_validation_commands(rows: Any, errors: list[str]) -> None:
    if not isinstance(rows, list):
        return
    if OFFLINE_VALIDATION_COMMANDS[0] not in rows:
        errors.append("validation commands must include ppd daemon self-test")
    if OFFLINE_VALIDATION_COMMANDS[1] not in rows:
        errors.append("validation commands must include user gap analysis packet v6 test command")
    for index, command in enumerate(rows):
        if not isinstance(command, list) or not command or not all(isinstance(part, str) and part for part in command):
            errors.append(f"offline_validation_commands[{index}] must be a non-empty string list")


def _scan_for_forbidden_values(value: Any, errors: list[str], path: str = "packet") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            lowered_key = str(key).lower()
            if lowered_key in PRIVATE_VALUE_KEYS:
                errors.append(f"private document values are not allowed at {child_path}")
            if "active_mutation" in lowered_key or lowered_key == "mutation_flags":
                if child not in (False, None, "", [], {}):
                    errors.append(f"active mutation flags are not allowed at {child_path}")
            _scan_for_forbidden_values(child, errors, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_for_forbidden_values(child, errors, f"{path}[{index}]")
    elif isinstance(value, str):
        for label, pattern in FORBIDDEN_TEXT_PATTERNS.items():
            if pattern.search(value):
                errors.append(f"{label} are not allowed at {path}")
