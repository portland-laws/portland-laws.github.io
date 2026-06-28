from __future__ import annotations

from pathlib import Path

import pytest

from ppd.devhub.read_only_pilot_operator_checklist import (
    REQUIRED_PACKET_ID,
    assert_valid_operator_checklist,
    load_operator_checklist,
    validate_operator_checklist,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "read_only_pilot_operator_checklist.json"


def _fixture() -> dict[str, object]:
    return load_operator_checklist(FIXTURE_PATH)


def test_operator_checklist_fixture_is_valid() -> None:
    packet = _fixture()

    result = validate_operator_checklist(packet)

    assert result.packet_id == REQUIRED_PACKET_ID
    assert result.ok is True
    assert result.errors == ()


def test_operator_checklist_blocks_playwright_and_live_session() -> None:
    packet = _fixture()

    assert packet["manual_session_only"] is True
    assert packet["launches_playwright"] is False
    assert packet["live_session_authorized"] is False
    assert packet["stores_private_session_state"] is False
    assert packet["stores_browser_artifacts"] is False


def test_operator_checklist_requires_login_attendance_step() -> None:
    packet = _fixture()
    steps = packet["checklist_steps"]
    assert isinstance(steps, list)
    packet["checklist_steps"] = [step for step in steps if isinstance(step, dict) and step.get("step_id") != "login_attendance_handoff"]

    result = validate_operator_checklist(packet)

    assert result.ok is False
    assert any("login_attendance_handoff" in error for error in result.errors)


@pytest.mark.parametrize(
    "artifact",
    [
        "credentials",
        "credential_prompts",
        "cookies",
        "auth_state",
        "session_state",
        "screenshots",
        "traces",
        "har_files",
        "raw_dom",
        "raw_authenticated_text",
        "private_field_values",
        "payment_details",
        "downloads",
        "local_private_file_paths",
    ],
)
def test_operator_checklist_requires_forbidden_artifact_redaction(artifact: str) -> None:
    packet = _fixture()
    redaction = packet["redaction_policy"]
    assert isinstance(redaction, dict)
    forbidden = redaction["forbidden_artifacts"]
    assert isinstance(forbidden, list)
    redaction["forbidden_artifacts"] = [item for item in forbidden if item != artifact]

    with pytest.raises(AssertionError, match="redaction_policy.forbidden_artifacts"):
        assert_valid_operator_checklist(packet)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("automated_login_allowed", "automated_login_allowed must be false"),
        ("credential_prompt_capture_allowed", "credential_prompt_capture_allowed must be false"),
        ("mfa_automation_allowed", "mfa_automation_allowed must be false"),
        ("captcha_automation_allowed", "captcha_automation_allowed must be false"),
        ("account_creation_automation_allowed", "account_creation_automation_allowed must be false"),
        ("password_recovery_automation_allowed", "password_recovery_automation_allowed must be false"),
    ],
)
def test_operator_checklist_rejects_login_and_security_automation(field: str, message: str) -> None:
    packet = _fixture()
    automation = packet["automation_policy"]
    assert isinstance(automation, dict)
    automation[field] = True

    with pytest.raises(AssertionError, match=message):
        assert_valid_operator_checklist(packet)


@pytest.mark.parametrize(
    "field",
    [
        "no_credentials",
        "no_credential_prompts",
        "no_cookies",
        "no_auth_state",
        "no_screenshots",
        "no_traces",
        "no_har_files",
        "no_private_field_values",
        "no_consequential_controls",
        "no_live_evidence_captured",
    ],
)
def test_operator_checklist_requires_redaction_attestations(field: str) -> None:
    packet = _fixture()
    attestations = packet["redaction_attestations"]
    assert isinstance(attestations, dict)
    attestations.pop(field)

    result = validate_operator_checklist(packet)

    assert result.ok is False
    assert any(f"redaction_attestations.{field} must be true" in error for error in result.errors)


def test_operator_checklist_rejects_consequential_control_allowance() -> None:
    packet = _fixture()
    controls = packet["consequential_controls"]
    assert isinstance(controls, list)
    first = controls[0]
    assert isinstance(first, dict)
    first["allowed_in_read_only_pilot"] = True

    result = validate_operator_checklist(packet)

    assert result.ok is False
    assert any("allowed_in_read_only_pilot must be false" in error for error in result.errors)


def test_operator_checklist_rejects_missing_consequential_control() -> None:
    packet = _fixture()
    controls = packet["consequential_controls"]
    assert isinstance(controls, list)
    packet["consequential_controls"] = [control for control in controls if isinstance(control, dict) and control.get("control_id") != "submit"]

    result = validate_operator_checklist(packet)

    assert result.ok is False
    assert any("consequential_controls missing: submit" in error for error in result.errors)


def test_operator_checklist_rejects_live_evidence_capture_claims() -> None:
    packet = _fixture()
    claims = packet["evidence_claims"]
    assert isinstance(claims, dict)
    claims["live_evidence_captured"] = True
    claims["claims_live_evidence_was_captured"] = True

    result = validate_operator_checklist(packet)

    assert result.ok is False
    assert any("live_evidence_captured must be false" in error for error in result.errors)
    assert any("claims_live_evidence_was_captured must be false" in error for error in result.errors)


def test_operator_checklist_rejects_unlinked_abort_condition() -> None:
    packet = _fixture()
    abort_conditions = packet["abort_conditions"]
    assert isinstance(abort_conditions, list)
    first = abort_conditions[0]
    assert isinstance(first, dict)
    first["journal_event_id"] = "JRN-UNKNOWN-EVENT"

    result = validate_operator_checklist(packet)

    assert result.ok is False
    assert any("must link to a known journal event" in error for error in result.errors)


def test_operator_checklist_rejects_browser_artifact_creation_after_session() -> None:
    packet = _fixture()
    hardening = packet["post_action_hardening"]
    assert isinstance(hardening, dict)
    hardening["browser_artifacts_created"] = True

    with pytest.raises(AssertionError, match="browser_artifacts_created must be false"):
        assert_valid_operator_checklist(packet)
