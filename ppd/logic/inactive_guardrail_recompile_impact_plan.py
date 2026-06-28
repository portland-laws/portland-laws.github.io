"""Validation for inactive guardrail recompile impact plan v1.

The validator is intentionally side-effect free. It accepts already-loaded plan
objects, reports deterministic errors, and never performs crawl, DevHub, or
promotion work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


REQUIRED_NON_EMPTY_SECTIONS = (
    "process_model_delta_refs",
    "inactive_guardrail_patch_placeholders",
    "deterministic_predicate_impacts",
    "deontic_rule_impacts",
    "temporal_rule_impacts",
    "reversible_action_predicate_impacts",
    "exact_confirmation_predicate_impacts",
    "refused_action_predicate_impacts",
    "agent_facing_explanation_impacts",
    "reviewer_holds",
    "rollback_notes",
    "validation_commands",
)

FORBIDDEN_KEY_FRAGMENTS = (
    "auth_state",
    "captcha",
    "cookie",
    "credential",
    "downloaded_artifact",
    "har",
    "live_crawl",
    "password",
    "private_artifact",
    "raw_artifact",
    "raw_crawl",
    "session_file",
    "trace",
)

FORBIDDEN_TEXT_CLAIMS = (
    "active mutation",
    "actively mutates",
    "automated devhub",
    "completed official action",
    "devhub verified",
    "downloaded artifact",
    "final submission complete",
    "guaranteed approval",
    "guaranteed permit",
    "legal advice",
    "legal guarantee",
    "live crawl",
    "official action complete",
    "officially submitted",
    "permitting guarantee",
    "private artifact",
    "promote to production",
    "promoted guardrail",
    "raw artifact",
    "raw crawl",
    "scraped devhub",
)

ACTIVE_MUTATION_KEYS = (
    "active",
    "active_mutation",
    "active_mutation_enabled",
    "apply_patch",
    "auto_promote",
    "enabled",
    "execute_actions",
    "mutate_active_guardrails",
    "promotion_enabled",
    "write_to_devhub",
)


@dataclass(frozen=True)
class ImpactPlanFinding:
    """A deterministic validation finding for an impact plan."""

    path: str
    message: str

    def render(self) -> str:
        return f"{self.path}: {self.message}"


class InactiveGuardrailRecompileImpactPlanError(ValueError):
    """Raised when an inactive guardrail recompile impact plan is invalid."""


def validate_inactive_guardrail_recompile_impact_plan_v1(
    plan: Mapping[str, Any],
) -> list[ImpactPlanFinding]:
    """Return all validation findings for an inactive recompile impact plan.

    A valid plan must be explicitly versioned, explicitly inactive, contain all
    required impact sections, and avoid claims or flags that imply live crawl,
    DevHub automation, promotion, official-action completion, guarantees, raw or
    private artifacts, or active mutation.
    """

    findings: list[ImpactPlanFinding] = []

    if not isinstance(plan, Mapping):
        return [ImpactPlanFinding("$", "plan must be a mapping")]

    version = plan.get("version")
    if version != "inactive_guardrail_recompile_impact_plan_v1":
        findings.append(
            ImpactPlanFinding(
                "version",
                "must equal inactive_guardrail_recompile_impact_plan_v1",
            )
        )

    if plan.get("status") != "inactive":
        findings.append(ImpactPlanFinding("status", "must be inactive"))

    for key in REQUIRED_NON_EMPTY_SECTIONS:
        value = plan.get(key)
        if _is_empty(value):
            findings.append(ImpactPlanFinding(key, "must be present and non-empty"))

    findings.extend(_scan_for_forbidden_content(plan, "$"))
    return findings


def assert_valid_inactive_guardrail_recompile_impact_plan_v1(
    plan: Mapping[str, Any],
) -> None:
    """Raise a stable error message if the plan is invalid."""

    findings = validate_inactive_guardrail_recompile_impact_plan_v1(plan)
    if findings:
        rendered = "; ".join(finding.render() for finding in findings)
        raise InactiveGuardrailRecompileImpactPlanError(rendered)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return len(value) == 0
    return False


def _scan_for_forbidden_content(value: Any, path: str) -> list[ImpactPlanFinding]:
    findings: list[ImpactPlanFinding] = []

    if isinstance(value, Mapping):
        for raw_key, raw_child in value.items():
            key = str(raw_key)
            normalized_key = _normalize(key)
            child_path = f"{path}.{key}" if path != "$" else key

            for fragment in FORBIDDEN_KEY_FRAGMENTS:
                if fragment in normalized_key:
                    findings.append(
                        ImpactPlanFinding(child_path, f"forbidden artifact or live-operation key: {fragment}")
                    )

            if normalized_key in ACTIVE_MUTATION_KEYS and _truthy(raw_child):
                findings.append(
                    ImpactPlanFinding(child_path, "active mutation or promotion flag must not be true")
                )

            findings.extend(_scan_for_forbidden_content(raw_child, child_path))
        return findings

    if isinstance(value, str):
        normalized_value = _normalize(value)
        for claim in FORBIDDEN_TEXT_CLAIMS:
            if claim in normalized_value:
                findings.append(ImpactPlanFinding(path, f"forbidden claim: {claim}"))
        return findings

    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        for index, item in enumerate(value):
            findings.extend(_scan_for_forbidden_content(item, f"{path}[{index}]"))

    return findings


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return bool(value)


def _normalize(value: str) -> str:
    return " ".join(value.replace("-", "_").replace(".", "_").lower().split())
