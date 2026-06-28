from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ppd.devhub.surface_registry_promotion_candidate import (
    REQUIRED_PACKET_TYPE,
    assert_valid_surface_registry_promotion_candidate_packet,
    build_surface_registry_promotion_candidate_packet,
    load_json_packet,
    validate_surface_registry_promotion_candidate_packet,
)


FIXTURE = Path(__file__).parent / "fixtures" / "devhub_surface_registry_promotion_candidate" / "input_packets.json"


def _inputs() -> dict[str, object]:
    return load_json_packet(FIXTURE)


def _packet() -> dict[str, object]:
    inputs = _inputs()
    return build_surface_registry_promotion_candidate_packet(
        inputs["pilot_evidence_review_packet"],
        inputs["surface_drift_comparison_packet"],
    )


def test_builds_fixture_first_surface_registry_promotion_candidate() -> None:
    packet = _packet()

    assert packet["packet_type"] == REQUIRED_PACKET_TYPE
    assert packet["fixture_first"] is True
    assert packet["active_promotion_state"] == "inactive"
    assert packet["stores_browser_artifacts"] is False
    assert packet["writes_surface_registry"] is False
    assert packet["mutates_active_surface_registry"] is False
    assert packet["mutates_active_surface_map"] is False
    assert validate_surface_registry_promotion_candidate_packet(packet) == ()
    assert_valid_surface_registry_promotion_candidate_packet(packet)


def test_candidate_contains_cited_deltas_thresholds_and_handoff_carryovers() -> None:
    packet = _packet()

    deltas = packet["synthetic_surface_map_deltas"]
    thresholds = packet["selector_confidence_thresholds"]
    carryovers = packet["manual_handoff_carryovers"]
    signoffs = packet["reviewer_signoff_slots"]

    assert len(deltas) == 1
    assert deltas[0]["promotion_effect"] == "synthetic_delta_only"
    assert deltas[0]["active_registry_mutation"] is False
    assert deltas[0]["citations"]
    assert deltas[0]["heading_deltas"][0]["status"] == "synthetic_difference"

    assert thresholds[0]["promotion_allowed"] is False
    assert thresholds[0]["threshold_action"] == "manual_handoff_before_active_registry"
    assert thresholds[0]["minimum_candidate_confidence"] == "redacted_fixture_review"
    assert thresholds[0]["active_registry_confidence_required"] == "attended_review_required"
    assert thresholds[0]["citations"]

    assert {item["carryover_id"] for item in carryovers} >= {
        "manual-login-required",
        "consequential-actions-blocked",
        "unsupported-drift-devhub_home_redacted",
    }
    assert all(item["status"] == "carried_forward" for item in carryovers)
    assert all(item["citations"] for item in carryovers)
    assert {slot["status"] for slot in signoffs} == {"pending"}
    assert all(slot["citations"] for slot in signoffs)


def test_candidate_records_redaction_and_no_active_promotion_attestations() -> None:
    packet = _packet()

    assert all(packet["redaction_attestations"].values())
    assert all(packet["no_active_promotion_attestations"].values())
    assert packet["no_active_promotion_attestations"]["active_surface_registry_not_mutated"] is True
    assert packet["no_active_promotion_attestations"]["selector_confidence_not_upgraded"] is True


def test_validator_rejects_active_promotion_or_private_browser_artifacts() -> None:
    packet = _packet()
    unsafe = deepcopy(packet)
    unsafe["active_promotion_state"] = "active"
    unsafe["writes_surface_registry"] = True
    unsafe["screenshot_path"] = "devhub-home.png"

    errors = validate_surface_registry_promotion_candidate_packet(unsafe)

    assert any("active_promotion_state must be inactive" in error for error in errors)
    assert any("writes_surface_registry must be false" in error for error in errors)
    assert any("screenshot_path must not store private DevHub or browser artifacts" in error for error in errors)


def test_validator_rejects_raw_authenticated_values_and_private_paths() -> None:
    packet = _packet()
    unsafe = deepcopy(packet)
    unsafe["raw_authenticated_values"] = {"permit_number": "123-private"}
    unsafe["review_notes"] = "raw authenticated value captured from DevHub"
    unsafe["local_private_path"] = "/home/reviewer/devhub/auth_state.json"

    errors = validate_surface_registry_promotion_candidate_packet(unsafe)

    assert any("raw_authenticated_values must not store private DevHub or browser artifacts" in error for error in errors)
    assert any("must not include raw authenticated values" in error for error in errors)
    assert any("local_private_path must not store private DevHub or browser artifacts" in error for error in errors)
    assert any("must not reference private paths or browser artifacts" in error for error in errors)


def test_validator_rejects_screenshots_traces_har_and_stored_auth_state() -> None:
    packet = _packet()
    unsafe = deepcopy(packet)
    unsafe["trace_path"] = "trace.zip"
    unsafe["har_path"] = "review.har"
    unsafe["stored_auth_state"] = "storage_state.json"

    errors = validate_surface_registry_promotion_candidate_packet(unsafe)

    assert any("trace_path must not store private DevHub or browser artifacts" in error for error in errors)
    assert any("har_path must not store private DevHub or browser artifacts" in error for error in errors)
    assert any("stored_auth_state must not store private DevHub or browser artifacts" in error for error in errors)


def test_validator_rejects_uncited_selector_changes_and_missing_thresholds() -> None:
    packet = _packet()
    unsafe = deepcopy(packet)
    unsafe["selector_confidence_thresholds"] = []
    unsafe["selector_change"] = {
        "selector": "role=button[name='Submit']",
        "status": "synthetic_difference",
        "candidate": "role=button[name='Submit permit']",
    }

    errors = validate_surface_registry_promotion_candidate_packet(unsafe)

    assert any("selector_confidence_thresholds must not be empty" in error for error in errors)
    assert any("selector changes must include citations" in error for error in errors)


def test_validator_rejects_missing_reviewer_signoffs() -> None:
    packet = _packet()
    unsafe = deepcopy(packet)
    unsafe["reviewer_signoff_slots"] = []

    errors = validate_surface_registry_promotion_candidate_packet(unsafe)

    assert any("reviewer_signoff_slots must not be empty" in error for error in errors)


def test_validator_rejects_enabled_consequential_controls_live_claims_and_mutation_flags() -> None:
    packet = _packet()
    unsafe = deepcopy(packet)
    unsafe["controls"] = [{"control_id": "submit-application", "action": "submit_application", "enabled": True}]
    unsafe["browser_execution"] = "live"
    unsafe["review_summary"] = "Ran Playwright against a real DevHub session."
    unsafe["active_surface_registry_mutation_flags"] = {"enabled": True}

    errors = validate_surface_registry_promotion_candidate_packet(unsafe)

    assert any("must not enable consequential controls" in error for error in errors)
    assert any("must remain fixture-only or review-only" in error for error in errors)
    assert any("must not claim live browser execution" in error for error in errors)
    assert any("must not include active surface-registry mutation flags" in error for error in errors)


def test_builder_rejects_input_with_enabled_registry_mutation() -> None:
    inputs = _inputs()
    evidence = deepcopy(inputs["pilot_evidence_review_packet"])
    evidence["surface_registry_mutation"]["active"] = True

    try:
        build_surface_registry_promotion_candidate_packet(evidence, inputs["surface_drift_comparison_packet"])
    except ValueError as exc:
        assert "active_surface_registry_mutation" in str(exc)
    else:
        raise AssertionError("expected active registry mutation input to be rejected")
