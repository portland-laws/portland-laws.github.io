from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.source_registry_promotion_rehearsal import (
    RehearsalPacketError,
    build_rehearsal_packet,
    validate_rehearsal_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "source_registry_promotion"


def _load_fixture(name: str) -> dict:
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _safe_packet() -> dict:
    return build_rehearsal_packet(_load_fixture("promotion_review.json"), _load_fixture("public_recrawl_operator_checklist.json"))


def test_builds_expected_disabled_rehearsal_packet() -> None:
    packet = _safe_packet()

    assert packet == _load_fixture("expected_rehearsal_packet.json")
    assert packet["promotion_decision"]["enabled"] is False
    assert packet["promotion_decision"]["decision"] == "rehearsal_only_defer_promotion"
    assert packet["safety"]["live_source_records_edited"] is False
    assert packet["safety"]["raw_crawl_output_included"] is False
    assert packet["safety"]["authenticated_state_included"] is False


def test_rejects_live_source_record_field_edits() -> None:
    review = _load_fixture("promotion_review.json")
    review["candidate_metadata_diffs"][0]["metadata_field_diffs"].append(
        {
            "field": "freshness_status",
            "before": "stale",
            "after": "fresh",
            "reason": "This would edit a live source registry field, not rehearsal metadata.",
        }
    )

    with pytest.raises(RehearsalPacketError, match="live source record field edit"):
        build_rehearsal_packet(review, _load_fixture("public_recrawl_operator_checklist.json"))


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda packet: packet["consumes"].pop("promotion_review_id"), "promotion-review link"),
        (lambda packet: packet["consumes"].pop("operator_checklist_id"), "operator-checklist link"),
        (lambda packet: packet.update({"raw_crawl_output_path": "ppd/raw-crawl/run-1/page.html"}), "raw crawl or archive path"),
        (lambda packet: packet.update({"archive_path": "ppd/archive-raw/run-1.warc.gz"}), "raw crawl or archive path"),
        (lambda packet: packet.update({"downloaded_document_path": "/tmp/downloads/devhub-faq.pdf"}), "downloaded document"),
        (lambda packet: packet.update({"replace_live_registry": True}), "direct live registry replacement"),
        (lambda packet: packet["rollback_checkpoints"].clear(), "rollback_checkpoints"),
        (lambda packet: packet["metadata_only_field_diffs"][0].update({"canonical_url": "https://devhub.portlandoregon.gov/permits/123?token=secret"}), "private or authenticated"),
    ],
)
def test_validation_rejects_unsafe_rehearsal_packets(mutator, message: str) -> None:
    packet = _safe_packet()
    mutator(packet)

    with pytest.raises(RehearsalPacketError, match=message):
        validate_rehearsal_packet(packet)


def test_rejects_unresolved_blockers_marked_approved() -> None:
    review = _load_fixture("promotion_review.json")
    review["unresolved_blockers"] = ["blocker-source-citation"]
    review["release_blockers"] = [
        {
            "id": "blocker-source-citation",
            "status": "approved",
            "resolved": False,
            "summary": "Still lacks cited evidence.",
        }
    ]

    with pytest.raises(RehearsalPacketError, match="unresolved blocker cannot be marked approved"):
        build_rehearsal_packet(review, _load_fixture("public_recrawl_operator_checklist.json"))


def test_validation_rejects_missing_matching_input_artifact_links() -> None:
    packet = _safe_packet()
    broken = copy.deepcopy(packet)
    broken["input_artifact_links"]["promotion_review_id"] = "different-review"

    with pytest.raises(RehearsalPacketError, match="matching promotion-review link"):
        validate_rehearsal_packet(broken)
