from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.devhub.fee_payment_guardrail_packet_validation import (
    FeePaymentGuardrailPacketError,
    validate_fee_payment_guardrail_packet,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub_fee_payment_guardrail_packets"
    / "guardrail_packet_validation_cases.json"
)


def load_fixture() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_accepts_commit_safe_read_only_fee_payment_guardrail_packet() -> None:
    fixture = load_fixture()

    result = validate_fee_payment_guardrail_packet(fixture["accepted_packet"])

    assert result.packet_id == "fee-payment-guardrail-accepted-read-only-review"
    assert result.fee_trigger_count == 1
    assert result.safe_action_count == 1
    assert result.source_evidence_count == 2
    assert result.to_dict()["validation_status"] == "accepted_commit_safe_fee_payment_guardrail_packet"


@pytest.mark.parametrize("case", load_fixture()["rejected_packets"], ids=lambda case: case["name"])
def test_rejects_unsafe_fee_payment_guardrail_packet_content(case: dict) -> None:
    with pytest.raises(FeePaymentGuardrailPacketError) as exc_info:
        validate_fee_payment_guardrail_packet(case["packet"])

    assert case["expected_error"] in str(exc_info.value)


def test_rejects_fee_trigger_citing_undeclared_packet_evidence() -> None:
    packet = dict(load_fixture()["accepted_packet"])
    packet["fee_triggers"] = [
        {
            "trigger": "A fee is due for this review checkpoint.",
            "source_evidence_ids": ["missing-from-packet"],
        }
    ]

    with pytest.raises(FeePaymentGuardrailPacketError) as exc_info:
        validate_fee_payment_guardrail_packet(packet)

    assert "cites evidence not declared by the packet" in str(exc_info.value)
