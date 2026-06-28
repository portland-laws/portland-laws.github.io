import json
from datetime import datetime, timezone
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "blocked_cascade_daemon_repair_tranche7_item2.json"
)


def _parse_utc(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _required_repair_target(blocked_by):
    prefix = "daemon-repair:"
    if not blocked_by.startswith(prefix):
        return None
    return blocked_by[len(prefix) :]


def _state_after_repair_check(blocked_work, repair_tasks):
    if blocked_work["state"] != "parked":
        return blocked_work["state"]

    required_target = _required_repair_target(blocked_work["blocked_by"])
    blocked_at = _parse_utc(blocked_work["blocked_at"])

    for task in repair_tasks:
        if task.get("kind") != "daemon-repair":
            continue
        if task.get("target") != required_target:
            continue
        if task.get("status") != "validated":
            continue
        validated_at = _parse_utc(task["validated_at"])
        if validated_at > blocked_at:
            return "ready"

    return "parked"


def test_blocked_cascade_stays_parked_until_fresh_daemon_repair_validates():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    blocked_work = fixture["blocked_work"]

    assert fixture["generated_for"] == "checkbox-271"
    assert fixture["tranche"] == 7
    assert fixture["item"] == 2

    for case in fixture["cases"]:
        actual_state = _state_after_repair_check(blocked_work, case["repair_tasks"])
        assert actual_state == case["expected_state"], case["name"]
