from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.devhub.read_only_observation_checklist import (
    assert_valid_read_only_observation_packet,
    validate_read_only_observation_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_read_only_observation"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_read_only_observation_packet_is_accepted() -> None:
    packet = _load_fixture("valid_packet.json")

    result = validate_read_only_observation_packet(packet)

    assert result.ok
    assert result.findings == ()
    assert_valid_read_only_observation_packet(packet)


def test_invalid_read_only_observation_packet_rejects_all_prohibited_categories() -> None:
    packet = _load_fixture("invalid_packet.json")

    result = validate_read_only_observation_packet(packet)

    assert not result.ok
    categories = {finding.category for finding in result.findings}
    assert "automated login" in categories
    assert "MFA" in categories
    assert "CAPTCHA" in categories
    assert "account creation" in categories
    assert "credential prompt" in categories
    assert "private field value" in categories
    assert "screenshot" in categories
    assert "trace" in categories
    assert "HAR data" in categories
    assert "cookie" in categories
    assert "auth state" in categories
    assert "consequential control" in categories
    assert "live authenticated capture claim" in categories


def test_invalid_read_only_observation_packet_raises_actionable_error() -> None:
    packet = _load_fixture("invalid_packet.json")

    with pytest.raises(ValueError, match="DevHub read-only observation packet rejected"):
        assert_valid_read_only_observation_packet(packet)
