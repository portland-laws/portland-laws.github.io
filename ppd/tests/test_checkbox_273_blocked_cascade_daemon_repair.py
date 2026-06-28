import json
from datetime import datetime
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "blocked_cascade" / "tranche_7_item_4.json"


def _instant(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _parked_after_each_repair_attempt(case: dict) -> list[bool]:
    blocked_work = case["blocked_work"]
    blocked_at = _instant(blocked_work["blocked_at"])
    required_repair_task = blocked_work["requires_repair_task"]
    parked = blocked_work["status"] == "blocked"
    observed = []

    for attempt in case["repair_attempts"]:
        is_required_task = attempt["id"] == required_repair_task
        is_fresh = _instant(attempt["submitted_at"]) > blocked_at
        is_validated = attempt["validation"] == "passed" and _instant(attempt["validated_at"]) >= _instant(attempt["submitted_at"])

        if parked and is_required_task and is_fresh and is_validated:
            parked = False
        observed.append(parked)

    return observed


def test_blocked_ppd_work_stays_parked_until_fresh_daemon_repair_validates() -> None:
    case = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert _parked_after_each_repair_attempt(case) == case["expected_parked_after_attempts"]
