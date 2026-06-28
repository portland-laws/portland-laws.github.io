import json
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "playwright_draft_fill_refusal_plan.json"


REFUSED_BY_DEFAULT_KINDS = {
    "selector",
    "upload",
    "submission",
    "payment",
    "certification",
    "cancellation",
    "mfa",
    "captcha",
    "inspection_scheduling",
}


PROHIBITED_ACTIONS = {
    "upload",
    "submit",
    "pay",
    "certify",
    "cancel",
    "solve",
    "schedule",
}


def load_fixture():
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_playwright_draft_fill_fixture_refuses_guarded_actions_by_default():
    plan = load_fixture()

    assert plan["mode"] == "draft_fill"
    assert plan["default_policy"] == "refuse"

    steps = plan["steps"]
    kinds = {step["kind"] for step in steps}
    assert kinds == REFUSED_BY_DEFAULT_KINDS

    for step in steps:
        assert step["default_decision"] == "refuse", step["id"]
        assert step["reason"].strip(), step["id"]


def test_low_confidence_selector_is_represented_and_refused():
    plan = load_fixture()
    selector_steps = [step for step in plan["steps"] if step["kind"] == "selector"]

    assert len(selector_steps) == 1
    selector_step = selector_steps[0]
    assert selector_step["confidence"] < 0.8
    assert selector_step["default_decision"] == "refuse"


def test_fixture_does_not_authorize_prohibited_actions():
    plan = load_fixture()

    for step in plan["steps"]:
        assert step["default_decision"] == "refuse", step["id"]
        assert not step.get("approved", False), step["id"]
        assert step.get("default_decision") != "allow", step["id"]

        action_text = " ".join(
            str(step.get(field, "")).lower()
            for field in ("id", "kind", "requested_action")
        )
        if any(action in action_text for action in PROHIBITED_ACTIONS):
            assert step["default_decision"] == "refuse", step["id"]
