from __future__ import annotations

import json
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "daemon_repair"
    / "blocked_cascade_tranche9_item1.json"
)


def _fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _fresh_validating_repair(blocked_task: dict[str, Any], repair_task: dict[str, Any]) -> bool:
    validation = repair_task.get("validation", {})
    return (
        repair_task.get("kind") == "daemon-repair"
        and repair_task.get("repairs_task") == blocked_task.get("id")
        and repair_task.get("status") == "validated"
        and validation.get("passed") is True
        and int(repair_task.get("sequence", -1)) > int(blocked_task.get("sequence", -1))
    )


def test_blocked_cascade_fixture_targets_tranche_9_item_1() -> None:
    data = _fixture()
    blocked = data["blocked_task"]

    assert blocked["id"] == "checkbox-278"
    assert blocked["tranche"] == 9
    assert blocked["item"] == 1
    assert blocked["status"] == "parked"


def test_blocked_work_stays_parked_until_fresh_daemon_repair_validates() -> None:
    data = _fixture()
    blocked = data["blocked_task"]
    repair_attempts = data["repair_attempts"]

    releasing_repairs = [
        repair for repair in repair_attempts if _fresh_validating_repair(blocked, repair)
    ]

    assert [repair["id"] for repair in releasing_repairs] == [
        data["expected_release_repair"]
    ]

    parked_attempt_ids = [
        repair["id"]
        for repair in repair_attempts
        if repair["id"] != data["expected_release_repair"]
    ]
    assert parked_attempt_ids == [
        "daemon-repair-277",
        "daemon-repair-279",
        "daemon-repair-280",
    ]


def test_stale_failed_and_unrelated_repairs_do_not_release_blocked_work() -> None:
    data = _fixture()
    blocked = data["blocked_task"]
    repairs_by_id = {repair["id"]: repair for repair in data["repair_attempts"]}

    assert not _fresh_validating_repair(blocked, repairs_by_id["daemon-repair-277"])
    assert not _fresh_validating_repair(blocked, repairs_by_id["daemon-repair-279"])
    assert not _fresh_validating_repair(blocked, repairs_by_id["daemon-repair-280"])
    assert _fresh_validating_repair(blocked, repairs_by_id["daemon-repair-281"])
