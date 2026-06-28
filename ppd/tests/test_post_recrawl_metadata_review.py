from __future__ import annotations

import json
from pathlib import Path

from ppd.source_freshness.post_recrawl_metadata_review import (
    build_post_recrawl_metadata_review_packet,
    normalize_document_ref,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "post_recrawl_metadata_review"
    / "archive_manifest_delta.json"
)


def test_normalize_document_ref_is_deterministic() -> None:
    assert normalize_document_ref(" LU_24-100002   DZM ") == "lu-24-100002 dzm"
    assert normalize_document_ref(None) is None
    assert normalize_document_ref("   ") is None


def test_build_packet_compares_expected_and_observed_metadata_only() -> None:
    delta = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    packet = build_post_recrawl_metadata_review_packet(delta)

    assert packet["fixture_id"] == "synthetic-archive-manifest-delta-001"
    assert packet["privacy"] == {
        "stores_page_bodies": False,
        "stores_pdfs": False,
        "stores_downloaded_documents": False,
        "metadata_only": True,
    }
    assert packet["summary"] == {
        "expected_count": 3,
        "observed_count": 3,
        "matched_count": 1,
        "metadata_changed_count": 1,
        "missing_observed_count": 1,
        "unexpected_observed_count": 1,
        "source_freshness_update_count": 1,
        "downstream_invalidation_candidate_count": 3,
    }

    by_url = {row["url"]: row for row in packet["comparisons"]}
    assert by_url["https://example.test/ppd/archive/lu-24-100001.pdf"]["outcome"] == "matched"
    assert by_url["https://example.test/ppd/archive/lu-24-100002.pdf"]["changed_fields"] == ["content_hash"]
    assert by_url["https://example.test/ppd/archive/lu-24-100003.pdf"]["outcome"] == "missing_observed"
    assert by_url["https://example.test/ppd/archive/lu-24-100004.pdf"]["outcome"] == "unexpected_observed"

    assert packet["source_freshness_updates"] == [
        {
            "source_id": "ppd-archive-search",
            "previous_fetched_at": "2026-05-20T10:00:00Z",
            "current_fetched_at": "2026-05-28T08:00:00Z",
            "changed": True,
        }
    ]
    assert {candidate["reason"] for candidate in packet["downstream_invalidation_candidates"]} == {
        "metadata_changed",
        "missing_observed",
        "unexpected_observed",
    }
