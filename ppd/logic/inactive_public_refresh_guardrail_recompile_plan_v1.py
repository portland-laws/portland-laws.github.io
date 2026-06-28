"""Validation for inactive public refresh guardrail recompile plans.

This module is intentionally side-effect free. It validates a proposed plan shape for
recompiling inactive public GuardrailBundle candidates after public-source refreshes.
It does not crawl, extract, mutate active bundles, or call DevHub.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


REQUIRED_SEQUENCE_FIELDS: tuple[str, ...] = (
    "process_model_delta_refs",
    "requirement_reextraction_queue_refs",
    "inactive_guardrail_bundle_recompile_candidates",
    "deterministic_predicate_placeholder_changes",
    "reversible_action_predicate_impacts",
    "exact_confirmation_predicate_impacts",
    "refused_action_predicate_impacts",
    "explanation_template_refresh_notes",
    "validation_status_holds",
    "rollback_notes",
    "validation_commands",
)

ACTIVE_MUTATION_FLAGS: tuple[str, ...] = (
    "active_mutation",
    "active_mutation_enabled",
    "allow_active_mutation",
    "mutates_active_guardrails",
    "mutates_active_process_models",
    "mutates_active_requirements",
    "writes_active_guardrails",
    "writes_active_process_models",
    "writes_active_requirements",
)

FORBIDDEN_CLAIM_FIELDS: tuple[str, ...] = (
    "claims",
    "assumptions",
    "notes",
    "scope_notes",
    "completion_notes",
)

FORBIDDEN_CLAIM_PHRASES: tuple[tuple[str, str], ...] = (
    ("private_artifact_claim", "private artifact"),
    ("private_artifact_claim", "private devhub"),
    ("private_artifact_claim", "session file"),
    ("private_artifact_claim", "auth state"),
    ("raw_artifact_claim", "raw crawl output"),
    ("raw_artifact_claim", "raw downloaded"),
    ("raw_artifact_claim", "downloaded artifact"),
    ("downloaded_artifact_claim", "downloaded document"),
    ("live_extraction_claim", "live extraction"),
    ("live_crawl_claim", "live crawl"),
    ("live_crawl_claim", "recrawled live"),
    ("devhub_claim", "devhub"),
    ("active_guardrail_mutation_claim", "active guardrail"),
    ("active_process_model_mutation_claim", "active process-model"),
    ("active_process_model_mutation_claim", "active process model"),
    ("active_requirement_mutation_claim", "active requirement"),
    ("official_action_completion_claim", "official action completed"),
    ("official_action_completion_claim", "submitted successfully"),
    ("official_action_completion_claim", "payment completed"),
    ("official_action_completion_claim", "inspection scheduled"),
    ("official_action_completion_claim", "permit issued"),
    ("legal_or_permitting_guarantee", "guaranteed approval"),
    ("legal_or_permitting_guarantee", "permit guaranteed"),
    ("legal_or_permitting_guarantee", "legal guarantee"),
    ("legal_or_permitting_guarantee", "will be approved"),
)


@dataclass(frozen=True)
class ValidationIssue:
    """One deterministic validation failure."""

    code: str
    message: str
    path: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "path": self.path}


@dataclass(frozen=True)
class ValidationResult:
    """Validation result for an inactive public refresh recompile plan."""

    accepted: bool
    issues: tuple[ValidationIssue, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "accepted": self.accepted,
            "issues": [issue.as_dict() for issue in self.issues],
        }


def validate_inactive_public_refresh_guardrail_recompile_plan_v1(
    plan: Mapping[str, Any],
) -> ValidationResult:
    """Validate an inactive public refresh guardrail recompile plan.

    The accepted shape is intentionally conservative: every recompile candidate must
    be inactive, every required reference set must be present and non-empty, and the
    plan must avoid claims or flags that imply live crawling, private artifacts,
    DevHub work, official action completion, guarantees, or mutation of active state.
    """

    issues: list[ValidationIssue] = []

    if plan.get("plan_version") != "inactive-public-refresh-guardrail-recompile-plan-v1":
        issues.append(
            ValidationIssue(
                code="invalid_plan_version",
                message="plan_version must be inactive-public-refresh-guardrail-recompile-plan-v1",
                path="plan_version",
            )
        )

    if plan.get("mode") != "inactive_public_refresh_guardrail_recompile":
        issues.append(
            ValidationIssue(
                code="invalid_mode",
                message="mode must be inactive_public_refresh_guardrail_recompile",
                path="mode",
            )
        )

    for field_name in REQUIRED_SEQUENCE_FIELDS:
        value = plan.get(field_name)
        if not _is_non_empty_sequence(value):
            issues.append(
                ValidationIssue(
                    code=f"missing_{field_name}",
                    message=f"{field_name} must be present and non-empty",
                    path=field_name,
                )
            )

    issues.extend(_validate_inactive_candidates(plan.get("inactive_guardrail_bundle_recompile_candidates")))
    issues.extend(_validate_validation_commands(plan.get("validation_commands")))
    issues.extend(_validate_active_mutation_flags(plan))
    issues.extend(_validate_claim_text(plan))

    return ValidationResult(accepted=not issues, issues=tuple(issues))


def reject_reasons(plan: Mapping[str, Any]) -> tuple[str, ...]:
    """Return stable reject reason codes for callers that only need codes."""

    result = validate_inactive_public_refresh_guardrail_recompile_plan_v1(plan)
    return tuple(issue.code for issue in result.issues)


def _is_non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and len(value) > 0


def _validate_inactive_candidates(value: Any) -> tuple[ValidationIssue, ...]:
    if not _is_non_empty_sequence(value):
        return ()

    issues: list[ValidationIssue] = []
    for index, candidate in enumerate(value):
        path = f"inactive_guardrail_bundle_recompile_candidates[{index}]"
        if not isinstance(candidate, Mapping):
            issues.append(
                ValidationIssue(
                    code="invalid_recompile_candidate",
                    message="each recompile candidate must be an object",
                    path=path,
                )
            )
            continue

        candidate_status = candidate.get("status") or candidate.get("bundle_status")
        if candidate_status != "inactive":
            issues.append(
                ValidationIssue(
                    code="missing_inactive_guardrailbundle_recompile_candidate",
                    message="each GuardrailBundle recompile candidate must be marked inactive",
                    path=f"{path}.status",
                )
            )

        if not candidate.get("guardrail_bundle_id"):
            issues.append(
                ValidationIssue(
                    code="missing_guardrail_bundle_id",
                    message="each recompile candidate must include guardrail_bundle_id",
                    path=f"{path}.guardrail_bundle_id",
                )
            )

    return tuple(issues)


def _validate_validation_commands(value: Any) -> tuple[ValidationIssue, ...]:
    if not _is_non_empty_sequence(value):
        return ()

    issues: list[ValidationIssue] = []
    for index, command in enumerate(value):
        path = f"validation_commands[{index}]"
        if not _is_non_empty_sequence(command) or not all(isinstance(part, str) and part for part in command):
            issues.append(
                ValidationIssue(
                    code="invalid_validation_command",
                    message="each validation command must be a non-empty list of non-empty strings",
                    path=path,
                )
            )
    return tuple(issues)


def _validate_active_mutation_flags(plan: Mapping[str, Any]) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for flag_name in ACTIVE_MUTATION_FLAGS:
        if plan.get(flag_name) is True:
            issues.append(
                ValidationIssue(
                    code="active_mutation_flag",
                    message=f"{flag_name} must not be true for an inactive public refresh recompile plan",
                    path=flag_name,
                )
            )
    return tuple(issues)


def _validate_claim_text(plan: Mapping[str, Any]) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    for field_name in FORBIDDEN_CLAIM_FIELDS:
        for path, text in _iter_text(plan.get(field_name), field_name):
            lowered = text.lower()
            for code, phrase in FORBIDDEN_CLAIM_PHRASES:
                if phrase in lowered:
                    issues.append(
                        ValidationIssue(
                            code=code,
                            message=f"forbidden claim phrase found: {phrase}",
                            path=path,
                        )
                    )
    return tuple(issues)


def _iter_text(value: Any, path: str) -> Iterable[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, Mapping):
        for key, nested_value in value.items():
            yield from _iter_text(nested_value, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        for index, nested_value in enumerate(value):
            yield from _iter_text(nested_value, f"{path}[{index}]")
