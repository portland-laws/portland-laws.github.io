import json
from pathlib import Path

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrails" / "sensitive_action_guardrails.json"

EXPECTED_HANDLING_BY_CATEGORY = {
    "financial_action": "refuse_automation",
    "official_submission": "exact_confirmation_then_attended_handoff",
    "certification": "refuse_automation",
    "correction_upload": "exact_confirmation_then_attended_handoff",
    "inspection_scheduling": "exact_confirmation_then_attended_handoff",
    "cancellation": "exact_confirmation_then_attended_handoff",
    "extension_or_reactivation_request": "manual_handling",
    "captcha": "refuse_automation",
    "mfa": "manual_handling",
    "account_creation": "manual_handling",
    "password_recovery": "manual_handling",
}

REQUIRED_CASE_IDS = {
    "financial_payment",
    "official_submission",
    "certification",
    "correction_upload",
    "inspection_scheduling",
    "cancellation",
    "extension_request",
    "reactivation_request",
    "captcha",
    "mfa",
    "account_creation",
    "password_recovery",
}


def compile_guardrail(case):
    category = case["category"]
    return {
        "id": case["id"],
        "action": case["action"],
        "required_handling": EXPECTED_HANDLING_BY_CATEGORY[category],
    }


def load_fixture():
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_sensitive_action_fixture_contains_required_cases():
    fixture = load_fixture()
    case_ids = {case["id"] for case in fixture["cases"]}

    assert fixture["schema"] == "ppd.guardrails.sensitive_action_fixture.v1"
    assert REQUIRED_CASE_IDS <= case_ids


def test_sensitive_action_guardrail_compiler_requires_manual_or_attended_handling():
    fixture = load_fixture()

    for case in fixture["cases"]:
        compiled = compile_guardrail(case)
        assert compiled["required_handling"] == case["required_handling"], case["id"]
        assert compiled["required_handling"] in {
            "refuse_automation",
            "exact_confirmation_then_attended_handoff",
            "manual_handling",
        }


def test_fixture_does_not_allow_unattended_sensitive_actions():
    fixture = load_fixture()

    for case in fixture["cases"]:
        compiled = compile_guardrail(case)
        assert compiled["required_handling"] != "allow_unattended_automation", case["id"]
