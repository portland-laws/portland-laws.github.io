from __future__ import annotations

from pathlib import Path

import pytest

from ppd.requirement_review_queue import (
    build_human_review_queue_packet,
    load_review_queue_fixture,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "requirement_review_queue" / "synthetic_public_records.json"


def test_builds_fixture_first_review_queue_packet_without_extraction_or_raw_text_storage() -> None:
    fixture = load_review_queue_fixture(FIXTURE_PATH)

    packet = build_human_review_queue_packet(fixture)

    assert packet["generated_from_fixture"] is True
    assert packet["extraction_executed"] is False
    assert packet["requirements_changed"] is False
    assert packet["raw_source_text_stored"] is False
    assert packet["packet_id"].startswith("ppd-review-queue-")
    assert len(packet["candidate_requirement_nodes"]) == 3

    for candidate in packet["candidate_requirement_nodes"]:
        assert candidate["human_review_status"] == "queued"
        assert candidate["formalization_status"] == "deferred_pending_human_review"
        assert candidate["citations"]
        assert candidate["reviewer_owner"].startswith("ppd-")
        assert "Do not compile" in candidate["deferred_formalization_note"]
        for citation in candidate["citations"]:
            assert citation["canonical_url"].startswith("https://")
            assert "content_hash" in citation
            assert "location_ref" in citation


def test_confidence_bands_review_reasons_and_owners_are_deterministic() -> None:
    fixture = load_review_queue_fixture(FIXTURE_PATH)

    first = build_human_review_queue_packet(fixture)
    second = build_human_review_queue_packet(fixture)

    assert first == second
    candidates = {item["requirement_id"]: item for item in first["candidate_requirement_nodes"]}

    document_candidate = candidates["candidate-single-pdf-document-requirement"]
    assert document_candidate["confidence_band"] == "high"
    assert document_candidate["reviewer_owner"] == "ppd-document-reviewer"
    assert document_candidate["review_reasons"] == ["confirm cited candidate before formalization"]

    upload_candidate = candidates["candidate-devhub-upload-action-gate"]
    assert upload_candidate["confidence_band"] == "medium"
    assert upload_candidate["reviewer_owner"] == "ppd-guardrails-reviewer"
    assert "candidate requires human interpretation before formalization" in upload_candidate["review_reasons"]

    payment_candidate = candidates["candidate-fee-payment-action-gate"]
    assert payment_candidate["confidence_band"] == "medium"
    assert payment_candidate["reviewer_owner"] == "ppd-fee-reviewer"
    assert "source evidence evidence-fee-payment-guide has stale freshness badge" in payment_candidate["review_reasons"]


def test_deferred_formalization_notes_match_candidate_requirements() -> None:
    fixture = load_review_queue_fixture(FIXTURE_PATH)

    packet = build_human_review_queue_packet(fixture)

    candidate_ids = {item["requirement_id"] for item in packet["candidate_requirement_nodes"]}
    note_ids = {item["requirement_id"] for item in packet["deferred_formalization_notes"]}
    assert note_ids == candidate_ids
    for note in packet["deferred_formalization_notes"]:
        assert note["formalization_status"] == "deferred_pending_human_review"
        assert note["reviewer_owner"].startswith("ppd-")
        assert "until a human reviewer accepts" in note["note"]


def test_rejects_raw_source_text_fields() -> None:
    fixture = load_review_queue_fixture(FIXTURE_PATH)
    fixture["synthetic_public_document_records"][0]["raw_source_text"] = "not allowed"

    with pytest.raises(ValueError, match="raw source text field"):
        build_human_review_queue_packet(fixture)
