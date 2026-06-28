from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.extraction.requirement_rerun_review_disposition_packet import (
    RequirementRerunReviewDispositionPacketError,
    build_requirement_rerun_review_disposition_packet,
    require_valid_requirement_rerun_review_disposition_packet,
    validate_requirement_rerun_review_disposition_packet,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "requirement_rerun_review_disposition" / "valid_disposition_inputs.json"


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_builds_fixture_first_requirement_rerun_review_disposition_packet() -> None:
    fixture = _fixture()

    packet = build_requirement_rerun_review_disposition_packet(
        fixture["requirement_extraction_rerun_rehearsal_packet"],
        fixture["validation_fixture"],
        generated_at=fixture["generated_at"],
    )

    result = validate_requirement_rerun_review_disposition_packet(packet)
    assert result.valid, result.errors
    assert packet["disposition_summary"] == {
        "accepted_count": 1,
        "deferred_count": 1,
        "superseded_count": 1,
        "withdrawn_count": 1,
        "reviewer_owner_assignment_count": 4,
        "stale_evidence_acknowledgement_count": 2,
        "formalization_deferral_count": 4,
        "extraction_executed": False,
        "requirements_mutated": False,
        "active_requirements_changed": False,
    }
    assert packet["accepted_candidate_deltas"][0]["candidate_id"] == "cand-single-pdf-upload-rule"
    assert packet["deferred_candidate_deltas"][0]["candidate_id"] == "cand-devhub-save-later"
    assert packet["superseded_candidate_deltas"][0]["candidate_id"] == "cand-old-upload-copy"
    assert packet["withdrawn_candidate_deltas"][0]["candidate_id"] == "cand-retired-devhub-note"
    assert {row["reviewer_owner"] for row in packet["reviewer_owner_assignments"]} == {
        "requirements-intake-reviewer",
        "devhub-guidance-reviewer",
    }
    assert packet["no_requirement_mutation_attestations"]["requirements_mutated"] is False
    assert packet["no_requirement_mutation_attestations"]["active_requirements_changed"] is False


def test_validation_rejects_requirement_mutation_attestation_claims() -> None:
    fixture = _fixture()
    packet = build_requirement_rerun_review_disposition_packet(
        fixture["requirement_extraction_rerun_rehearsal_packet"],
        fixture["validation_fixture"],
        generated_at=fixture["generated_at"],
    )
    packet["no_requirement_mutation_attestations"]["active_requirements_changed"] = True

    result = validate_requirement_rerun_review_disposition_packet(packet)

    assert not result.valid
    assert "no_requirement_mutation_attestations.active_requirements_changed must be false" in result.errors


def test_builder_rejects_unknown_disposition_candidate() -> None:
    fixture = _fixture()
    fixture["validation_fixture"]["disposition_reviews"][0]["candidate_id"] = "cand-not-in-rehearsal"

    with pytest.raises(RequirementRerunReviewDispositionPacketError):
        build_requirement_rerun_review_disposition_packet(
            fixture["requirement_extraction_rerun_rehearsal_packet"],
            fixture["validation_fixture"],
            generated_at=fixture["generated_at"],
        )


def test_committed_fixture_packet_can_be_validated_without_live_execution() -> None:
    fixture = _fixture()
    packet = build_requirement_rerun_review_disposition_packet(
        fixture["requirement_extraction_rerun_rehearsal_packet"],
        fixture["validation_fixture"],
        generated_at=fixture["generated_at"],
    )

    require_valid_requirement_rerun_review_disposition_packet(packet)
    assert all(row["formal_requirement_written"] is False for row in packet["formalization_deferrals"])
