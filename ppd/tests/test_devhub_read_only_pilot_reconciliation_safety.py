from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ppd.devhub.read_only_pilot_reconciliation import build_post_observation_reconciliation_packet, load_json_packet
from ppd.devhub.read_only_pilot_reconciliation_safety import (
    assert_commit_safe_reconciliation_packet,
    validate_commit_safe_reconciliation_packet,
)


FIXTURE = Path(__file__).parent / "fixtures" / "devhub_read_only_pilot_reconciliation" / "input_packets.json"


def _packet() -> dict[str, object]:
    inputs = load_json_packet(FIXTURE)
    return build_post_observation_reconciliation_packet(
        inputs["operator_transcript_packet"],
        inputs["surface_registry_reviewer_approval_packet"],
        inputs["observation_redaction_review_packet"],
    )


def test_commit_safe_reconciliation_packet_accepts_fixture_builder_output() -> None:
    packet = _packet()

    result = validate_commit_safe_reconciliation_packet(packet)

    assert result.ok is True
    assert result.errors == ()
    assert_commit_safe_reconciliation_packet(packet)


def test_commit_safe_reconciliation_rejects_missing_required_review_sections() -> None:
    packet = _packet()
    unsafe = deepcopy(packet)
    unsafe["manual_handoff_decisions"] = []
    unsafe["redaction_follow_ups"] = []
    unsafe["reviewer_owner_fields"] = []
    unsafe["observed_surface_deltas"][0]["citations"] = []

    result = validate_commit_safe_reconciliation_packet(unsafe)

    assert result.ok is False
    assert "manual_handoff_decisions must be non-empty" in result.errors
    assert "redaction_follow_ups must be non-empty" in result.errors
    assert "reviewer_owner_fields must be non-empty" in result.errors
    assert "observed_surface_deltas[0].citations must be non-empty" in result.errors


def test_commit_safe_reconciliation_rejects_private_browser_artifacts_and_local_paths() -> None:
    packet = _packet()
    unsafe = deepcopy(packet)
    unsafe["session_state"] = {"stored": True}
    unsafe["screenshot_path"] = "/home/user/devhub/screenshot.png"
    unsafe["trace_path"] = "trace.zip"
    unsafe["har_path"] = "/tmp/devhub.har"
    unsafe["storage_state_path"] = "/Users/operator/storage_state.json"
    unsafe["raw_authenticated_text"] = "private DevHub page text"

    result = validate_commit_safe_reconciliation_packet(unsafe)

    assert result.ok is False
    assert any("session_state contains forbidden private/session artifact field" in error for error in result.errors)
    assert any("screenshot_path contains forbidden private/session artifact field" in error for error in result.errors)
    assert any("trace_path contains forbidden private/session artifact field" in error for error in result.errors)
    assert any("har_path contains forbidden private/session artifact field" in error for error in result.errors)
    assert any("storage_state_path contains forbidden private/session artifact field" in error for error in result.errors)
    assert any("raw_authenticated_text contains forbidden private/session artifact field" in error for error in result.errors)
    assert any("contains private value or browser artifact reference" in error for error in result.errors)


def test_commit_safe_reconciliation_rejects_live_claims_outcome_guarantees_controls_and_mutations() -> None:
    packet = _packet()
    unsafe = deepcopy(packet)
    unsafe["observed_surface_deltas"][0]["operator_note"] = "Launched live browser, ran Playwright, and clicked in DevHub."
    unsafe["kept_decisions"][0]["guarantee"] = "Permit approval is guaranteed after this reconciliation."
    unsafe["controls"] = [{"control_id": "submit-application", "label": "Submit permit application", "enabled": True}]
    unsafe["nested_flags"] = {
        "surface_registry_mutation_enabled": True,
        "active_agent_state_mutation": True,
    }

    result = validate_commit_safe_reconciliation_packet(unsafe)

    assert result.ok is False
    assert any("must not claim live browser execution" in error for error in result.errors)
    assert any("must not guarantee legal or permitting outcomes" in error for error in result.errors)
    assert any("must not enable consequential DevHub controls" in error for error in result.errors)
    assert any("surface_registry_mutation_enabled must not enable active surface-registry or agent-state mutation" in error for error in result.errors)
    assert any("active_agent_state_mutation must not enable active surface-registry or agent-state mutation" in error for error in result.errors)
