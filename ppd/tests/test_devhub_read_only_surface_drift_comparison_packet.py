from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from ppd.devhub.read_only_surface_drift_comparison_packet import (
    REQUIRED_PACKET_TYPE,
    assert_valid_read_only_surface_drift_comparison_packet,
    build_read_only_surface_drift_comparison_packet,
    load_json_packet,
    validate_read_only_surface_drift_comparison_packet,
)


FIXTURES = Path(__file__).parent / "fixtures"
OBSERVATION_PACKET = FIXTURES / "devhub" / "read_only_observation_packet_valid.json"
SURFACE_CANDIDATE = FIXTURES / "devhub_surface_registry_update_candidate" / "surface_registry_update_candidate_packet.json"
COMPARISON_PACKET = FIXTURES / "devhub_read_only_surface_drift_comparison" / "comparison_packet.json"


def _candidate_packet() -> dict[str, object]:
    return load_json_packet(SURFACE_CANDIDATE)


def _expected_packet() -> dict[str, object]:
    return load_json_packet(COMPARISON_PACKET)


def _read_only_observation_packet() -> dict[str, object]:
    packet = load_json_packet(OBSERVATION_PACKET)
    packet["packet_id"] = "devhub-read-only-observation-comparison-input-v1"
    packet["observations"] = [
        {
            "surface_id": "devhub_home_redacted",
            "auth_scope": "authenticated_read_only_metadata",
            "route_pattern": "/dashboard",
            "redacted_heading": "[REDACTED_HEADING:devhub-dashboard]",
            "reviewer_notes": ["Fixture keeps only redacted home surface structure."],
            "abort_prompts": ["Abort before upload, submit, certify, payment, scheduling, cancellation, MFA, CAPTCHA, or account changes."],
            "controls": [
                {"control_id": "upload", "enabled": False, "allowed": False, "control_state": "disabled"},
                {"control_id": "submit", "enabled": False, "allowed": False, "control_state": "disabled"},
                {"control_id": "certify", "enabled": False, "allowed": False, "control_state": "disabled"},
                {"control_id": "payment", "enabled": False, "allowed": False, "control_state": "disabled"},
                {"control_id": "schedule-inspection", "enabled": False, "allowed": False, "control_state": "disabled"},
                {"control_id": "cancel", "enabled": False, "allowed": False, "control_state": "disabled"},
            ],
        },
        {
            "surface_id": "devhub_permit_detail_redacted",
            "auth_scope": "authenticated_read_only_metadata",
            "route_pattern": "/permits/{permit_id}",
            "redacted_heading": "[REDACTED_HEADING:permit-detail]",
            "reviewer_notes": ["Fixture keeps permit identifier as a route placeholder."],
            "abort_prompts": ["Abort before upload, payment, scheduling, submit, certification, cancellation, extension, or reactivation controls."],
            "controls": [
                {"control_id": "upload-correction", "enabled": False, "allowed": False, "control_state": "disabled"},
                {"control_id": "pay-fee", "enabled": False, "allowed": False, "control_state": "disabled"},
                {"control_id": "schedule-inspection", "enabled": False, "allowed": False, "control_state": "disabled"},
                {"control_id": "request-extension", "enabled": False, "allowed": False, "control_state": "disabled"},
                {"control_id": "reactivate", "enabled": False, "allowed": False, "control_state": "disabled"},
                {"control_id": "withdraw", "enabled": False, "allowed": False, "control_state": "disabled"},
            ],
        },
    ]
    return packet


def test_comparison_fixture_is_valid() -> None:
    packet = _expected_packet()
    errors = validate_read_only_surface_drift_comparison_packet(packet)

    assert packet["packet_type"] == REQUIRED_PACKET_TYPE
    assert packet["launches_devhub"] is False
    assert packet["writes_surface_registry"] is False
    assert packet["mutates_active_surface_maps"] is False
    assert errors == ()
    assert_valid_read_only_surface_drift_comparison_packet(packet)


def test_builder_consumes_read_only_observation_and_surface_candidate_without_mutation() -> None:
    packet = build_read_only_surface_drift_comparison_packet(_read_only_observation_packet(), _candidate_packet())

    assert packet == _expected_packet()
    assert packet["source_packets"]["devhub_read_only_observation_packet"]["consumed"] is True
    assert packet["source_packets"]["devhub_surface_registry_update_candidate"]["consumed"] is True
    assert packet["launches_devhub"] is False
    assert packet["writes_surface_registry"] is False
    assert packet["mutates_active_surface_maps"] is False


def test_packet_records_cited_route_heading_action_and_selector_notes() -> None:
    packet = _expected_packet()
    comparisons = packet["surface_comparisons"]
    assert isinstance(comparisons, list)

    first = comparisons[0]
    assert isinstance(first, dict)
    assert first["route_differences"][0]["citations"]
    assert first["heading_differences"][0]["status"] == "synthetic_difference"
    assert first["action_differences"][0]["status"] == "disabled_controls_attested"
    assert first["selector_confidence_notes"][0]["upgrade_requested"] is False


def test_packet_records_reviewer_owners_and_unsupported_drift_deferrals() -> None:
    packet = _expected_packet()
    owners = packet["reviewer_owners"]
    deferrals = packet["unsupported_drift_deferrals"]

    assert isinstance(owners, list)
    assert {owner["owner"] for owner in owners if isinstance(owner, dict)} == {
        "ppd-devhub-reviewer",
        "ppd-selector-reviewer",
        "ppd-action-guardrail-reviewer",
    }
    assert isinstance(deferrals, list)
    assert all(deferral["resolution"] == "defer_no_registry_mutation" for deferral in deferrals if isinstance(deferral, dict))


def test_validator_rejects_registry_mutation_and_selector_upgrade_claims() -> None:
    packet = deepcopy(_expected_packet())
    packet["writes_surface_registry"] = True
    packet["surface_comparisons"][0]["selector_confidence_notes"][0]["upgrade_requested"] = True

    errors = validate_read_only_surface_drift_comparison_packet(packet)

    assert any("writes_surface_registry must be false" in error for error in errors)
    assert any("upgrade_requested must be false" in error for error in errors)


def test_builder_rejects_inputs_that_enable_consequential_controls() -> None:
    observation = _read_only_observation_packet()
    observation["observations"][0]["controls"][0]["enabled"] = True

    try:
        build_read_only_surface_drift_comparison_packet(observation, _candidate_packet())
    except ValueError as exc:
        assert "failed validation" in str(exc)
    else:
        raise AssertionError("expected enabled consequential control to be rejected")
