import json
from pathlib import Path


FIXTURE = Path(__file__).parent / "fixtures" / "blocked_cascade" / "tranche12_item2_daemon_repair.json"


def _parked_until_fresh_validated_repair(blocked_task, repair_attempts):
    parked_states = []
    task_generation = blocked_task["generation"]

    for repair in repair_attempts:
        is_fresh = repair["generation"] > task_generation
        is_validated_daemon_repair = repair["kind"] == "daemon-repair" and repair["validated"] is True
        parked = not (is_fresh and is_validated_daemon_repair)
        parked_states.append({"repair_id": repair["id"], "parked": parked})

    return parked_states


def test_blocked_ppd_work_stays_parked_until_fresh_daemon_repair_validates():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    states = _parked_until_fresh_validated_repair(
        fixture["blocked_task"],
        fixture["repair_attempts"],
    )

    assert states == [
        {"repair_id": "daemon-repair-tranche12-item2-old", "parked": True},
        {"repair_id": "daemon-repair-tranche12-item2-failed", "parked": True},
        {"repair_id": "daemon-repair-tranche12-item2-fresh", "parked": False},
    ]
