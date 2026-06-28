"""Validation for safe-action freshness regression packets.

The validator is intentionally side-effect free. It checks committed regression
fixtures before they can be used as evidence for agent action behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping


_LOCAL_PATH_PATTERNS = (
    re.compile(r"\b/home/[^\s\"']+"),
    re.compile(r"\b/Users/[^\s\"']+"),
    re.compile(r"\b(?:[A-Za-z]:\\\\)[^\s\"']+"),
    re.compile(r"\bfile://[^\s\"']+"),
)

_PRIVATE_FACT_KEYS = {
    "private_case_fact",
    "private_case_facts",
    "case_fact_private",
    "private_fact",
    "private_facts",
    "applicant_name",
    "applicant_email",
    "applicant_phone",
    "owner_name",
    "owner_email",
    "owner_phone",
    "street_address",
    "site_address",
    "mailing_address",
    "parcel_owner",
    "tax_account",
    "tax_account_id",
    "permit_number_private",
}

_RAW_AUTH_KEYS = {
    "raw_authenticated_value",
    "raw_authenticated_values",
    "authenticated_value_raw",
    "authenticated_values",
    "auth_state",
    "browser_state",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "csrf_token",
    "devhub_raw_value",
    "har",
    "password",
    "session",
    "session_state",
    "trace",
}

_LIVE_EXECUTION_KEYS = {
    "live_execution_claim",
    "live_execution_claims",
    "live_llm_execution",
    "live_devhub_execution",
    "live_crawler_execution",
    "live_processor_execution",
    "llm_executed_live",
    "devhub_executed_live",
    "crawler_executed_live",
    "processor_executed_live",
    "ran_live_llm",
    "ran_devhub",
    "ran_crawler",
    "ran_processor",
}

_MUTATION_FLAGS = {
    "prompt_mutation_enabled",
    "active_prompt_mutation",
    "guardrail_mutation_enabled",
    "active_guardrail_mutation",
    "surface_registry_mutation_enabled",
    "active_surface_registry_mutation",
    "agent_state_mutation_enabled",
    "active_agent_state_mutation",
}

_CONSEQUENTIAL_CONTROL_KEYS = {
    "consequential_controls_enabled",
    "enabled_consequential_controls",
    "submit_enabled",
    "payment_enabled",
    "upload_enabled",
    "certification_enabled",
    "schedule_enabled",
    "cancel_enabled",
    "withdraw_enabled",
}

_CONSEQUENTIAL_ACTION_WORDS = {
    "submit",
    "certify",
    "upload",
    "payment",
    "pay",
    "schedule",
    "cancel",
    "withdraw",
    "purchase",
    "reactivate",
    "extend",
}

_OUTCOME_GUARANTEE_RE = re.compile(
    r"\b(guarantee[sd]?|will\s+(?:be\s+)?(?:approve|approved|issued|pass|accepted)|"
    r"assure[sd]?\s+(?:approval|issuance|acceptance)|permit\s+will\s+be\s+approved|"
    r"legal\s+outcome\s+is\s+guaranteed)\b",
    re.IGNORECASE,
)

_STALE_EVIDENCE_KEYS = {"stale_evidence", "stale_evidence_ids", "stale_sources"}
_CITATION_KEYS = {"citation", "citations", "source_evidence_id", "source_evidence_ids", "evidence_citations"}
_PROMPT_KEYS = {"expected_prompt", "expected_prompts", "expected_question", "expected_questions"}
_REFUSAL_KEYS = {"expected_refusal", "expected_refusals", "expected_block", "expected_blocks"}
_REVIEWER_OWNER_KEYS = {"reviewer_owner", "reviewer_owners", "owner", "owners"}


@dataclass(frozen=True)
class ValidationIssue:
    """A deterministic validation failure for a regression packet."""

    code: str
    path: str
    message: str


def validate_safe_action_freshness_packet(packet: Mapping[str, Any]) -> list[ValidationIssue]:
    """Return validation issues for an agent safe-action freshness packet."""

    issues: list[ValidationIssue] = []
    if not isinstance(packet, Mapping):
        return [ValidationIssue("packet_not_mapping", "$", "packet must be a JSON object")]

    _validate_required_packet_metadata(packet, issues)
    _scan_node(packet, "$", issues)

    scenarios = _scenario_nodes(packet)
    for index, scenario in enumerate(scenarios):
        path = f"$.scenarios[{index}]"
        _validate_scenario(path, scenario, issues)

    return issues


def assert_valid_safe_action_freshness_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a packet contains any validation issue."""

    issues = validate_safe_action_freshness_packet(packet)
    if issues:
        detail = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in issues)
        raise ValueError(detail)


