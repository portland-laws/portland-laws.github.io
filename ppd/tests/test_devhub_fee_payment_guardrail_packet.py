import copy
from pathlib import Path

import pytest

from ppd.devhub.fee_payment_guardrail_packet import (
    BLOCKED_PAYMENT_ACTION_IDS,
    REQUIRED_SECTION_IDS,
    FeePaymentGuardrailPacketError,
    load_fee_payment_guardrail_packet,
    validate_fee_payment_guardrail_packet,
    validate_fee_payment_guardrail_packet_file,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "fee_payment_guardrail_packet_synthetic_permit.json"


def test_synthetic_fee_payment_guardrail_packet_validates_required_sections() -> None:
    result = validate_fee_payment_guardrail_packet_file(FIXTURE_PATH)

    assert result.packet_id == "synthetic-devhub-fee-payment-guardrail-packet-v1"
    assert result.workflow_id == "synthetic-residential-trade-fee-review"
    assert result.section_ids == REQUIRED_SECTION_IDS
    assert result.blocked_action_ids == BLOCKED_PAYMENT_ACTION_IDS
    assert result.next_safe_alternative_ids == (
        "summarize_fee_notice_structure",
        "cite_fee_payment_guidance",
        "prepare_manual_handoff_note",
    )
    assert result.to_dict()["validation_status"] == "accepted_fixture_first_fee_payment_guardrail_packet"


def test_packet_separates_read_only_review_from_payment_stop_points() -> None:
    packet = load_fee_payment_guardrail_packet(FIXTURE_PATH)
    sections = {section["section_id"]: section for section in packet["guardrail_sections"]}

    assert sections["fee_notice_read_only_review"]["allowed_autonomous"] is True
    assert sections["fee_notice_read_only_review"]["requires_manual_handoff"] is False
    assert sections["fee_notice_read_only_review"]["requires_exact_confirmation"] is False

    for section_id in ("blocked_payment_detail_entry", "blocked_final_payment_execution"):
        assert sections[section_id]["allowed_autonomous"] is False
        assert sections[section_id]["requires_manual_handoff"] is True
        assert sections[section_id]["requires_exact_confirmation"] is True


def test_packet_requires_exact_confirmation_language_without_authorizing_execution() -> None:
    packet = load_fee_payment_guardrail_packet(FIXTURE_PATH)
    sections = {section["section_id"]: section for section in packet["guardrail_sections"]}
    language = sections["exact_confirmation_language"]["guardrail"]

    assert "I am present in my own DevHub account" in language
    assert "I understand this is a City of Portland financial action" in language
    assert "does not authorize agent execution" in language
    assert set(sections["exact_confirmation_language"]["blocked_action_ids"]) == set(BLOCKED_PAYMENT_ACTION_IDS)


def test_packet_rejects_live_or_private_session_artifacts() -> None:
    packet = load_fee_payment_guardrail_packet(FIXTURE_PATH)
    unsafe = copy.deepcopy(packet)
    unsafe["live_devhub_session"] = True

    with pytest.raises(FeePaymentGuardrailPacketError, match="live_devhub_session"):
        validate_fee_payment_guardrail_packet(unsafe)

    unsafe = copy.deepcopy(packet)
    unsafe["auth_state"] = "storage_state"

    with pytest.raises(FeePaymentGuardrailPacketError, match="private value|browser artifact"):
        validate_fee_payment_guardrail_packet(unsafe)


def test_packet_rejects_safe_alternative_that_is_financial_or_official() -> None:
    packet = load_fee_payment_guardrail_packet(FIXTURE_PATH)
    unsafe = copy.deepcopy(packet)
    unsafe["next_safe_alternatives"][0]["financial_action"] = True

    with pytest.raises(FeePaymentGuardrailPacketError, match="must not be official or financial"):
        validate_fee_payment_guardrail_packet(unsafe)


def test_packet_rejects_missing_required_section_order() -> None:
    packet = load_fee_payment_guardrail_packet(FIXTURE_PATH)
    unsafe = copy.deepcopy(packet)
    unsafe["guardrail_sections"] = list(reversed(unsafe["guardrail_sections"]))

    with pytest.raises(FeePaymentGuardrailPacketError, match="required task order"):
        validate_fee_payment_guardrail_packet(unsafe)
