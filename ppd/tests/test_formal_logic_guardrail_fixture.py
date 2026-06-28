import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "formal_logic"
    / "archived_ppd_residential_permit_guardrails.json"
)


def test_archived_ppd_guardrail_fixture_has_required_logic_sections():
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert data["fixture_type"] == "ppd_formal_logic_guardrail_bundle"
    assert data["source_archive"]["agency"] == "Portland Permitting & Development"
    assert data["requirements"]

    requirement = data["requirements"][0]
    for key in (
        "obligations",
        "prerequisites",
        "stop_gates",
        "reversible_actions",
        "exact_confirmations",
    ):
        assert requirement[key], key


def test_exact_confirmation_blocks_non_fixture_sensitive_actions():
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    confirmation = data["requirements"][0]["exact_confirmations"][0]

    assert confirmation["phrase"].startswith("I confirm ")
    assert "submission" in confirmation["blocked_automation"]
    assert "payment" in confirmation["blocked_automation"]
    assert "captcha" in confirmation["blocked_automation"]


def test_reversible_actions_are_explicitly_marked():
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    reversible_action = data["requirements"][0]["reversible_actions"][0]

    assert reversible_action["action"]
    assert reversible_action["reversal"]
    assert reversible_action["allowed_without_exact_confirmation"] is True
