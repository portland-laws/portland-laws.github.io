from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.agent_readiness.devhub_attended_read_only_pilot import (
    LaunchReadinessError,
    iter_launch_readiness_violations,
    packet_is_launch_ready,
    validate_launch_readiness_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_attended_read_only_pilot_launch_readiness"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_devhub_attended_read_only_pilot_launch_readiness_packet_passes() -> None:
    packet = _load_fixture("launch_readiness_packet.json")

    validate_launch_readiness_packet(packet)

    assert packet_is_launch_ready(packet) is True
    assert list(iter_launch_readiness_violations(packet)) == []


def test_invalid_devhub_attended_read_only_pilot_launch_readiness_packet_rejects_required_failures() -> None:
    packet = _load_fixture("invalid_launch_readiness_packet.json")

    violations = list(iter_launch_readiness_violations(packet))
    codes = {violation.code for violation in violations}

    assert "missing_attendance_prerequisite" in codes
    assert "missing_manual_stop_point" in codes
    assert "uncited_selector_confidence_note" in codes
    assert "missing_redaction_checklist_item" in codes
    assert "missing_reviewer_owner" in codes
    assert "raw_authenticated_value" in codes
    assert "private_or_session_artifact" in codes
    assert "local_private_path" in codes
    assert "screenshot_artifact" in codes
    assert "trace_or_har_artifact" in codes
    assert "stored_auth_state" in codes
    assert "live_browser_execution_claim" in codes
    assert "enabled_consequential_control" in codes
    assert "active_surface_registry_mutation_flag" in codes
    assert "active_agent_state_mutation_flag" in codes
    assert packet_is_launch_ready(packet) is False

    with pytest.raises(LaunchReadinessError) as exc_info:
        validate_launch_readiness_packet(packet)

    assert {violation.code for violation in exc_info.value.violations} == codes


def test_enabled_consequential_control_is_rejected_for_otherwise_valid_launch_packet() -> None:
    packet = _load_fixture("launch_readiness_packet.json")
    packet["controls"] = [
        {
            "label": "Schedule inspection",
            "kind": "consequential_official",
            "enabled": True,
        }
    ]

    violations = list(iter_launch_readiness_violations(packet))

    assert [violation.code for violation in violations] == ["enabled_consequential_control"]


def test_active_mutation_flags_are_rejected_for_otherwise_valid_launch_packet() -> None:
    packet = _load_fixture("launch_readiness_packet.json")
    packet["active_surface_registry_mutation"] = True
    packet["agent_state_mutation_enabled"] = True

    codes = [violation.code for violation in iter_launch_readiness_violations(packet)]

    assert codes == ["active_surface_registry_mutation_flag", "active_agent_state_mutation_flag"]
