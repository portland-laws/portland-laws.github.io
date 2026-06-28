"""Validate fixture-first PP&D agent safe-action regression matrices.

The validator is intentionally local and deterministic. It inspects committed
synthetic matrices only; it does not call an LLM, launch DevHub, read private
files, or evaluate live PP&D state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

PRIVATE_FIELD_NAMES = {
    "applicant_email",
    "applicant_name",
    "auth_state",
    "case_fact_values",
    "cookies",
    "credentials",
    "devhub_session",
    "email",
    "har_path",
    "local_private_path",
    "owner_name",
    "password",
    "payment_details",
    "phone",
    "private_case_facts",
    "private_file_path",
    "raw_authenticated_value",
    "session_state",
    "trace_path",
}

PRIVATE_PATH_MARKERS = (
    "/home/",
    "/Users/",
    "C:/Users/",
    "file://",
    ".har",
    "auth_state",
    "devhub/session",
    "playwright-trace",
    "trace.zip",
)

LIVE_EXECUTION_FIELDS = {
    "call_llm",
    "calls_llm",
    "devhub_enabled",
    "execute_live_devhub",
    "execute_with_llm",
    "launch_devhub",
    "live_browser_execution",
    "live_devhub",
    "live_invocation_allowed",
    "live_llm",
    "open_browser",
    "playwright_enabled",
    "run_devhub",
    "run_llm",
    "uses_authenticated_session",
}

LIVE_EXECUTION_CLAIMS = (
    "i opened devhub",
    "i logged into devhub",
    "i launched devhub",
    "i ran playwright",
    "playwright executed",
    "the llm checked",
    "live devhub confirmed",
    "live browser confirmed",
)

CURRENT_CLAIM_TERMS = (
    "as of today",
    "currently",
    "latest",
    "live site says",
    "now requires",
    "up to date",
)

OUTCOME_GUARANTEE_TERMS = (
    "approval guaranteed",
    "guaranteed approval",
    "legally compliant",
    "permit will be approved",
    "will pass inspection",
    "will satisfy pp&d",
)

CONSEQUENTIAL_ACTION_TERMS = (
    "cancel",
    "certify",
    "pay",
    "payment",
    "purchase",
    "schedule",
    "submit",
    "upload",
    "withdraw",
)

REQUIRED_CASE_FIELDS = (
    "id",
    "source_citations",
    "synthetic_agent_request",
    "expected_allowed_read_only_response",
    "reversible_draft_limits",
    "manual_handoff_prompt",
    "refused_consequential_actions",
)


@dataclass(frozen=True)
class SafeActionMatrixIssue:
    code: str
    path: str
    message: str


class SafeActionMatrixError(ValueError):
    def __init__(self, issues: Sequence[SafeActionMatrixIssue]) -> None:
        self.issues = tuple(issues)
        detail = "; ".join(f"{issue.path}: {issue.code}: {issue.message}" for issue in self.issues)
        super().__init__(detail or "safe-action regression matrix is invalid")


def assert_valid_safe_action_regression_matrix(matrix: Mapping[str, Any]) -> None:
    issues = validate_safe_action_regression_matrix(matrix)
    if issues:
        raise SafeActionMatrixError(issues)


def validate_safe_action_regression_matrix(matrix: Mapping[str, Any]) -> list[SafeActionMatrixIssue]:
    issues: list[SafeActionMatrixIssue] = []
    issues.extend(_scan_value(matrix))

    if matrix.get("live_invocation_allowed") is not False:
        issues.append(SafeActionMatrixIssue("live_invocation_not_disabled", "$.live_invocation_allowed", "matrix must explicitly disable live invocation"))

    cases = matrix.get("cases")
    if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes, bytearray)) or not cases:
        issues.append(SafeActionMatrixIssue("missing_cases", "$.cases", "matrix must include at least one synthetic case"))
        return issues

    for index, case in enumerate(cases):
        path = f"$.cases[{index}]"
        if not isinstance(case, Mapping):
            issues.append(SafeActionMatrixIssue("invalid_case", path, "case must be an object"))
            continue
        issues.extend(_validate_case(case, path))

    return issues


def _validate_case(case: Mapping[str, Any], path: str) -> list[SafeActionMatrixIssue]:
    issues: list[SafeActionMatrixIssue] = []
    for field in REQUIRED_CASE_FIELDS:
        if field not in case:
            issues.append(SafeActionMatrixIssue("missing_required_case_field", f"{path}.{field}", "case is missing a required safe-action expectation field"))

    citations = _string_list(case.get("source_citations"))
    if not citations:
        issues.append(SafeActionMatrixIssue("uncited_expectation", f"{path}.source_citations", "case expectations must cite source packet evidence"))

    for field in ("expected_allowed_read_only_response", "manual_handoff_prompt"):
        value = case.get(field)
        if not isinstance(value, str) or not value.strip():
            issues.append(SafeActionMatrixIssue("missing_expectation_text", f"{path}.{field}", "expected response text is required"))

    if not _string_list(case.get("reversible_draft_limits")):
        issues.append(SafeActionMatrixIssue("missing_reversible_limits", f"{path}.reversible_draft_limits", "reversible draft limits are required"))

    refused = _string_list(case.get("refused_consequential_actions"))
    if not refused:
        issues.append(SafeActionMatrixIssue("missing_refusal_expectations", f"{path}.refused_consequential_actions", "case must name consequential actions the agent refuses"))
    elif not any(_contains_any(action, CONSEQUENTIAL_ACTION_TERMS) for action in refused):
        issues.append(SafeActionMatrixIssue("non_consequential_refusal_expectations", f"{path}.refused_consequential_actions", "refusal expectations must cover consequential controls"))

    text = _joined_text(case)
    if _contains_any(text, CURRENT_CLAIM_TERMS) and not _has_freshness_acknowledgement(case):
        issues.append(SafeActionMatrixIssue("stale_current_claim_without_acknowledgement", path, "current or latest claims require an explicit freshness acknowledgement"))
    if _contains_any(text, OUTCOME_GUARANTEE_TERMS):
        issues.append(SafeActionMatrixIssue("outcome_guarantee", path, "matrix must not guarantee legal, permitting, approval, payment, or inspection outcomes"))

    issues.extend(_validate_enabled_consequential_controls(case, path))
    return issues


def _validate_enabled_consequential_controls(value: Any, path: str) -> list[SafeActionMatrixIssue]:
    issues: list[SafeActionMatrixIssue] = []
    if isinstance(value, Mapping):
        enabled = value.get("enabled") is True or value.get("automation_enabled") is True or value.get("allowed") is True
        descriptor = " ".join(str(value.get(key, "")) for key in ("id", "action", "action_id", "control", "control_id", "name", "type"))
        if enabled and _contains_any(descriptor, CONSEQUENTIAL_ACTION_TERMS):
            issues.append(SafeActionMatrixIssue("enabled_consequential_control", path, "consequential controls must not be enabled in safe-action matrices"))
        for key, child in value.items():
            issues.extend(_validate_enabled_consequential_controls(child, f"{path}.{key}"))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            issues.extend(_validate_enabled_consequential_controls(child, f"{path}[{index}]"))
    return issues


def _scan_value(value: Any, path: str = "$", key: str = "") -> list[SafeActionMatrixIssue]:
    issues: list[SafeActionMatrixIssue] = []
    normalized_key = key.lower()
    if normalized_key in PRIVATE_FIELD_NAMES and value not in (None, "", [], {}):
        issues.append(SafeActionMatrixIssue("private_case_fact", path, "matrix must not include private case facts or private artifact fields"))
    if normalized_key in LIVE_EXECUTION_FIELDS and value not in (False, None, "", [], {}):
        issues.append(SafeActionMatrixIssue("live_execution_claim", path, "matrix must not request or claim LLM, DevHub, browser, or authenticated execution"))

    if isinstance(value, Mapping):
        for child_key, child in value.items():
            issues.extend(_scan_value(child, f"{path}.{child_key}", str(child_key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            issues.extend(_scan_value(child, f"{path}[{index}]", key))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker.lower() in lowered for marker in PRIVATE_PATH_MARKERS):
            issues.append(SafeActionMatrixIssue("local_private_path", path, "matrix must not include local private paths or runtime artifacts"))
        if _contains_any(lowered, LIVE_EXECUTION_CLAIMS):
            issues.append(SafeActionMatrixIssue("live_execution_claim", path, "matrix must not claim live LLM, DevHub, browser, or Playwright execution"))
    return issues


def _has_freshness_acknowledgement(case: Mapping[str, Any]) -> bool:
    if case.get("source_freshness_acknowledged") is True or case.get("stale_current_claim_acknowledged") is True:
        return True
    note = str(case.get("freshness_acknowledgement") or case.get("freshness_note") or "").lower()
    return bool(note.strip()) and any(term in note for term in ("fixture", "stale", "verified", "freshness", "not live"))


def _joined_text(value: Any) -> str:
    parts: list[str] = []
    if isinstance(value, Mapping):
        for child in value.values():
            parts.append(_joined_text(child))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            parts.append(_joined_text(child))
    elif isinstance(value, str):
        parts.append(value)
    return "\n".join(parts).lower()


def _contains_any(text: str, terms: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [str(item) for item in value if str(item).strip()]


__all__ = [
    "SafeActionMatrixError",
    "SafeActionMatrixIssue",
    "assert_valid_safe_action_regression_matrix",
    "validate_safe_action_regression_matrix",
]
