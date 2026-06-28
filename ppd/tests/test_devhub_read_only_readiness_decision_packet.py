from __future__ import annotations

import json
from pathlib import Path

from ppd.devhub.read_only_readiness_decision_packet import (
    REQUIRED_DEFERRALS,
    assert_valid_read_only_readiness_decision_packet,
    build_read_only_readiness_decision_packet,
    validate_read_only_readiness_decision_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"
CHECKLIST_PATH = FIXTURE_DIR / "devhub_attended_read_only" / "devhub_observation_checklist_packet.json"
SURFACE_CANDIDATE_PATH = FIXTURE_DIR / "devhub_surface_registry_update_candidate" / "surface_registry_update_candidate_packet.json"
AUDIT_PATH = FIXTURE_DIR / "post_release_audit" / "findings_packets.json"
EXPECTED_PATH = FIXTURE_DIR / "devhub_read_only_readiness_decision" / "read_only_readiness_decision_packet.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_read_only_readiness_decision_packet_consumes_prerequisite_packets_without_browser_launch() -> None:
    audit_fixtures = _load(AUDIT_PATH)

    packet = build_read_only_readiness_decision_packet(
        _load(CHECKLIST_PATH),
        _load(SURFACE_CANDIDATE_PATH),
        audit_fixtures["valid"],
    )

    assert packet["packet_type"] == "ppd.devhub.read_only_readiness_decision_packet.v1"
    assert packet["fixture_first"] is True
    assert packet["offline_only"] is True
    assert packet["launches_devhub"] is False
    assert packet["launches_playwright"] is False
    assert packet["network_requests_made"] is False
    assert packet["stores_private_artifacts"] is False
    assert packet["source_packets"]["devhub_read_only_pilot_operator_checklist"]["consumed"] is True
    assert packet["source_packets"]["devhub_surface_registry_update_candidate"]["consumed"] is True
    assert packet["source_packets"]["post_release_audit_findings_packet"]["consumed"] is True
    assert {row["action_id"] for row in packet["explicit_deferrals"]} == set(REQUIRED_DEFERRALS)
    assert all(row["allowed"] is False for row in packet["explicit_deferrals"])
    assert all(row["deferred"] is True for row in packet["explicit_deferrals"])
    assert any(row["owner_id"] == "devhub_surface_reviewer" for row in packet["reviewer_owners"])
    assert any("Do not store screenshots" in row["prohibition"] for row in packet["private_artifact_prohibitions"])
    assert validate_read_only_readiness_decision_packet(packet) == ()


def test_committed_read_only_readiness_decision_fixture_is_valid_and_explicitly_defers_actions() -> None:
    packet = _load(EXPECTED_PATH)

    assert_valid_read_only_readiness_decision_packet(packet)
    deferrals = {row["action_id"]: row for row in packet["explicit_deferrals"]}
    for action_id in REQUIRED_DEFERRALS:
        assert deferrals[action_id]["allowed"] is False
        assert deferrals[action_id]["requires_future_attended_confirmation"] is True

    abort_text = "\n".join(row["condition"] for row in packet["abort_conditions"])
    assert "MFA" in abort_text
    assert "payment" in abort_text
    assert "upload" in abort_text
