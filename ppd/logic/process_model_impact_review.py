"""Validation for PP&D process-model impact review packets.

The validator is intentionally side-effect free. Impact review packets may describe
findings, but they must not smuggle in private case facts, live execution claims,
outcome guarantees, enabled consequential controls, or mutation flags.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ImpactReviewIssue:
    """A single deterministic validation issue."""

    code: str
    message: str
    path: str


@dataclass(frozen=True)
class ImpactReviewValidationResult:
    """Validation result for an impact review packet."""

    valid: bool
    issues: tuple[ImpactReviewIssue, ...]

    def codes(self) -> tuple[str, ...]:
        return tuple(issue.code for issue in self.issues)


class ImpactReviewValidationError(ValueError):
    """Raised when an impact review packet fails validation."""

    def __init__(self, issues: Sequence[ImpactReviewIssue]) -> None:
        self.issues = tuple(issues)
        codes = ", ".join(issue.code for issue in self.issues)
        super().__init__(f"process-model impact review packet failed validation: {codes}")


_CITATION_FIELDS = (
    "citations",
    "citation_ids",
    "citation_spans",
    "evidence_ids",
    "source_evidence_ids",
    "source_ids",
)

_STAGE_FIELDS = ("process_stage", "process_stage_id", "stage", "stage_id")

_PRIVATE_KEY_PATTERNS = (
    "private_case_fact",
    "private_case_facts",
    "case_fact",
    "case_facts",
    "applicant_name",
    "owner_name",
    "tenant_name",
    "phone",
    "email",
    "payment_detail",
    "credential",
    "cookie",
    "auth_state",
    "session_state",
)

_LIVE_EXECUTION_FIELDS = (
    "live_execution_claims",
    "live_llm_execution",
    "live_devhub_execution",
    "live_crawler_execution",
    "live_processor_execution",
    "executed_live_llm",
    "executed_live_devhub",
    "executed_live_crawler",
    "executed_live_processor",
    "ran_live_llm",
    "ran_live_devhub",
    "ran_live_crawler",
    "ran_live_processor",
)

_MUTATION_FLAG_FIELDS = (
    "active_process_mutation",
    "active_guardrail_mutation",
    "active_prompt_mutation",
    "active_release_state_mutation",
    "process_mutation_enabled",
    "guardrail_mutation_enabled",
    "prompt_mutation_enabled",
    "release_state_mutation_enabled",
    "mutate_process_model",
    "mutate_guardrails",
    "mutate_prompts",
    "mutate_release_state",
)

_LIVE_EXECUTION_RE = re.compile(
    r"\b(?:ran|run|executed|invoked|called|crawled|processed)\s+"
    r"(?:a\s+)?(?:live\s+)?(?:llm|devhub|crawler|processor)\b|"
    r"\b(?:live|real)\s+(?:llm|devhub|crawler|processor)\s+"
    r"(?:run|execution|crawl|processor|processing|invocation)\b",
    re.IGNORECASE,
)

_OUTCOME_GUARANTEE_RE = re.compile(
    r"\bguarantee(?:d|s)?\b|"
    r"\bwill\s+(?:be\s+)?(?:approved|issued|accepted|permitted)\b|"
    r"\b(?:approval|issuance|permit)\s+(?:is\s+)?(?:assured|guaranteed)\b|"
    r"\blegal(?:ly)?\s+(?:safe|compliant|valid)\b",
    re.IGNORECASE,
)

_NEGATED_LIVE_RE = re.compile(r"\b(?:no|not|without)\s+live\b", re.IGNORECASE)


def validate_process_model_impact_review_packet(
    packet: Mapping[str, Any],
) -> ImpactReviewValidationResult:
    """Validate an impact review packet without mutating it or calling services."""

    issues: list[ImpactReviewIssue] = []
    if not isinstance(packet, Mapping):
        issue = ImpactReviewIssue(
            code="invalid_packet_type",
            message="Impact review packet must be a mapping.",
            path="$",
        )
        return ImpactReviewValidationResult(valid=False, issues=(issue,))

    issues.extend(_validate_process_stage_claims(packet))
    issues.extend(_validate_required_ids(packet))
    issues.extend(_validate_blocked_action_carryovers(packet))
    issues.extend(_validate_reviewer_owners(packet))
    issues.extend(_scan_for_private_case_facts(packet))
    issues.extend(_scan_for_live_execution_claims(packet))
    issues.extend(_scan_for_outcome_guarantees(packet))
    issues.extend(_scan_for_enabled_consequential_controls(packet))
    issues.extend(_scan_for_active_mutation_flags(packet))

    return ImpactReviewValidationResult(valid=not issues, issues=tuple(issues))


def assert_valid_process_model_impact_review_packet(packet: Mapping[str, Any]) -> None:
    """Raise ImpactReviewValidationError if the packet is invalid."""

    result = validate_process_model_impact_review_packet(packet)
    if not result.valid:
        raise ImpactReviewValidationError(result.issues)


def _validate_process_stage_claims(packet: Mapping[str, Any]) -> list[ImpactReviewIssue]:
    issues: list[ImpactReviewIssue] = []
    for path, claim in _iter_process_stage_claims(packet):
        if not _has_any_nonempty_field(claim, _CITATION_FIELDS):
            issues.append(
                ImpactReviewIssue(
                    code="uncited_process_stage_impact_claim",
                    message="Process-stage impact claims must include source citations or evidence IDs.",
                    path=path,
                )
            )
    return issues


def _validate_required_ids(packet: Mapping[str, Any]) -> list[ImpactReviewIssue]:
    issues: list[ImpactReviewIssue] = []
    if not _first_nonempty(packet, ("affected_process_ids", "process_ids", "affected_processes")):
        issues.append(
            ImpactReviewIssue(
                code="missing_affected_process_ids",
                message="Impact review packets must identify affected process IDs.",
                path="$.affected_process_ids",
            )
        )
    if not _first_nonempty(packet, ("affected_guardrail_ids", "guardrail_ids", "affected_guardrails")):
        issues.append(
            ImpactReviewIssue(
                code="missing_affected_guardrail_ids",
                message="Impact review packets must identify affected guardrail IDs.",
                path="$.affected_guardrail_ids",
            )
        )
    return issues


def _validate_blocked_action_carryovers(packet: Mapping[str, Any]) -> list[ImpactReviewIssue]:
    carryovers = _first_nonempty(packet, ("blocked_action_carryovers", "blocked_actions", "carried_over_blocked_actions"))
    if carryovers:
        return []
    return [
        ImpactReviewIssue(
            code="missing_blocked_action_carryovers",
            message="Impact review packets must carry over blocked actions from the source guardrails.",
            path="$.blocked_action_carryovers",
        )
    ]


def _validate_reviewer_owners(packet: Mapping[str, Any]) -> list[ImpactReviewIssue]:
    owners = _first_nonempty(packet, ("reviewer_owners", "reviewers", "review_owner_ids"))
    if owners:
        return []
    return [
        ImpactReviewIssue(
            code="missing_reviewer_owners",
            message="Impact review packets must identify reviewer owners.",
            path="$.reviewer_owners",
        )
    ]


def _scan_for_private_case_facts(value: Any, path: str = "$") -> list[ImpactReviewIssue]:
    issues: list[ImpactReviewIssue] = []
    if isinstance(value, Mapping):
        privacy = str(value.get("privacy_classification", "")).lower()
        if privacy in {"private", "confidential", "restricted", "case_private"}:
            issues.append(
                ImpactReviewIssue(
                    code="private_case_facts_present",
                    message="Impact review packets must not contain private or case-specific facts.",
                    path=f"{path}.privacy_classification",
                )
            )
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = f"{path}.{key_text}"
            if any(pattern in key_lower for pattern in _PRIVATE_KEY_PATTERNS):
                issues.append(
                    ImpactReviewIssue(
                        code="private_case_facts_present",
                        message="Impact review packets must not contain private or case-specific facts.",
                        path=child_path,
                    )
                )
            issues.extend(_scan_for_private_case_facts(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_scan_for_private_case_facts(child, f"{path}[{index}]"))
    return issues


def _scan_for_live_execution_claims(value: Any, path: str = "$") -> list[ImpactReviewIssue]:
    issues: list[ImpactReviewIssue] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in _LIVE_EXECUTION_FIELDS and _truthy_or_nonempty(child):
                issues.append(
                    ImpactReviewIssue(
                        code="live_execution_claim_present",
                        message="Impact review packets must not claim live LLM, DevHub, crawler, or processor execution.",
                        path=child_path,
                    )
                )
            issues.extend(_scan_for_live_execution_claims(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_scan_for_live_execution_claims(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        if _LIVE_EXECUTION_RE.search(value) and not _NEGATED_LIVE_RE.search(value):
            issues.append(
                ImpactReviewIssue(
                    code="live_execution_claim_present",
                    message="Impact review packets must not claim live LLM, DevHub, crawler, or processor execution.",
                    path=path,
                )
            )
    return issues


def _scan_for_outcome_guarantees(value: Any, path: str = "$") -> list[ImpactReviewIssue]:
    issues: list[ImpactReviewIssue] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in {"outcome_guarantees", "legal_guarantees", "permitting_guarantees"} and _truthy_or_nonempty(child):
                issues.append(
                    ImpactReviewIssue(
                        code="outcome_guarantee_present",
                        message="Impact review packets must not include legal or permitting outcome guarantees.",
                        path=child_path,
                    )
                )
            issues.extend(_scan_for_outcome_guarantees(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_scan_for_outcome_guarantees(child, f"{path}[{index}]"))
    elif isinstance(value, str) and _OUTCOME_GUARANTEE_RE.search(value):
        issues.append(
            ImpactReviewIssue(
                code="outcome_guarantee_present",
                message="Impact review packets must not include legal or permitting outcome guarantees.",
                path=path,
            )
        )
    return issues


def _scan_for_enabled_consequential_controls(value: Any, path: str = "$") -> list[ImpactReviewIssue]:
    issues: list[ImpactReviewIssue] = []
    if isinstance(value, Mapping):
        if _mapping_enables_consequential_control(value):
            issues.append(
                ImpactReviewIssue(
                    code="enabled_consequential_control",
                    message="Impact review packets must not enable consequential official or financial controls.",
                    path=path,
                )
            )
        for key, child in value.items():
            issues.extend(_scan_for_enabled_consequential_controls(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_scan_for_enabled_consequential_controls(child, f"{path}[{index}]"))
    return issues


def _scan_for_active_mutation_flags(value: Any, path: str = "$") -> list[ImpactReviewIssue]:
    issues: list[ImpactReviewIssue] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = f"{path}.{key_text}"
            if key_lower in _MUTATION_FLAG_FIELDS and _truthy_or_nonempty(child):
                issues.append(
                    ImpactReviewIssue(
                        code="active_mutation_flag",
                        message="Impact review packets must not activate process, guardrail, prompt, or release-state mutation flags.",
                        path=child_path,
                    )
                )
            if key_lower == "mutation_flags" and isinstance(child, Mapping):
                for flag_key, flag_value in child.items():
                    if _truthy_or_nonempty(flag_value):
                        issues.append(
                            ImpactReviewIssue(
                                code="active_mutation_flag",
                                message="Impact review packets must not activate process, guardrail, prompt, or release-state mutation flags.",
                                path=f"{child_path}.{flag_key}",
                            )
                        )
            issues.extend(_scan_for_active_mutation_flags(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            issues.extend(_scan_for_active_mutation_flags(child, f"{path}[{index}]"))
    return issues


def _iter_process_stage_claims(packet: Mapping[str, Any]) -> Iterable[tuple[str, Mapping[str, Any]]]:
    for field in ("process_stage_impact_claims", "stage_impact_claims", "impact_claims", "claims", "stage_impacts"):
        for index, claim in enumerate(_as_list(packet.get(field))):
            if isinstance(claim, Mapping) and _is_process_stage_claim(claim):
                yield f"$.{field}[{index}]", claim


def _is_process_stage_claim(claim: Mapping[str, Any]) -> bool:
    if _has_any_nonempty_field(claim, _STAGE_FIELDS):
        return True
    claim_type = str(claim.get("claim_type", claim.get("type", ""))).lower()
    return claim_type in {"process_stage_impact", "stage_impact", "process-stage-impact"}


def _mapping_enables_consequential_control(value: Mapping[str, Any]) -> bool:
    enabled = any(_truthy_or_nonempty(value.get(key)) for key in ("enabled", "is_enabled", "active"))
    if not enabled:
        return False
    category = str(value.get("category", value.get("action_category", value.get("control_category", "")))).lower()
    kind = str(value.get("kind", value.get("type", value.get("control_type", "")))).lower()
    consequential = _truthy_or_nonempty(value.get("consequential"))
    return consequential or category in {"consequential", "official", "financial"} or kind in {"consequential", "official", "financial"}


def _first_nonempty(packet: Mapping[str, Any], fields: Sequence[str]) -> Any:
    for field in fields:
        value = packet.get(field)
        if _truthy_or_nonempty(value):
            return value
    affected = packet.get("affected")
    if isinstance(affected, Mapping):
        for field in fields:
            value = affected.get(field)
            if _truthy_or_nonempty(value):
                return value
    return None


def _has_any_nonempty_field(value: Mapping[str, Any], fields: Sequence[str]) -> bool:
    return any(_truthy_or_nonempty(value.get(field)) for field in fields)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, (str, bytes)):
        return [value] if value else []
    return [value]


def _truthy_or_nonempty(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return bool(value)
