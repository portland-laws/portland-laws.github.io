from __future__ import annotations

import json
from pathlib import Path

from ppd.release.rollback_drill_packets import (
    RollbackDrillValidationError,
    validate_release_rollback_drill_packet,
    validate_release_rollback_drill_packet_or_raise,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "release" / "rollback_drill_packets.json"


def _fixtures() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_valid_release_rollback_drill_packet_passes() -> None:
    packet = _fixtures()["valid"]

    result = validate_release_rollback_drill_packet(packet)  # type: ignore[arg-type]

    assert result.ok
    assert result.errors == ()
    validate_release_rollback_drill_packet_or_raise(packet)  # type: ignore[arg-type]


def test_invalid_release_rollback_drill_packet_rejects_guardrail_violations() -> None:
    packet = _fixtures()["invalid"]

    result = validate_release_rollback_drill_packet(packet)  # type: ignore[arg-type]

    assert not result.ok
    joined_errors = "\n".join(result.errors)
    assert "uncited" in joined_errors
    assert "affected-artifact" in joined_errors
    assert "reviewer owners" in joined_errors
    assert "smoke-test rerun checklist" in joined_errors
    assert "private/session artifact" in joined_errors
    assert "local private path" in joined_errors
    assert "raw crawl/download/archive reference" in joined_errors
    assert "live rollback or publication" in joined_errors
    assert "legal or permitting outcome guarantee" in joined_errors
    assert "enabled consequential control" in joined_errors
    assert "active artifact mutation flag" in joined_errors


def test_invalid_release_rollback_drill_packet_raise_helper_reports_all_errors() -> None:
    packet = _fixtures()["invalid"]

    try:
        validate_release_rollback_drill_packet_or_raise(packet)  # type: ignore[arg-type]
    except RollbackDrillValidationError as exc:
        assert len(exc.errors) >= 10
    else:
        raise AssertionError("expected rollback drill validation to fail")
