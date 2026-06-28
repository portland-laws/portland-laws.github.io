"""Fixture-first DevHub read-only observation intake schema v3.

This module intentionally consumes only synthetic attended authorization checklist
rows and emits redacted read-only observation placeholders. It does not open
DevHub, authenticate, crawl, fill forms, upload files, submit, pay, schedule, or
perform official actions.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCHEMA_VERSION = "devhub-readonly-observation-intake-v3"

OFFLINE_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "-m", "py_compile", "ppd/devhub_observation_intake_v3.py"),
    ("python3", "-m", "pytest", "ppd/tests/test_devhub_observation_intake_v3.py"),
)

REQUIRED_CHECKLIST_FIELDS = (
    "checklist_id",
    "synthetic",
    "attended_authorization",
    "page_title_hint",
    "visible_heading_hint",
    "url_pattern_hint",
    "accessible_landmark_hints",
    "read_only_action_label_hints",
    "validation_message_hints",
    "upload_control_label_hints",
    "state_transition_hints",
    "selector_confidence_note_hints",
    "source_evidence_hints",
    "reviewer_hold_hints",
)

FORBIDDEN_CHECKLIST_FIELDS = (
    "auth_state",
    "session_cookie",
    "session_storage",
    "local_storage",
    "screenshot",
    "trace",
    "har",
    "private_value",
    "raw_crawl_output",
    "downloaded_document",
    "form_fill",
    "upload_attempt",
    "submission_attempt",
    "payment_attempt",
    "scheduling_attempt",
    "official_action_attempt",
)

OBSERVATION_FIELDS = (
    "schema_version",
    "checklist_id",
    "page_title_placeholder",
    "visible_heading_placeholder",
    "url_pattern_placeholder",
    "accessible_landmark_placeholders",
    "read_only_action_label_placeholders",
    "validation_message_placeholders",
    "upload_control_label_placeholders",
    "upload_control_evidence_note",
    "state_transition_placeholders",
    "selector_confidence_notes",
    "source_evidence_placeholders",
    "reviewer_holds",
    "offline_validation_commands",
)


@dataclass(frozen=True)
class IntakeError(ValueError):
    """Raised when synthetic checklist rows violate the v3 intake contract."""

    message: str

    def __str__(self) -> str:
        return self.message


def build_observation_rows(checklist_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert synthetic attended checklist rows into redacted observation placeholders."""

    observations: list[dict[str, Any]] = []
    for index, row in enumerate(checklist_rows):
        _validate_checklist_row(row, index)
        observations.append(
            {
                "schema_version": SCHEMA_VERSION,
                "checklist_id": _text(row["checklist_id"]),
                "page_title_placeholder": _placeholder("page title", row["page_title_hint"]),
                "visible_heading_placeholder": _placeholder("visible heading", row["visible_heading_hint"]),
                "url_pattern_placeholder": _placeholder("URL pattern", row["url_pattern_hint"]),
                "accessible_landmark_placeholders": _placeholder_list("accessible landmark", row["accessible_landmark_hints"]),
                "read_only_action_label_placeholders": _placeholder_list("read-only action label", row["read_only_action_label_hints"]),
                "validation_message_placeholders": _placeholder_list("validation message", row["validation_message_hints"]),
                "upload_control_label_placeholders": _placeholder_list("upload-control label", row["upload_control_label_hints"]),
                "upload_control_evidence_note": "Upload controls are recorded only as non-action evidence placeholders; no upload is attempted.",
                "state_transition_placeholders": _placeholder_list("state transition", row["state_transition_hints"]),
                "selector_confidence_notes": _placeholder_list("selector confidence note", row["selector_confidence_note_hints"]),
                "source_evidence_placeholders": _placeholder_list("source evidence", row["source_evidence_hints"]),
                "reviewer_holds": _placeholder_list("reviewer hold", row["reviewer_hold_hints"]),
                "offline_validation_commands": [list(command) for command in OFFLINE_VALIDATION_COMMANDS],
            }
        )
    return observations


def validate_observation_rows(observation_rows: list[dict[str, Any]]) -> None:
    """Validate emitted observation rows without requiring live DevHub access."""

    for index, row in enumerate(observation_rows):
        if set(row) != set(OBSERVATION_FIELDS):
            missing = sorted(set(OBSERVATION_FIELDS) - set(row))
            extra = sorted(set(row) - set(OBSERVATION_FIELDS))
            raise IntakeError(f"observation row {index} field mismatch: missing={missing} extra={extra}")
        if row["schema_version"] != SCHEMA_VERSION:
            raise IntakeError(f"observation row {index} has unsupported schema_version")
        for field, value in row.items():
            if field == "offline_validation_commands":
                _validate_commands(value, index)
            elif isinstance(value, list):
                for item in value:
                    _reject_private_or_live_values(str(item), index, field)
            else:
                _reject_private_or_live_values(str(value), index, field)


def _validate_checklist_row(row: dict[str, Any], index: int) -> None:
    missing = [field for field in REQUIRED_CHECKLIST_FIELDS if field not in row]
    if missing:
        raise IntakeError(f"checklist row {index} missing required fields: {missing}")
    present_forbidden = [field for field in FORBIDDEN_CHECKLIST_FIELDS if field in row]
    if present_forbidden:
        raise IntakeError(f"checklist row {index} includes forbidden fields: {present_forbidden}")
    if row["synthetic"] is not True:
        raise IntakeError(f"checklist row {index} must be synthetic")
    if row["attended_authorization"] is not True:
        raise IntakeError(f"checklist row {index} must document attended authorization")
    for field in REQUIRED_CHECKLIST_FIELDS:
        value = row[field]
        if isinstance(value, list):
            if not value:
                raise IntakeError(f"checklist row {index} field {field} must not be empty")
            for item in value:
                _reject_private_or_live_values(str(item), index, field)
        else:
            _reject_private_or_live_values(str(value), index, field)


def _validate_commands(value: Any, index: int) -> None:
    if value != [list(command) for command in OFFLINE_VALIDATION_COMMANDS]:
        raise IntakeError(f"observation row {index} must use exact offline validation commands")


def _placeholder(label: str, value: Any) -> str:
    return f"REDACTED {label} placeholder derived from synthetic attended checklist hint: {_text(value)}"


def _placeholder_list(label: str, values: Any) -> list[str]:
    if not isinstance(values, list):
        raise IntakeError(f"{label} hints must be a list")
    return [_placeholder(label, value) for value in values]


def _text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise IntakeError("synthetic checklist values must be non-empty strings")
    return value.strip()


def _reject_private_or_live_values(value: str, index: int, field: str) -> None:
    lowered = value.lower()
    blocked_fragments = (
        "cookie",
        "bearer ",
        "password",
        "secret",
        "token",
        "session",
        "screenshot",
        "trace",
        "har",
        "captcha",
        "mfa",
        "payment",
        "submit now",
        "upload file",
    )
    if any(fragment in lowered for fragment in blocked_fragments):
        raise IntakeError(f"row {index} field {field} appears to contain private or live-action material")
