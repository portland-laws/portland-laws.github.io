from pathlib import Path

import pytest

from ppd.extraction.requirement_node_candidate_set_v7 import (
    build_candidate_set_v7,
    load_work_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "requirement_reextract_v7" / "work_packet_v7.json"


def test_candidate_set_v7_uses_only_fixture_packet_rows() -> None:
    packet = load_work_packet(FIXTURE_PATH)

    candidate_set = build_candidate_set_v7(packet).to_dict()

    assert candidate_set["candidate_set_version"] == "requirement-node-candidate-set-v7"
    assert candidate_set["packet_id"] == "ppd-reextract-v7-fixture-001"
    assert candidate_set["offline_only"] is True
    assert len(candidate_set["rows"]) == 4
    assert {row["candidate_action"] for row in candidate_set["rows"]} == {
        "add",
        "update",
        "deprecate",
    }
    assert all(row["offline_fixture_only"] is True for row in candidate_set["rows"])


def test_candidate_set_v7_adds_review_placeholders_and_flags() -> None:
    packet = load_work_packet(FIXTURE_PATH)

    rows = {row["requirement_id"]: row for row in build_candidate_set_v7(packet).to_dict()["rows"]}

    fee_gate = rows["REQ-PPD-FEE-GATE-001"]
    assert fee_gate["candidate_action"] == "add"
    assert "permit_type_mapping_placeholder" in fee_gate["review_flags"]
    assert fee_gate["formalization_status"] == "formalization_placeholder"
    assert fee_gate["reviewer_owner"] == "reviewer_owner_placeholder"

    correction_upload = rows["REQ-PPD-CORRECTION-UPLOAD-001"]
    assert "conflict_review" in correction_upload["review_flags"]
    assert "stale_evidence_review" in correction_upload["review_flags"]

    legacy_upload = rows["REQ-PPD-LEGACY-UPLOAD-001"]
    assert legacy_upload["candidate_action"] == "deprecate"
    assert "deprecation_review" in legacy_upload["review_flags"]
    assert "stale_evidence_review" in legacy_upload["review_flags"]


def test_candidate_set_v7_reports_evidence_continuity() -> None:
    packet = load_work_packet(FIXTURE_PATH)

    continuity = {
        row["requirement_id"]: row
        for row in build_candidate_set_v7(packet).to_dict()["evidence_continuity"]
    }

    plan_review = continuity["REQ-PPD-PLAN-REVIEW-001"]
    assert plan_review["continuity_status"] == "continuous"
    assert plan_review["retained_evidence_ids"] == [
        "evidence::apply-permits::plan-review::2026-05-08"
    ]
    assert plan_review["added_evidence_ids"] == [
        "evidence::submit-plans-online::single-pdf::2026-05-08"
    ]

    legacy_upload = continuity["REQ-PPD-LEGACY-UPLOAD-001"]
    assert legacy_upload["continuity_status"] == "needs_review"
    assert legacy_upload["removed_evidence_ids"] == [
        "evidence::devhub-faq::upload-corrections::2026-05-08"
    ]


def test_candidate_set_v7_rejects_non_fixture_source_mode() -> None:
    packet = load_work_packet(FIXTURE_PATH)
    packet["source_mode"] = "live_crawl"

    with pytest.raises(ValueError, match="fixture_only"):
        build_candidate_set_v7(packet)


def test_candidate_set_v7_rejects_live_access_flag() -> None:
    packet = load_work_packet(FIXTURE_PATH)
    packet["live_access_performed"] = True

    with pytest.raises(ValueError, match="live_access_performed=false"):
        build_candidate_set_v7(packet)
