"""Regression coverage for blocked-cascade daemon-repair parking.

Tranche 8 item 2 requires blocked PP&D work to stay parked until a fresh
validated daemon repair task exists.  This test uses a local deterministic
fixture so it never depends on live daemon state, DevHub access, or ledger
mutation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_fixture() -> dict[str, Any]:
    fixture_path = Path(__file__).parent / "fixtures" / "blocked_cascade" / "tranche8_item2.json"
    with fixture_path.open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _eligible_ppd_work_ids(tasks: list[dict[str, Any]]) -> list[str]:
    validated_repairs = {
        task["id"]
        for task in tasks
        if task.get("kind") == "daemon-repair"
        and task.get("state") == "validated"
        and task.get("validated_at")
    }

    eligible: list[str] = []
    for task in tasks:
        if task.get("kind") != "ppd-work":
            continue
        if task.get("state") == "blocked" and task.get("blocked_by") not in validated_repairs:
            continue
        eligible.append(task["id"])
    return eligible


def test_blocked_ppd_work_stays_parked_until_fresh_daemon_repair_validates() -> None:
    fixture = _load_fixture()
    parked_tasks = fixture["tasks"]

    assert _eligible_ppd_work_ids(parked_tasks) == []

    repaired_tasks = [*parked_tasks, fixture["fresh_repair"]]
    repaired_tasks[0] = {
        **repaired_tasks[0],
        "blocked_by": fixture["fresh_repair"]["id"],
    }

    assert _eligible_ppd_work_ids(repaired_tasks) == ["task-checkbox-275"]
