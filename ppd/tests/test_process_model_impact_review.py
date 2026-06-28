from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.logic.process_model_impact_review import (
    ImpactReviewValidationError,
    assert_valid_process_model_impact_review_packet,
    validate_process_model_impact_review_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "process_model_impact_review"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_packet_passes() -> None:
    packet = _load_fixture("valid_packet.json")

    result = validate_process_model_impact_review_packet(packet)

    assert result.valid
    assert result.issues == ()
    assert_valid_process_model_impact_review_packet(packet)


def test_invalid_packet_rejects_required_safety_failures() -> None:
    packet = _load_fixture("invalid_packet.json")

    result = validate_process_model_impact_review_packet(packet)

    assert not result.valid
    assert set(result.codes()) >= {
        "uncited_process_stage_impact_claim",
        "missing_affected_process_ids",
        "missing_affected_guardrail_ids",
        "missing_blocked_action_carryovers",
        "missing_reviewer_owners",
        "private_case_facts_present",
        "live_execution_claim_present",
        "outcome_guarantee_present",
        "enabled_consequential_control",
        "active_mutation_flag",
    }


def test_assert_valid_raises_with_issue_codes() -> None:
    packet = _load_fixture("invalid_packet.json")

    with pytest.raises(ImpactReviewValidationError) as excinfo:
        assert_valid_process_model_impact_review_packet(packet)

    assert "uncited_process_stage_impact_claim" in str(excinfo.value)
