from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from ppd.devhub.read_only_pilot_result_intake import (
    REQUIRED_PACKET_TYPE,
    assert_valid_pilot_result_intake,
    load_pilot_result_intake,
    validate_pilot_result_intake,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "read_only_pilot_result_intake.json"


def _fixture() -> dict[str, object]:
    return load_pilot_result_intake(FIXTURE_PATH)


def test_result_intake_fixture_is_valid() -> None:
    packet = _fixture()
    result = validate_pilot_result_intake(packet)
    assert packet["packet_type"] == REQUIRED_PACKET_TYPE
    assert result.ok is True
    assert result.errors == ()


@pytest.mark.parametrize(
    "flag",
    [
        "automated_login",
        "mfa_automated",
        "captcha_automated",
        "account_creation_automated",
        "credential_prompted",
        "stores_browser_artifacts",
        "screenshots_captured",
        "traces_captured",
        "har_captured",
        "official_actions_completed",
    ],
)
def test_result_intake_rejects_unsafe_top_level_claims(flag: str) -> None:
    packet = _fixture()
    packet[flag] = True
    result = validate_pilot_result_intake(packet)
    assert result.ok is False
    assert any(f"{flag} must be false" in error for error in result.errors)


@pytest.mark.parametrize(
    "field",
    [
        "no_automated_login",
        "no_mfa_automation",
        "no_captcha_automation",
        "no_account_creation_automation",
        "no_credential_prompts",
        "no_credentials",
        "no_cookies",
        "no_auth_state",
        "no_stored_browser_artifacts",
        "no_screenshots",
        "no_traces",
        "no_har_data",
        "no_private_field_values",
        "no_consequential_controls",
        "no_official_actions_completed",
    ],
)
def test_result_intake_requires_redaction_attestations(field: str) -> None:
    packet = _fixture()
    attestations = packet["redaction_attestations"]
    assert isinstance(attestations, dict)
    attestations.pop(field)
    with pytest.raises(AssertionError, match=f"redaction_attestations.{field} must be true"):
        assert_valid_pilot_result_intake(packet)


def test_result_intake_rejects_private_fields_and_browser_artifacts() -> None:
    packet = _fixture()
    observations = packet["observations"]
    assert isinstance(observations, list)
    first = observations[0]
    assert isinstance(first, dict)
    first["private_field_value"] = "1234 SE Example St"
    first["screenshot_path"] = "/tmp/devhub.png"
    result = validate_pilot_result_intake(packet)
    assert result.ok is False
    assert any("private_field_value" in error for error in result.errors)
    assert any("screenshot_path" in error for error in result.errors)


def test_result_intake_rejects_extra_observation_notes() -> None:
    packet = _fixture()
    observations = packet["observations"]
    assert isinstance(observations, list)
    first = observations[0]
    assert isinstance(first, dict)
    first["notes"] = "Only hardening notes are accepted."
    result = validate_pilot_result_intake(packet)
    assert result.ok is False
    assert any("observations[0] contains disallowed field" in error for error in result.errors)


def test_result_intake_rejects_consequential_control_allowance() -> None:
    packet = _fixture()
    controls = packet["consequential_controls"]
    assert isinstance(controls, list)
    first = controls[0]
    assert isinstance(first, dict)
    first["allowed"] = True
    first["official_action_completed"] = True
    result = validate_pilot_result_intake(packet)
    assert result.ok is False
    assert any("consequential_controls[0].allowed must be false" in error for error in result.errors)
    assert any("official_action_completed must be false" in error for error in result.errors)


def test_result_intake_rejects_claims_that_official_actions_were_completed() -> None:
    packet = _fixture()
    hardening = packet["post_action_hardening"]
    assert isinstance(hardening, dict)
    hardening["official_actions_completed"] = True
    result = validate_pilot_result_intake(packet)
    assert result.ok is False
    assert any("post_action_hardening.official_actions_completed must be false" in error for error in result.errors)


def test_result_intake_rejects_unlinked_journal_ids() -> None:
    packet = _fixture()
    observations = packet["observations"]
    assert isinstance(observations, list)
    first = observations[0]
    assert isinstance(first, dict)
    first["journal_event_id"] = "JRN-UNKNOWN"
    result = validate_pilot_result_intake(packet)
    assert result.ok is False
    assert any("journal_event_id must link to a known journal event" in error for error in result.errors)


def test_result_intake_rejects_prohibited_observation_text_claims() -> None:
    packet = _fixture()
    mutated = deepcopy(packet)
    observations = mutated["observations"]
    assert isinstance(observations, list)
    first = observations[0]
    assert isinstance(first, dict)
    first["redacted_heading"] = "Operator submitted the application."
    result = validate_pilot_result_intake(mutated)
    assert result.ok is False
    assert any("contains prohibited live/session/action content" in error for error in result.errors)
