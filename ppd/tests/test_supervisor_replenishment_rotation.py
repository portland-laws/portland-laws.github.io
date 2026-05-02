"""Fixture-only tests for supervisor replenishment broad-title rotation."""

from __future__ import annotations

import json
from pathlib import Path

from ppd.daemon.replenishment_rotation import (
    replenishment_tranche_from_dict,
    validate_completed_tranche_rotation,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "daemon" / "supervisor_replenishment_rotation.json"


def _load_fixture(name: str):
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return tuple(replenishment_tranche_from_dict(item) for item in data[name])


def test_third_and_later_completed_tranches_rotate_broad_titles() -> None:
    findings = validate_completed_tranche_rotation(_load_fixture("validCompletedRotation"))
    assert findings == []


def test_duplicate_third_completed_tranche_title_is_rejected() -> None:
    findings = validate_completed_tranche_rotation(_load_fixture("duplicateThirdCompletedRotation"))
    assert len(findings) == 1
    assert findings[0].tranche_id == "replenishment-003"
    assert findings[0].previous_tranche_id == "replenishment-001"
    assert "third and later" in findings[0].reason


def test_pending_duplicate_title_does_not_count_as_completed_rotation() -> None:
    findings = validate_completed_tranche_rotation(_load_fixture("pendingDuplicateDoesNotCount"))
    assert findings == []


if __name__ == "__main__":
    test_third_and_later_completed_tranches_rotate_broad_titles()
    test_duplicate_third_completed_tranche_title_is_rejected()
    test_pending_duplicate_title_does_not_count_as_completed_rotation()
