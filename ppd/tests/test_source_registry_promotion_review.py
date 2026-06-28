from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.source_freshness.source_registry_promotion_review import build_source_registry_promotion_review_packet
from ppd.source_freshness.source_registry_update_candidate import build_source_registry_update_candidate_packet

FIXTURE_DIR = Path(__file__).parent / "fixtures"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _valid_inputs() -> tuple[dict, dict]:
    readiness = _load_json(FIXTURE_DIR / "readiness" / "reconciliation_packet.json")
    recrawl_outcomes = _load_json(FIXTURE_DIR / "source_registry_update_candidate" / "reviewed_metadata_outcomes.json")
    candidate_packet = build_source_registry_update_candidate_packet(
        recrawl_outcomes,
        generated_at="2026-05-28T10:00:00Z",
    )
    return readiness, candidate_packet


def test_source_registry_promotion_review_accepts_fixture_first_candidate_packet() -> None:
    readiness, candidate_packet = _valid_inputs()

    packet = build_source_registry_promotion_review_packet(
        readiness,
        candidate_packet,
        generated_at="2026-05-28T10:00:00Z",
    )

    assert packet["review_mode"] == "promotion_review_only"
    assert packet["production_promotion_status"]["enabled"] is False
    assert packet["production_promotion_status"]["live_registry_records_edited"] is False
    assert packet["input_artifact_links"]["release_readiness_packet_id"] == readiness["packet_id"]
    assert packet["input_artifact_links"]["source_registry_candidate_fixture_id"] == candidate_packet["fixture_id"]
    changed_rows = packet["reviewed_metadata_only_field_changes"]
    assert changed_rows
    for row in changed_rows:
        for change in row["exact_metadata_field_changes"]:
            assert change["review_evidence_id"]


def test_source_registry_promotion_review_rejects_missing_release_snapshot_link() -> None:
    readiness, candidate_packet = _valid_inputs()
    readiness = copy.deepcopy(readiness)
    readiness.pop("linked_artifacts")

    with pytest.raises(ValueError, match="release readiness snapshot"):
        build_source_registry_promotion_review_packet(readiness, candidate_packet)


def test_source_registry_promotion_review_rejects_missing_candidate_link() -> None:
    readiness, candidate_packet = _valid_inputs()
    candidate_packet = copy.deepcopy(candidate_packet)
    candidate_packet.pop("fixture_id")

    with pytest.raises(ValueError, match="source registry candidate link"):
        build_source_registry_promotion_review_packet(readiness, candidate_packet)


def test_source_registry_promotion_review_rejects_uncited_field_changes() -> None:
    readiness, candidate_packet = _valid_inputs()
    candidate_packet = copy.deepcopy(candidate_packet)
    candidate_packet["source_registry_update_candidates"][0]["review_evidence_id"] = ""

    with pytest.raises(ValueError, match="uncited field changes"):
        build_source_registry_promotion_review_packet(readiness, candidate_packet)


def test_source_registry_promotion_review_rejects_private_authenticated_urls() -> None:
    readiness, candidate_packet = _valid_inputs()
    candidate_packet = copy.deepcopy(candidate_packet)
    candidate_packet["source_registry_update_candidates"][0]["canonical_url"] = "https://devhub.portlandoregon.gov/account"

    with pytest.raises(ValueError, match="private or authenticated URL"):
        build_source_registry_promotion_review_packet(readiness, candidate_packet)


def test_source_registry_promotion_review_rejects_raw_crawl_or_archive_paths() -> None:
    readiness, candidate_packet = _valid_inputs()
    candidate_packet = copy.deepcopy(candidate_packet)
    candidate_packet["source_registry_update_candidates"][0]["raw_archive_path"] = "/tmp/raw-crawl/source.warc.gz"

    with pytest.raises(ValueError, match="raw crawl or archive path"):
        build_source_registry_promotion_review_packet(readiness, candidate_packet)


def test_source_registry_promotion_review_rejects_downloaded_document_paths() -> None:
    readiness, candidate_packet = _valid_inputs()
    candidate_packet = copy.deepcopy(candidate_packet)
    candidate_packet["source_registry_update_candidates"][0]["downloaded_document_path"] = "/home/example/Downloads/permit.pdf"

    with pytest.raises(ValueError, match="downloaded document path"):
        build_source_registry_promotion_review_packet(readiness, candidate_packet)


def test_source_registry_promotion_review_rejects_unresolved_blocker_marked_approved() -> None:
    readiness, candidate_packet = _valid_inputs()
    readiness = copy.deepcopy(readiness)
    readiness["release_blockers"][0]["status"] = "approved"

    with pytest.raises(ValueError, match="unresolved blocker"):
        build_source_registry_promotion_review_packet(readiness, candidate_packet)


def test_source_registry_promotion_review_rejects_live_registry_replacement() -> None:
    readiness, candidate_packet = _valid_inputs()
    candidate_packet = copy.deepcopy(candidate_packet)
    candidate_packet["replacement_source_registry"] = [{"source_id": "live-replacement"}]

    with pytest.raises(ValueError, match="live registry replacement"):
        build_source_registry_promotion_review_packet(readiness, candidate_packet)
