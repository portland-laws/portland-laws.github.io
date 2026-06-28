from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ppd.agent_consumer_regression import validate_agent_consumer_regression_rerun_plan
from ppd.agent_readiness.dry_run_promotion_sequence_packet import validate_dry_run_promotion_sequence_packet

PACKET_TYPE = "ppd.post_promotion_smoke_test_plan.v1"

_PRIVATE_KEYS = {
    "private_case_fact",
    "private_case_facts",
    "case_fact",
    "case_facts",
    "applicant_name",
    "owner_name",
    "email_address",
    "phone_number",
    "permit_number",
    "project_address",
    "tax_account_number",
    "private_case_file",
    "private_case_path",
    "auth_state_path",
    "trace_path",
    "har_path",
    "screenshot_path",
    "downloaded_document_path",
    "local_path",
}
_LIVE_KEYS = {
    "agent_invoked",
    "agent_consumer_invoked",
    "agent_consumers_invoked",
    "browser_automation_executed",
    "compiler_invoked",
    "compiler_executed",
    "crawler_invoked",
    "crawler_executed",
    "devhub_executed",
    "devhub_invoked",
    "devhub_session_executed",
    "live_devhub_executed",
    "live_llm_executed",
    "live_llm_invoked",
    "live_crawler_executed",
    "live_processor_executed",
    "llm_executed",
    "llm_invoked",
    "llm_called",
    "processor_invoked",
    "processor_executed",
}
_POLICY_FALSE_KEYS = {
    "agents_invoked",
    "agent_consumers_invoked",
    "devhub_invoked",
    "live_crawlers_invoked",
    "processors_invoked",
    "compilers_invoked",
    "private_case_files_read",
    "writes_active_state",
}
_CONTROL_WORDS = (
    "submit",
    "submission",
    "upload",
    "payment",
    "pay",
    "schedule",
    "scheduling",
    "certify",
    "certification",
)
_CONTROL_KEY_WORDS = _CONTROL_WORDS + ("button", "control", "action")
_LIVE_PHRASES = (
    "agent invoked",
    "consumer executed",
    "crawler ran",
    "crawler executed",
    "devhub executed",
    "devhub session ran",
    "live devhub",
    "live llm",
    "llm executed",
    "llm invoked",
    "processor ran",
    "processor executed",
    "compiler ran",
)
_GUARANTEE_PHRASES = (
    "guarantee approval",
    "guaranteed approval",
    "permit will be approved",
    "application will be approved",
    "permit will issue",
    "approval is guaranteed",
    "issuance is guaranteed",
    "legally valid",
    "legal outcome guaranteed",
    "no legal risk",
    "no permitting risk",
    "cannot be denied",
    "will satisfy code",
)
_CONSEQUENTIAL_ACTION_CLASSES = {
    "consequential_official_action",
    "financial",
    "refused_consequential_action",
    "submission",
    "upload",
    "payment",
    "scheduling",
    "certification",
}
_LOCAL_PATH_RE = re.compile(r"(^file://)|(^/home/)|(^/Users/)|(^/tmp/)|(^/root/)|(^/private/)|(^/var/folders/)|([A-Za-z]:[\\/])")


@dataclass(frozen=True)
class PostPromotionSmokeTestPlanValidationResult:
    valid: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "problems": list(self.problems)}


