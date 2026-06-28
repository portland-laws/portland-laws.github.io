from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ppd.devhub.read_only_pilot_reconciliation import (
    REQUIRED_PACKET_TYPE,
    assert_valid_reconciliation_packet,
    build_post_observation_reconciliation_packet,
    load_json_packet,
    validate_reconciliation_packet,
)


FIXTURE = Path(__file__).parent / "fixtures" / "devhub_read_only_pilot_reconciliation" / "input_packets.json"


def _inputs() -> dict[str, object]:
    return load_json_packet(FIXTURE)


def _packet() -> dict[str, object]:
    inputs = _inputs()
    return build_post_observation_reconciliation_packet(
        inputs["operator_transcript_packet"],
        inputs["surface_registry_reviewer_approval_packet"],
        inputs["observation_redaction_review_packet"],
    )


def test_builds_fixture_first_post_observation_reconciliation_packet() -> None:
    packet = _packet()

    assert packet["packet_type"] == REQUIRED_PACKET_TYPE
    assert packet["fixture_first"] is True
    assert packet["offline_only"] is True
    assert packet["read_only_only"] is True
    assert packet["launches_devhub"] is False
    assert packet["launches_playwright"] is False
    assert packet["stores_browser_artifacts"] is False
    assert packet["writes_surface_registry"] is False
    assert packet["mutates_active_surface_registry"] is False
    assert packet["mutates_agent_state"] is False
    assert validate_reconciliation_packet(packet).ok is True
    assert_valid_reconciliation_packet(packet)


def test_packet_contains_cited_deltas_decisions_followups_and_owner_fields() -> None:
    packet = _packet()

    assert packet["observed_surface_deltas"]
    assert packet["observed_surface_deltas"][0]["decision"] == "keep_as_redacted_observation_delta"
    assert packet["observed_surface_deltas"][0]["citations"]
    assert all(row["active_registry_mutation"] is False for row in packet["observed_surface_deltas"])
    assert all(row["agent_state_mutation"] is False for row in packet["observed_surface_deltas"])

    assert packet["kept_decisions"]
    assert all(row["status"] == "kept_for_reviewer_packet_only" for row in packet["kept_decisions"])
    assert all(row["citations"] for row in packet["kept_decisions"])

    assert packet["manual_handoff_decisions"]
    assert all(row["decision"] == "manual_handoff_required" for row in packet["manual_handoff_decisions"])
    assert all(row["attended_operator_required"] is True for row in packet["manual_handoff_decisions"])
    assert all(row["live_devhub_launch_allowed_by_packet"] is False for row in packet["manual_handoff_decisions"])

    assert packet["redaction_follow_ups"]
    assert all(row["status"] == "open_for_reviewer_follow_up" for row in packet["redaction_follow_ups"])
    assert all(row["citations"] for row in packet["redaction_follow_ups"])

    assert packet["reviewer_owner_fields"]
    assert all(row["owner_id"] for row in packet["reviewer_owner_fields"])
    assert all(row["reviewer_id"] for row in packet["reviewer_owner_fields"])
    assert all(row["approval_required_before_live_use"] is True for row in packet["reviewer_owner_fields"])


def test_packet_records_no_registry_and_no_agent_state_mutation_attestations() -> None:
    packet = _packet()
    attestations = packet["no_active_surface_registry_no_agent_state_mutation_attestations"]

    assert all(attestations.values())
    assert attestations["no_active_surface_registry_read_or_write"] is True
    assert attestations["no_active_surface_registry_mutation"] is True
    assert attestations["no_agent_state_read_or_write"] is True
    assert attestations["no_agent_state_mutation"] is True


def test_validator_rejects_private_artifacts_enabled_consequential_controls_and_mutations() -> None:
    packet = _packet()
    unsafe = deepcopy(packet)
    unsafe["trace_path"] = "trace.zip"
    unsafe["controls"] = [{"control_id": "submit-application", "label": "Submit application", "enabled": True}]
    unsafe["writes_surface_registry"] = True
    unsafe["mutates_agent_state"] = True
    unsafe["observed_surface_deltas"][0]["citations"] = []

    result = validate_reconciliation_packet(unsafe)

    assert result.ok is False
    assert any("trace_path contains forbidden private/session field" in error for error in result.errors)
    assert any("must not enable consequential DevHub controls" in error for error in result.errors)
    assert any("writes_surface_registry must be false" in error for error in result.errors)
    assert any("mutates_agent_state must be false" in error for error in result.errors)
    assert any("observed_surface_deltas[0].citations must be non-empty" in error for error in result.errors)
