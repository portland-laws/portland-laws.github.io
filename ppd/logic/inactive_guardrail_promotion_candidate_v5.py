"""Validation for inactive guardrail promotion candidate v5 records.

The v5 inactive candidate is a staging artifact only. It must prove that
promotion readiness has been replayed and reviewed while still refusing any
claim that activation, official action, private session capture, or mutation is
complete.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


_REQUIRED_NONEMPTY_SEQUENCES = {
    "readiness_replay_refs": "missing_readiness_replay_references",
    "inactive_promotion_rows": "missing_inactive_promotion_rows",
    "activation_prerequisites": "missing_activation_prerequisites",
    "unresolved_hold_inventory": "missing_unresolved_hold_inventory",
    "reviewer_signoff_placeholders": "missing_reviewer_signoff_placeholders",
    "source_freshness_clearance_criteria": "missing_source_freshness_clearance_criteria",
    "rollback_checkpoint_rows": "missing_rollback_checkpoint_rows",
    "post_promotion_smoke_checks": "missing_post_promotion_smoke_checks",
    "agent_notification_notes": "missing_agent_notification_notes",
    "validation_commands": "missing_validation_commands",
}

_ACTIVE_STATUS_VALUES = {"active", "activated", "promoted", "enabled", "live"}
_PRIVATE_ARTIFACT_KEYS = {
    "auth_state",
    "browser_trace",
    "cookies",
    "credentials",
    "devhub_session",
    "har_path",
    "local_private_file_path",
    "mfa_secret",
    "password",
    "payment_details",
    "playwright_storage_state",
    "private_artifacts",
    "raw_authenticated_capture",
    "session_artifacts",
    "session_state",
    "screenshot_path",
    "trace_path",
}
_OFFICIAL_COMPLETION_KEYS = {
    "certification_complete",
    "fee_payment_complete",
    "inspection_scheduled",
    "official_action_complete",
    "official_submission_complete",
    "permit_issued",
    "plans_uploaded_to_official_record",
    "submitted",
}
_MUTATION_FLAG_KEYS = {
    "active_mutation_flags",
    "allow_mutation",
    "can_mutate_active_guardrails",
    "mutation_enabled",
    "writes_enabled",
}


@dataclass(frozen=True)
class ValidationIssue:
    """A deterministic validation issue for an inactive candidate."""

    code: str
    path: str
    message: str


def validate_inactive_guardrail_promotion_candidate_v5(
    candidate: Mapping[str, Any],
) -> list[ValidationIssue]:
    """Return all reasons an inactive promotion candidate v5 must be rejected."""

    issues: list[ValidationIssue] = []

    version = candidate.get("candidate_version", candidate.get("version"))
    if version != 5 and version != "5" and version != "v5":
        issues.append(
            ValidationIssue(
                "wrong_candidate_version",
                "candidate_version",
                "inactive guardrail promotion validation only accepts candidate version v5",
            )
        )

    state = _normalized_text(candidate.get("candidate_state", candidate.get("status")))
    if state != "inactive":
        issues.append(
            ValidationIssue(
                "missing_inactive_candidate_state",
                "candidate_state",
                "candidate must explicitly remain inactive",
            )
        )

    for field, code in _REQUIRED_NONEMPTY_SEQUENCES.items():
        value = candidate.get(field)
        if not _nonempty_sequence(value):
            issues.append(
                ValidationIssue(
                    code,
                    field,
                    f"{field} must be present as a non-empty list",
                )
            )

    _validate_inactive_promotion_rows(candidate.get("inactive_promotion_rows"), issues)
    _validate_reviewer_placeholders(candidate.get("reviewer_signoff_placeholders"), issues)
    _validate_clearance_criteria(candidate.get("source_freshness_clearance_criteria"), issues)
    _validate_validation_commands(candidate.get("validation_commands"), issues)
    _validate_activation_claims(candidate, issues)
    _validate_forbidden_artifacts(candidate, issues)
    _validate_official_completion_claims(candidate, issues)
    _validate_mutation_flags(candidate, issues)

    return issues


def assert_valid_inactive_guardrail_promotion_candidate_v5(
    candidate: Mapping[str, Any],
) -> None:
    """Raise ValueError with stable issue codes when the candidate is invalid."""

    issues = validate_inactive_guardrail_promotion_candidate_v5(candidate)
    if issues:
        codes = ", ".join(issue.code for issue in issues)
        raise ValueError(f"inactive guardrail promotion candidate v5 rejected: {codes}")


def _validate_inactive_promotion_rows(value: Any, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            issues.append(
                ValidationIssue(
                    "invalid_inactive_promotion_row",
                    f"inactive_promotion_rows[{index}]",
                    "inactive promotion rows must be objects",
                )
            )
            continue
        row_state = _normalized_text(row.get("state", row.get("status")))
        if row_state != "inactive":
            issues.append(
                ValidationIssue(
                    "active_activation_claim",
                    f"inactive_promotion_rows[{index}].state",
                    "inactive promotion rows may not claim active promotion state",
                )
            )


def _validate_reviewer_placeholders(value: Any, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return
    for index, placeholder in enumerate(value):
        if not isinstance(placeholder, Mapping):
            issues.append(
                ValidationIssue(
                    "invalid_reviewer_signoff_placeholder",
                    f"reviewer_signoff_placeholders[{index}]",
                    "reviewer signoff placeholders must be objects",
                )
            )
            continue
        if _truthy(placeholder.get("signed")) or _truthy(placeholder.get("approved")):
            issues.append(
                ValidationIssue(
                    "official_action_completion_claim",
                    f"reviewer_signoff_placeholders[{index}]",
                    "inactive candidates may include placeholders, not completed reviewer signoffs",
                )
            )
        if placeholder.get("signed_at") or placeholder.get("approved_by"):
            issues.append(
                ValidationIssue(
                    "official_action_completion_claim",
                    f"reviewer_signoff_placeholders[{index}]",
                    "inactive candidates may not claim completed reviewer approval metadata",
                )
            )


def _validate_clearance_criteria(value: Any, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return
    for index, criterion in enumerate(value):
        if not isinstance(criterion, Mapping):
            issues.append(
                ValidationIssue(
                    "invalid_source_freshness_clearance_criterion",
                    f"source_freshness_clearance_criteria[{index}]",
                    "source freshness clearance criteria must be objects",
                )
            )
            continue
        if _truthy(criterion.get("cleared")) or _truthy(criterion.get("complete")):
            issues.append(
                ValidationIssue(
                    "official_action_completion_claim",
                    f"source_freshness_clearance_criteria[{index}]",
                    "inactive candidates must describe clearance criteria without claiming final clearance",
                )
            )


def _validate_validation_commands(value: Any, issues: list[ValidationIssue]) -> None:
    if not _nonempty_sequence(value):
        return
    for index, command in enumerate(value):
        if isinstance(command, str):
            if not command.strip():
                issues.append(
                    ValidationIssue(
                        "invalid_validation_command",
                        f"validation_commands[{index}]",
                        "validation command strings must be non-empty",
                    )
                )
            continue
        if isinstance(command, Sequence) and not isinstance(command, (bytes, bytearray)):
            if not command or not all(isinstance(part, str) and part for part in command):
                issues.append(
                    ValidationIssue(
                        "invalid_validation_command",
                        f"validation_commands[{index}]",
                        "validation command arrays must contain non-empty string parts",
                    )
                )
            continue
        issues.append(
            ValidationIssue(
                "invalid_validation_command",
                f"validation_commands[{index}]",
                "validation commands must be strings or argv arrays",
            )
        )


def _validate_activation_claims(candidate: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    for key in ("activation_state", "promotion_state", "runtime_state"):
        value = _normalized_text(candidate.get(key))
        if value in _ACTIVE_STATUS_VALUES:
            issues.append(
                ValidationIssue(
                    "active_activation_claim",
                    key,
                    "inactive promotion candidates may not claim active activation",
                )
            )
    if _truthy(candidate.get("activated")) or _truthy(candidate.get("active")):
        issues.append(
            ValidationIssue(
                "active_activation_claim",
                "active",
                "inactive promotion candidates may not set active activation booleans",
            )
        )


def _validate_forbidden_artifacts(candidate: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    for path, value in _walk(candidate):
        leaf = path.rsplit(".", 1)[-1]
        if leaf in _PRIVATE_ARTIFACT_KEYS and _present(value):
            issues.append(
                ValidationIssue(
                    "private_session_auth_artifact",
                    path,
                    "candidate must not contain private, session, auth, trace, payment, or raw authenticated artifacts",
                )
            )


def _validate_official_completion_claims(
    candidate: Mapping[str, Any], issues: list[ValidationIssue]
) -> None:
    for path, value in _walk(candidate):
        leaf = path.rsplit(".", 1)[-1]
        if leaf in _OFFICIAL_COMPLETION_KEYS and _truthy(value):
            issues.append(
                ValidationIssue(
                    "official_action_completion_claim",
                    path,
                    "candidate must not claim official action completion",
                )
            )
        if leaf in {"legal_guarantee", "permitting_guarantee"} and _present(value):
            issues.append(
                ValidationIssue(
                    "legal_or_permitting_guarantee",
                    path,
                    "candidate must not contain legal or permitting guarantees",
                )
            )


def _validate_mutation_flags(candidate: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    for path, value in _walk(candidate):
        leaf = path.rsplit(".", 1)[-1]
        if leaf in _MUTATION_FLAG_KEYS and _truthy(value):
            issues.append(
                ValidationIssue(
                    "active_mutation_flag",
                    path,
                    "inactive candidates may not enable active mutation flags",
                )
            )


def _walk(value: Any, prefix: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path, child
            yield from _walk(child, path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            path = f"{prefix}[{index}]"
            yield path, child
            yield from _walk(child, path)


def _nonempty_sequence(value: Any) -> bool:
    return bool(value) and isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    )


def _normalized_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return bool(value)
    if isinstance(value, Mapping):
        return bool(value)
    return True


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "active", "enabled", "complete", "completed"}
    return bool(value)
