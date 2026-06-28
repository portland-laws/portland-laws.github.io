import json
from pathlib import Path

from ppd.daemon.blocked_cascade_repair import (
    blocked_work_from_mapping,
    decide_blocked_cascade,
    repair_task_from_mapping,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "blocked_cascade" / "daemon_repair_tranche2_item1.json"


def load_case(name):
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return fixture["cases"][name]


def build_decision(case_name):
    case = load_case(case_name)
    work = blocked_work_from_mapping(case["blocked_work"])
    repairs = [repair_task_from_mapping(item) for item in case["repair_tasks"]]
    return decide_blocked_cascade(
        work,
        repairs,
        previous_validated_repair_ids=case.get("previous_validated_repair_ids", []),
    )


def test_blocked_work_stays_parked_without_fresh_validated_daemon_repair():
    decision = build_decision("stale_and_unvalidated_repairs")

    assert decision.parked is True
    assert decision.reason == "no-fresh-validated-repair"
    assert decision.repair_task_id is None


def test_blocked_work_resumes_after_fresh_daemon_repair_validates():
    decision = build_decision("fresh_validated_repair")

    assert decision.parked is False
    assert decision.reason == "fresh-validated-repair"
    assert decision.repair_task_id == "daemon-repair-2026-05-08T13-10-00Z"
