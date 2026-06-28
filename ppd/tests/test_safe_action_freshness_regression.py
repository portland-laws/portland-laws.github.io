from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.safe_action_freshness_regression import (
    assert_valid_safe_action_freshness_packet,
    validate_safe_action_freshness_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "safe_action_freshness"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_accepts_minimal_cited_stale_evidence_packet() -> None:
    packet = _load_fixture("valid_cited_stale_evidence_packet.json")

    assert validate_safe_action_freshness_packet(packet) == []
    assert_valid_safe_action_freshness_packet(packet)


def test_rejects_unsafe_regression_packet_shapes() -> None:
    packet = _load_fixture("invalid_unsafe_packet.json")

    codes = {issue.code for issue in validate_safe_action_freshness_packet(packet)}

    assert "uncited_stale_evidence" in codes
    assert "missing_expected_prompt_or_refusal" in codes
    assert "missing_blocked_action_explanation" in codes
    assert "missing_reviewer_owner" in codes
    assert "private_case_fact" in codes
    assert "raw_authenticated_value" in codes
    assert "local_private_path" in codes
    assert "live_execution_claim" in codes
    assert "outcome_guarantee" in codes
    assert "enabled_consequential_control" in codes
    assert "active_mutation_flag" in codes


def test_assertion_error_lists_actionable_issue_codes() -> None:
    packet = _load_fixture("invalid_unsafe_packet.json")

    try:
        assert_valid_safe_action_freshness_packet(packet)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("invalid packet unexpectedly passed")

    assert "uncited_stale_evidence" in message
    assert "missing_blocked_action_explanation" in message
    assert "active_mutation_flag" in message
