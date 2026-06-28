from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.evidence_freshness_watchlist import (
    require_valid_watchlist_packet,
    validate_watchlist_packet,
)


FIXTURES = Path(__file__).parent / "fixtures" / "evidence_freshness_watchlist"


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_watchlist_packet_fixture_passes() -> None:
    packet = _load_fixture("valid_packet.json")

    result = validate_watchlist_packet(packet)

    assert result.ok, result.errors
    require_valid_watchlist_packet(packet)


def test_invalid_watchlist_packet_fixture_rejects_guardrail_failures() -> None:
    packet = _load_fixture("invalid_packet.json")

    result = validate_watchlist_packet(packet)

    assert not result.ok
    joined = "\n".join(result.errors)
    assert "uncited" in joined
    assert "offline_review_triggers" in joined
    assert "reviewers" in joined
    assert "not allowlisted" in joined
    assert "authenticated URL" in joined
    assert "raw/download/archive" in joined
    assert "live crawl or processor execution" in joined
    assert "outcome guarantee" in joined
    assert "active mutation flag" in joined


def test_require_valid_watchlist_packet_raises_value_error() -> None:
    packet = _load_fixture("invalid_packet.json")

    with pytest.raises(ValueError):
        require_valid_watchlist_packet(packet)
