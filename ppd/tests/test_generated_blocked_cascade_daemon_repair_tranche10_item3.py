import json
from datetime import datetime, timezone
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "blocked_cascade_daemon_repair"
    / "tranche10_item3.json"
)


def _parse_instant(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _is_valid_fresh_daemon_repair(event, work_id, blocked_at):
    return (
        event.get("kind") == "repair_task"
        and event.get("task_type") == "daemon-repair"
        and event.get("target_work_id") == work_id
        and event.get("validation") == "passed"
        and _parse_instant(event["created_at"]) > blocked_at
    )


def _blocked_work_state(work_id, blocked_at_value, events):
    blocked_at = _parse_instant(blocked_at_value)
    validated_repair = None

    for event in events:
        if _is_valid_fresh_daemon_repair(event, work_id, blocked_at):
            validated_repair = event
            break

    if validated_repair is None:
        return {
            "parked": True,
            "release_event_id": None,
        }

    return {
        "parked": False,
        "release_event_id": validated_repair["id"],
    }


def test_blocked_ppd_work_stays_parked_until_fresh_daemon_repair_validates():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    work_id = fixture["work_id"]
    blocked_at = fixture["blocked_at"]
    events = fixture["events"]

    blocked_only = _blocked_work_state(work_id, blocked_at, events[:1])
    after_stale_repair = _blocked_work_state(work_id, blocked_at, events[:2])
    after_unrelated_repair = _blocked_work_state(work_id, blocked_at, events[:3])
    after_failed_targeted_repair = _blocked_work_state(work_id, blocked_at, events[:4])
    after_validated_targeted_repair = _blocked_work_state(work_id, blocked_at, events[:5])

    assert blocked_only == {"parked": True, "release_event_id": None}
    assert after_stale_repair == {"parked": True, "release_event_id": None}
    assert after_unrelated_repair == {"parked": True, "release_event_id": None}
    assert after_failed_targeted_repair == {"parked": True, "release_event_id": None}
    assert after_validated_targeted_repair == {
        "parked": False,
        "release_event_id": "fresh-targeted-repair-validated",
    }
