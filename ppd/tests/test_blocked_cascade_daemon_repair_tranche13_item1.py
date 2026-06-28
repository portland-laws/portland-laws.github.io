from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "blocked_cascade_daemon_repair_tranche13_item1.json"
)


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _blocked_work_state(blocked_work: dict[str, Any], repair_tasks: list[dict[str, Any]]) -> str:
    blocked_at = _parse_utc(blocked_work["blocked_at"])
    has_fresh_validated_repair = any(
        task.get("kind") == "daemon-repair"
        and task.get("state") == "validated"
        and _parse_utc(task["created_at"]) > blocked_at
        for task in repair_tasks
    )
    return "ready" if has_fresh_validated_repair else "parked"


def test_blocked_cascade_work_stays_parked_until_fresh_daemon_repair_validates() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    blocked_work = fixture["blocked_work"]

    observed = {
        scenario["name"]: _blocked_work_state(blocked_work, scenario["repair_tasks"])
        for scenario in fixture["scenarios"]
    }

    expected = {
        scenario["name"]: scenario["expected_state"]
        for scenario in fixture["scenarios"]
    }

    assert observed == expected


def test_fixture_is_scoped_to_ppd_tests_fixtures() -> None:
    assert FIXTURE_PATH.is_file()
    assert FIXTURE_PATH.parent == Path(__file__).parent / "fixtures"
