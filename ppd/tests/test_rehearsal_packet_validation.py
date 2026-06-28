from __future__ import annotations

import json
from pathlib import Path

from ppd.guardrails.rehearsal_packet_validation import (
    REQUIRED_REFUSAL_DOMAINS,
    assert_valid_rehearsal_packet,
    validate_rehearsal_packet,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "guardrails" / "rehearsal_packets"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_rehearsal_packet_passes() -> None:
    packet = _load_fixture("valid_rehearsal_packet.json")

    assert validate_rehearsal_packet(packet) == []
    assert_valid_rehearsal_packet(packet)


def test_invalid_rehearsal_packet_reports_required_guardrails() -> None:
    packet = _load_fixture("invalid_rehearsal_packet.json")

    codes = {issue.code for issue in validate_rehearsal_packet(packet)}

    assert "uncited_predicate_change" in codes
    assert "missing_refusal_coverage" in codes
    assert "missing_exact_confirmation_gate" in codes
    assert "private_fact_present" in codes
    assert "unresolved_reviewer_prompt_marked_resolved" in codes
    assert "production_activation_flag" in codes
    assert "active_guardrail_bundle_mutation" in codes


def test_required_refusal_domains_are_the_sensitive_actions() -> None:
    assert REQUIRED_REFUSAL_DOMAINS == (
        "payment",
        "upload",
        "submission",
        "scheduling",
        "cancellation",
        "certification",
    )
