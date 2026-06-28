from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "blocked_cascade_daemon_repair_tranche2_item4.json"
)


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _can_unpark(blocked_work: dict[str, Any], repair_task: dict[str, Any]) -> bool:
    return (
        blocked_work.get("status") == "parked"
        and repair_task.get("target") == blocked_work.get("blocked_by")
        and repair_task.get("fresh") is True
        and repair_task.get("validated") is True
    )


def test_blocked_cascade_work_stays_parked_until_fresh_repair_validates() -> None:
    fixture = _load_fixture()
    blocked_work = fixture["blocked_work"]
    attempts = fixture["repair_attempts"]

    parked_results = [_can_unpark(blocked_work, attempt) for attempt in attempts[:-1]]
    assert parked_results == [False, False, False]

    final_attempt = attempts[-1]
    assert _can_unpark(blocked_work, final_attempt) is True


def test_fixture_uses_expected_blocking_repair_task() -> None:
    fixture = _load_fixture()
    blocked_work = fixture["blocked_work"]

    assert blocked_work["status"] == "parked"
    assert blocked_work["blocked_by"] == "daemon-repair-tranche-2-item-4"
