"""Fixture-first DevHub read-only observation authorization checklist v1.

This module builds a deterministic checklist from synthetic next-observation
seed rows and official DevHub guidance placeholders. It is offline-only and
must not open DevHub, sign in, create browser artifacts, store private values,
perform form fills, upload, submit, pay, schedule, or take other official
actions.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ppd.agent_readiness.devhub_fixture_first_read_only_observation_seed_packet_v1 import (
    assert_valid_devhub_fixture_first_read_only_observation_seed_packet_v1,
)

CHECKLIST_VERSION = "attended_devhub_read_only_observation_authorization_checklist_v1"

_REQUIRED_SECTIONS = (
    "per_target_attendance_prerequisites",
    "account_scope_reminders",
    "read_only_route_expectations",
    "manual_login_handoff_notes",
    "prohibited_capture_artifact_reminders",
    "redaction_acceptance_prerequisites",
    "reviewer_routing",
    "rollback_notes",
    "offline_validation_commands",
)

_ARTIFACT_POLICY_KEYS = (
    "opens_devhub",
    "logs_in",
    "stores_auth_artifacts",
    "stores_session_artifacts",
    "stores_screenshots",
    "stores_traces",
    "stores_har_files",
    "stores_private_values",
    "stores_raw_crawl_output",
    "stores_downloaded_documents",
    "performs_form_fills",
    "performs_uploads",
    "performs_submissions",
    "performs_payments",
    "performs_scheduling",
    "performs_other_official_actions",
)

_ALLOWED_OFFLINE_VALIDATION_COMMANDS = (
    (
        "python3",
        "-m",
        "py_compile",
        "ppd/authorization/devhub_read_only_observation_authorization_checklist_v1.py",
        "ppd/tests/test_devhub_read_only_observation_authorization_checklist_v1.py",
    ),
    (
        "python3",
        "-m",
        "unittest",
        "ppd.tests.test_devhub_read_only_observation_authorization_checklist_v1",
    ),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

_FORBIDDEN_TEXT_TERMS = (
    "storage_state",
    "auth_state",
    "cookie",
    "session token",
    "password",
    "credential value",
    "screenshot.png",
    "trace.zip",
    ".har",
    "private value:",
    "form value:",
)

_ALLOWED_FORBIDDEN_CONTEXTS = (
    ".manual_login_handoff_notes[",
    ".prohibited_capture_artifact_reminders[",
    ".artifact_policy.",
)


@dataclass(frozen=True)
class ChecklistIssue:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "path": self.path, "message": self.message}


def load_json_packet(path: str | Path) -> dict[str, Any]:
    packet_path = Path(path)
    with packet_path.open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise ValueError(f"packet must be a JSON object: {packet_path}")
    return packet


def build_authorization_checklist_v1(seed_packet: Mapping[str, Any]) -> dict[str, Any]:
    """Build an offline-only authorization checklist from a valid seed packet."""

    assert_valid_devhub_fixture_first_read_only_observation_seed_packet_v1(seed_packet)
    targets = list(seed_packet.get("observation_targets", ()))
    input_rows = _index_by_id(seed_packet.get("input_rows"), "row_id")
    guidance = _index_by_id(seed_packet.get("official_guidance_placeholders"), "placeholder_id")
    prerequisites = _index_by_id(seed_packet.get("authorization_prerequisites"), "prerequisite_id")
    redactions = _index_by_id(seed_packet.get("redaction_expectations"), "redaction_id")
    routes = _index_by_id(seed_packet.get("reviewer_routing"), "route_id")

    checklist = {
        "checklist_version": CHECKLIST_VERSION,
        "checklist_id": "attended-devhub-read-only-observation-authorization-checklist-v1",
        "source_seed_packet_version": str(seed_packet.get("packet_version")),
        "mode": "fixture_first_offline_authorization_checklist",
        "fixture_first": True,
        "devhub_access_performed": False,
        "artifact_policy": {key: False for key in _ARTIFACT_POLICY_KEYS},
        "per_target_attendance_prerequisites": _target_prerequisites(targets, input_rows, guidance, prerequisites),
        "account_scope_reminders": _account_scope_reminders(targets, input_rows, guidance),
        "read_only_route_expectations": _route_expectations(targets, input_rows, guidance),
        "manual_login_handoff_notes": _manual_handoff_notes(),
        "prohibited_capture_artifact_reminders": _prohibited_capture_reminders(),
        "redaction_acceptance_prerequisites": _redaction_prerequisites(targets, redactions),
        "reviewer_routing": _reviewer_routing(targets, routes),
        "rollback_notes": _rollback_notes(seed_packet),
        "offline_validation_commands": [list(command) for command in _ALLOWED_OFFLINE_VALIDATION_COMMANDS],
    }
    assert_valid_authorization_checklist_v1(checklist)
    return checklist


def validate_authorization_checklist_v1(packet: Mapping[str, Any]) -> list[ChecklistIssue]:
    issues: list[ChecklistIssue] = []
    if not isinstance(packet, Mapping):
        return [ChecklistIssue("invalid_packet", "$", "checklist must be an object")]

    if packet.get("checklist_version") != CHECKLIST_VERSION:
        _add(issues, "invalid_version", "checklist_version", f"checklist_version must be {CHECKLIST_VERSION}")
    if packet.get("fixture_first") is not True:
        _add(issues, "not_fixture_first", "fixture_first", "checklist must be fixture_first")
    if packet.get("devhub_access_performed") is not False:
        _add(issues, "devhub_access_not_allowed", "devhub_access_performed", "checklist must not perform DevHub access")

    for section in _REQUIRED_SECTIONS:
        if not _non_empty_sequence(packet.get(section)):
            _add(issues, "missing_required_section", section, f"{section} must be a non-empty list")

    artifact_policy = packet.get("artifact_policy")
    if not isinstance(artifact_policy, Mapping):
        _add(issues, "missing_artifact_policy", "artifact_policy", "artifact_policy must be an object")
    else:
        for key in _ARTIFACT_POLICY_KEYS:
            if artifact_policy.get(key) is not False:
                _add(issues, "unsafe_artifact_policy", f"artifact_policy.{key}", f"artifact_policy.{key} must be false")

    _validate_per_target_rows(packet.get("per_target_attendance_prerequisites"), issues)
    _validate_validation_commands(packet.get("offline_validation_commands"), issues)
    _scan_for_forbidden_text(packet, issues)
    return _dedupe(issues)


def assert_valid_authorization_checklist_v1(packet: Mapping[str, Any]) -> None:
    issues = validate_authorization_checklist_v1(packet)
    if issues:
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise AssertionError("invalid DevHub read-only observation authorization checklist v1: " + details)


def _target_prerequisites(
    targets: Sequence[Any],
    input_rows: Mapping[str, Mapping[str, Any]],
    guidance: Mapping[str, Mapping[str, Any]],
    prerequisites: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    rows = []
    for target in targets:
        if not isinstance(target, Mapping):
            continue
        basis_rows = [input_rows[row_id] for row_id in target.get("basis_row_ids", ()) if row_id in input_rows]
        guidance_rows = [guidance[item_id] for item_id in target.get("guidance_placeholder_ids", ()) if item_id in guidance]
        prerequisite_rows = [prerequisites[item_id] for item_id in target.get("authorization_prerequisite_ids", ()) if item_id in prerequisites]
        rows.append(
            {
                "target_id": str(target.get("target_id")),
                "surface_label": str(target.get("surface_label", target.get("target_id"))),
                "attendance_required": True,
                "operator_presence_required_before_observation": True,
                "manual_control_required_for_auth_prompts": True,
                "basis_row_ids": [str(row.get("row_id")) for row in basis_rows],
                "guidance_placeholder_ids": [str(row.get("placeholder_id")) for row in guidance_rows],
                "prerequisite_ids": [str(row.get("prerequisite_id")) for row in prerequisite_rows],
                "prerequisite_notes": [str(row.get("note", row.get("description", "manual attendance required"))) for row in prerequisite_rows],
                "allowed_observation_result": "redacted metadata-only read-only observation notes for reviewer intake",
            }
        )
    return rows


def _account_scope_reminders(
    targets: Sequence[Any],
    input_rows: Mapping[str, Mapping[str, Any]],
    guidance: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    reminders = []
    for target in targets:
        if not isinstance(target, Mapping):
            continue
        row_ids = [row_id for row_id in target.get("basis_row_ids", ()) if row_id in input_rows]
        guidance_ids = [item_id for item_id in target.get("guidance_placeholder_ids", ()) if item_id in guidance]
        reminders.append(
            {
                "target_id": str(target.get("target_id")),
                "basis_row_ids": row_ids,
                "guidance_placeholder_ids": guidance_ids,
                "reminder": "Treat all observed account-scoped permit, fee, correction, contact, address, license, document, and status details as private and replace them with placeholders.",
                "private_values_allowed_in_checklist": False,
            }
        )
    return reminders


def _route_expectations(
    targets: Sequence[Any],
    input_rows: Mapping[str, Mapping[str, Any]],
    guidance: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    expectations = []
    for target in targets:
        if not isinstance(target, Mapping):
            continue
        rows = [input_rows[row_id] for row_id in target.get("basis_row_ids", ()) if row_id in input_rows]
        guidance_ids = [item_id for item_id in target.get("guidance_placeholder_ids", ()) if item_id in guidance]
        expectations.append(
            {
                "target_id": str(target.get("target_id")),
                "expected_route_label": str(target.get("route_label", target.get("surface_label", target.get("target_id")))),
                "basis_row_ids": [str(row.get("row_id")) for row in rows],
                "guidance_placeholder_ids": guidance_ids,
                "expected_read_only_elements": sorted({str(item) for row in rows for item in row.get("expected_read_only_elements", ())}),
                "blocked_controls": sorted({str(item) for row in rows for item in row.get("blocked_controls", ())}),
                "route_must_remain_read_only": True,
            }
        )
    return expectations


def _manual_handoff_notes() -> list[dict[str, Any]]:
    return [
        {
            "handoff_id": "manual-login-mfa-captcha-handoff",
            "operator_only": True,
            "note": "Manual login, MFA, CAPTCHA, account recovery, and security prompts stay under the attended operator's direct control and produce no stored values.",
        },
        {
            "handoff_id": "private-value-visibility-stop",
            "operator_only": True,
            "note": "If private account values are visible, continue only when they can be represented as placeholders in metadata-only notes.",
        },
        {
            "handoff_id": "official-action-stop",
            "operator_only": True,
            "note": "Stop before any form fill, upload, submission, payment, scheduling, certification, cancellation, or other official action control.",
        },
    ]


def _prohibited_capture_reminders() -> list[dict[str, Any]]:
    return [
        {"reminder_id": "no-auth-or-session-artifacts", "required": True, "note": "Do not create or store auth state, session state, cookies, tokens, profiles, or credential material."},
        {"reminder_id": "no-browser-capture-artifacts", "required": True, "note": "Do not create or store screenshots, traces, HAR files, video, raw page bodies, or downloaded documents."},
        {"reminder_id": "no-private-values", "required": True, "note": "Do not record account, address, contact, permit, invoice, license, fee, document, or field values."},
    ]


def _redaction_prerequisites(targets: Sequence[Any], redactions: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for target in targets:
        if not isinstance(target, Mapping):
            continue
        expectation_ids = [item_id for item_id in target.get("redaction_expectation_ids", ()) if item_id in redactions]
        rows.append(
            {
                "target_id": str(target.get("target_id")),
                "redaction_expectation_ids": expectation_ids,
                "acceptance_required_before_reviewer_routing": True,
                "acceptance_note": "Reviewer intake may proceed only after every account-scoped value is placeholder-only and no prohibited artifact reference is present.",
            }
        )
    return rows


def _reviewer_routing(targets: Sequence[Any], routes: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for target in targets:
        if not isinstance(target, Mapping):
            continue
        for route_id in target.get("reviewer_route_ids", ()):
            route = routes.get(route_id)
            if route is None:
                continue
            rows.append(
                {
                    "target_id": str(target.get("target_id")),
                    "route_id": str(route.get("route_id")),
                    "reviewer_role": str(route.get("reviewer_role")),
                    "routing_note": str(route.get("note", "review redacted read-only observation checklist")),
                    "requires_redaction_acceptance": True,
                }
            )
    return rows


def _rollback_notes(seed_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for index, note in enumerate(seed_packet.get("rollback_notes", ()), start=1):
        if isinstance(note, Mapping):
            rows.append(
                {
                    "rollback_note_id": str(note.get("rollback_note_id", f"rollback-note-{index}")),
                    "note": str(note.get("note", "discard checklist candidate and rerun offline fixture validation")),
                    "requires_no_live_cleanup": True,
                }
            )
        else:
            rows.append(
                {
                    "rollback_note_id": f"rollback-note-{index}",
                    "note": str(note),
                    "requires_no_live_cleanup": True,
                }
            )
    return rows


def _validate_per_target_rows(value: Any, issues: list[ChecklistIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    for index, row in enumerate(value):
        path = f"per_target_attendance_prerequisites[{index}]"
        if not isinstance(row, Mapping):
            _add(issues, "invalid_target_row", path, "target prerequisite row must be an object")
            continue
        if row.get("attendance_required") is not True:
            _add(issues, "missing_attendance_requirement", f"{path}.attendance_required", "attendance_required must be true")
        if row.get("operator_presence_required_before_observation") is not True:
            _add(issues, "missing_operator_presence", f"{path}.operator_presence_required_before_observation", "operator presence must be required")
        if row.get("manual_control_required_for_auth_prompts") is not True:
            _add(issues, "missing_manual_auth_control", f"{path}.manual_control_required_for_auth_prompts", "manual control must be required for auth prompts")


def _validate_validation_commands(value: Any, issues: list[ChecklistIssue]) -> None:
    if not _non_empty_sequence(value):
        return
    normalized = []
    for index, command in enumerate(value):
        path = f"offline_validation_commands[{index}]"
        if not isinstance(command, Sequence) or isinstance(command, (str, bytes)):
            _add(issues, "invalid_validation_command", path, "validation command must be an argv list")
            continue
        command_tuple = tuple(command)
        normalized.append(command_tuple)
        if command_tuple not in _ALLOWED_OFFLINE_VALIDATION_COMMANDS:
            _add(issues, "unsupported_validation_command", path, "validation command must be one of the exact offline commands")
    if tuple(normalized) != _ALLOWED_OFFLINE_VALIDATION_COMMANDS:
        _add(issues, "incomplete_validation_commands", "offline_validation_commands", "offline_validation_commands must match the exact command set in order")


def _scan_for_forbidden_text(value: Any, issues: list[ChecklistIssue], path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            _scan_for_forbidden_text(nested, issues, f"{path}.{key}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, nested in enumerate(value):
            _scan_for_forbidden_text(nested, issues, f"{path}[{index}]")
        return
    if not isinstance(value, str):
        return
    if any(allowed in path for allowed in _ALLOWED_FORBIDDEN_CONTEXTS):
        return
    text = value.lower()
    for term in _FORBIDDEN_TEXT_TERMS:
        if term in text:
            _add(issues, "forbidden_private_or_artifact_text", path, f"checklist contains prohibited private or artifact term: {term}")


def _index_by_id(value: Any, id_key: str) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return indexed
    for item in value:
        if isinstance(item, Mapping):
            item_id = item.get(id_key)
            if isinstance(item_id, str):
                indexed[item_id] = item
    return indexed


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) > 0


def _add(issues: list[ChecklistIssue], code: str, path: str, message: str) -> None:
    issues.append(ChecklistIssue(code, path, message))


def _dedupe(issues: list[ChecklistIssue]) -> list[ChecklistIssue]:
    seen: set[tuple[str, str, str]] = set()
    deduped: list[ChecklistIssue] = []
    for issue in issues:
        key = (issue.code, issue.path, issue.message)
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    return deduped
