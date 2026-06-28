"""Validation for inactive PP&D rollback drill packet v6 fixtures.

The validator is intentionally conservative: packet v6 is a dry-run planning
artifact only. It must contain placeholders and review scaffolding, while
rejecting claims that imply live rollback, live crawl execution, official action,
legal certainty, private artifacts, or active mutation behavior.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


REQUIRED_NON_EMPTY_FIELDS = (
    "smoke_replay_plan_references",
    "rollback_decision_rows",
    "held_source_citation_continuity_checks",
    "affected_agent_capability_notes",
    "safe_downgrade_expectations",
    "manual_reviewer_approval_placeholders",
    "recovery_journal_event_templates",
    "validation_commands",
)

PROHIBITED_TEXT_PATTERNS = (
    ("live rollback", "inactive packet must not claim live rollback execution"),
    ("rollback executed", "inactive packet must not claim rollback execution"),
    ("activation complete", "inactive packet must not claim activation completion"),
    ("activated in production", "inactive packet must not claim production activation"),
    ("live crawl", "inactive packet must not claim live crawl execution"),
    ("crawl executed", "inactive packet must not claim crawl execution"),
    ("official action complete", "inactive packet must not claim official-action completion"),
    ("official submission complete", "inactive packet must not claim official submission completion"),
    ("permit guaranteed", "inactive packet must not provide permitting guarantees"),
    ("approval guaranteed", "inactive packet must not provide legal or permitting guarantees"),
    ("legally guaranteed", "inactive packet must not provide legal guarantees"),
    ("mutation_enabled", "inactive packet must not enable mutation flags"),
    ("active_mutation", "inactive packet must not include active mutation flags"),
    ("write_enabled", "inactive packet must not enable write behavior"),
    ("session cookie", "inactive packet must not include private session artifacts"),
    ("auth token", "inactive packet must not include auth artifacts"),
    ("password", "inactive packet must not include authentication secrets"),
    ("private upload", "inactive packet must not include private upload artifacts"),
    ("trace.zip", "inactive packet must not include browser trace artifacts"),
    ("storage_state", "inactive packet must not include browser auth state"),
    ("har", "inactive packet must not include HAR artifacts"),
)

PROHIBITED_KEY_FRAGMENTS = (
    "cookie",
    "password",
    "auth_token",
    "access_token",
    "refresh_token",
    "storage_state",
    "session_state",
    "private_upload",
    "trace_path",
    "har_path",
)


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str


def load_packet(path: str | Path) -> dict[str, Any]:
    packet_path = Path(path)
    with packet_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("rollback drill packet must be a JSON object")
    return data


def validate_inactive_rollback_drill_packet_v6(packet: dict[str, Any]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    if packet.get("packet_version") != 6:
        issues.append(ValidationIssue("packet_version", "packet_version must be 6"))

    if packet.get("packet_state") != "inactive":
        issues.append(ValidationIssue("packet_state", "packet_state must be inactive"))

    for field in REQUIRED_NON_EMPTY_FIELDS:
        value = packet.get(field)
        if not _is_non_empty_sequence(value):
            issues.append(ValidationIssue(field, f"{field} must be a non-empty list"))

    _validate_validation_commands(packet.get("validation_commands"), issues)
    _validate_recovery_templates(packet.get("recovery_journal_event_templates"), issues)
    _validate_decision_rows(packet.get("rollback_decision_rows"), issues)
    _validate_no_active_mutation_flags(packet, issues)
    _validate_no_prohibited_content(packet, issues)

    return issues


def assert_valid_inactive_rollback_drill_packet_v6(packet: dict[str, Any]) -> None:
    issues = validate_inactive_rollback_drill_packet_v6(packet)
    if issues:
        rendered = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ValueError(rendered)


def _is_non_empty_sequence(value: Any) -> bool:
    return isinstance(value, list) and len(value) > 0


def _validate_validation_commands(value: Any, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, list):
        return
    for index, command in enumerate(value):
        path = f"validation_commands[{index}]"
        if not isinstance(command, list) or not command:
            issues.append(ValidationIssue(path, "validation command must be a non-empty argv list"))
            continue
        if not all(isinstance(part, str) and part for part in command):
            issues.append(ValidationIssue(path, "validation command argv entries must be non-empty strings"))


def _validate_recovery_templates(value: Any, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, list):
        return
    for index, template in enumerate(value):
        path = f"recovery_journal_event_templates[{index}]"
        if not isinstance(template, dict):
            issues.append(ValidationIssue(path, "recovery journal event template must be an object"))
            continue
        if template.get("event_type") not in {"manual handoff", "refused action", "post-action hardening review", "completion evidence"}:
            issues.append(ValidationIssue(f"{path}.event_type", "event_type must be a commit-safe journal event type"))
        if template.get("contains_private_artifacts") is not False:
            issues.append(ValidationIssue(f"{path}.contains_private_artifacts", "template must explicitly exclude private artifacts"))


def _validate_decision_rows(value: Any, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, list):
        return
    required = {"condition", "decision", "reviewer_placeholder", "citation_ref"}
    for index, row in enumerate(value):
        path = f"rollback_decision_rows[{index}]"
        if not isinstance(row, dict):
            issues.append(ValidationIssue(path, "rollback decision row must be an object"))
            continue
        missing = sorted(required.difference(row))
        if missing:
            issues.append(ValidationIssue(path, "rollback decision row is missing: " + ", ".join(missing)))


def _validate_no_active_mutation_flags(packet: dict[str, Any], issues: list[ValidationIssue]) -> None:
    for path, value in _walk(packet):
        leaf = path.rsplit(".", 1)[-1].lower()
        if leaf in {"active", "enabled", "mutation_enabled", "write_enabled"} and value is True:
            issues.append(ValidationIssue(path, "inactive rollback packet must not contain true active mutation flags"))


def _validate_no_prohibited_content(packet: dict[str, Any], issues: list[ValidationIssue]) -> None:
    for path, value in _walk(packet):
        key = path.rsplit(".", 1)[-1].lower()
        if any(fragment in key for fragment in PROHIBITED_KEY_FRAGMENTS):
            issues.append(ValidationIssue(path, "inactive rollback packet must not contain private/session/auth artifact keys"))
        if isinstance(value, str):
            lowered = value.lower()
            for pattern, message in PROHIBITED_TEXT_PATTERNS:
                if pattern in lowered:
                    issues.append(ValidationIssue(path, message))


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield from _walk(child, child_path)
