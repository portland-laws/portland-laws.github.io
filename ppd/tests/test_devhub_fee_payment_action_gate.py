import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub_fee_payment_action_gate"
    / "fee_payment_actions.json"
)

READ_ONLY_CLASSIFICATION = "read_only_evidence"
GATED_CLASSIFICATIONS = {"financial_action", "consequential_action"}
PAYMENT_ACTION_IDS = {
    "payment_detail_entry",
    "save_payment_information",
    "final_payment_submission",
}
FORBIDDEN_PRIVATE_KEYS = {
    "account_number",
    "auth_state",
    "bank_account",
    "billing_address",
    "card_number",
    "cardholder_name",
    "cookie",
    "cookies",
    "cvc",
    "cvv",
    "expiration_date",
    "har",
    "mfa_code",
    "password",
    "payment_token",
    "private_file_path",
    "routing_number",
    "screenshot",
    "session_state",
    "trace",
}


def load_fixture():
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def actions_by_id(fixture):
    return {action["action_id"]: action for action in fixture["actions"]}


def walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def test_fee_payment_fixture_contains_no_private_payment_or_session_material():
    fixture = load_fixture()

    observed_keys = {key.lower() for key in walk_keys(fixture)}

    assert observed_keys.isdisjoint(FORBIDDEN_PRIVATE_KEYS)
    assert "No credentials" in fixture["privacy_note"]


def test_fee_notice_review_is_read_only_evidence_not_a_payment_action():
    fixture = load_fixture()
    actions = actions_by_id(fixture)
    fee_notice = actions["fee_notice_review"]

    assert fee_notice["classification"] == READ_ONLY_CLASSIFICATION
    assert fee_notice["allowed_autonomous"] is True
    assert fee_notice["requires_manual_handoff"] is False
    assert fee_notice["requires_exact_confirmation"] is False
    assert "amount due summary" in fee_notice["permitted_observation"]
    assert fee_notice["prohibited_automation"] == []


def test_payment_detail_saved_payment_and_final_submission_are_manual_exact_confirmation_gates():
    fixture = load_fixture()
    actions = actions_by_id(fixture)

    assert PAYMENT_ACTION_IDS.issubset(actions)

    for action_id in sorted(PAYMENT_ACTION_IDS):
        action = actions[action_id]

        assert action["classification"] in GATED_CLASSIFICATIONS
        assert action["allowed_autonomous"] is False
        assert action["requires_manual_handoff"] is True
        assert action["requires_exact_confirmation"] is True
        assert action["permitted_observation"] == []
        assert action["prohibited_automation"]
        assert "handoff" in action["handoff_reason"].lower() or "attended" in action["handoff_reason"].lower()


def test_fixture_models_the_expected_fee_payment_boundary_without_live_devhub_automation():
    fixture = load_fixture()
    actions = actions_by_id(fixture)

    autonomous_actions = {
        action_id
        for action_id, action in actions.items()
        if action["allowed_autonomous"] is True
    }
    handoff_actions = {
        action_id
        for action_id, action in actions.items()
        if action["requires_manual_handoff"] is True
    }
    exact_confirmation_actions = {
        action_id
        for action_id, action in actions.items()
        if action["requires_exact_confirmation"] is True
    }

    assert autonomous_actions == {"fee_notice_review"}
    assert handoff_actions == PAYMENT_ACTION_IDS
    assert exact_confirmation_actions == PAYMENT_ACTION_IDS
