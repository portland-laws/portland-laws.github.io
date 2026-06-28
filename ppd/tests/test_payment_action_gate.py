from pathlib import Path

from ppd.devhub.payment_action_gate import (
    PaymentActionCategory,
    PaymentGate,
    decide_payment_action,
    validate_payment_action_fixtures,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "payment_action_gates.json"


def test_payment_action_gate_fixture_expectations() -> None:
    decisions = validate_payment_action_fixtures(FIXTURE_PATH)

    assert len(decisions) == 6
    assert {decision.action_id for decision in decisions} == {
        "review_fee_notice",
        "open_payment_page",
        "enter_card_fields",
        "submit_payment",
        "download_receipt",
        "mark_payment_done",
    }


def test_fee_notice_review_is_the_only_allowed_fixture_action() -> None:
    decisions = validate_payment_action_fixtures(FIXTURE_PATH)
    allowed = [decision for decision in decisions if decision.allowed]

    assert len(allowed) == 1
    assert allowed[0].category is PaymentActionCategory.FEE_NOTICE_REVIEW
    assert allowed[0].gate is PaymentGate.SAFE_READ_ONLY


def test_payment_details_and_submit_actions_are_refused() -> None:
    detail_decision = decide_payment_action(
        {
            "action_id": "ach_payment_fields",
            "label": "Enter bank account payment information",
            "fields": [
                {"name": "routing", "label": "Routing number"},
                {"name": "account", "label": "Account number"},
            ],
        }
    )
    submit_decision = decide_payment_action(
        {
            "action_id": "pay_now",
            "label": "Pay now",
            "kind": "click",
        }
    )

    assert detail_decision.category is PaymentActionCategory.PAYMENT_DETAIL_ENTRY
    assert detail_decision.gate is PaymentGate.REFUSED
    assert detail_decision.allowed is False
    assert submit_decision.category is PaymentActionCategory.SUBMIT_PAYMENT
    assert submit_decision.gate is PaymentGate.REFUSED
    assert submit_decision.allowed is False


def test_unknown_payment_action_defaults_to_manual_handoff() -> None:
    decision = decide_payment_action(
        {
            "action_id": "unrecognized_payment_widget",
            "label": "Continue",
            "kind": "button",
        }
    )

    assert decision.category is PaymentActionCategory.UNKNOWN_PAYMENT_ACTION
    assert decision.gate is PaymentGate.MANUAL_HANDOFF
    assert decision.allowed is False
    assert decision.required_confirmation is not None
