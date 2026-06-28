from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ppd.public_refresh.public_refresh_preflight_packet_v5 import (
    MODE,
    PACKET_VERSION,
    VALIDATION_COMMANDS,
    PublicRefreshPreflightPacketV5Error,
    PublicRefreshPreflightPacketV5ValidationError,
    assemble_preflight_packet,
    assert_valid_preflight_packet,
    validate_preflight_packet,
)
from ppd.public_refresh.next_public_refresh_seed_packet_v5 import load_packet

FIXTURE_DIR = Path(__file__).parent / "fixtures"
SEED_FIXTURE = FIXTURE_DIR / "next_public_refresh_seed_packet_v5" / "valid_packet.json"
EXPECTED_FIXTURE = FIXTURE_DIR / "public_refresh_preflight_packet_v5" / "expected_packet.json"


def _seed_packet() -> dict:
    return load_packet(SEED_FIXTURE)


def _valid_packet() -> dict[str, Any]:
    return assemble_preflight_packet(_seed_packet())


def test_assembles_expected_fixture_first_preflight_packet_v5() -> None:
    packet = _valid_packet()
    expected = load_packet(EXPECTED_FIXTURE)

    assert packet == expected
    assert packet["packet_version"] == PACKET_VERSION
    assert packet["mode"] == MODE
    assert packet["offline_only"] is True
    assert packet["validation_commands"] == VALIDATION_COMMANDS
    assert validate_preflight_packet(packet) == []


def test_packet_refuses_live_crawl_download_raw_body_devhub_and_guarantees() -> None:
    packet = _valid_packet()
    policy = packet["source_fixture_policy"]

    assert policy["accepted_input"] == "next public refresh seed packet v5 fixture only"
    assert policy["live_crawl_permitted"] is False
    assert policy["document_download_permitted"] is False
    assert policy["raw_body_storage_permitted"] is False
    assert policy["devhub_access_permitted"] is False
    assert policy["legal_or_permitting_guarantees_permitted"] is False
    assert packet["raw_body_persistence_refusal"]["decision"] == "refuse_raw_body_persistence"


def test_packet_inventory_covers_skips_reviewer_holds_and_processor_blocks() -> None:
    packet = _valid_packet()

    assert packet["skipped_source_inventory"] == [
        {
            "seed_id": "seed-file-standards-review-hold",
            "skipped_source_reason": "robots_or_policy_disallowed",
            "reviewer_route": "PPD stale source hold review",
        }
    ]
    assert packet["reviewer_holds"]["candidate_holds"] == [
        {
            "seed_id": "seed-file-standards-review-hold",
            "stale_source_hold_key": "hold-file-standards-review",
            "hold_disposition": "candidate remains reviewer-held until stale file-standard evidence is reconciled",
            "reviewer_route": "PPD stale source hold review",
        }
    ]
    assert [row["processor_handoff_state"] for row in packet["processor_handoff_readiness"]] == [
        "metadata_manifest_candidate_ready",
        "blocked_by_skip_or_reviewer_hold",
    ]


@pytest.mark.parametrize(
    ("field", "expected_error"),
    [
        ("input_packet_version", "missing packet.input_packet_version"),
        ("allowlist_checks", "missing packet.allowlist_checks"),
        ("robots_policy_preflight_placeholders", "missing packet.robots_policy_preflight_placeholders"),
        ("processor_handoff_readiness", "missing packet.processor_handoff_readiness"),
        ("raw_body_persistence_refusal", "missing packet.raw_body_persistence_refusal"),
        ("rate_limit_notes", "missing packet.rate_limit_notes"),
        ("skipped_source_inventory", "missing packet.skipped_source_inventory"),
        ("reviewer_holds", "missing packet.reviewer_holds"),
        ("rollback_notes", "missing packet.rollback_notes"),
        ("validation_commands", "missing packet.validation_commands"),
    ],
)
def test_validate_rejects_missing_required_preflight_sections(field: str, expected_error: str) -> None:
    packet = _valid_packet()
    del packet[field]

    errors = validate_preflight_packet(packet)

    assert expected_error in errors


@pytest.mark.parametrize(
    "mutator, expected_fragment",
    [
        (
            lambda packet: packet["allowlist_checks"][0].pop("seed_id"),
            "missing packet.allowlist_checks[0].seed_id",
        ),
        (
            lambda packet: packet["allowlist_checks"][0].pop("source_registry_placeholder_id"),
            "missing packet.allowlist_checks[0].source_registry_placeholder_id",
        ),
        (
            lambda packet: packet["allowlist_checks"][0].pop("source_registry_ref"),
            "missing packet.allowlist_checks[0].source_registry_ref",
        ),
        (
            lambda packet: packet["processor_handoff_readiness"][0].pop("source_registry_placeholder_id"),
            "missing packet.processor_handoff_readiness[0].source_registry_placeholder_id",
        ),
        (
            lambda packet: packet["rollback_notes"]["candidate_level"][0].pop("seed_id"),
            "missing packet.rollback_notes.candidate_level[0].seed_id",
        ),
    ],
)
def test_validate_rejects_missing_seed_packet_references(mutator: Any, expected_fragment: str) -> None:
    packet = _valid_packet()
    mutator(packet)

    errors = validate_preflight_packet(packet)

    assert expected_fragment in errors


@pytest.mark.parametrize(
    "field, value",
    [
        ("live_crawl_claim", "live crawl completed for this seed"),
        ("raw_body_artifact", "raw body artifact saved to fixture"),
        ("download_claim", "downloaded document is available"),
        ("private_session_artifact", "auth_state and session_state captured"),
        ("legal_guarantee", "legal guarantee and approval guaranteed"),
        ("mutation_claim", "active mutation enabled for release"),
    ],
)
def test_validate_rejects_forbidden_claim_text(field: str, value: str) -> None:
    packet = _valid_packet()
    packet[field] = value

    errors = validate_preflight_packet(packet)

    assert any("forbidden live, raw, downloaded, private, auth, guarantee, or mutation claim" in error for error in errors)


@pytest.mark.parametrize(
    "field, value",
    [
        ("active_mutation", True),
        ("active_mutation_flags", ["mutates_registry"]),
        ("live_crawl_enabled", True),
        ("download_enabled", True),
        ("auth_enabled", True),
        ("official_action_enabled", True),
    ],
)
def test_validate_rejects_active_mutation_flags(field: str, value: Any) -> None:
    packet = _valid_packet()
    packet["unsafe_flags"] = {field: value}

    errors = validate_preflight_packet(packet)

    assert any("active mutation flag must be false, empty, or absent" in error for error in errors)


def test_assert_valid_preflight_packet_raises_validation_error() -> None:
    packet = _valid_packet()
    packet["source_fixture_policy"]["live_crawl_permitted"] = True

    with pytest.raises(PublicRefreshPreflightPacketV5ValidationError, match="live_crawl_permitted"):
        assert_valid_preflight_packet(packet)


def test_rejects_non_seed_packet_input() -> None:
    with pytest.raises(PublicRefreshPreflightPacketV5Error, match="seed packet must be a JSON object"):
        assemble_preflight_packet([])  # type: ignore[arg-type]


def test_rejects_invalid_seed_packet_fixture() -> None:
    packet = deepcopy(_seed_packet())
    del packet["refresh_candidate_ranking"][0]["seed_id"]

    with pytest.raises(ValueError, match="next public refresh seed packet v5 rejected"):
        assemble_preflight_packet(packet)
