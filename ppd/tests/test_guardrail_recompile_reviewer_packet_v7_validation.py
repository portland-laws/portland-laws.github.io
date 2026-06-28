from __future__ import annotations

from pathlib import Path

import pytest

from ppd.logic.guardrail_recompile_reviewer_packet_v7 import build_guardrail_recompile_reviewer_packet_v7_from_fixture
from ppd.validation.guardrail_recompile_reviewer_packet_v7 import reject_packet, validate_packet

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "guardrail_recompile_reviewer_packet_v7"
    / "inactive_guardrail_recompile_staging_packet_v7.json"
)


def _valid_packet() -> dict:
    return build_guardrail_recompile_reviewer_packet_v7_from_fixture(FIXTURE)


def test_guardrail_recompile_reviewer_packet_v7_validation_accepts_fixture_built_packet() -> None:
    packet = _valid_packet()

    assert validate_packet(packet) == []
    reject_packet(packet)


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("staging_packet_references", "missing_staging_packet_references"),
        ("reviewer_comparison_rows", "missing_reviewer_comparison_rows"),
        ("inactive_guardrail_status_notes", "missing_inactive_guardrail_status_notes"),
        ("source_evidence_continuity_checks", "missing_source_evidence_continuity_checks"),
        ("deterministic_predicate_review_prompts", "missing_deterministic_predicate_review_prompts"),
        ("exact_confirmation_preservation_summaries", "missing_exact_confirmation_preservation_summaries"),
        ("refused_action_preservation_summaries", "missing_refused_action_preservation_summaries"),
        ("stale_evidence_hold_carry_forward_rows", "missing_stale_evidence_hold_carry_forward_rows"),
        ("rollback_readiness_notes", "missing_rollback_readiness_notes"),
        ("signoff_owner_placeholders", "missing_signoff_owner_placeholders"),
        ("validation_commands", "missing_validation_commands"),
    ],
)
def test_guardrail_recompile_reviewer_packet_v7_validation_rejects_missing_required_sections(field: str, code: str) -> None:
    packet = _valid_packet()
    packet[field] = []

    issues = validate_packet(packet)

    assert code in {issue.code for issue in issues}


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("reviewer_comparison_rows", "invalid_reviewer_comparison_rows"),
        ("source_evidence_continuity_checks", "invalid_source_evidence_continuity_checks"),
    ],
)
def test_guardrail_recompile_reviewer_packet_v7_validation_rejects_invalid_row_shapes(field: str, code: str) -> None:
    packet = _valid_packet()
    packet[field] = ["not a row object"]

    issues = validate_packet(packet)

    assert code in {issue.code for issue in issues}


@pytest.mark.parametrize(
    ("mutator", "code"),
    [
        (lambda packet: packet.update({"review_note": "activation complete for this guardrail"}), "active_activation_claim"),
        (lambda packet: packet.update({"review_note": "executed a crawl against public pages"}), "live_crawl_execution_claim"),
        (lambda packet: packet.update({"review_note": "saved pdf and raw crawl artifact are attached"}), "downloaded_or_raw_crawl_artifact"),
        (lambda packet: packet.update({"review_note": "DevHub session cookie captured"}), "private_session_auth_artifact"),
        (lambda packet: packet.update({"review_note": "permit submitted to the city"}), "official_action_completion_claim"),
        (lambda packet: packet.update({"review_note": "permit approval is assured"}), "legal_or_permitting_guarantee"),
        (lambda packet: packet.update({"active_mutation": True}), "active_mutation_flag"),
    ],
)
def test_guardrail_recompile_reviewer_packet_v7_validation_rejects_prohibited_claims_artifacts_and_flags(mutator, code: str) -> None:
    packet = _valid_packet()
    mutator(packet)

    issues = validate_packet(packet)

    assert code in {issue.code for issue in issues}


def test_guardrail_recompile_reviewer_packet_v7_validation_rejects_active_activation_rows_and_attestations() -> None:
    packet = _valid_packet()
    packet["reviewer_comparison_rows"][0]["activation_allowed"] = True
    packet["attestations"]["guardrails_activated"] = True

    issues = validate_packet(packet)

    codes = {issue.code for issue in issues}
    assert "row_activation_not_false" in codes
    assert "attestation_not_false" in codes


def test_guardrail_recompile_reviewer_packet_v7_validation_rejects_non_exact_validation_commands() -> None:
    packet = _valid_packet()
    packet["validation_commands"] = [["python3", "-m", "pytest"]]

    issues = validate_packet(packet)

    assert "invalid_validation_commands" in {issue.code for issue in issues}
    with pytest.raises(ValueError):
        reject_packet(packet)
