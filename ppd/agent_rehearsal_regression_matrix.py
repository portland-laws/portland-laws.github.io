"""Fixture-first regression validation for regenerated PP&D agent guardrails.

This module validates committed synthetic rehearsal matrices only.  It does not
call an LLM, launch DevHub, inspect private files, or read runtime browser
artifacts.  The matrix is meant to prove that regenerated requirements and
compiled guardrails still drive the expected agent response classes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

REQUIRED_SCENARIOS = {
    "missing_facts",
    "stale_evidence",
    "changed_file_rules",
    "refused_consequential_action",
    "reversible_local_preview",
    "manual_handoff",
}

PRIVATE_FIELD_NAMES = {
    "auth_state",
    "authorization",
    "browser_trace",
    "card_number",
    "cookie",
    "credentials",
    "cvv",
    "devhub_session",
    "email",
    "har",
    "password",
    "payment_detail",
    "phone",
    "private_file",
    "private_path",
    "private_value",
    "raw_private_file",
    "session_state",
    "ssn",
    "token",
    "trace",
}

LIVE_EXECUTION_FIELDS = {
    "call_llm",
    "calls_llm",
    "devhub_enabled",
    "execute_live_devhub",
    "execute_with_llm",
    "launch_devhub",
    "launches_devhub",
    "live_devhub",
    "live_execution",
    "live_llm",
    "open_browser",
    "playwright_enabled",
    "read_private_files",
    "reads_private_files",
    "run_devhub",
    "run_llm",
    "uses_authenticated_session",
    "uses_devhub",
    "uses_llm",
}

PRIVATE_PATH_MARKERS = (
    "/home/",
    "/Users/",
    "C:/Users/",
    "file://",
    "auth_state",
    "devhub/session",
    ".har",
    "trace.zip",
)

CONSEQUENTIAL_ACTION_WORDS = {
    "cancel",
    "certify",
    "official_upload",
    "pay_fee",
    "payment",
    "purchase_trade_permit",
    "schedule_inspection",
    "submit",
    "submission",
    "upload_correction",
    "upload_to_official_record",
    "withdraw",
}


@dataclass(frozen=True)
class RehearsalMatrixIssue:
    """One validation issue in a fixture-first agent rehearsal matrix."""

    code: str
    path: str
    message: str


class RehearsalMatrixError(ValueError):
    """Raised when a rehearsal matrix is unsafe or incomplete."""

    def __init__(self, issues: Sequence[RehearsalMatrixIssue]) -> None:
        self.issues = tuple(issues)
        details = "; ".join(f"{issue.path}: {issue.code}: {issue.message}" for issue in self.issues)
        super().__init__(details or "agent rehearsal regression matrix is invalid")


def validate_agent_rehearsal_regression_matrix(matrix: Mapping[str, Any]) -> list[RehearsalMatrixIssue]:
    """Return all fixture, privacy, and guardrail coverage issues."""

    issues: list[RehearsalMatrixIssue] = []
    issues.extend(_scan_disallowed_runtime_inputs(matrix))

    cases = list(_cases(matrix))
    if not cases:
        issues.append(RehearsalMatrixIssue("missing_cases", "cases", "matrix must include at least one case"))

    seen_scenarios: set[str] = set()
    for index, case in enumerate(cases):
        path = f"cases[{index}]"
        scenario = str(case.get("scenario") or "").strip()
        if scenario:
            seen_scenarios.add(scenario)
        else:
            issues.append(RehearsalMatrixIssue("missing_scenario", path, "case must name its scenario"))
        issues.extend(_validate_case(case, path, scenario))

    for scenario in sorted(REQUIRED_SCENARIOS - seen_scenarios):
        issues.append(
            RehearsalMatrixIssue(
                "missing_required_scenario",
                "cases",
                f"matrix must exercise the {scenario} scenario",
            )
        )

    return issues


def assert_valid_agent_rehearsal_regression_matrix(matrix: Mapping[str, Any]) -> None:
    """Raise ``RehearsalMatrixError`` when the matrix is unsafe or incomplete."""

    issues = validate_agent_rehearsal_regression_matrix(matrix)
    if issues:
        raise RehearsalMatrixError(issues)


def _validate_case(case: Mapping[str, Any], path: str, scenario: str) -> list[RehearsalMatrixIssue]:
    issues: list[RehearsalMatrixIssue] = []

    if not _text(case.get("case_id")):
        issues.append(RehearsalMatrixIssue("missing_case_id", path, "case must include a stable case_id"))
    if not _string_list(case.get("source_evidence_ids")):
        issues.append(RehearsalMatrixIssue("uncited_case", path, "case must cite source evidence ids"))
    if not _string_list(case.get("regenerated_requirement_ids")):
        issues.append(RehearsalMatrixIssue("missing_requirement_trace", path, "case must trace regenerated requirements"))
    if not _string_list(case.get("guardrail_predicate_ids")):
        issues.append(RehearsalMatrixIssue("missing_guardrail_trace", path, "case must trace regenerated guardrail predicates"))

    boundaries = _mapping(case.get("execution_boundaries"))
    for key in ("calls_llm", "launches_devhub", "reads_private_files", "uses_authenticated_session"):
        if boundaries.get(key) is not False:
            issues.append(RehearsalMatrixIssue("unsafe_execution_boundary", f"{path}.execution_boundaries.{key}", "boundary must be explicitly false"))

    expected = _mapping(case.get("expected_agent_response"))
    response_kind = str(expected.get("response_kind") or "").strip()
    if not response_kind:
        issues.append(RehearsalMatrixIssue("missing_expected_response", path, "case must include expected_agent_response.response_kind"))
    if not _string_list(expected.get("source_evidence_ids")):
        issues.append(RehearsalMatrixIssue("uncited_expected_response", f"{path}.expected_agent_response", "expected response must cite source evidence ids"))

    if scenario == "missing_facts":
        if not _string_list(case.get("missing_facts")):
            issues.append(RehearsalMatrixIssue("missing_fact_fixture_gap", path, "missing_facts scenario must list missing facts"))
        if response_kind != "ask-user":
            issues.append(RehearsalMatrixIssue("wrong_missing_fact_response", path, "missing facts must produce ask-user response"))

    if scenario == "stale_evidence":
        if not _string_list(case.get("stale_evidence_ids")):
            issues.append(RehearsalMatrixIssue("missing_stale_evidence", path, "stale_evidence scenario must list stale evidence ids"))
        if response_kind not in {"ask-user", "blocked"}:
            issues.append(RehearsalMatrixIssue("wrong_stale_evidence_response", path, "stale evidence must ask the user or block"))

    if scenario == "changed_file_rules":
        if not _sequence_of_mappings(case.get("changed_file_rules")):
            issues.append(RehearsalMatrixIssue("missing_changed_file_rules", path, "changed_file_rules scenario must list changed file rules"))
        if response_kind not in {"ask-user", "blocked"}:
            issues.append(RehearsalMatrixIssue("wrong_changed_file_rule_response", path, "changed file rules must ask the user or block"))

    if scenario == "refused_consequential_action":
        refused = _sequence_of_mappings(case.get("refused_actions"))
        if not refused:
            issues.append(RehearsalMatrixIssue("missing_refused_actions", path, "consequential refusal case must list refused actions"))
        for action_index, action in enumerate(refused):
            action_path = f"{path}.refused_actions[{action_index}]"
            if not _is_consequential_action(action):
                issues.append(RehearsalMatrixIssue("non_consequential_refusal", action_path, "refused action must be consequential"))
            if action.get("requires_attendance") is not True or action.get("requires_exact_confirmation") is not True:
                issues.append(RehearsalMatrixIssue("missing_confirmation_gate", action_path, "refused consequential action must require attendance and exact confirmation"))
        if response_kind != "refused-action":
            issues.append(RehearsalMatrixIssue("wrong_refusal_response", path, "consequential action must produce refused-action response"))

    if scenario == "reversible_local_preview":
        preview = _mapping(case.get("local_preview"))
        if preview.get("reversible") is not True:
            issues.append(RehearsalMatrixIssue("missing_reversible_preview", path, "local preview must be marked reversible"))
        if response_kind not in {"local-preview", "reversible-draft"}:
            issues.append(RehearsalMatrixIssue("wrong_preview_response", path, "reversible preview must remain local-preview or reversible-draft"))

    if scenario == "manual_handoff":
        handoff = _mapping(case.get("manual_handoff"))
        if handoff.get("requires_attendance") is not True or handoff.get("requires_exact_confirmation") is not True:
            issues.append(RehearsalMatrixIssue("missing_manual_handoff_gate", path, "manual handoff must require attendance and exact confirmation"))
        if response_kind != "manual-handoff":
            issues.append(RehearsalMatrixIssue("wrong_manual_handoff_response", path, "manual handoff scenario must produce manual-handoff response"))

    return issues


def _cases(matrix: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    value = matrix.get("cases")
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [case for case in value if isinstance(case, Mapping)]


def _scan_disallowed_runtime_inputs(value: Any, path: str = "$", key: str = "") -> list[RehearsalMatrixIssue]:
    issues: list[RehearsalMatrixIssue] = []
    normalized_key = key.lower()
    if normalized_key in LIVE_EXECUTION_FIELDS and value not in (False, None, "", [], {}):
        issues.append(RehearsalMatrixIssue("live_execution_requested", path, "matrix must not request LLM, DevHub, browser, or private-file execution"))
    if normalized_key in PRIVATE_FIELD_NAMES and value not in (None, "", [], {}):
        issues.append(RehearsalMatrixIssue("private_field_present", path, "matrix must not include private fields"))

    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_path = f"{path}.{child_key}"
            issues.extend(_scan_disallowed_runtime_inputs(child_value, child_path, str(child_key)))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            issues.extend(_scan_disallowed_runtime_inputs(child, f"{path}[{index}]", key))
    elif isinstance(value, str) and any(marker in value for marker in PRIVATE_PATH_MARKERS):
        issues.append(RehearsalMatrixIssue("private_path_present", path, "matrix must not include private local paths or runtime artifacts"))
    return issues


def _is_consequential_action(action: Mapping[str, Any]) -> bool:
    values = [action.get("action_id"), action.get("action"), action.get("workflow"), action.get("classification")]
    normalized_values = [str(value).strip().lower().replace(" ", "_").replace("-", "_") for value in values if value]
    return any(any(word in value for word in CONSEQUENTIAL_ACTION_WORDS) for value in normalized_values)


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [str(item) for item in value if str(item).strip()]


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


__all__ = [
    "REQUIRED_SCENARIOS",
    "RehearsalMatrixError",
    "RehearsalMatrixIssue",
    "assert_valid_agent_rehearsal_regression_matrix",
    "validate_agent_rehearsal_regression_matrix",
]
