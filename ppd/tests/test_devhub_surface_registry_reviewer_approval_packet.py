from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ppd.devhub.surface_registry_reviewer_approval_packet import (
    REQUIRED_PACKET_TYPE,
    assert_valid_surface_registry_reviewer_approval_packet,
    build_surface_registry_reviewer_approval_packet,
    load_json_packet,
    validate_surface_registry_reviewer_approval_packet,
)


FIXTURE = Path(__file__).parent / "fixtures" / "devhub_surface_registry_reviewer_approval_packet" / "input_packets.json"


def _inputs() -> dict[str, object]:
    return load_json_packet(FIXTURE)


def _packet() -> dict[str, object]:
    inputs = _inputs()
    return build_surface_registry_reviewer_approval_packet(
        inputs["promotion_candidate_packet"],
        inputs["pilot_evidence_review_packet"],
        inputs["surface_drift_comparison_packet"],
    )


def test_builds_fixture_first_reviewer_approval_packet() -> None:
    packet = _packet()

    assert packet["packet_type"] == REQUIRED_PACKET_TYPE
    assert packet["fixture_first"] is True
    assert packet["launches_devhub"] is False
    assert packet["launches_playwright"] is False
    assert packet["stores_browser_artifacts"] is False
    assert packet["writes_surface_registry"] is False
    assert packet["mutates_active_surface_registry"] is False
    assert validate_surface_registry_reviewer_approval_packet(packet) == ()
    assert_valid_surface_registry_reviewer_approval_packet(packet)


def test_packet_contains_cited_selector_approvals_signoffs_handoffs_and_rollback_notes() -> None:
    packet = _packet()

    approval_items = packet["selector_delta_approval_items"]
    assert approval_items
    assert approval_items[0]["approval_status"] == "pending_reviewer_approval"
    assert approval_items[0]["approval_effect"] == "reviewer_packet_only_no_promotion"
    assert approval_items[0]["active_registry_mutation"] is False
    assert approval_items[0]["citations"]

    assert {slot["status"] for slot in packet["reviewer_signoff_slots"]} == {"pending"}
    assert all(slot["owner"] for slot in packet["reviewer_signoff_slots"])
    assert all(slot["citations"] for slot in packet["reviewer_signoff_slots"])
    assert all(item["status"] == "carried_forward" for item in packet["manual_handoff_carryovers"])
    assert all(item["citations"] for item in packet["manual_handoff_carryovers"])
    assert all(note["active_rollback_executed"] is False for note in packet["rollback_notes"])
    assert all(note["citations"] for note in packet["rollback_notes"])


def test_packet_records_redaction_and_no_active_registry_mutation_attestations() -> None:
    packet = _packet()

    assert packet["redaction_attestations"]
    assert all(item["accepted"] is True for item in packet["redaction_attestations"])
    attestations = packet["no_active_surface_registry_mutation_attestations"]
    assert all(attestations.values())
    assert attestations["active_surface_registry_not_mutated"] is True
    assert attestations["no_auth_state_or_browser_artifacts_stored"] is True
    assert attestations["review_packet_only_no_promotion"] is True


def test_validator_rejects_missing_citations_private_artifacts_live_claims_and_mutations() -> None:
    packet = _packet()
    unsafe = deepcopy(packet)
    unsafe["selector_delta_approval_items"][0]["citations"] = []
    unsafe["trace_path"] = "trace.zip"
    unsafe["review_notes"] = "Ran Playwright in a live browser and captured raw authenticated value."
    unsafe["controls"] = [{"control_id": "submit-application", "action": "submit_application", "enabled": True}]
    unsafe["writes_surface_registry"] = True

    errors = validate_surface_registry_reviewer_approval_packet(unsafe)

    assert any("selector_delta_approval_items[0].citations must not be empty" in error for error in errors)
    assert any("trace_path must not contain private DevHub" in error for error in errors)
    assert any("must not claim live browser execution" in error for error in errors)
    assert any("must not include raw authenticated values" in error for error in errors)
    assert any("must not enable consequential DevHub controls" in error for error in errors)
    assert any("writes_surface_registry must be false" in error for error in errors)
    assert any("writes_surface_registry must not enable active surface-registry mutation" in error for error in errors)


def test_builder_rejects_unsafe_promotion_candidate_input() -> None:
    inputs = _inputs()
    promotion = deepcopy(inputs["promotion_candidate_packet"])
    promotion["writes_surface_registry"] = True

    try:
        build_surface_registry_reviewer_approval_packet(
            promotion,
            inputs["pilot_evidence_review_packet"],
            inputs["surface_drift_comparison_packet"],
        )
    except AssertionError as exc:
        assert "writes_surface_registry must be false" in str(exc)
    else:
        raise AssertionError("expected unsafe promotion candidate input to be rejected")
