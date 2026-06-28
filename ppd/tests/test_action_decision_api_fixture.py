import json
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "action_decision_api_fixture.json"

EXPECTED_CLASSIFICATIONS = {
    "read_only_review",
    "reversible_draft",
    "save_for_later",
    "manual_handoff",
    "refused_consequential_action",
    "financial_boundary",
}

CONSEQUENTIAL_ACTIONS = {
    "submit",
    "pay",
    "upload",
    "certify",
    "cancel",
    "create_account",
    "mfa",
    "account_login",
    "authenticated_browser_control",
}


def load_fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_action_decision_fixture_covers_required_classifications():
    fixture = load_fixture()
    cases = fixture["decision_cases"]

    assert fixture["browser_automation"] == {
        "allowed": False,
        "reason": "This fixture is for deterministic decision classification only; it must not drive browser actions.",
    }
    assert {case["classification"] for case in cases} == EXPECTED_CLASSIFICATIONS
    assert len(cases) == len(EXPECTED_CLASSIFICATIONS)


def test_action_decision_cases_include_citations_confirmations_and_boundaries():
    fixture = load_fixture()

    for case in fixture["decision_cases"]:
        assert case["id"]
        assert case["user_request"]
        assert case["allowed_agent_response"]
        assert case["citations"]
        assert all(item["source"] and item["explanation"] for item in case["citations"])
        assert isinstance(case["required_confirmations"], list)
        assert isinstance(case["prohibited_actions"], list)

    by_classification = {case["classification"]: case for case in fixture["decision_cases"]}
    assert by_classification["read_only_review"]["required_confirmations"] == []

    for classification in EXPECTED_CLASSIFICATIONS - {"read_only_review"}:
        assert by_classification[classification]["required_confirmations"]

    for classification in {"manual_handoff", "refused_consequential_action", "financial_boundary"}:
        prohibited = set(by_classification[classification]["prohibited_actions"])
        assert prohibited & CONSEQUENTIAL_ACTIONS
