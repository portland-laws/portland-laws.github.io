"""Commit-safe validation for PP&D action journal fixtures.

The action journal is allowed to preserve workflow evidence, but it must not
preserve secrets, browser artifacts, payment details, private page values, or
local private paths.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any


ALLOWED_EVENT_TYPES = {
    "local_pdf_preview",
    "reversible_draft_plan",
    "refused_action",
    "exact_confirmation_checkpoint",
}

_REQUIRED_EVENT_FIELDS = {
    "event_id",
    "event_type",
    "occurred_at",
    "actor",
    "summary",
    "action",
    "redaction_policy",
    "payload",
}

_PROHIBITED_KEY_TERMS = {
    "absolute_path",
    "account_number",
    "auth",
    "auth_state",
    "bank",
    "card",
    "card_number",
    "cookie",
    "credential",
    "cvv",
    "har",
    "local_path",
    "password",
    "payment",
    "private_path",
    "private_value",
    "routing",
    "screenshot",
    "secret",
    "session",
    "ssn",
    "storage_state",
    "trace",
    "token",
}

_VALUE_PATTERNS = {
    "cookie": re.compile(r"\b(set-cookie|cookie|sessionid|xsrf|csrf)\s*[:=]", re.IGNORECASE),
    "auth_state": re.compile(r"\b(storageState|authState|bearer\s+[A-Za-z0-9._~-]+)", re.IGNORECASE),
    "browser_artifact": re.compile(r"\.(png|jpe?g|webp|zip|trace|har)\b", re.IGNORECASE),
    "local_private_path": re.compile(r"(file://|/home/[^\s]+|/Users/[^\s]+|[A-Za-z]:\\\\[^\s]+)"),
    "payment_detail": re.compile(r"\b(?:\d[ -]*?){13,19}\b|\b(cvv|card number|routing number|account number)\b", re.IGNORECASE),
    "private_value": re.compile(r"\b(ssn|social security|date of birth|dob|private value|driver license)\b", re.IGNORECASE),
}


@dataclass(frozen=True)
class RedactionIssue:
    """A single commit-safety validation issue."""

    path: str
    reason: str


def validate_action_journal_event(event: dict[str, Any]) -> list[RedactionIssue]:
    """Return redaction issues for one action-journal event."""

    issues: list[RedactionIssue] = []
    missing_fields = sorted(_REQUIRED_EVENT_FIELDS.difference(event))
    for field in missing_fields:
        issues.append(RedactionIssue(field, "missing required action-journal field"))

    event_type = event.get("event_type")
    if event_type not in ALLOWED_EVENT_TYPES:
        issues.append(RedactionIssue("event_type", "unsupported commit-safe event type"))

    issues.extend(_walk_for_sensitive_material(event, "$"))
    return issues


def assert_commit_safe_action_journal(events: list[dict[str, Any]]) -> None:
    """Raise AssertionError if any event is unsafe for committed fixtures."""

    all_issues: list[str] = []
    for index, event in enumerate(events):
        for issue in validate_action_journal_event(event):
            all_issues.append(f"events[{index}].{issue.path}: {issue.reason}")
    if all_issues:
        raise AssertionError("unsafe action journal fixture:\n" + "\n".join(all_issues))


def validate_redaction_fixture(fixture: dict[str, Any]) -> None:
    """Validate the deterministic redaction fixture contract used by tests."""

    safe_events = fixture.get("commit_safe_events")
    rejected_events = fixture.get("rejected_events")
    if not isinstance(safe_events, list):
        raise AssertionError("fixture.commit_safe_events must be a list")
    if not isinstance(rejected_events, list):
        raise AssertionError("fixture.rejected_events must be a list")

    assert_commit_safe_action_journal(safe_events)

    rejection_reasons: set[str] = set()
    for rejected in rejected_events:
        if not isinstance(rejected, dict):
            raise AssertionError("fixture.rejected_events entries must be objects")
        reason = rejected.get("expected_rejection")
        event = rejected.get("event")
        if not isinstance(reason, str) or not reason:
            raise AssertionError("rejected event is missing expected_rejection")
        if not isinstance(event, dict):
            raise AssertionError("rejected event is missing event object")
        issues = validate_action_journal_event(event)
        if not issues:
            raise AssertionError(f"rejected fixture event was accepted: {reason}")
        rejection_reasons.add(reason)

    required_reasons = {
        "credentials",
        "cookies",
        "auth_state",
        "screenshots",
        "traces",
        "har_data",
        "private_values",
        "payment_details",
        "local_private_paths",
    }
    missing_reasons = sorted(required_reasons.difference(rejection_reasons))
    if missing_reasons:
        raise AssertionError("fixture is missing rejection coverage: " + ", ".join(missing_reasons))


def _walk_for_sensitive_material(value: Any, path: str) -> list[RedactionIssue]:
    issues: list[RedactionIssue] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            normalized_key = key_text.lower().replace("-", "_")
            if _key_is_prohibited(normalized_key):
                issues.append(RedactionIssue(child_path, "prohibited sensitive journal key"))
            issues.extend(_walk_for_sensitive_material(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_walk_for_sensitive_material(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        for reason, pattern in _VALUE_PATTERNS.items():
            if pattern.search(value):
                issues.append(RedactionIssue(path, f"prohibited sensitive journal value: {reason}"))
    return issues


def _key_is_prohibited(normalized_key: str) -> bool:
    parts = set(normalized_key.split("_"))
    return normalized_key in _PROHIBITED_KEY_TERMS or bool(parts.intersection(_PROHIBITED_KEY_TERMS))
