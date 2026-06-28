from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.devhub.playwright_draft_fill_plan_validation import (
    REQUIRED_REFUSAL_CATEGORIES,
    validate_playwright_draft_fill_plan_fixture,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "playwright_draft_fill_default_refusals.json"


def load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _refusal(plan: dict[str, object], category: str) -> dict[str, object]:
    draft_fill_plan = plan["draft_fill_plan"]
    assert isinstance(draft_fill_plan, dict)
    refusals = draft_fill_plan["default_refusals"]
    assert isinstance(refusals, list)
    for item in refusals:
        assert isinstance(item, dict)
        if item.get("category") == category:
            return item
    raise AssertionError(f"missing refusal category {category}")


def test_playwright_draft_fill_plan_fixture_refuses_required_categories_by_default() -> None:
    plan = load_fixture()

    result = validate_playwright_draft_fill_plan_fixture(plan)

    assert result.fixture_id == "devhub-playwright-draft-fill-default-refusals-001"
    assert set(result.refused_categories) == REQUIRED_REFUSAL_CATEGORIES
    assert "ambiguous label evidence: project name" in result.selector_problems
    assert "ambiguous heading evidence: permit draft" in result.selector_problems
    assert "ambiguous route evidence: /permits/draft" in result.selector_problems


def test_fixture_is_commit_safe_and_does_not_require_browser_artifacts() -> None:
    plan = load_fixture()
    draft_fill_plan = plan["draft_fill_plan"]
    assert isinstance(draft_fill_plan, dict)

    assert plan["privacy_classification"] == "commit_safe_synthetic_fixture"
    assert plan["live_automation_allowed"] is False
    assert plan["stores_private_session_artifacts"] is False
    assert draft_fill_plan["playwright_import_required"] is False
    assert draft_fill_plan["browser_launch_required"] is False


def test_upload_submission_payment_certification_cancellation_and_scheduling_are_not_allowed_without_user() -> None:
    plan = load_fixture()

    for category in (
        "upload",
        "submission",
        "payment",
        "certification",
        "cancellation",
        "inspection_scheduling",
    ):
        item = _refusal(plan, category)
        assert item["default_allowed"] is False
        assert item["default_decision"] == "refuse"
        assert item["may_execute_without_user"] is False
        assert item["requires_user_attendance"] is True
        assert item["requires_exact_confirmation"] is True
        assert str(item["confirmation_text"]).startswith("I confirm I am present and authorize: ")


def test_mfa_and_captcha_require_manual_handoff() -> None:
    plan = load_fixture()

    for category in ("mfa", "captcha"):
        item = _refusal(plan, category)
        assert item["default_allowed"] is False
        assert item["default_decision"] == "refuse"
        assert item["automation_supported"] is False
        assert item["manual_handoff_required"] is True
        assert item["may_execute_without_user"] is False


def test_validation_rejects_missing_required_refusal_category() -> None:
    plan = load_fixture()
    mutated = copy.deepcopy(plan)
    draft_fill_plan = mutated["draft_fill_plan"]
    assert isinstance(draft_fill_plan, dict)
    refusals = draft_fill_plan["default_refusals"]
    assert isinstance(refusals, list)
    draft_fill_plan["default_refusals"] = [item for item in refusals if item.get("category") != "captcha"]

    with pytest.raises(ValueError, match="missing required refusal categories: captcha"):
        validate_playwright_draft_fill_plan_fixture(mutated)


def test_validation_rejects_low_confidence_selector_when_not_refused() -> None:
    plan = load_fixture()
    mutated = copy.deepcopy(plan)
    item = _refusal(mutated, "low_confidence_selector")
    item["default_allowed"] = True

    with pytest.raises(ValueError, match="low_confidence_selector must set default_allowed to false"):
        validate_playwright_draft_fill_plan_fixture(mutated)


def test_validation_rejects_consequential_action_allowed_by_default() -> None:
    plan = load_fixture()
    mutated = copy.deepcopy(plan)
    item = _refusal(mutated, "upload")
    item["default_decision"] = "allow"

    with pytest.raises(ValueError, match="upload must default to refuse"):
        validate_playwright_draft_fill_plan_fixture(mutated)


def test_validation_rejects_mfa_or_captcha_automation_support() -> None:
    plan = load_fixture()
    mutated = copy.deepcopy(plan)
    item = _refusal(mutated, "mfa")
    item["automation_supported"] = True

    with pytest.raises(ValueError, match="mfa automation must be unsupported"):
        validate_playwright_draft_fill_plan_fixture(mutated)