def _validate_required_packet_metadata(packet: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    if not _has_any(packet, _REVIEWER_OWNER_KEYS):
        issues.append(
            ValidationIssue(
                "missing_reviewer_owner",
                "$",
                "packet must name a reviewer owner for accountable fixture maintenance",
            )
        )

    if not _has_any(packet, _PROMPT_KEYS | _REFUSAL_KEYS):
        issues.append(
            ValidationIssue(
                "missing_expected_prompt_or_refusal",
                "$",
                "packet must include at least one expected prompt or refusal",
            )
        )


def _validate_scenario(path: str, scenario: Mapping[str, Any], issues: list[ValidationIssue]) -> None:
    if not _has_any(scenario, _PROMPT_KEYS | _REFUSAL_KEYS):
        issues.append(
            ValidationIssue(
                "missing_expected_prompt_or_refusal",
                path,
                "scenario must declare the expected prompt or refusal",
            )
        )

    if _has_any(scenario, _STALE_EVIDENCE_KEYS):
        stale_value = _first_value(scenario, _STALE_EVIDENCE_KEYS)
        if _is_present(stale_value) and not _has_any(scenario, _CITATION_KEYS):
            issues.append(
                ValidationIssue(
                    "uncited_stale_evidence",
                    path,
                    "stale evidence scenarios must cite the source evidence being treated as stale",
                )
            )

    blocked_actions = scenario.get("blocked_actions")
    if isinstance(blocked_actions, list):
        for index, blocked_action in enumerate(blocked_actions):
            action_path = f"{path}.blocked_actions[{index}]"
            if not isinstance(blocked_action, Mapping):
                issues.append(
                    ValidationIssue(
                        "missing_blocked_action_explanation",
                        action_path,
                        "blocked action entries must be objects with explanations",
                    )
                )
                continue
            explanation = blocked_action.get("explanation") or blocked_action.get("blocked_explanation")
            if not _is_non_empty_text(explanation):
                issues.append(
                    ValidationIssue(
                        "missing_blocked_action_explanation",
                        action_path,
                        "blocked action must include a non-empty explanation",
                    )
                )


def _scan_node(node: Any, path: str, issues: list[ValidationIssue]) -> None:
    if isinstance(node, Mapping):
        for raw_key, value in node.items():
            key = str(raw_key)
            normalized_key = _normalize_key(key)
            child_path = f"{path}.{key}"

            if normalized_key in _PRIVATE_FACT_KEYS:
                issues.append(
                    ValidationIssue(
                        "private_case_fact",
                        child_path,
                        "regression packets must not contain private case facts",
                    )
                )

            if normalized_key in _RAW_AUTH_KEYS:
                issues.append(
                    ValidationIssue(
                        "raw_authenticated_value",
                        child_path,
                        "regression packets must not contain raw authenticated values or browser state",
                    )
                )

            if normalized_key in _LIVE_EXECUTION_KEYS and _is_enabled_or_present(value):
                issues.append(
                    ValidationIssue(
                        "live_execution_claim",
                        child_path,
                        "regression packets must not claim live LLM, DevHub, crawler, or processor execution",
                    )
                )

            if normalized_key in _MUTATION_FLAGS and bool(value):
                issues.append(
                    ValidationIssue(
                        "active_mutation_flag",
                        child_path,
                        "prompt, guardrail, surface-registry, and agent-state mutation flags must be inactive",
                    )
                )

            if normalized_key in _CONSEQUENTIAL_CONTROL_KEYS and _is_enabled_or_present(value):
                issues.append(
                    ValidationIssue(
                        "enabled_consequential_control",
                        child_path,
                        "consequential controls must not be enabled in safe-action freshness packets",
                    )
                )

            if normalized_key == "privacy_classification" and str(value).lower() in {"private", "confidential", "restricted"}:
                issues.append(
                    ValidationIssue(
                        "private_case_fact",
                        child_path,
                        "private, confidential, or restricted fixture data is not allowed",
                    )
                )

            if _contains_local_private_path(value):
                issues.append(
                    ValidationIssue(
                        "local_private_path",
                        child_path,
                        "regression packets must not contain local private filesystem paths",
                    )
                )

            if _contains_outcome_guarantee(value):
                issues.append(
                    ValidationIssue(
                        "outcome_guarantee",
                        child_path,
                        "regression packets must not guarantee legal, permitting, approval, issuance, or acceptance outcomes",
                    )
                )

            _scan_node(value, child_path, issues)
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _scan_node(value, f"{path}[{index}]", issues)
    elif isinstance(node, str):
        if _contains_local_private_path(node):
            issues.append(
                ValidationIssue(
                    "local_private_path",
                    path,
                    "regression packets must not contain local private filesystem paths",
                )
            )
        if _contains_outcome_guarantee(node):
            issues.append(
                ValidationIssue(
                    "outcome_guarantee",
                    path,
                    "regression packets must not guarantee legal, permitting, approval, issuance, or acceptance outcomes",
                )
            )


def _scenario_nodes(packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    scenarios = packet.get("scenarios")
    if isinstance(scenarios, list):
        return [scenario for scenario in scenarios if isinstance(scenario, Mapping)]
    if any(key in packet for key in _STALE_EVIDENCE_KEYS | _PROMPT_KEYS | _REFUSAL_KEYS):
        return [packet]
    return []


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")


def _has_any(mapping: Mapping[str, Any], keys: Iterable[str]) -> bool:
    normalized = {_normalize_key(str(key)): value for key, value in mapping.items()}
    return any(_is_present(normalized.get(key)) for key in keys)


def _first_value(mapping: Mapping[str, Any], keys: Iterable[str]) -> Any:
    normalized = {_normalize_key(str(key)): value for key, value in mapping.items()}
    for key in keys:
        if key in normalized:
            return normalized[key]
    return None


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _is_non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_enabled_or_present(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _is_present(value)


def _contains_local_private_path(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return any(pattern.search(value) for pattern in _LOCAL_PATH_PATTERNS)


def _contains_outcome_guarantee(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return bool(_OUTCOME_GUARANTEE_RE.search(value))


def consequential_action_words() -> set[str]:
    """Return the action vocabulary treated as consequential by this validator."""

    return set(_CONSEQUENTIAL_ACTION_WORDS)
