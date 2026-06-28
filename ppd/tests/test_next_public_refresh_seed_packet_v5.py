from __future__ import annotations

from pathlib import Path

import pytest

from ppd.agent_readiness.next_public_refresh_seed_packet_v5 import (
    OFFLINE_VALIDATION_COMMANDS,
    PACKET_VERSION,
    build_seed_packet_from_files,
    validate_seed_packet,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "next_public_refresh_seed_packet_v5"
REGISTRY_FIXTURE = FIXTURE_DIR / "current_public_source_registry_placeholders.json"
REHEARSAL_FIXTURE = FIXTURE_DIR / "post_activation_monitoring_rehearsal_v4.json"


def test_builds_fixture_first_seed_packet_without_live_boundaries() -> None:
    packet = build_seed_packet_from_files(REGISTRY_FIXTURE, REHEARSAL_FIXTURE)

    assert packet["packet_version"] == PACKET_VERSION
    assert packet["fixture_first"] is True
    assert packet["source_boundaries"] == {
        "live_crawl": False,
        "document_download": False,
        "raw_body_storage": False,
        "devhub_opened": False,
        "legal_or_permitting_guarantee": False,
    }
    assert packet["offline_validation_commands"] == OFFLINE_VALIDATION_COMMANDS
    assert packet["candidate_count"] == len(packet["candidates"])


def test_ranks_next_public_refresh_candidates_by_fixture_signals() -> None:
    packet = build_seed_packet_from_files(REGISTRY_FIXTURE, REHEARSAL_FIXTURE)
    candidates = packet["candidates"]

    assert [candidate["rank"] for candidate in candidates] == [1, 2, 3, 4]
    assert [candidate["source_id"] for candidate in candidates] == [
        "ppd-devhub-faq-placeholder",
        "ppd-submit-plans-online-placeholder",
        "ppd-fee-payment-guide-placeholder",
        "ppd-forms-index-placeholder",
    ]
    assert candidates[0]["stale_source_hold"] is True
    assert candidates[0]["changed_requirement_risk"] == "high"
    assert "stale_source_hold" in candidates[0]["skipped_source_reasons"]
    assert candidates[0]["reviewer_routing"] == "devhub-public-guidance-reviewer"
    assert "offline" in candidates[0]["rollback_notes"]


def test_validator_rejects_live_crawl_boundary() -> None:
    packet = build_seed_packet_from_files(REGISTRY_FIXTURE, REHEARSAL_FIXTURE)
    packet["source_boundaries"]["live_crawl"] = True

    with pytest.raises(ValueError, match="live_crawl"):
        validate_seed_packet(packet)


def test_validator_rejects_unsorted_candidates() -> None:
    packet = build_seed_packet_from_files(REGISTRY_FIXTURE, REHEARSAL_FIXTURE)
    packet["candidates"][0], packet["candidates"][1] = packet["candidates"][1], packet["candidates"][0]

    with pytest.raises(ValueError, match="sorted"):
        validate_seed_packet(packet)
