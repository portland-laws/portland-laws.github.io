from __future__ import annotations

from pathlib import Path

import json
import pytest

from ppd.acceptance_packet_v2_validator import assert_valid_acceptance_packet_v2, validate_acceptance_packet_v2

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "acceptance_packet_v2"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_accepts_complete_public_extraction_packet() -> None:
    assert validate_acceptance_packet_v2(load_fixture("valid_packet.json")) == []


def test_rejects_missing_required_evidence() -> None:
    packet = load_fixture("valid_packet.json")
    for key in (
        "page_anchors",
        "extraction_confidence",
        "checklist_rows",
        "required_document_rows",
        "fillable_field_metadata",
        "deadline_rows",
        "file_preparation_rows",
        "ocr_review_holds",
        "validation_commands",
    ):
        broken = dict(packet)
        broken[key] = []
        codes = {issue.code for issue in validate_acceptance_packet_v2(broken)}
        assert key in codes


def test_rejects_missing_expected_certification_block_label() -> None:
    packet = load_fixture("valid_packet.json")
    packet["certification_block_labels"] = ["Applicant signature"]
    issues = validate_acceptance_packet_v2(packet)
    assert "certification_block_labels" in {issue.code for issue in issues}


def test_rejects_prohibited_artifacts_claims_and_mutations() -> None:
    packet = load_fixture("valid_packet.json")
    packet.update(
        {
            "raw_artifacts": ["raw.html"],
            "browser_artifacts": ["trace.zip"],
            "live_crawl_claims": ["Crawled DevHub live"],
            "official_action_completion_claims": ["Permit submitted"],
            "legal_guarantees": ["Legally sufficient"],
            "active_mutation_flags": ["submit"],
            "uploads_documents": True,
        }
    )
    codes = {issue.code for issue in validate_acceptance_packet_v2(packet)}
    assert "prohibited_artifacts" in codes
    assert "prohibited_claims" in codes
    assert "active_mutation_flags" in codes


def test_assert_valid_raises_value_error_with_issue_codes() -> None:
    packet = load_fixture("valid_packet.json")
    packet["packet_version"] = 1
    with pytest.raises(ValueError, match="packet_version"):
        assert_valid_acceptance_packet_v2(packet)
