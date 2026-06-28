from __future__ import annotations

import json
from pathlib import Path

from ppd.devhub.observation_redaction_acceptance_v3 import (
    assert_acceptance_packet_v3,
    validate_acceptance_packet_v3,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_observation_redaction_acceptance_v3"


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_packet_has_no_issues() -> None:
    packet = _load_fixture("valid_packet.json")

    assert validate_acceptance_packet_v3(packet) == []
    assert_acceptance_packet_v3(packet)


def test_rejects_required_evidence_omissions() -> None:
    packet = _load_fixture("valid_packet.json")
    for field in (
        "observation_intake_references",
        "redaction_coverage_checks",
        "private_value_omission_evidence",
        "route_pattern_normalization_checks",
        "selector_evidence_confidence_summaries",
        "unsupported_manual_handoff_reminders",
        "fixture_promotion_holds",
        "reviewer_routing",
        "rollback_notes",
        "validation_commands",
    ):
        packet[field] = []

    codes = {issue.code for issue in validate_acceptance_packet_v3(packet)}

    assert "missing_observation_intake_references" in codes
    assert "missing_redaction_coverage_checks" in codes
    assert "missing_private_value_omission_evidence" in codes
    assert "missing_route_pattern_normalization_checks" in codes
    assert "missing_selector_evidence_confidence_summaries" in codes
    assert "missing_unsupported_manual_handoff_reminders" in codes
    assert "missing_fixture_promotion_holds" in codes
    assert "missing_reviewer_routing" in codes
    assert "missing_rollback_notes" in codes
    assert "missing_validation_commands" in codes


def test_rejects_private_artifacts_and_prohibited_claims() -> None:
    packet = _load_fixture("invalid_prohibited_claims_packet.json")

    codes = {issue.code for issue in validate_acceptance_packet_v3(packet)}

    assert "private_session_auth_artifact" in codes
    assert "screenshot_trace_har_claim" in codes
    assert "live_devhub_interaction_claim" in codes
    assert "form_fill_or_upload_claim" in codes
    assert "official_action_completion_claim" in codes
    assert "legal_or_permitting_guarantee" in codes
    assert "active_mutation_flag" in codes


def test_assertion_raises_with_stable_issue_codes() -> None:
    packet = _load_fixture("invalid_prohibited_claims_packet.json")

    try:
        assert_acceptance_packet_v3(packet)
    except ValueError as exc:
        message = str(exc)
    else:
        raise AssertionError("Expected invalid packet to raise ValueError")

    assert "private_session_auth_artifact" in message
    assert "active_mutation_flag" in message
