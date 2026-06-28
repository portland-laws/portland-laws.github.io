import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "playwright_draft_fill"
    / "ppd_residential_building_permit_draft_fill_plan.json"
)


PROHIBITED_ACTIONS = {
    "captcha",
    "mfa",
    "account_creation",
    "payment",
    "upload",
    "certification",
    "cancellation",
    "submission",
}


def load_fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_fixture_is_mocked_draft_preview_only_plan():
    fixture = load_fixture()

    assert fixture["fixture_kind"] == "mocked_playwright_draft_fill_plan"
    assert fixture["form"]["live_navigation_allowed"] is False
    assert fixture["automation_scope"]["mode"] == "draft_preview_only"
    assert PROHIBITED_ACTIONS.issubset(set(fixture["automation_scope"]["prohibited_actions"]))


def test_selectors_are_ranked_by_evidence_confidence():
    fixture = load_fixture()

    for field_plan in fixture["field_plans"]:
        selectors = field_plan["selectors_by_evidence_confidence"]
        confidences = [selector["confidence"] for selector in selectors]
        assert confidences == sorted(confidences, reverse=True)
        assert all(0 <= confidence <= 1 for confidence in confidences)
        assert all(selector["evidence"] for selector in selectors)


def test_missing_facts_map_to_questions():
    fixture = load_fixture()
    question_keys = {question["fact_key"] for question in fixture["missing_user_fact_questions"]}
    missing_field_keys = {
        field_plan["missing_fact_key"]
        for field_plan in fixture["field_plans"]
        if field_plan.get("missing_fact_key")
    }

    assert missing_field_keys
    assert missing_field_keys.issubset(question_keys)
    assert all(question["question"].endswith("?") for question in fixture["missing_user_fact_questions"])


def test_planned_actions_are_reversible_and_never_submission_like():
    fixture = load_fixture()
    allowed_actions = set(fixture["automation_scope"]["allowed_actions"])

    for action in fixture["planned_actions"]:
        assert action["action"] in allowed_actions
        assert action["action"] not in PROHIBITED_ACTIONS
        if action["action"] == "preview_fill_value":
            assert action["reversible"] is True
            assert any(
                later_action["action"] == "clear_preview_value"
                and later_action.get("field_key") == action.get("field_key")
                for later_action in fixture["planned_actions"]
            )

    assert all(field_plan["preview_only"] is True for field_plan in fixture["field_plans"])
