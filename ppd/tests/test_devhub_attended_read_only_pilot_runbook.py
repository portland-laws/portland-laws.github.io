from __future__ import annotations

from pathlib import Path

import pytest

from ppd.devhub.attended_read_only_pilot_runbook import (
    REQUIRED_PACKET_ID,
    assert_valid_runbook_packet,
    build_attended_read_only_pilot_runbook,
    load_json_packet,
    load_runbook_packet,
    validate_runbook_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"
RUNBOOK_PATH = FIXTURE_DIR / "devhub" / "attended_read_only_pilot_runbook_packet.json"
OPERATOR_CHECKLIST_PATH = FIXTURE_DIR / "devhub" / "read_only_pilot_operator_checklist.json"
OBSERVATION_PACKET_PATH = FIXTURE_DIR / "devhub" / "read_only_observation_packet_valid.json"
DRIFT_COMPARISON_PATH = FIXTURE_DIR / "devhub_read_only_surface_drift_comparison" / "comparison_packet.json"


def test_fixture_runbook_packet_is_valid() -> None:
    packet = load_runbook_packet(RUNBOOK_PATH)

    result = validate_runbook_packet(packet)

    assert result.packet_id == REQUIRED_PACKET_ID
    assert result.ok is True
    assert result.errors == ()


def test_builder_consumes_current_read_only_packets() -> None:
    operator_checklist = load_json_packet(OPERATOR_CHECKLIST_PATH)
    observation_packet = load_json_packet(OBSERVATION_PACKET_PATH)
    drift_comparison_packet = load_json_packet(DRIFT_COMPARISON_PATH)

    packet = build_attended_read_only_pilot_runbook(
        operator_checklist,
        observation_packet,
        drift_comparison_packet,
    )

    assert_valid_runbook_packet(packet)
    assert packet["source_packets"]["devhub_read_only_pilot_operator_checklist"]["packet_id"] == operator_checklist["packet_id"]
    assert packet["source_packets"]["devhub_read_only_observation_packet"]["packet_id"] == observation_packet["packet_id"]
    assert packet["source_packets"]["devhub_read_only_surface_drift_comparison_packet"]["packet_id"] == drift_comparison_packet["packet_id"]


def test_fixture_runbook_blocks_browser_launch_and_private_artifacts() -> None:
    packet = load_runbook_packet(RUNBOOK_PATH)

    assert packet["launches_browser"] is False
    assert packet["launches_playwright"] is False
    assert packet["stores_private_session_state"] is False
    assert packet["stores_browser_artifacts"] is False
    assert packet["stores_auth_state"] is False
    assert packet["stores_screenshots"] is False
    assert packet["stores_traces"] is False
    assert packet["stores_har_files"] is False
    assert packet["stores_raw_authenticated_values"] is False
    assert all(step["automated"] is False for step in packet["synthetic_attended_pilot_steps"])
    assert all(step["browser_launch_allowed_by_runbook"] is False for step in packet["synthetic_attended_pilot_steps"])


def test_fixture_runbook_has_manual_login_boundary() -> None:
    packet = load_runbook_packet(RUNBOOK_PATH)
    boundary = packet["manual_login_boundaries"][0]

    assert boundary["human_operator_required"] is True
    assert boundary["agent_may_request_credentials"] is False
    assert boundary["agent_may_store_credentials"] is False
    assert boundary["agent_may_automate_mfa_or_captcha"] is False
    assert boundary["account_creation_allowed"] is False
    assert boundary["browser_state_storage_allowed"] is False


def test_fixture_runbook_has_page_observation_fields_and_reviewer_checkpoints() -> None:
    packet = load_runbook_packet(RUNBOOK_PATH)

    field_ids = {field["field_id"] for field in packet["page_observation_fields"]}
    checkpoint_ids = {checkpoint["checkpoint_id"] for checkpoint in packet["reviewer_checkpoints"]}

    assert "stable_surface_id" in field_ids
    assert "page_heading" in field_ids
    assert "disabled_consequential_controls" in field_ids
    assert "surface_drift_review" in checkpoint_ids
    assert "selector_confidence_review" in checkpoint_ids
    assert "consequential_control_review" in checkpoint_ids
    assert all(checkpoint["approval_can_enable_official_action"] is False for checkpoint in packet["reviewer_checkpoints"])


def test_validator_rejects_missing_observation_source_packet() -> None:
    packet = load_runbook_packet(RUNBOOK_PATH)
    packet["source_packets"].pop("devhub_read_only_observation_packet")

    result = validate_runbook_packet(packet)

    assert result.ok is False
    assert "source_packets.devhub_read_only_observation_packet.packet_id is required" in result.errors


def test_validator_rejects_browser_launch_claim() -> None:
    packet = load_runbook_packet(RUNBOOK_PATH)
    packet["launches_browser"] = True

    result = validate_runbook_packet(packet)

    assert result.ok is False
    assert "launches_browser must be false" in result.errors


def test_validator_rejects_missing_abort_prompts() -> None:
    packet = load_runbook_packet(RUNBOOK_PATH)
    packet["abort_prompts"] = ["Abort on timeout only."]

    result = validate_runbook_packet(packet)

    assert result.ok is False
    assert any("abort_prompts missing required terms" in error for error in result.errors)


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ({"automation_claim": "Agent will automate MFA, solve CAPTCHA, and complete account creation."}, "CAPTCHA/MFA/account-creation automation"),
        ({"candidate_artifacts": {"screenshot_path": "screenshots/devhub-private.png"}}, "private/session/browser artifact paths"),
        ({"candidate_artifacts": {"trace_path": "trace.zip", "har_path": "network.har", "auth_state_path": "storage_state.json"}}, "private/session/browser artifact paths"),
        ({"local_private_path": "/home/operator/devhub/session-state.json"}, "local private paths"),
        ({"raw_authenticated_value": "Permit number: 24-000000 private field value: owner email"}, "raw authenticated values"),
        ({"execution_claim": "Live browser execution completed with Playwright."}, "live browser execution"),
        ({"controls": {"upload_enabled": True, "submission_enabled": True, "payment_enabled": True}}, "upload/submission/payment/scheduling/cancellation/certification controls"),
        ({"controls": {"scheduling_enabled": True, "cancellation_enabled": True, "certification_enabled": True}}, "upload/submission/payment/scheduling/cancellation/certification controls"),
    ],
)
def test_validator_rejects_unsafe_runbook_candidate_claims(mutation: dict[str, object], expected_error: str) -> None:
    packet = load_runbook_packet(RUNBOOK_PATH)
    packet.update(mutation)

    result = validate_runbook_packet(packet)

    assert result.ok is False
    assert any(expected_error in error for error in result.errors)


def test_validator_rejects_missing_redaction_check_for_har_files() -> None:
    packet = load_runbook_packet(RUNBOOK_PATH)
    packet["redaction_checks"] = [check for check in packet["redaction_checks"] if check["check_id"] != "no_har_files"]

    result = validate_runbook_packet(packet)

    assert result.ok is False
    assert any("redaction_checks missing" in error and "no_har_files" in error for error in result.errors)


def test_assert_valid_runbook_packet_raises_stable_error() -> None:
    packet = load_runbook_packet(RUNBOOK_PATH)
    packet["manual_login_boundaries"][0]["agent_may_store_credentials"] = True

    with pytest.raises(AssertionError, match="agent_may_store_credentials must be false"):
        assert_valid_runbook_packet(packet)
