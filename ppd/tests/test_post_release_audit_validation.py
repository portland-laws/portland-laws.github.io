from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.agent_readiness.post_release_audit_validation import (
    require_post_release_audit_findings_packet,
    validate_post_release_audit_findings_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "post_release_audit" / "findings_packets.json"


def _fixtures() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_post_release_audit_findings_packet_accepts_metadata_only_blocked_release() -> None:
    packet = _fixtures()["valid"]

    result = validate_post_release_audit_findings_packet(packet)

    assert result.ready is True
    assert result.problems == ()
    require_post_release_audit_findings_packet(packet)


def test_post_release_audit_findings_packet_rejects_unsafe_release_claims() -> None:
    packet = _fixtures()["invalid"]

    result = validate_post_release_audit_findings_packet(packet)

    assert result.ready is False
    problems = "\n".join(result.problems)
    assert "audit finding lacks citation" in problems
    assert "unknown source evidence missing-ev" in problems
    assert "private or session artifact" in problems
    assert "local private path" in problems
    assert "raw crawl/download/archive reference" in problems
    assert "legal or permitting outcome guarantee" in problems
    assert "production-ready label" in problems
    assert "live network or DevHub execution claim" in problems
    assert "blocked consequential capability" in problems

    with pytest.raises(ValueError, match="invalid_post_release_audit_findings_packet"):
        require_post_release_audit_findings_packet(packet)
