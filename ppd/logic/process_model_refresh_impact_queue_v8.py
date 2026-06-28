"""Validation for PP&D process model refresh impact queue v8 records.

The queue is a deterministic handoff artifact. It should describe what a
source or requirement refresh would affect without claiming live execution,
mutation, legal certainty, or official-action completion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ValidationIssue:
    """One deterministic validation failure."""

    code: str
    message: str
    path: str


_REQUIRED_TOP_LEVEL_FIELDS: tuple[tuple[str, str], ...] = (
    ("requirement_node_candidate_set_refs", "missing RequirementNode candidate set references"),
    ("process_model_refs", "missing process model references"),
    ("affected_process_ids", "missing affected process IDs"),
    ("permit_type_impact_rows", "missing permit-type impact rows"),
    ("eligibility_impact_placeholders", "missing eligibility impact placeholders"),
    ("required_fact_impact_placeholders", "missing required-fact impact placeholders"),
    ("required_document_impact_placeholders", "missing required-document impact placeholders"),
    ("file_rule_impact_placeholders", "missing file-rule impact placeholders"),
    ("fee_impact_placeholders", "missing fee impact placeholders"),
    ("deadline_impact_placeholders", "missing deadline impact placeholders"),
    ("action_gate_impact_placeholders", "missing action-gate impact placeholders"),
    ("unsupported_path_carry_forward_rows", "missing unsupported-path carry-forward rows"),
    ("guardrail_recompile_candidate_refs", "missing guardrail recompile candidate references"),
    ("reviewer_hold_notes", "missing reviewer hold notes"),
    ("validation_commands", "missing validation commands"),
)

_PRIVATE_ARTIFACT_KEYS = {
    "auth_state",
    "browser_state",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "har",
    "local_private_file_path",
    "password",
    "payment_detail",
    "private_upload",
    "raw_authenticated_value",
    "raw_crawl_output",
    "screenshot",
    "session",
    "session_file",
    "session_state",
    "storage_state",
    "trace",
    "token",
}

_ACTIVE_MUTATION_KEYS = {
    "active_mutation",
    "apply_mutations",
    "execute_mutations",
    "live_mutation",
    "mutation_enabled",
    "mutations_enabled",
    "official_write_enabled",
    "write_enabled",
    "writes_enabled",
}

_ACTIVE_MUTATION_VALUES = {"active", "apply", "execute", "live", "mutate", "mutation", "write"}

_PROHIBITED_TEXT_PATTERNS: tuple[tuple[str, str, str], ...] = (
    ("active_guardrail_activation_claim", "active guardrail activation claim", "guardrail activated"),
    ("active_guardrail_activation_claim", "active guardrail activation claim", "guardrails activated"),
    ("active_guardrail_activation_claim", "active guardrail activation claim", "activated guardrail"),
    ("active_guardrail_activation_claim", "active guardrail activation claim", "activated guardrails"),
    ("live_crawl_execution_claim", "live crawl execution claim", "live crawl executed"),
    ("live_crawl_execution_claim", "live crawl execution claim", "crawl executed"),
    ("live_crawl_execution_claim", "live crawl execution claim", "crawler executed"),
    ("official_action_completion_claim", "official-action completion claim", "official action completed"),
    ("official_action_completion_claim", "official-action completion claim", "permit submitted"),
    ("official_action_completion_claim", "official-action completion claim", "payment submitted"),
    ("official_action_completion_claim", "official-action completion claim", "inspection scheduled"),
    ("official_action_completion_claim", "official-action completion claim", "application certified"),
    ("legal_or_permitting_guarantee", "legal or permitting guarantee", "guaranteed approval"),
    ("legal_or_permitting_guarantee", "legal or permitting guarantee", "permit guaranteed"),
    ("legal_or_permitting_guarantee", "legal or permitting guarantee", "legally guaranteed"),
    ("legal_or_permitting_guarantee", "legal or permitting guarantee", "will be approved"),
)


class ProcessModelRefreshImpactQueueV8Error(ValueError):
    """Raised when a queue record fails deterministic validation."""

    def __init__(self, issues: Sequence[ValidationIssue]):
        self.issues = tuple(issues)
        detail = "; ".join(f"{issue.path}: {issue.message}" for issue in self.issues)
        super().__init__(detail)


def validate_process_model_refresh_impact_queue_v8(record: Mapping[str, Any]) -> list[ValidationIssue]:
    """Return deterministic validation failures for a v8 refresh impact record."""

    issues: list[ValidationIssue] = []

    if not isinstance(record, Mapping):
        return [ValidationIssue("invalid_record", "queue record must be a mapping", "$")]

    version = record.get("queue_version")
    if version != "process_model_refresh_impact_queue_v8":
        issues.append(
            ValidationIssue(
                "invalid_queue_version",
                "queue_version must be process_model_refresh_impact_queue_v8",
                "$.queue_version",
            )
        )

    for field_name, message in _REQUIRED_TOP_LEVEL_FIELDS:
        if _is_missing_or_empty(record.get(field_name)):
            issues.append(ValidationIssue("missing_required_field", message, f"$.{field_name}"))

    for issue in _scan_value(record, "$"):
        issues.append(issue)

    return issues


def assert_valid_process_model_refresh_impact_queue_v8(record: Mapping[str, Any]) -> None:
    """Raise if a v8 refresh impact queue record is invalid."""

    issues = validate_process_model_refresh_impact_queue_v8(record)
    if issues:
        raise ProcessModelRefreshImpactQueueV8Error(issues)


def _is_missing_or_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return len(value) == 0
    return False


def _scan_value(value: Any, path: str) -> Iterable[ValidationIssue]:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized_key = key.strip().lower()
            child_path = f"{path}.{key}"

            if normalized_key in _PRIVATE_ARTIFACT_KEYS and not _is_missing_or_empty(child):
                yield ValidationIssue(
                    "private_session_auth_artifact",
                    "private/session/auth artifacts are not allowed in queue records",
                    child_path,
                )

            if normalized_key in _ACTIVE_MUTATION_KEYS and _truthy(child):
                yield ValidationIssue(
                    "active_mutation_flag",
                    "active mutation flags are not allowed in queue records",
                    child_path,
                )

            if normalized_key in {"mutation_mode", "run_mode", "execution_mode"}:
                if isinstance(child, str) and child.strip().lower() in _ACTIVE_MUTATION_VALUES:
                    yield ValidationIssue(
                        "active_mutation_flag",
                        "active mutation modes are not allowed in queue records",
                        child_path,
                    )

            yield from _scan_value(child, child_path)
        return

    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        for index, child in enumerate(value):
            yield from _scan_value(child, f"{path}[{index}]")
        return

    if isinstance(value, str):
        normalized = " ".join(value.lower().split())
        for code, label, pattern in _PROHIBITED_TEXT_PATTERNS:
            if pattern in normalized:
                yield ValidationIssue(code, f"{label} is not allowed in queue records", path)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on", "active", "enabled"}
    if isinstance(value, (int, float)):
        return value != 0
    return bool(value)
