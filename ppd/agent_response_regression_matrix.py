"""Validation helpers for PP&D agent response regression matrices.

The regression matrix is intentionally plain JSON-compatible data.  These
helpers validate safety properties that must hold before a matrix can be used
as evidence that an agent response policy is still compliant.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


PRIVATE_KEY_HINTS = {
    "auth_state",
    "authorization",
    "bank_account",
    "card_number",
    "cookie",
    "credentials",
    "cvv",
    "devhub_session",
    "driver_license",
    "email",
    "har",
    "password",
    "payment_detail",
    "phone",
    "private_value",
    "session_state",
    "ssn",
    "tax_id",
    "trace",
}

CONSEQUENTIAL_ACTION_WORDS = {
    "account creation",
    "cancel",
    "certification",
    "certify",
    "create account",
    "final payment",
    "mfa",
    "payment",
    "schedule inspection",
    "submit",
    "submission",
    "upload",
}

BLOCKED_POLICY_WORDS = {"blocked", "refused", "manual_handoff", "requires_confirmation"}
ALLOWED_POLICY_WORDS = {"allow", "allowed", "autonomous", "safe"}
VALID_STATUS_WORDS = {"valid", "accepted", "pass", "passing"}
STALE_STATUS_WORDS = {"stale", "expired", "superseded", "unknown"}

LOCAL_PRIVATE_PATH_RE = re.compile(
    r"(?i)(?:file://|/home/[^\s,;]+|/users/[^\s,;]+|/var/folders/[^\s,;]+|[a-z]:\\\\users\\\\[^\s,;]+|\\\\users\\\\[^\s,;]+)"
)
PRIVATE_VALUE_RE = re.compile(
    r"(?i)(?:password\s*[=:]|bearer\s+[a-z0-9._\-]+|sk-[a-z0-9]{12,}|\b\d{3}-\d{2}-\d{4}\b|\b\d{13,19}\b)"
)


@dataclass(frozen=True)
class MatrixValidationIssue:
    """One validation failure in an agent response regression matrix."""

    code: str
    path: str
    message: str


class MatrixValidationError(ValueError):
    """Raised when an agent response regression matrix is unsafe to use."""

    def __init__(self, issues: Sequence[MatrixValidationIssue]) -> None:
        self.issues = tuple(issues)
        details = "; ".join(f"{issue.path}: {issue.code}: {issue.message}" for issue in self.issues)
        super().__init__(details or "agent response regression matrix is invalid")


def validate_agent_response_regression_matrix(
    matrix: Mapping[str, Any] | Sequence[Any],
    *,
    source_registry: Mapping[str, Any] | None = None,
) -> list[MatrixValidationIssue]:
    """Return all safety issues found in a regression matrix.

    The validator accepts the loose fixture shapes used by PP&D tests: either a
    top-level list of cases or a mapping with ``cases`` / ``regression_cases``.
    It is deliberately conservative and treats consequential official actions
    as requiring an explicit manual handoff expectation.
    """

    registry = _source_registry(matrix, source_registry)
    issues: list[MatrixValidationIssue] = []
    issues.extend(_scan_private_values(matrix))

    for index, case in enumerate(_cases(matrix)):
        if not isinstance(case, Mapping):
            issues.append(MatrixValidationIssue("invalid_case", f"cases[{index}]", "case must be an object"))
            continue
        path = f"cases[{index}]"
        issues.extend(_validate_case(case, path, registry))

    return issues


def assert_valid_agent_response_regression_matrix(
    matrix: Mapping[str, Any] | Sequence[Any],
    *,
    source_registry: Mapping[str, Any] | None = None,
) -> None:
    """Raise ``MatrixValidationError`` if the matrix violates PP&D guardrails."""

    issues = validate_agent_response_regression_matrix(matrix, source_registry=source_registry)
    if issues:
        raise MatrixValidationError(issues)


# Backwards-friendly aliases for callers that use shorter names.
validate_regression_matrix = validate_agent_response_regression_matrix
assert_valid_regression_matrix = assert_valid_agent_response_regression_matrix


def _validate_case(case: Mapping[str, Any], path: str, registry: Mapping[str, Any]) -> list[MatrixValidationIssue]:
    issues: list[MatrixValidationIssue] = []
    outcome = _first_present(case, "expected_outcome", "expected", "expectation")
    outcome_map = outcome if isinstance(outcome, Mapping) else {}

    if outcome is not None and not _has_citation(case, outcome_map):
        issues.append(
            MatrixValidationIssue(
                "uncited_expected_outcome",
                path,
                "expected outcomes must include citation/source evidence ids",
            )
        )

    source_ids = _source_ids(case, outcome_map)
    valid_marked = _is_valid_marked(case) or _is_valid_marked(outcome_map)
    for source_id in source_ids:
        if valid_marked and _source_is_stale(source_id, registry):
            issues.append(
                MatrixValidationIssue(
                    "stale_source_marked_valid",
                    path,
                    f"source id {source_id!r} is stale but the case is marked valid",
                )
            )

    if _blocked_action_downgraded_to_allowed(case, outcome_map):
        issues.append(
            MatrixValidationIssue(
                "blocked_action_downgraded_to_allowed",
                path,
                "blocked/refused actions cannot have an allowed expected policy",
            )
        )

    if _is_consequential_case(case) and not _requires_manual_handoff(case, outcome_map):
        issues.append(
            MatrixValidationIssue(
                "missing_manual_handoff_expectation",
                path,
                "consequential workflows must expect manual handoff or exact user confirmation",
            )
        )

    return issues


def _cases(matrix: Mapping[str, Any] | Sequence[Any]) -> Iterable[Any]:
    if isinstance(matrix, Mapping):
        for key in ("cases", "regression_cases", "matrix"):
            value = matrix.get(key)
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
                return value
        return [matrix]
    return matrix


def _source_registry(matrix: Mapping[str, Any] | Sequence[Any], explicit: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if explicit is not None:
        return explicit
    if isinstance(matrix, Mapping):
        for key in ("source_registry", "sources", "source_freshness"):
            value = matrix.get(key)
            if isinstance(value, Mapping):
                return value
    return {}


def _first_present(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping:
            return mapping[key]
    return None


def _has_citation(case: Mapping[str, Any], outcome: Mapping[str, Any]) -> bool:
    return bool(_source_ids(case, outcome) or _nonempty_listish(outcome.get("citations")) or _nonempty_listish(case.get("citations")))


def _source_ids(case: Mapping[str, Any], outcome: Mapping[str, Any]) -> list[str]:
    ids: list[str] = []
    for container in (outcome, case):
        for key in ("source_id", "source_ids", "source_evidence_id", "source_evidence_ids", "citation_ids"):
            value = container.get(key)
            ids.extend(_as_string_list(value))
    return ids


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [item for item in value if isinstance(item, str) and item.strip()]
    return []


def _nonempty_listish(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return bool(value)
    return False


def _is_valid_marked(mapping: Mapping[str, Any]) -> bool:
    for key in ("valid", "is_valid", "validation_status", "status", "expected_status"):
        value = mapping.get(key)
        if value is True:
            return True
        if isinstance(value, str) and value.strip().lower() in VALID_STATUS_WORDS:
            return True
    return False


def _source_is_stale(source_id: str, registry: Mapping[str, Any]) -> bool:
    entry = registry.get(source_id)
    if isinstance(entry, str):
        return entry.strip().lower() in STALE_STATUS_WORDS
    if isinstance(entry, Mapping):
        for key in ("freshness_status", "status", "source_status"):
            value = entry.get(key)
            if isinstance(value, str) and value.strip().lower() in STALE_STATUS_WORDS:
                return True
        if entry.get("stale") is True or entry.get("is_stale") is True:
            return True
    return source_id.lower().startswith("stale-")


def _blocked_action_downgraded_to_allowed(case: Mapping[str, Any], outcome: Mapping[str, Any]) -> bool:
    has_blocked_signal = bool(case.get("blocked_actions") or outcome.get("blocked_actions"))
    policy_values = [
        case.get("action_policy"),
        case.get("expected_action_policy"),
        case.get("expected_policy"),
        outcome.get("action_policy"),
        outcome.get("policy"),
        outcome.get("classification"),
    ]
    policy_words = {str(value).strip().lower() for value in policy_values if value is not None}
    if has_blocked_signal and policy_words & ALLOWED_POLICY_WORDS:
        return True
    blocked_values = [case.get("actual_policy"), case.get("source_policy"), case.get("guardrail_policy")]
    blocked_words = {str(value).strip().lower() for value in blocked_values if value is not None}
    return bool((blocked_words & BLOCKED_POLICY_WORDS) and (policy_words & ALLOWED_POLICY_WORDS))


def _is_consequential_case(case: Mapping[str, Any]) -> bool:
    fields = [
        case.get("workflow"),
        case.get("workflow_type"),
        case.get("action"),
        case.get("action_type"),
        case.get("stage"),
        case.get("name"),
        case.get("id"),
    ]
    text = " ".join(str(value).lower() for value in fields if value is not None)
    return any(word in text for word in CONSEQUENTIAL_ACTION_WORDS) or case.get("consequential") is True


def _requires_manual_handoff(case: Mapping[str, Any], outcome: Mapping[str, Any]) -> bool:
    for container in (case, outcome):
        for key in (
            "manual_handoff_required",
            "requires_manual_handoff",
            "requires_attendance",
            "requires_exact_confirmation",
            "exact_confirmation_required",
        ):
            if container.get(key) is True:
                return True
        expected = container.get("expected_guardrail") or container.get("expected_action")
        if isinstance(expected, str) and expected.strip().lower() in {"manual_handoff", "exact_confirmation", "refused"}:
            return True
    return False


def _scan_private_values(value: Any, path: str = "$", parent_key: str = "") -> list[MatrixValidationIssue]:
    issues: list[MatrixValidationIssue] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in PRIVATE_KEY_HINTS and item not in (None, "", [], {}):
                issues.append(MatrixValidationIssue("private_value", child_path, "private or credential-like fields are not allowed in committed matrices"))
            issues.extend(_scan_private_values(item, child_path, key_text))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            issues.extend(_scan_private_values(item, f"{path}[{index}]", parent_key))
    elif isinstance(value, str):
        lower_key = parent_key.lower()
        if LOCAL_PRIVATE_PATH_RE.search(value):
            issues.append(MatrixValidationIssue("local_private_path", path, "local private file paths are not allowed in committed matrices"))
        if lower_key in PRIVATE_KEY_HINTS or PRIVATE_VALUE_RE.search(value):
            issues.append(MatrixValidationIssue("private_value", path, "private values are not allowed in committed matrices"))
    return issues


__all__ = [
    "MatrixValidationError",
    "MatrixValidationIssue",
    "assert_valid_agent_response_regression_matrix",
    "assert_valid_regression_matrix",
    "validate_agent_response_regression_matrix",
    "validate_regression_matrix",
]
