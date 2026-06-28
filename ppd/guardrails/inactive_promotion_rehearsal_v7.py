"""Validation for inactive guardrail promotion rehearsal v7 records.

The rehearsal is an evidence checklist only. It must remain inactive, cite its
release-review dependencies, and avoid claims that imply live promotion, live
crawl execution, official action completion, legal guarantees, private session
artifacts, or enabled mutation behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class RehearsalValidationIssue:
    code: str
    path: str
    message: str


_REQUIRED_LISTS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "release_decision_references",
        ("decision_id", "evidence_ref", "reviewer_role"),
        "release decision references are required before rehearsal can pass",
    ),
    (
        "reviewer_controlled_promotion_checklist_rows",
        ("row_id", "reviewer_role", "check", "manual_status"),
        "reviewer-controlled promotion checklist rows are required",
    ),
    (
        "unresolved_hold_carry_forward_conditions",
        ("condition_id", "source_reference", "carry_forward_reason", "owner_role"),
        "unresolved hold carry-forward conditions must be listed explicitly",
    ),
    (
        "pre_promotion_source_freshness_reminders",
        ("source_id", "reminder", "freshness_reference"),
        "pre-promotion source freshness reminders are required",
    ),
    (
        "agent_notification_placeholders",
        ("placeholder_id", "audience", "message_template"),
        "agent notification placeholders are required",
    ),
    (
        "rollback_checkpoint_references",
        ("checkpoint_id", "rollback_reference", "reviewer_role"),
        "rollback checkpoint references are required",
    ),
    (
        "monitoring_watch_rows",
        ("watch_id", "source_id", "watch_condition", "owner_role"),
        "monitoring watch rows are required",
    ),
    (
        "validation_commands",
        ("command", "purpose"),
        "validation commands are required",
    ),
)

_PRIVATE_ARTIFACT_KEYS = {
    "auth_state",
    "authorization",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "har",
    "local_private_path",
    "password",
    "private_file_path",
    "session",
    "session_state",
    "screenshot",
    "secret",
    "token",
    "trace",
}

_ACTIVE_MUTATION_FLAGS = {
    "active": True,
    "activation_enabled": True,
    "allow_live_mutation": True,
    "live_mutation": True,
    "mutation_enabled": True,
    "promoted": True,
    "promotion_enabled": True,
}

_PROHIBITED_TEXT: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "actual_activation_or_promotion_claim",
        (
            "activated in production",
            "actual activation complete",
            "actual promotion complete",
            "live promotion complete",
            "promoted to production",
            "production activation complete",
        ),
    ),
    (
        "live_crawl_execution_claim",
        (
            "executed live crawl",
            "live crawl completed",
            "live crawl execution complete",
            "performed live crawl",
            "ran the live crawl",
        ),
    ),
    (
        "official_action_completion_claim",
        (
            "certification completed",
            "official action complete",
            "paid fees",
            "scheduled inspection",
            "submitted application",
            "submitted permit",
            "uploaded corrections",
        ),
    ),
    (
        "legal_or_permitting_guarantee",
        (
            "approval guaranteed",
            "guaranteed approval",
            "guaranteed permit",
            "legal advice",
            "permit guaranteed",
        ),
    ),
)


def validate_inactive_guardrail_promotion_rehearsal_v7(payload: dict[str, Any]) -> list[RehearsalValidationIssue]:
    """Return validation issues for an inactive promotion rehearsal v7 record."""

    issues: list[RehearsalValidationIssue] = []

    if payload.get("rehearsal_version") != 7:
        issues.append(
            RehearsalValidationIssue(
                code="missing_rehearsal_version_v7",
                path="rehearsal_version",
                message="inactive guardrail promotion rehearsal records must declare rehearsal_version 7",
            )
        )

    if payload.get("rehearsal_mode") != "inactive":
        issues.append(
            RehearsalValidationIssue(
                code="not_inactive_rehearsal",
                path="rehearsal_mode",
                message="promotion rehearsal v7 must remain inactive",
            )
        )

    for field_name, required_keys, message in _REQUIRED_LISTS:
        value = payload.get(field_name)
        if not isinstance(value, list) or not value:
            issues.append(RehearsalValidationIssue(code=f"missing_{field_name}", path=field_name, message=message))
            continue
        for index, row in enumerate(value):
            row_path = f"{field_name}[{index}]"
            if not isinstance(row, dict):
                issues.append(
                    RehearsalValidationIssue(
                        code=f"invalid_{field_name}_row",
                        path=row_path,
                        message="checklist rows must be objects with reviewer-visible evidence fields",
                    )
                )
                continue
            for required_key in required_keys:
                if _is_blank(row.get(required_key)):
                    issues.append(
                        RehearsalValidationIssue(
                            code=f"missing_{field_name}_{required_key}",
                            path=f"{row_path}.{required_key}",
                            message=f"{field_name} row is missing {required_key}",
                        )
                    )

    for path, value in _walk(payload):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0].lower()
        if key in _PRIVATE_ARTIFACT_KEYS and not _is_blank(value):
            issues.append(
                RehearsalValidationIssue(
                    code="private_session_or_auth_artifact",
                    path=path,
                    message="private, session, auth, trace, screenshot, credential, or token artifacts are not allowed in committed rehearsal records",
                )
            )

        if key in _ACTIVE_MUTATION_FLAGS and value is _ACTIVE_MUTATION_FLAGS[key]:
            issues.append(
                RehearsalValidationIssue(
                    code="active_mutation_flag",
                    path=path,
                    message="inactive promotion rehearsal v7 must not enable activation, promotion, or live mutation flags",
                )
            )

        if isinstance(value, str):
            normalized = " ".join(value.lower().split())
            for code, phrases in _PROHIBITED_TEXT:
                if any(phrase in normalized for phrase in phrases):
                    issues.append(
                        RehearsalValidationIssue(
                            code=code,
                            path=path,
                            message="inactive rehearsal text must not claim live activation, live crawl execution, official-action completion, or legal/permitting guarantees",
                        )
                    )

    return issues


def assert_valid_inactive_guardrail_promotion_rehearsal_v7(payload: dict[str, Any]) -> None:
    issues = validate_inactive_guardrail_promotion_rehearsal_v7(payload)
    if issues:
        formatted = "; ".join(f"{issue.code} at {issue.path}" for issue in issues)
        raise ValueError(formatted)


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
