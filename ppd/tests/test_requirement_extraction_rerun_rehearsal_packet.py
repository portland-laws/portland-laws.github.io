from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.extraction.requirement_extraction_rerun_rehearsal_packet import (
    RequirementExtractionRerunRehearsalPacketError,
    build_requirement_extraction_rerun_rehearsal_packet,
    require_valid_requirement_extraction_rerun_rehearsal_packet,
    validate_requirement_extraction_rerun_rehearsal_packet,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "requirement_extraction_rerun_rehearsal" / "valid_rehearsal_inputs.json"


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_builds_fixture_first_requirement_extraction_rerun_rehearsal_packet() -> None:
    fixture = _fixture()

    packet = build_requirement_extraction_rerun_rehearsal_packet(
        fixture["public_recrawl_post_intake_review_packet"],
        fixture["requirement_human_review_queue_packet"],
        fixture["synthetic_public_document_records"],
        generated_at=fixture["generated_at"],
    )

    result = validate_requirement_extraction_rerun_rehearsal_packet(packet)
    assert result.valid, result.errors
    assert packet["no_extraction_execution_attestations"]["extraction_executed"] is False
    assert packet["no_extraction_execution_attestations"]["requirements_mutated"] is False
    assert packet["rehearsal_summary"] == {
        "candidate_delta_count": 2,
        "stale_withdrawal_note_count": 1,
        "human_review_owner_count": 2,
        "deferred_formalization_note_count": 2,
        "extraction_executed": False,
        "requirements_mutated": False,
    }
    assert {row["candidate_id"] for row in packet["cited_candidate_requirement_deltas"]} == {
        "cand-single-pdf-upload-rule",
        "cand-devhub-save-later",
    }
    assert packet["stale_candidate_withdrawal_notes"][0]["candidate_id"] == "cand-single-pdf-upload-rule"
    assert {row["reviewer_owner"] for row in packet["human_review_owners"]} == {
        "requirements-intake-reviewer",
        "devhub-guidance-reviewer",
    }


def test_validation_rejects_extraction_execution_claims() -> None:
    fixture = _fixture()
    packet = build_requirement_extraction_rerun_rehearsal_packet(
        fixture["public_recrawl_post_intake_review_packet"],
        fixture["requirement_human_review_queue_packet"],
        fixture["synthetic_public_document_records"],
        generated_at=fixture["generated_at"],
    )
    packet["no_extraction_execution_attestations"]["extraction_executed"] = True

    result = validate_requirement_extraction_rerun_rehearsal_packet(packet)

    assert not result.valid
    assert "no_extraction_execution_attestations.extraction_executed must be false" in result.errors


def test_builder_rejects_raw_or_private_artifact_inputs() -> None:
    fixture = _fixture()
    fixture["synthetic_public_document_records"][0]["raw_html"] = "raw body is not commit safe"

    with pytest.raises(RequirementExtractionRerunRehearsalPacketError):
        build_requirement_extraction_rerun_rehearsal_packet(
            fixture["public_recrawl_post_intake_review_packet"],
            fixture["requirement_human_review_queue_packet"],
            fixture["synthetic_public_document_records"],
            generated_at=fixture["generated_at"],
        )


def test_committed_fixture_packet_can_be_validated_without_live_execution() -> None:
    fixture = _fixture()
    packet = build_requirement_extraction_rerun_rehearsal_packet(
        fixture["public_recrawl_post_intake_review_packet"],
        fixture["requirement_human_review_queue_packet"],
        fixture["synthetic_public_document_records"],
        generated_at=fixture["generated_at"],
    )

    require_valid_requirement_extraction_rerun_rehearsal_packet(packet)
