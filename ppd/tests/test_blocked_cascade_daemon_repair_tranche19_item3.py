import json
from datetime import datetime, timezone
from pathlib import Path


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "blocked_cascade"
    / "tranche19_item3_daemon_repair.json"
)


def _parse_time(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _blocked_work_release(events, blocked_work_id):
    blocked_at = None
    release_event_id = None

    for event in events:
        event_time = _parse_time(event["created_at"])
        if event["id"] == blocked_work_id or (
            event["kind"] == "ppd_work" and event["status"] == "blocked"
        ):
            blocked_at = event_time
            release_event_id = None
            continue

        if blocked_at is None:
            continue

        is_fresh_repair = event["kind"] == "daemon_repair" and event_time > blocked_at
        is_validated = event["status"] == "validated" and "blocked-cascade" in event.get(
            "validates", []
        )
        if is_fresh_repair and is_validated:
            release_event_id = event["id"]

    return release_event_id


def test_blocked_ppd_work_stays_parked_until_fresh_daemon_repair_validates():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    events = fixture["events"]

    assert _blocked_work_release(events[:1], fixture["blocked_work_id"]) is None
    assert _blocked_work_release(events[:2], fixture["blocked_work_id"]) is None
    assert _blocked_work_release(events[:3], fixture["blocked_work_id"]) is None
    assert (
        _blocked_work_release(events, fixture["blocked_work_id"])
        == "repair-after-block-validated"
    )
