from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.public_refresh_authorization_v6 import (
    assert_valid_public_refresh_authorization_packet_v6,
    validate_public_refresh_authorization_packet_v6,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_refresh_authorization_v6"


def _load_fixture(name: str) -> dict[str, object]:
    with (FIXTURE_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


def test_valid_public_refresh_authorization_packet_v6_fixture_passes() -> None:
    packet = _load_fixture("valid_packet.json")

    assert validate_public_refresh_authorization_packet_v6(packet) == []
    assert_valid_public_refresh_authorization_packet_v6(packet)


@pytest.mark.parametrize(
    "field",
    [
        "freshness_watchlist_refs",
        "smoke_replay_refs",
        "live_crawl_deferral_criteria",
        "allowlisted_source_groups",
        "robots_policy_preflight_checklist_rows",
        "no_raw_body_persistence_reminders",
        "processor_handoff_manifest_expectations",
        "reviewer_authorization_placeholders",
        "abort_thresholds",
        "validation_commands",
    ],
)
def test_public_refresh_authorization_packet_v6_rejects_missing_required_rows(field: str) -> None:
    packet = _load_fixture("valid_packet.json")
    packet.pop(field)

    errors = validate_public_refresh_authorization_packet_v6(packet)

    assert any(field in error for error in errors)


@pytest.mark.parametrize(
    "field",
    [
        "claims_live_crawl_execution",
        "has_downloaded_or_raw_crawl_artifacts",
        "has_private_session_or_auth_artifacts",
        "claims_official_action_completion",
        "claims_legal_or_permitting_guarantees",
        "has_active_mutation_flags",
    ],
)
def test_public_refresh_authorization_packet_v6_rejects_prohibited_flags(field: str) -> None:
    packet = _load_fixture("valid_packet.json")
    packet[field] = True

    errors = validate_public_refresh_authorization_packet_v6(packet)

    assert f"prohibited {field}" in errors


def test_public_refresh_authorization_packet_v6_rejects_prohibited_claim_text() -> None:
    packet = _load_fixture("valid_packet.json")
    packet["notes"] = ["No legal guarantee may be made by this packet."]

    with pytest.raises(ValueError):
        assert_valid_public_refresh_authorization_packet_v6(packet)