def build_post_promotion_smoke_test_plan(
    dry_run_promotion_sequence_packet: Mapping[str, Any],
    agent_consumer_regression_rerun_plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a deterministic read-only post-promotion smoke-test plan from fixture packets."""

    dry_run_validation = validate_dry_run_promotion_sequence_packet(dry_run_promotion_sequence_packet)
    if not dry_run_validation.valid:
        raise ValueError("invalid_source_dry_run_promotion_sequence_packet: " + "; ".join(dry_run_validation.problems))

    regression_findings = validate_agent_consumer_regression_rerun_plan(agent_consumer_regression_rerun_plan)
    if regression_findings:
        details = "; ".join(f"{finding['code']} at {finding['path']}" for finding in regression_findings)
        raise ValueError("invalid_source_agent_consumer_regression_rerun_plan: " + details)

    source_cases = _mapping_sequence(agent_consumer_regression_rerun_plan.get("synthetic_request_cases"))
    dry_run_steps = _mapping_sequence(dry_run_promotion_sequence_packet.get("ordered_synthetic_promotion_steps"))
    reviewer_owners = _reviewer_owners(dry_run_promotion_sequence_packet, agent_consumer_regression_rerun_plan)
    owner_ids = [owner["owner_id"] for owner in reviewer_owners]
    default_owner = owner_ids[0] if owner_ids else "ppd-release-operator"

    smoke_cases = []
    citation_coverage = []
    draft_checks = []
    refusal_checks = []
    for index, case in enumerate(source_cases, start=1):
        case_id = str(case.get("case_id") or f"synthetic-case-{index}")
        evidence_ids = _string_list(case.get("source_evidence_ids") or case.get("citations"))
        owner = _owner_id(case.get("reviewer_owner") or default_owner)
        smoke_case_id = f"post-promotion-smoke:{case_id}"
        expected_response_fields = _expected_response_fields(case)
        smoke_cases.append(
            {
                "smoke_case_id": smoke_case_id,
                "source_case_id": case_id,
                "action_class": str(case.get("action_class") or "read_only"),
                "synthetic_user_request": str(case.get("synthetic_user_request") or "Review the synthetic post-promotion fixture case."),
                "expected_read_only_answer": {
                    "must_remain_read_only": True,
                    "source_response_fields": expected_response_fields,
                    "must_cite_source_evidence_ids": evidence_ids,
                    "must_not_invoke": ["agents", "DevHub", "live crawlers", "processors", "compilers"],
                },
                "source_evidence_ids": evidence_ids,
                "reviewer_owner": owner,
                "no_consumer_execution_attestation": True,
            }
        )
        citation_coverage.append(
            {
                "coverage_id": f"citation-coverage:{case_id}",
                "smoke_case_id": smoke_case_id,
                "required_source_evidence_ids": evidence_ids,
                "covers_expected_response": True,
            }
        )
        if case.get("action_class") == "reversible_draft" or case.get("reversible_draft_limits"):
            draft_checks.append(
                {
                    "check_id": f"reversible-draft-boundary:{case_id}",
                    "smoke_case_id": smoke_case_id,
                    "allowed_preview_only_actions": _string_list(_nested(case, "reversible_draft_limits", "allowed")),
                    "blocked_boundary_actions": _string_list(_nested(case, "reversible_draft_limits", "blocked")),
                    "requires_missing_information_prompts": _string_list(case.get("missing_information_prompts")),
                    "reviewer_owner": owner,
                    "source_evidence_ids": evidence_ids,
                }
            )
        if case.get("action_class") == "refused_consequential_action" or case.get("refused_consequential_action_response"):
            response = case.get("refused_consequential_action_response") if isinstance(case.get("refused_consequential_action_response"), Mapping) else {}
            refusal_checks.append(
                {
                    "check_id": f"refusal-check:{case_id}",
                    "smoke_case_id": smoke_case_id,
                    "expected_refusal_reason": str(response.get("refusal_reason") or "Consequential actions remain refused in smoke tests."),
                    "safe_alternatives": _string_list(response.get("safe_alternatives")),
                    "blocked_predicates": _string_list(response.get("blocked_predicates")) or ["consequential_actions_require_attended_exact_confirmation"],
                    "reviewer_owner": owner,
                    "source_evidence_ids": evidence_ids,
                }
            )

    for index, step in enumerate(dry_run_steps, start=1):
        evidence_ids = _string_list(step.get("prerequisite_evidence_ids"))
        smoke_case_id = f"post-promotion-smoke:dry-run-step-{index}"
        smoke_cases.append(
            {
                "smoke_case_id": smoke_case_id,
                "source_step_id": str(step.get("step_id") or index),
                "action_class": "read_only",
                "synthetic_user_request": "Confirm the dry-run promotion step remains synthetic and read-only.",
                "expected_read_only_answer": {
                    "must_remain_read_only": True,
                    "source_response_fields": ["synthetic_only", "writes_active_state", "abort_condition_ids", "rollback_action_id"],
                    "must_cite_source_evidence_ids": evidence_ids,
                    "must_not_invoke": ["agents", "DevHub", "live crawlers", "processors", "compilers"],
                },
                "source_evidence_ids": evidence_ids,
                "reviewer_owner": _owner_id(step.get("reviewer_owner") or default_owner),
                "no_consumer_execution_attestation": True,
            }
        )
        citation_coverage.append(
            {
                "coverage_id": f"citation-coverage:dry-run-step-{index}",
                "smoke_case_id": smoke_case_id,
                "required_source_evidence_ids": evidence_ids,
                "covers_expected_response": True,
            }
        )

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_id": "fixture-first-post-promotion-smoke-test-plan",
        "fixture_only": True,
        "source_packet_ids": {
            "dry_run_promotion_sequence_packet": str(dry_run_promotion_sequence_packet.get("packet_id") or "dry-run-promotion-sequence"),
            "agent_consumer_regression_rerun_plan": str(agent_consumer_regression_rerun_plan.get("plan_id") or "agent-consumer-regression-rerun"),
        },
        "execution_policy": {
            "fixtures_only": True,
            "agents_invoked": False,
            "agent_consumers_invoked": False,
            "devhub_invoked": False,
            "live_crawlers_invoked": False,
            "processors_invoked": False,
            "compilers_invoked": False,
            "private_case_files_read": False,
            "writes_active_state": False,
        },
        "synthetic_read_only_smoke_cases": smoke_cases,
        "reversible_draft_boundary_checks": draft_checks or [_default_draft_boundary_check(default_owner)],
        "refusal_checks": refusal_checks,
        "expected_citation_coverage": citation_coverage,
        "reviewer_owners": reviewer_owners,
        "no_consumer_execution_attestations": [
            {
                "attestation_id": "no-agent-or-consumer-execution",
                "attested": True,
                "method": "fixture transformation only",
                "prohibited_invocations": ["agents", "agent consumers", "DevHub", "live crawlers", "processors", "compilers", "private case files"],
            }
        ],
    }
    assert_valid_post_promotion_smoke_test_plan(packet)
    return packet


def validate_post_promotion_smoke_test_plan(packet: Mapping[str, Any]) -> PostPromotionSmokeTestPlanValidationResult:
    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append("packet_type must be ppd.post_promotion_smoke_test_plan.v1")
    if packet.get("fixture_only") is not True:
        problems.append("fixture_only must be true")

    policy = packet.get("execution_policy") if isinstance(packet.get("execution_policy"), Mapping) else {}
    if policy.get("fixtures_only") is not True:
        problems.append("execution_policy.fixtures_only must be true")
    for key in sorted(_POLICY_FALSE_KEYS):
        if policy.get(key) is not False:
            problems.append(f"execution_policy.{key} must be false")

    cases = _mapping_sequence(packet.get("synthetic_read_only_smoke_cases"))
    draft_checks = _mapping_sequence(packet.get("reversible_draft_boundary_checks"))
    refusal_checks = _mapping_sequence(packet.get("refusal_checks"))
    coverage = _mapping_sequence(packet.get("expected_citation_coverage"))
    owners = _mapping_sequence(packet.get("reviewer_owners"))
    attestations = _mapping_sequence(packet.get("no_consumer_execution_attestations"))

    if not cases:
        problems.append("synthetic_read_only_smoke_cases must be a non-empty list")
    if not draft_checks:
        problems.append("reversible_draft_boundary_checks must be a non-empty list")
    if not refusal_checks:
        problems.append("refusal_checks must be a non-empty list")
    if not coverage:
        problems.append("expected_citation_coverage must be a non-empty list")
    if not owners:
        problems.append("reviewer_owners must be a non-empty list")
    if not attestations:
        problems.append("no_consumer_execution_attestations must be a non-empty list")

    owner_ids = {str(owner.get("owner_id")) for owner in owners if owner.get("owner_id")}
    coverage_by_case = {str(item.get("smoke_case_id")): item for item in coverage if item.get("smoke_case_id")}
    refusal_case_ids = {str(item.get("smoke_case_id")) for item in refusal_checks if item.get("smoke_case_id")}

    for index, owner in enumerate(owners):
        if not owner.get("owner_id"):
            problems.append(f"reviewer_owners[{index}] lacks owner_id")
        if not owner.get("role"):
            problems.append(f"reviewer_owners[{index}] lacks role")

    for index, case in enumerate(cases):
        path = f"synthetic_read_only_smoke_cases[{index}]"
        case_id = str(case.get("smoke_case_id") or "")
        if not case_id:
            problems.append(f"{path} lacks smoke_case_id")
        if case.get("no_consumer_execution_attestation") is not True:
            problems.append(f"{path} lacks no-consumer-execution attestation")
        source_evidence_ids = _string_list(case.get("source_evidence_ids"))
        if not source_evidence_ids:
            problems.append(f"{path} lacks source_evidence_ids")
        coverage_item = coverage_by_case.get(case_id)
        if case_id and coverage_item is None:
            problems.append(f"{path} lacks expected citation coverage")
        owner = str(case.get("reviewer_owner") or "")
        if not owner:
            problems.append(f"{path} lacks reviewer_owner")
        elif owner_ids and owner not in owner_ids:
            problems.append(f"{path} reviewer_owner is not declared")
        if _requires_refusal_check(case) and case_id not in refusal_case_ids:
            problems.append(f"{path} lacks refusal check")
        expected = case.get("expected_read_only_answer")
        if not isinstance(expected, Mapping):
            problems.append(f"{path} lacks expected_read_only_answer")
        else:
            cited_ids = _string_list(expected.get("must_cite_source_evidence_ids"))
            if not cited_ids:
                problems.append(f"{path} expected response lacks citations")
            if expected.get("must_remain_read_only") is not True:
                problems.append(f"{path} expected response must remain read-only")
            if coverage_item and coverage_item.get("covers_expected_response") is not True:
                problems.append(f"{path} expected response is not covered by citation coverage")
            if cited_ids and source_evidence_ids and not set(cited_ids).issubset(set(source_evidence_ids)):
                problems.append(f"{path} expected response cites evidence outside source_evidence_ids")

    for index, check in enumerate(draft_checks):
        path = f"reversible_draft_boundary_checks[{index}]"
        _validate_owned_evidenced_check(check, path, owner_ids, problems)
        if not _string_list(check.get("blocked_boundary_actions")):
            problems.append(f"{path} lacks blocked_boundary_actions")

    for index, check in enumerate(refusal_checks):
        path = f"refusal_checks[{index}]"
        _validate_owned_evidenced_check(check, path, owner_ids, problems)
        if not check.get("smoke_case_id"):
            problems.append(f"{path} lacks smoke_case_id")
        if not check.get("expected_refusal_reason"):
            problems.append(f"{path} lacks expected_refusal_reason")
        if not _string_list(check.get("blocked_predicates")):
            problems.append(f"{path} lacks blocked_predicates")

    for index, item in enumerate(coverage):
        if item.get("covers_expected_response") is not True:
            problems.append(f"expected_citation_coverage[{index}] must cover expected response")
        if not _string_list(item.get("required_source_evidence_ids")):
            problems.append(f"expected_citation_coverage[{index}] lacks required_source_evidence_ids")

    for index, attestation in enumerate(attestations):
        if attestation.get("attested") is not True:
            problems.append(f"no_consumer_execution_attestations[{index}] must be attested")
        if not _string_list(attestation.get("prohibited_invocations")):
            problems.append(f"no_consumer_execution_attestations[{index}] lacks prohibited_invocations")

    problems.extend(_recursive_safety_problems(packet))
    return PostPromotionSmokeTestPlanValidationResult(valid=not problems, problems=tuple(_dedupe(problems)))


def assert_valid_post_promotion_smoke_test_plan(packet: Mapping[str, Any]) -> None:
    result = validate_post_promotion_smoke_test_plan(packet)
    if not result.valid:
        raise ValueError("invalid_post_promotion_smoke_test_plan: " + "; ".join(result.problems))


def require_post_promotion_smoke_test_plan(packet: Mapping[str, Any]) -> None:
    assert_valid_post_promotion_smoke_test_plan(packet)


def _validate_owned_evidenced_check(check: Mapping[str, Any], path: str, owner_ids: set[str], problems: list[str]) -> None:
    owner = str(check.get("reviewer_owner") or "")
    if not owner:
        problems.append(f"{path} lacks reviewer_owner")
    elif owner_ids and owner not in owner_ids:
        problems.append(f"{path} reviewer_owner is not declared")
    if not _string_list(check.get("source_evidence_ids")):
        problems.append(f"{path} lacks source_evidence_ids")


def _requires_refusal_check(case: Mapping[str, Any]) -> bool:
    action_class = str(case.get("action_class") or "").lower()
    if action_class in _CONSEQUENTIAL_ACTION_CLASSES:
        return True
    if case.get("refused_consequential_action_response"):
        return True
    return any(_enabled_consequential_control(key.lower(), value) for _, key, value in _walk(case))


def _reviewer_owners(dry_run_packet: Mapping[str, Any], regression_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    owners: dict[str, dict[str, Any]] = {}
    for owner in _mapping_sequence(dry_run_packet.get("reviewer_owners")):
        owner_id = _owner_id(owner.get("owner_id") or owner.get("role"))
        owners[owner_id] = {
            "owner_id": owner_id,
            "role": str(owner.get("role") or owner_id.replace("-", "_")),
            "source": "dry_run_promotion_sequence_packet",
        }
    for owner in _mapping_sequence(regression_plan.get("reviewer_owners")):
        owner_id = _owner_id(owner.get("owner") or owner.get("owner_id"))
        owners.setdefault(
            owner_id,
            {
                "owner_id": owner_id,
                "role": owner_id.replace("-", "_"),
                "source": "agent_consumer_regression_rerun_plan",
            },
        )
    return [owners[key] for key in sorted(owners)] or [{"owner_id": "ppd-release-operator", "role": "ppd_release_operator", "source": "default"}]


def _expected_response_fields(case: Mapping[str, Any]) -> list[str]:
    fields = []
    for key in (
        "expected_read_only_answer",
        "reversible_draft_limits",
        "missing_information_prompts",
        "manual_handoff_prompts",
        "refused_consequential_action_response",
    ):
        if key in case:
            fields.append(key)
    return fields or ["expected_read_only_answer"]


def _default_draft_boundary_check(owner: str) -> dict[str, Any]:
    return {
        "check_id": "reversible-draft-boundary:no-draft-cases-present",
        "smoke_case_id": "post-promotion-smoke:global-read-only-boundary",
        "allowed_preview_only_actions": ["read fixture packet", "summarize cited expectations"],
        "blocked_boundary_actions": ["submit", "upload", "pay", "schedule", "certify"],
        "requires_missing_information_prompts": [],
        "reviewer_owner": owner,
        "source_evidence_ids": ["fixture-read-only-boundary"],
    }


def _recursive_safety_problems(value: Any) -> list[str]:
    problems: list[str] = []
    for path, key, child in _walk(value):
        key_text = key.lower()
        if key_text in _PRIVATE_KEYS and _non_empty(child):
            problems.append(f"private case facts or local private paths are not allowed at {path}")
        if key_text in _LIVE_KEYS and child not in (False, None, "", "not_run", "fixture_only"):
            problems.append(f"live LLM/DevHub/crawler/processor/compiler execution claims are not allowed at {path}")
        if _enabled_consequential_control(key_text, child):
            problems.append(f"enabled consequential controls are not allowed at {path}")
        if isinstance(child, str):
            lowered = child.lower()
            if _LOCAL_PATH_RE.search(child):
                problems.append(f"local private paths are not allowed at {path}")
            if "private case fact" in lowered:
                problems.append(f"private case facts are not allowed at {path}")
            if any(phrase in lowered for phrase in _LIVE_PHRASES):
                problems.append(f"live execution claims are not allowed at {path}")
            if any(phrase in lowered for phrase in _GUARANTEE_PHRASES):
                problems.append(f"legal or permitting outcome guarantees are not allowed at {path}")
    return problems


def _enabled_consequential_control(key_text: str, value: Any) -> bool:
    key_mentions_control = any(word in key_text for word in _CONTROL_WORDS)
    if key_mentions_control and "enabled" in key_text:
        return value not in (False, None, "", "false", "disabled", "not_enabled")
    if key_mentions_control and "disabled" in key_text:
        return value is False or str(value).lower() == "false"
    if key_mentions_control and any(word in key_text for word in ("control", "button", "action")):
        return value is True or str(value).lower() in {"enabled", "active", "available", "allowed"}
    if not isinstance(value, Mapping):
        return False
    label = " ".join(str(value.get(key, "")) for key in ("id", "name", "label", "action", "description", "control", "type"))
    label_mentions_control = any(word in label.lower() for word in _CONTROL_WORDS)
    path_mentions_control = any(word in key_text for word in _CONTROL_KEY_WORDS)
    if not (label_mentions_control or path_mentions_control):
        return False
    enabled = (
        value.get("enabled") is True
        or value.get("disabled") is False
        or value.get("aria_disabled") is False
        or str(value.get("status") or "").lower() in {"enabled", "active", "available", "allowed"}
        or str(value.get("state") or "").lower() in {"enabled", "active", "available", "allowed"}
    )
    return enabled


def _walk(value: Any, path: str = "$", key: str = "") -> list[tuple[str, str, Any]]:
    rows = [(path, key, value)]
    if isinstance(value, Mapping):
        for child_key, child in value.items():
            child_key_text = str(child_key)
            rows.extend(_walk(child, f"{path}.{child_key_text}", child_key_text))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            rows.extend(_walk(child, f"{path}[{index}]", key))
    return rows


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def _nested(value: Mapping[str, Any], key: str, nested_key: str) -> Any:
    nested = value.get(key)
    if isinstance(nested, Mapping):
        return nested.get(nested_key)
    return None


def _owner_id(value: Any) -> str:
    text = str(value or "ppd-release-operator").strip().replace("_", "-")
    return text or "ppd-release-operator"


def _non_empty(value: Any) -> bool:
    if value in (None, False, "", [], {}):
        return False
    if isinstance(value, Mapping):
        return any(_non_empty(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_non_empty(item) for item in value)
    return True


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


__all__ = [
    "PACKET_TYPE",
    "PostPromotionSmokeTestPlanValidationResult",
    "assert_valid_post_promotion_smoke_test_plan",
    "build_post_promotion_smoke_test_plan",
    "require_post_promotion_smoke_test_plan",
    "validate_post_promotion_smoke_test_plan",
]
