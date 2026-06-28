from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.post_recrawl_decision_queue import (
    PostRecrawlPacketError,
    build_invalidation_queue,
    export_invalidation_queue,
    load_post_recrawl_packet,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_recrawl"


def test_metadata_review_packet_builds_freshness_ordered_queue() -> None:
    packet = load_post_recrawl_packet(FIXTURE_DIR / "metadata_review_packet.json")

    queue = build_invalidation_queue(packet)

    assert queue
    assert [decision.freshness_risk for decision in queue] == sorted(
        [decision.freshness_risk for decision in queue], reverse=True
    )
    assert queue[0].decision_kind == "source"
    assert queue[0].target_id == "source:devhub-faq"
    assert "content_hash_changed" in queue[0].reasons

    kinds = {decision.decision_kind for decision in queue}
    assert kinds == {"source", "requirement", "process_model", "guardrail", "agent_readiness"}


def test_queue_preserves_metadata_only_and_does_not_change_active_bundles() -> None:
    packet = load_post_recrawl_packet(FIXTURE_DIR / "metadata_review_packet.json")

    exported = export_invalidation_queue(packet)

    assert exported["raw_body_persisted"] is False
    assert exported["active_bundle_change"] is False
    assert exported["decision_count"] == len(exported["decisions"])
    assert all(decision["raw_body_persisted"] is False for decision in exported["decisions"])
    assert all(decision["active_bundle_change"] is False for decision in exported["decisions"])

    encoded = json.dumps(exported, sort_keys=True)
    assert "raw_html" not in encoded
    assert "document_body" not in encoded
    assert "authenticated_values" not in encoded


def test_raw_body_fields_are_rejected() -> None:
    packet = load_post_recrawl_packet(FIXTURE_DIR / "metadata_review_packet.json")
    packet["sources"][0]["raw_html"] = "not commit safe"

    with pytest.raises(PostRecrawlPacketError):
        build_invalidation_queue(packet)


def test_active_bundle_changes_are_rejected() -> None:
    packet = load_post_recrawl_packet(FIXTURE_DIR / "metadata_review_packet.json")
    packet["active_bundle_change"] = True

    with pytest.raises(PostRecrawlPacketError):
        build_invalidation_queue(packet)
