"""Fixture-first agent consumer regression rerun planning.

This module builds deterministic synthetic request cases from committed guardrail
bundle update candidates and a safe-action regression matrix. It never invokes an
agent consumer, never reads private case files, and never requires LLM execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


READ_ONLY = "read_only"
REVERSIBLE_DRAFT = "reversible_draft"
MANUAL_HANDOFF = "manual_handoff"
REFUSED_CONSEQUENTIAL = "refused_consequential_action"

_PRIVATE_FACT_KEYS = {
    "private_case_fact",
    "private_case_facts",
    "case_fact",
    "case_facts",
    "known_private_fact",
    "known_private_facts",
    "observed_private_values",
    "private_values",
    "applicant_name",
    "owner_name",
    "email_address",
    "phone_number",
    "permit_number",
    "project_address",
    "tax_account_number",
}
_PRIVATE_PATH_KEYS = {
    "private_case_file",
    "private_case_path",
    "auth_state_path",
    "trace_path",
    "har_path",
    "screenshot_path",
    "downloaded_document_path",
    "local_path",
    "fixture_path",
}
_PRIVATE_CLASSIFICATIONS = {
    "private",
    "confidential",
    "restricted",
    "user_private",
    "case_private",
    "devhub_authenticated_private",
}
_LOCAL_PATH_PREFIXES = ("/home/", "/Users/", "/private/", "/tmp/", "file://", "C:\\", "D:\\")
_STALE_ACK_KEYS = {
    "stale_current_acknowledged",
    "stale_current_evidence_acknowledged",
    "reviewer_acknowledged_stale_current",
    "reviewer_acknowledged_stale_evidence",
    "stale_evidence_acknowledgement",
}
_LIVE_EXECUTION_KEYS = {
    "llm_execution_allowed",
    "llm_executed",
    "live_llm_executed",
    "agent_consumer_invoked",
    "agent_consumers_invoked",
    "devhub_executed",
    "devhub_browser_executed",
    "live_devhub_executed",
    "browser_automation_executed",
}
_LIVE_EXECUTION_PHRASES = (
    "live llm",
    "llm executed",
    "llm execution completed",
    "called the llm",
    "agent consumer invoked",
    "agent consumer executed",
    "live devhub",
    "devhub executed",
    "devhub browser ran",
    "opened devhub",
    "browser automation ran",
)
_OUTCOME_GUARANTEE_PHRASES = (
    "guarantee approval",
    "guaranteed approval",
    "permit will be approved",
    "application will be approved",
    "approval is guaranteed",
    "permit will issue",
    "permit issuance guaranteed",
    "will receive the permit",
    "legally valid",
    "no legal risk",
    "cannot be denied",
)
_CONSEQUENTIAL_CONTROL_WORDS = (
    "submit",
    "submission",
    "upload",
    "payment",
    "pay",
    "purchase",
    "schedule",
    "scheduling",
    "inspection",
    "certify",
    "certification",
    "acknowledge",
)


@dataclass(frozen=True)
class RegressionPlanInputError(ValueError):
    """Raised when fixture inputs would make the rerun plan unsafe or ambiguous."""

    message: str

    def __str__(self) -> str:
        return self.message


def build_agent_consumer_regression_rerun_plan(
    guardrail_bundle_candidates: dict[str, Any],
    safe_action_regression_matrix: dict[str, Any],
) -> dict[str, Any]:
    """Build a deterministic no-LLM rerun plan from fixture dictionaries."""

    _assert_no_private_case_references(guardrail_bundle_candidates, "guardrail_bundle_candidates")
    _assert_no_private_case_references(safe_action_regression_matrix, "safe_action_regression_matrix")

    candidates = _require_list(guardrail_bundle_candidates, "candidates")
    scenarios = _require_list(safe_action_regression_matrix, "scenarios")
    candidate_by_process = {
        _require_text(candidate, "process_id"): candidate
        for candidate in sorted(candidates, key=lambda item: _require_text(item, "candidate_id"))
    }

    cases: list[dict[str, Any]] = []
    owners: dict[str, list[str]] = {}

    for scenario in sorted(scenarios, key=lambda item: _require_text(item, "scenario_id")):
        process_id = _require_text(scenario, "process_id")
        if process_id not in candidate_by_process:
            raise RegressionPlanInputError(
                f"scenario {scenario.get('scenario_id', '')} references missing process_id {process_id}"
            )
        candidate = candidate_by_process[process_id]
        case = _build_case(candidate, scenario)
        cases.append(case)
        owner = case["reviewer_owner"]
        owners.setdefault(owner, []).append(case["case_id"])

    plan = {
        "plan_id": "fixture-first-agent-consumer-regression-rerun",
        "schema_version": 1,
        "execution_policy": {
            "agent_consumers_invoked": False,
            "private_case_files_read": False,
            "llm_execution_allowed": False,
            "fixtures_only": True,
        },
        "source_fixture_ids": {
            "guardrail_bundle_candidates": _require_text(guardrail_bundle_candidates, "fixture_id"),
            "safe_action_regression_matrix": _require_text(safe_action_regression_matrix, "fixture_id"),
        },
        "synthetic_request_cases": cases,
        "reviewer_owners": [
            {"owner": owner, "case_ids": case_ids}
            for owner, case_ids in sorted(owners.items())
        ],
        "no_llm_execution_attestation": {
            "attested": True,
            "method": "deterministic fixture transformation only",
            "prohibited_inputs": [
                "private case files",
                "authenticated DevHub state",
                "agent consumer traces",
                "LLM completions",
            ],
        },
    }
    assert_valid_agent_consumer_regression_rerun_plan(plan)
    return plan


def validate_agent_consumer_regression_rerun_plan(plan: Mapping[str, Any]) -> list[dict[str, str]]:
    """Return deterministic rejection findings for an agent rerun plan."""

    findings: list[dict[str, str]] = []
    _validate_reviewer_owners(plan, findings)
    _validate_cases(plan, findings)
    _validate_recursive_safety(plan, findings)
    return findings


def assert_valid_agent_consumer_regression_rerun_plan(plan: Mapping[str, Any]) -> None:
    """Raise when an agent consumer rerun plan violates PP&D safety rules."""

    findings = validate_agent_consumer_regression_rerun_plan(plan)
    if findings:
        details = "; ".join(f"{item['code']} at {item['path']}" for item in findings)
        raise RegressionPlanInputError(details)


def _build_case(candidate: dict[str, Any], scenario: dict[str, Any]) -> dict[str, Any]:
    action_class = _require_text(scenario, "action_class")
    base = {
        "case_id": f"synthetic-{_require_text(scenario, 'scenario_id')}",
        "candidate_id": _require_text(candidate, "candidate_id"),
        "guardrail_bundle_id": _require_text(candidate, "guardrail_bundle_id"),
        "process_id": _require_text(candidate, "process_id"),
        "synthetic_user_request": _require_text(scenario, "synthetic_user_request"),
        "action_class": action_class,
        "source_evidence_ids": sorted(_require_list(candidate, "source_evidence_ids")),
        "reviewer_owner": _require_text(scenario, "reviewer_owner"),
        "no_llm_execution_attestation": True,
    }

    if action_class == READ_ONLY:
        base["expected_read_only_answer"] = {
            "answer_style": "source-grounded summary",
            "must_include": sorted(_require_list(scenario, "expected_answer_must_include")),
            "must_not_include": [
                "drafted official changes",
                "uploads",
                "submission instructions that imply completion",
                "payment execution",
            ],
        }
        return base

    if action_class == REVERSIBLE_DRAFT:
        base["reversible_draft_limits"] = {
            "allowed": sorted(_require_list(scenario, "allowed_reversible_draft_actions")),
            "blocked": sorted(_require_list(candidate, "exact_confirmation_predicates")),
        }
        base["missing_information_prompts"] = sorted(
            _require_list(scenario, "missing_information_prompts")
        )
        return base

    if action_class == MANUAL_HANDOFF:
        base["manual_handoff_prompts"] = sorted(_require_list(scenario, "manual_handoff_prompts"))
        base["expected_read_only_answer"] = {
            "answer_style": "explain status and hand off exact official action",
            "must_include": sorted(_require_list(scenario, "expected_answer_must_include")),
            "must_not_include": sorted(_require_list(candidate, "refused_action_predicates")),
        }
        return base

    if action_class == REFUSED_CONSEQUENTIAL:
        base["refused_consequential_action_response"] = {
            "refusal_reason": _require_text(scenario, "refusal_reason"),
            "safe_alternatives": sorted(_require_list(scenario, "safe_alternatives")),
            "blocked_predicates": sorted(_require_list(candidate, "refused_action_predicates")),
        }
        return base

    raise RegressionPlanInputError(f"unsupported action_class {action_class}")


def _validate_reviewer_owners(plan: Mapping[str, Any], findings: list[dict[str, str]]) -> None:
    owners = plan.get("reviewer_owners")
    if not isinstance(owners, Sequence) or isinstance(owners, (str, bytes)) or not owners:
        findings.append(_finding("missing_reviewer_owners", "Rerun plans require reviewer owners.", "$.reviewer_owners"))


def _validate_cases(plan: Mapping[str, Any], findings: list[dict[str, str]]) -> None:
    cases = plan.get("synthetic_request_cases")
    if not isinstance(cases, Sequence) or isinstance(cases, (str, bytes)) or not cases:
        findings.append(_finding("missing_synthetic_cases", "Rerun plans require synthetic request cases.", "$.synthetic_request_cases"))
        return
    for index, case in enumerate(cases):
        path = f"$.synthetic_request_cases[{index}]"
        if not isinstance(case, Mapping):
            findings.append(_finding("invalid_case", "Synthetic request cases must be mappings.", path))
            continue
        if not str(case.get("reviewer_owner") or "").strip():
            findings.append(_finding("missing_reviewer_owner", "Each synthetic case requires a reviewer owner.", f"{path}.reviewer_owner"))
        if _case_has_expected_response(case) and not _has_citation(case.get("source_evidence_ids") or case.get("citations")):
            findings.append(_finding("uncited_expected_response", "Expected responses require source evidence citations.", path))
        if str(case.get("action_class") or "") == REFUSED_CONSEQUENTIAL:
            _validate_refusal_expectations(case, findings, path)


def _validate_refusal_expectations(case: Mapping[str, Any], findings: list[dict[str, str]], path: str) -> None:
    response = case.get("refused_consequential_action_response")
    response_path = f"{path}.refused_consequential_action_response"
    if not isinstance(response, Mapping):
        findings.append(_finding("missing_refusal_expectation", "Refused consequential cases require refusal expectations.", response_path))
        return
    if not str(response.get("refusal_reason") or "").strip():
        findings.append(_finding("missing_refusal_expectation", "Refusal expectations require a refusal reason.", f"{response_path}.refusal_reason"))
    if not _string_list(response.get("safe_alternatives")):
        findings.append(_finding("missing_refusal_expectation", "Refusal expectations require safe alternatives.", f"{response_path}.safe_alternatives"))
    if not _string_list(response.get("blocked_predicates")):
        findings.append(_finding("missing_refusal_expectation", "Refusal expectations require blocked predicates.", f"{response_path}.blocked_predicates"))


def _validate_recursive_safety(plan: Mapping[str, Any], findings: list[dict[str, str]]) -> None:
    for path, key, value in _walk(plan):
        key_text = key.lower()
        if key_text in _PRIVATE_FACT_KEYS and _non_empty(value):
            findings.append(_finding("private_case_facts", "Rerun plans must not carry private case facts.", path))
        if key_text in _PRIVATE_PATH_KEYS and _non_empty(value):
            findings.append(_finding("local_private_path", "Rerun plans must not reference private local paths or artifacts.", path))
        if key_text in {"privacy", "privacy_classification", "case_fact_privacy"} and str(value).lower() in _PRIVATE_CLASSIFICATIONS:
            findings.append(_finding("private_case_facts", "Rerun plans must not include private or authenticated case material.", path))
        if key_text in _LIVE_EXECUTION_KEYS and value not in (False, None, "", "not_run", "fixture_only"):
            findings.append(_finding("live_execution_claim", "Rerun plans must not claim live LLM, agent consumer, browser, or DevHub execution.", path))
        if _is_enabled_consequential_control(key_text, value):
            findings.append(_finding("enabled_consequential_control", "Submission, upload, payment, scheduling, and certification controls must be disabled.", path))
        if isinstance(value, str):
            lowered = value.lower()
            if _looks_like_local_private_path(value):
                findings.append(_finding("local_private_path", "Rerun plans must not reference private local paths or artifacts.", path))
            if any(phrase in lowered for phrase in _LIVE_EXECUTION_PHRASES):
                findings.append(_finding("live_execution_claim", "Rerun plans must not claim live LLM, agent consumer, browser, or DevHub execution.", path))
            if any(phrase in lowered for phrase in _OUTCOME_GUARANTEE_PHRASES):
                findings.append(_finding("outcome_guarantee", "Rerun plans must not guarantee legal or permitting outcomes.", path))
        if isinstance(value, Mapping) and _is_stale_current_without_ack(value):
            findings.append(_finding("stale_current_unacknowledged", "Stale-current claims require explicit reviewer acknowledgement.", path))


def _require_list(value: dict[str, Any], key: str) -> list[Any]:
    item = value.get(key)
    if not isinstance(item, list) or not item:
        raise RegressionPlanInputError(f"{key} must be a non-empty list")
    return item


def _require_text(value: dict[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise RegressionPlanInputError(f"{key} must be a non-empty string")
    return item


def _assert_no_private_case_references(value: Any, path: str) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in _PRIVATE_PATH_KEYS or key in _PRIVATE_FACT_KEYS:
                raise RegressionPlanInputError(f"{path}.{key} is prohibited in fixture-first reruns")
            if isinstance(item, str) and _looks_like_local_private_path(item):
                raise RegressionPlanInputError(f"{path}.{key} references a private local path")
            _assert_no_private_case_references(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_private_case_references(item, f"{path}[{index}]")


def _finding(code: str, message: str, path: str) -> dict[str, str]:
    return {"code": code, "message": message, "path": path}


def _case_has_expected_response(case: Mapping[str, Any]) -> bool:
    return any(
        key in case
        for key in (
            "expected_read_only_answer",
            "refused_consequential_action_response",
            "manual_handoff_prompts",
            "missing_information_prompts",
            "reversible_draft_limits",
        )
    )


def _has_citation(value: Any) -> bool:
    return bool(_string_list(value))


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def _non_empty(value: Any) -> bool:
    if value in (None, False, "", [], {}):
        return False
    if isinstance(value, Mapping):
        return any(_non_empty(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_non_empty(item) for item in value)
    return True


def _walk(value: Any, path: str = "$", key: str = "") -> list[tuple[str, str, Any]]:
    rows = [(path, key, value)]
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            child_key_text = str(child_key)
            rows.extend(_walk(child, f"{path}.{child_key_text}", child_key_text))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            rows.extend(_walk(child, f"{path}[{index}]", key))
    return rows


def _looks_like_local_private_path(value: str) -> bool:
    stripped = value.strip()
    if stripped.startswith(_LOCAL_PATH_PREFIXES):
        return True
    if "\\" in stripped and len(stripped) > 2 and stripped[1:3] == ":\\":
        return True
    return False


def _is_stale_current_without_ack(value: Mapping[str, Any]) -> bool:
    current = value.get("current") is True or value.get("is_current") is True
    status = str(value.get("freshness_status") or value.get("status") or value.get("evidence_status") or "").lower()
    stale = value.get("stale") is True or status in {"stale", "expired", "superseded"}
    if not current or not stale:
        return False
    return not any(value.get(key) is True or str(value.get(key) or "").strip() for key in _STALE_ACK_KEYS)


def _is_enabled_consequential_control(key_text: str, value: Any) -> bool:
    if "enabled" in key_text and any(word in key_text for word in _CONSEQUENTIAL_CONTROL_WORDS):
        return value not in (False, None, "", "false", "disabled", "not_enabled")
    if not isinstance(value, Mapping):
        return False
    enabled = value.get("enabled", False) is True or str(value.get("status") or "").lower() in {"enabled", "active", "allowed"}
    if not enabled:
        return False
    label = " ".join(str(value.get(item, "")) for item in ("id", "name", "label", "action", "description", "control"))
    return any(word in label.lower() for word in _CONSEQUENTIAL_CONTROL_WORDS)


def iter_case_ids(plan: dict[str, Any]) -> Iterable[str]:
    """Yield case ids from a built plan for narrow validation tests."""

    for case in plan.get("synthetic_request_cases", []):
        case_id = case.get("case_id")
        if isinstance(case_id, str):
            yield case_id


__all__ = [
    "MANUAL_HANDOFF",
    "READ_ONLY",
    "REFUSED_CONSEQUENTIAL",
    "REVERSIBLE_DRAFT",
    "RegressionPlanInputError",
    "assert_valid_agent_consumer_regression_rerun_plan",
    "build_agent_consumer_regression_rerun_plan",
    "iter_case_ids",
    "validate_agent_consumer_regression_rerun_plan",
]
