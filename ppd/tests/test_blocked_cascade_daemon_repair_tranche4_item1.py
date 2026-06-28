import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "blocked_cascade_daemon_repair_tranche4_item1.json"
)


def _load_fixture():
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _validated_fresh_repair_exists(blocked_work, repair_tasks):
    blocked_generation = blocked_work["blocked_generation"]
    blocked_id = blocked_work["id"]
    for task in repair_tasks:
        if task.get("validates_work") != blocked_id:
            continue
        if task.get("status") != "validated":
            continue
        if task.get("repair_generation", -1) <= blocked_generation:
            continue
        return True
    return False


def _should_remain_parked(blocked_work, repair_tasks):
    if blocked_work.get("status") != "blocked":
        return False
    return not _validated_fresh_repair_exists(blocked_work, repair_tasks)


def test_blocked_work_stays_parked_without_fresh_validated_daemon_repair():
    fixture = _load_fixture()
    blocked_work = fixture["blocked_work"]
    stale_or_unvalidated_repairs = fixture["repair_tasks"][:2]

    assert _should_remain_parked(blocked_work, stale_or_unvalidated_repairs) is True


def test_blocked_work_can_unpark_only_after_fresh_validated_daemon_repair():
    fixture = _load_fixture()
    blocked_work = fixture["blocked_work"]
    all_repairs = fixture["repair_tasks"]

    assert _validated_fresh_repair_exists(blocked_work, all_repairs) is True
    assert _should_remain_parked(blocked_work, all_repairs) is False
