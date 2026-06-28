from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from ppd.contracts.processes import ActionGateClassification
from ppd.devhub.action_classifier import decide_action_confirmation
from ppd.devhub.selector_confidence import check_draft_fill_selector_confidence
from ppd.devhub.workflow import DevHubActionKind, DevHubWorkflowAction


REQUIRED_REFUSAL_CATEGORIES = frozenset(
    {
        "low_confidence_selector",
        "upload",
        "submission",
        "payment",
        "certification",
        "cancellation",
        "mfa",
        "captcha",
        "inspection_scheduling",
    }
)

_ACTION_KIND_BY_CATEGORY = {
    "upload": DevHubActionKind.OFFICIAL_UPLOAD,
    "submission": DevHubActionKind.SUBMIT_APPLICATION,
    "payment": DevHubActionKind.PAY_FEE,
    "certification": DevHubActionKind.CERTIFY_ACKNOWLEDGMENT,
    "cancellation": DevHubActionKind.CANCEL_REQUEST,
    "inspection_scheduling": DevHubActionKind.SCHEDULE_INSPECTION,
}

_MANUAL_CHALLENGE_CATEGORIES = frozenset({"mfa", "captcha"})


@dataclass(frozen=True)
class DraftFillPlanValidationResult:
    fixture_id: str
    refused_categories: tuple[str, ...]
    selector_problems: tuple[str, ...]


def validate_playwright_draft_fill_plan_fixture(plan: Mapping[str, Any]) -> DraftFillPlanValidationResult:
    """Validate that a synthetic Playwright draft-fill plan refuses risky defaults.

    The validator is intentionally fixture-only. It does not import Playwright,
    launch a browser, inspect authenticated pages, upload files, submit forms,
    pay fees, schedule inspections, solve MFA, or solve CAPTCHA.
    """

    fixture_id = _required_text(plan, "fixture_id")
    if plan.get("privacy_classification") != "commit_safe_synthetic_fixture":
        raise ValueError("plan must be a commit-safe synthetic fixture")
    if plan.get("live_automation_allowed") is not False:
        raise ValueError("live automation must be disabled for the fixture")
    if plan.get("stores_private_session_artifacts") is not False:
        raise ValueError("fixture must not store private session artifacts")
    if plan.get("default_policy") != "refuse_unless_explicitly_allowed":
        raise ValueError("default_policy must refuse unless explicitly allowed")

    draft_fill_plan = _required_mapping(plan, "draft_fill_plan")
    surface_map = _required_mapping(draft_fill_plan, "selector_confidence_fixture")
    selector_result = check_draft_fill_selector_confidence(dict(surface_map))
    if selector_result.allowed:
        raise ValueError("low_confidence_selector fixture must contain ambiguous or missing selector evidence")

    refusals = _required_sequence(draft_fill_plan, "default_refusals")
    refusal_by_category: dict[str, Mapping[str, Any]] = {}
    for refusal in refusals:
        refusal_map = _as_mapping(refusal, "default_refusals[]")
        category = _required_text(refusal_map, "category")
        if category in refusal_by_category:
            raise ValueError(f"duplicate refusal category: {category}")
        refusal_by_category[category] = refusal_map

    missing = sorted(REQUIRED_REFUSAL_CATEGORIES.difference(refusal_by_category))
    if missing:
        raise ValueError(f"missing required refusal categories: {', '.join(missing)}")

    _validate_low_confidence_selector_refusal(refusal_by_category["low_confidence_selector"], selector_result.problems)

    for category, action_kind in _ACTION_KIND_BY_CATEGORY.items():
        _validate_action_refusal(category, action_kind, refusal_by_category[category])

    for category in _MANUAL_CHALLENGE_CATEGORIES:
        _validate_manual_challenge_refusal(category, refusal_by_category[category])

    return DraftFillPlanValidationResult(
        fixture_id=fixture_id,
        refused_categories=tuple(sorted(refusal_by_category)),
        selector_problems=selector_result.problems,
    )


def _validate_low_confidence_selector_refusal(refusal: Mapping[str, Any], selector_problems: tuple[str, ...]) -> None:
    _require_default_refusal(refusal, "low_confidence_selector")
    if not selector_problems:
        raise ValueError("low_confidence_selector refusal must be backed by selector problems")
    if refusal.get("requires_selector_confidence") != "unambiguous_label_heading_and_route":
        raise ValueError("low_confidence_selector must require unambiguous label, heading, and route evidence")


def _validate_action_refusal(category: str, action_kind: DevHubActionKind, refusal: Mapping[str, Any]) -> None:
    _require_default_refusal(refusal, category)
    if refusal.get("action_kind") != action_kind.value:
        raise ValueError(f"{category} refusal must use action_kind {action_kind.value}")
    if refusal.get("may_execute_without_user") is not False:
        raise ValueError(f"{category} must not execute without the user")
    if refusal.get("requires_user_attendance") is not True:
        raise ValueError(f"{category} must require user attendance")
    if refusal.get("requires_exact_confirmation") is not True:
        raise ValueError(f"{category} must require exact confirmation")

    action = DevHubWorkflowAction(
        id=f"fixture-{category}",
        label=category.replace("_", " ").title(),
        kind=action_kind,
        confirmation_text=str(refusal.get("confirmation_text") or "").strip() or None,
        consequence_summary="Synthetic draft-fill refusal validation; no browser automation is performed.",
    )
    decision = decide_action_confirmation(action, None)
    if decision.allowed:
        raise ValueError(f"{category} must be refused by default without exact confirmation")
    if decision.classification not in {
        ActionGateClassification.POTENTIALLY_CONSEQUENTIAL,
        ActionGateClassification.FINANCIAL,
    }:
        raise ValueError(f"{category} must classify as consequential or financial")


def _validate_manual_challenge_refusal(category: str, refusal: Mapping[str, Any]) -> None:
    _require_default_refusal(refusal, category)
    if refusal.get("automation_supported") is not False:
        raise ValueError(f"{category} automation must be unsupported")
    if refusal.get("manual_handoff_required") is not True:
        raise ValueError(f"{category} must require manual handoff")
    if refusal.get("may_execute_without_user") is not False:
        raise ValueError(f"{category} must not execute without the user")


def _require_default_refusal(refusal: Mapping[str, Any], category: str) -> None:
    if refusal.get("category") != category:
        raise ValueError(f"refusal category mismatch for {category}")
    if refusal.get("default_allowed") is not False:
        raise ValueError(f"{category} must set default_allowed to false")
    if refusal.get("default_decision") != "refuse":
        raise ValueError(f"{category} must default to refuse")
    reason = str(refusal.get("reason") or "").lower()
    if "refuse" not in reason and "manual" not in reason and "blocked" not in reason:
        raise ValueError(f"{category} refusal must include a refusal reason")


def _required_mapping(container: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    return _as_mapping(container.get(key), key)


def _as_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be an object")
    return value


def _required_sequence(container: Mapping[str, Any], key: str) -> tuple[Any, ...]:
    value = container.get(key)
    if isinstance(value, (str, bytes)) or not isinstance(value, list):
        raise ValueError(f"{key} must be a non-empty list")
    if not value:
        raise ValueError(f"{key} must be a non-empty list")
    return tuple(value)


def _required_text(container: Mapping[str, Any], key: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value.strip()
