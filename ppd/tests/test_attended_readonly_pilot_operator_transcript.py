from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ppd.devhub.attended_readonly_pilot_operator_transcript import (
    assert_valid_operator_transcript_packet,
    load_operator_transcript_packet,
    validate_operator_transcript_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub_attended_readonly_pilot" / "operator_transcript_packet.json"


def _packet() -> dict:
    return load_operator_transcript_packet(FIXTURE_PATH)


def _errors(packet: dict) -> str:
    return "; ".join(validate_operator_transcript_packet(packet).errors)


def test_operator_transcript_fixture_is_valid() -> None:
    assert_valid_operator_transcript_packet(_packet())


def test_operator_transcript_rejects_unordered_observations() -> None:
    packet = _packet()
    packet["ordered_operator_observations"][1]["sequence"] = 3

    assert "sequence must be 2" in _errors(packet)


def test_operator_transcript_rejects_missing_attendance_checkpoints() -> None:
    packet = _packet()
    packet["ordered_operator_observations"] = [
        item for item in packet["ordered_operator_observations"] if item["kind"] != "manual_user_attendance_checkpoint"
    ]
    for index, item in enumerate(packet["ordered_operator_observations"], start=1):
        item["sequence"] = index

    assert "attendance checkpoint" in _errors(packet)


def test_operator_transcript_rejects_uncited_selector_confirmations() -> None:
    packet = _packet()
    for item in packet["ordered_operator_observations"]:
        if item["kind"] == "selector_confidence_confirmation":
            item["citations"] = []
            break

    assert "citations must be non-empty" in _errors(packet)


def test_operator_transcript_rejects_missing_redaction_summaries() -> None:
    packet = _packet()
    packet["ordered_operator_observations"] = [
        item for item in packet["ordered_operator_observations"] if item["kind"] != "redacted_page_state_summary"
    ]
    for index, item in enumerate(packet["ordered_operator_observations"], start=1):
        item["sequence"] = index

    assert "redacted page state summary" in _errors(packet)


def test_operator_transcript_rejects_missing_reviewer_owners() -> None:
    packet = _packet()
    packet["reviewer_owner_fields"]["owner"] = ""

    assert "reviewer_owner_fields.owner is required" in _errors(packet)


def test_operator_transcript_rejects_raw_authenticated_values_and_private_artifacts() -> None:
    packet = _packet()
    packet["ordered_operator_observations"][0]["raw_authenticated_text"] = "raw authenticated value: permit applicant secret"

    errors = _errors(packet)
    assert "private/session artifact fields" in errors
    assert "raw authenticated values" in errors


def test_operator_transcript_rejects_local_private_paths_screenshots_traces_har_and_auth_state() -> None:
    packet = _packet()
    packet["prohibited_artifacts"]["auth_state_files"] = ["/home/example/auth_state.json"]
    packet["prohibited_artifacts"]["screenshots"] = ["screenshot.png"]
    packet["prohibited_artifacts"]["traces"] = ["trace.zip"]
    packet["prohibited_artifacts"]["har_files"] = ["devhub.har"]

    errors = _errors(packet)
    assert "auth_state_files must be an empty list" in errors
    assert "screenshots must be an empty list" in errors
    assert "traces must be an empty list" in errors
    assert "har_files must be an empty list" in errors
    assert "private paths" in errors


def test_operator_transcript_rejects_live_browser_execution_claims() -> None:
    packet = _packet()
    packet["ordered_operator_observations"][0]["operator_observation"] = "Operator launched live browser and captured screenshot evidence."

    assert "live browser execution" in _errors(packet)


def test_operator_transcript_rejects_enabled_consequential_controls() -> None:
    packet = _packet()
    packet["controls"] = [{"control_id": "submit-permit", "label": "Submit permit", "enabled": True}]

    assert "must not enable consequential controls" in _errors(packet)


def test_operator_transcript_rejects_active_surface_registry_or_agent_state_mutation_flags() -> None:
    packet = _packet()
    packet["active_surface_registry_mutation"] = True
    packet["agent_state_mutation_enabled"] = True

    errors = _errors(packet)
    assert "active_surface_registry_mutation must not enable" in errors
    assert "agent_state_mutation_enabled must not enable" in errors


def test_operator_transcript_validation_does_not_mutate_packet() -> None:
    packet = _packet()
    original = deepcopy(packet)

    assert_valid_operator_transcript_packet(packet)

    assert packet == original
