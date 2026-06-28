from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from ppd.devhub.attended_read_only_pilot_launch_readiness_packet import (
    REQUIRED_PACKET_ID,
    assert_valid_attended_read_only_pilot_launch_readiness_packet,
    build_attended_read_only_pilot_launch_readiness_packet,
    load_json_packet,
    validate_attended_read_only_pilot_launch_readiness_packet,
)
from ppd.devhub.surface_registry_reviewer_approval_packet import build_surface_registry_reviewer_approval_packet


FIXTURE_DIR = Path(__file__).parent / "fixtures"
RUNBOOK_PATH = FIXTURE_DIR / "devhub" / "attended_read_only_pilot_runbook_packet.json"
APPROVAL_INPUTS_PATH = FIXTURE_DIR / "devhub_surface_registry_reviewer_approval_packet" / "input_packets.json"
EVIDENCE_PATH = FIXTURE_DIR / "devhub_read_only_pilot_evidence_review" / "valid_packet.json"
REDACTION_PATH = FIXTURE_DIR / "devhub_read_only_observation_redaction_review" / "review_packet.json"
LAUNCH_PACKET_PATH = FIXTURE_DIR / "devhub_attended_read_only_pilot_launch_readiness" / "launch_readiness_packet.json"


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _approval_packet() -> dict[str, object]:
    inputs = load_json_packet(APPROVAL_INPUTS_PATH)
    return build_surface_registry_reviewer_approval_packet(
        inputs["promotion_candidate_packet"],
        inputs["pilot_evidence_review_packet"],
        inputs["surface_drift_comparison_packet"],
    )


def _built_packet() -> dict[str, object]:
    return build_attended_read_only_pilot_launch_readiness_packet(
        _load(RUNBOOK_PATH),
        _approval_packet(),
        _load(EVIDENCE_PATH),
        _load(REDACTION_PATH),
    )


def test_builds_fixture_first_launch_readiness_packet_from_required_inputs() -> None:
    packet = _built_packet()

    assert packet["packet_id"] == REQUIRED_PACKET_ID
    assert packet["fixture_first"] is True
    assert packet["offline_only"] is True
    assert packet["read_only_only"] is True
    assert packet["manual_attendance_required"] is True
    assert packet["launches_browser"] is False
    assert packet["launches_playwright"] is False
    assert packet["stores_auth_state"] is False
    assert packet["stores_screenshots"] is False
    assert packet["stores_traces"] is False
    assert packet["takes_official_action"] is False
    assert validate_attended_read_only_pilot_launch_readiness_packet(packet) == ()
    assert_valid_attended_read_only_pilot_launch_readiness_packet(packet)


def test_committed_launch_readiness_fixture_is_valid_and_consumes_all_source_packets() -> None:
    packet = _load(LAUNCH_PACKET_PATH)

    assert validate_attended_read_only_pilot_launch_readiness_packet(packet) == ()
    sources = packet["source_packets"]
    assert sources["devhub_attended_read_only_pilot_runbook"]["consumed"] is True
    assert sources["devhub_surface_registry_reviewer_approval_packet"]["consumed"] is True
    assert sources["devhub_read_only_pilot_evidence_review_packet"]["consumed"] is True
    assert sources["devhub_observation_redaction_review_packet"]["consumed"] is True


def test_launch_packet_contains_cited_prerequisites_stops_redaction_selector_notes_and_signoffs() -> None:
    packet = _load(LAUNCH_PACKET_PATH)

    assert packet["attendance_prerequisites"]
    assert packet["manual_stop_points"]
    assert packet["redaction_checklist_items"]
    assert packet["selector_confidence_notes"]
    assert packet["reviewer_owner_signoff_slots"]
    assert all(item["citations"] for item in packet["attendance_prerequisites"])
    assert all(item["agent_action"] == "stop_and_record_commit_safe_refusal" for item in packet["manual_stop_points"])
    assert all(item["private_value_allowed"] is False for item in packet["redaction_checklist_items"])
    assert all(item["launch_effect"] == "notes_only_no_registry_promotion" for item in packet["selector_confidence_notes"])
    assert all(slot["status"] == "pending" for slot in packet["reviewer_owner_signoff_slots"])
    assert all(slot["can_enable_official_action"] is False for slot in packet["reviewer_owner_signoff_slots"])


def test_launch_packet_has_required_no_browser_no_auth_no_screenshot_no_trace_no_official_action_attestations() -> None:
    packet = _load(LAUNCH_PACKET_PATH)
    attestations = packet["launch_attestations"]

    assert attestations["no_browser_execution"] is True
    assert attestations["no_auth_state_saved"] is True
    assert attestations["no_screenshots_saved"] is True
    assert attestations["no_traces_saved"] is True
    assert attestations["no_official_action_taken"] is True
    assert attestations["no_registry_mutation"] is True


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("launches_browser", True, "launches_browser must be false"),
        ("stores_auth_state", True, "stores_auth_state must be false"),
        ("stores_screenshots", True, "stores_screenshots must be false"),
        ("stores_traces", True, "stores_traces must be false"),
        ("takes_official_action", True, "takes_official_action must be false"),
    ],
)
def test_validator_rejects_launch_readiness_safety_flag_regressions(field: str, value: object, expected: str) -> None:
    packet = _load(LAUNCH_PACKET_PATH)
    packet[field] = value

    errors = validate_attended_read_only_pilot_launch_readiness_packet(packet)

    assert expected in errors


def test_validator_rejects_private_artifacts_live_claims_and_enabled_consequential_controls() -> None:
    packet = _load(LAUNCH_PACKET_PATH)
    unsafe = deepcopy(packet)
    unsafe["trace_path"] = "trace.zip"
    unsafe["review_note"] = "Playwright clicked in a live browser and captured a screenshot."
    unsafe["controls"] = [{"control_id": "submit-application", "enabled": True}]

    errors = validate_attended_read_only_pilot_launch_readiness_packet(unsafe)

    assert any("private DevHub artifact keys" in error for error in errors)
    assert any("live browser execution" in error for error in errors)
    assert any("consequential DevHub controls" in error for error in errors)


def test_builder_rejects_unsafe_source_packet() -> None:
    runbook = _load(RUNBOOK_PATH)
    runbook["launches_browser"] = True

    with pytest.raises(AssertionError, match="launches_browser must be false"):
        build_attended_read_only_pilot_launch_readiness_packet(
            runbook,
            _approval_packet(),
            _load(EVIDENCE_PATH),
            _load(REDACTION_PATH),
        )
