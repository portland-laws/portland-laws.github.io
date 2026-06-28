from __future__ import annotations

from pathlib import Path

import pytest

from ppd.logic.guardrail_recompile_reviewer_packet_v7 import (
    EXPECTED_VALIDATION_COMMANDS,
    ReviewerPacketV7Error,
    build_guardrail_recompile_reviewer_packet_v7_from_fixture,
    collect_guardrail_recompile_reviewer_packet_v7_findings,
    validate_guardrail_recompile_reviewer_packet_v7,
)

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "guardrail_recompile_reviewer_packet_v7"
    / "inactive_guardrail_recompile_staging_packet_v7.json"
)


def test_builds_reviewer_packet_v7_from_inactive_staging_fixture_only() -> None:
    packet = build_guardrail_recompile_reviewer_packet_v7_from_fixture(FIXTURE)

    assert packet["packet_type"] == "ppd.guardrail_recompile_reviewer_packet.v7"
    assert packet["packet_version"] == "v7"
    assert packet["fixture_first"] is True
    assert packet["inactive_only"] is True
    assert packet["consumes_only_inactive_guardrail_recompile_staging_packet_v7_fixtures"] is True
    assert packet["activation_allowed"] is False
    assert packet["validation_commands"] == EXPECTED_VALIDATION_COMMANDS
    assert packet["staging_packet_references"]
    assert packet["reviewer_comparison_rows"]
    assert packet["inactive_guardrail_status_notes"]
    assert packet["source_evidence_continuity_checks"]
    assert packet["deterministic_predicate_review_prompts"]
    assert packet["exact_confirmation_preservation_summaries"]
    assert packet["refused_action_preservation_summaries"]
    assert packet["stale_evidence_hold_carry_forward_rows"]
    assert packet["rollback_readiness_notes"]
    assert packet["signoff_owner_placeholders"]
    validate_guardrail_recompile_reviewer_packet_v7(packet)


def test_reviewer_packet_v7_preserves_inactive_rows_and_no_action_attestations() -> None:
    packet = build_guardrail_recompile_reviewer_packet_v7_from_fixture(FIXTURE)

    row_fields = (
        "reviewer_comparison_rows",
        "inactive_guardrail_status_notes",
        "source_evidence_continuity_checks",
        "deterministic_predicate_review_prompts",
        "exact_confirmation_preservation_summaries",
        "refused_action_preservation_summaries",
        "stale_evidence_hold_carry_forward_rows",
        "rollback_readiness_notes",
        "signoff_owner_placeholders",
    )
    for field in row_fields:
        assert all(row["activation_allowed"] is False for row in packet[field])
    assert all(value is False for value in packet["attestations"].values())


@pytest.mark.parametrize(
    "field",
    [
        "staging_packet_references",
        "reviewer_comparison_rows",
        "inactive_guardrail_status_notes",
        "source_evidence_continuity_checks",
        "deterministic_predicate_review_prompts",
        "exact_confirmation_preservation_summaries",
        "refused_action_preservation_summaries",
        "stale_evidence_hold_carry_forward_rows",
        "rollback_readiness_notes",
        "signoff_owner_placeholders",
    ],
)
def test_reviewer_packet_v7_reports_missing_required_sections(field: str) -> None:
    packet = build_guardrail_recompile_reviewer_packet_v7_from_fixture(FIXTURE)
    packet[field] = []

    findings = collect_guardrail_recompile_reviewer_packet_v7_findings(packet)

    assert any(finding.path == f"$.{field}" for finding in findings)


def test_reviewer_packet_v7_rejects_activation_allowed_rows() -> None:
    packet = build_guardrail_recompile_reviewer_packet_v7_from_fixture(FIXTURE)
    packet["reviewer_comparison_rows"][0]["activation_allowed"] = True

    with pytest.raises(ReviewerPacketV7Error):
        validate_guardrail_recompile_reviewer_packet_v7(packet)


def test_reviewer_packet_v7_rejects_non_offline_validation_commands() -> None:
    packet = build_guardrail_recompile_reviewer_packet_v7_from_fixture(FIXTURE)
    packet["validation_commands"] = [["python3", "-m", "pytest"]]

    findings = collect_guardrail_recompile_reviewer_packet_v7_findings(packet)

    assert "invalid_validation_commands" in {finding.code for finding in findings}
