from __future__ import annotations

from pathlib import Path

import pytest

from ppd.devhub.attended_pilot_preflight import (
    REQUIRED_PACKET_ID,
    assert_valid_preflight_packet,
    load_preflight_packet,
    validate_preflight_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "attended_pilot_preflight_packet.json"


def test_fixture_packet_is_valid_for_synthetic_readonly_review() -> None:
    packet = load_preflight_packet(FIXTURE_PATH)

    result = validate_preflight_packet(packet)

    assert result.packet_id == REQUIRED_PACKET_ID
    assert result.ok is True
    assert result.errors == ()


def test_fixture_blocks_live_automation_and_browser_artifacts() -> None:
    packet = load_preflight_packet(FIXTURE_PATH)

    assert packet["live_automation_allowed"] is False
    assert packet["playwright_launch_allowed"] is False
    assert packet["browser_artifacts_allowed"] is False
    assert packet["redaction_checks"]["before_journal_write"] is True


def test_validator_rejects_missing_manual_handoff() -> None:
    packet = load_preflight_packet(FIXTURE_PATH)
    packet["manual_login_handoff"] = {"required": False}

    result = validate_preflight_packet(packet)

    assert result.ok is False
    assert any("manual login handoff" in error for error in result.errors)


def test_assert_valid_preflight_packet_raises_stable_error() -> None:
    packet = load_preflight_packet(FIXTURE_PATH)
    packet["timeout_handling"]["timeout_seconds"] = 30

    with pytest.raises(AssertionError, match="timeout must be 900 seconds"):
        assert_valid_preflight_packet(packet)
