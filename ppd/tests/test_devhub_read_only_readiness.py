from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.devhub.read_only_readiness import (
    ReadOnlyReadinessError,
    iter_read_only_readiness_violations,
    packet_is_read_only_ready,
    validate_read_only_readiness_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_read_only_readiness"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_attended_read_only_readiness_packet_passes() -> None:
    packet = _load_fixture("valid_packet.json")

    validate_read_only_readiness_packet(packet)

    assert packet_is_read_only_ready(packet) is True
    assert list(iter_read_only_readiness_violations(packet)) == []


def test_invalid_attended_read_only_readiness_packet_reports_required_rejections() -> None:
    packet = _load_fixture("invalid_packet.json")

    violations = list(iter_read_only_readiness_violations(packet))
    codes = {violation.code for violation in violations}

    assert "missing_prerequisite_links" in codes
    assert "uncited_readiness_claim" in codes
    assert "private_or_session_artifact" in codes
    assert "forbidden_auth_or_account_automation" in codes
    assert "live_browser_execution_claim" in codes
    assert "missing_abort_conditions" in codes
    assert "enabled_consequential_control" in codes
    assert packet_is_read_only_ready(packet) is False

    with pytest.raises(ReadOnlyReadinessError) as exc_info:
        validate_read_only_readiness_packet(packet)

    assert {violation.code for violation in exc_info.value.violations} == codes


def test_enabled_consequential_control_is_rejected_even_when_other_evidence_is_valid() -> None:
    packet = _load_fixture("valid_packet.json")
    packet["controls"].append(
        {
            "label": "Schedule inspection",
            "kind": "consequential_official",
            "enabled": True,
        }
    )

    violations = list(iter_read_only_readiness_violations(packet))

    assert [violation.code for violation in violations] == ["enabled_consequential_control"]


def test_missing_abort_conditions_are_required_for_read_only_packets() -> None:
    packet = _load_fixture("valid_packet.json")
    packet.pop("abort_conditions")

    violations = list(iter_read_only_readiness_violations(packet))

    assert [violation.code for violation in violations] == ["missing_abort_conditions"]
