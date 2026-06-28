from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "blocked_cascade"
    / "tranche8_item4_daemon_repair.json"
)


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _fresh_validated_repair_exists(
    repairs: list[dict[str, Any]], blocked_at: datetime
) -> bool:
    for repair in repairs:
        if repair.get("kind") != "daemon-repair":
            continue
        if repair.get("status") != "validated":
            continue
        validated_at = repair.get("validated_at")
        if not isinstance(validated_at, str):
            continue
        if _parse_utc(validated_at) > blocked_at:
            return True
    return False


def _parked_work_items(
    blocked_work: list[dict[str, Any]], repairs: list[dict[str, Any]]
) -> list[str]:
    parked: list[str] = []
    for item in blocked_work:
        blocked_at = _parse_utc(item["blocked_at"])
        if not _fresh_validated_repair_exists(repairs, blocked_at):
            parked.append(item["id"])
    return parked


def test_blocked_ppd_work_stays_parked_until_fresh_daemon_repair_validates() -> None:
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    blocked_work = fixture["blocked_work"]
    repairs = fixture["repair_tasks"]

    stale_and_unvalidated_repairs = repairs[:2]
    assert _parked_work_items(blocked_work, stale_and_unvalidated_repairs) == [
        "ppd-tranche8-item4-crawl-normalization"
    ]

    assert _parked_work_items(blocked_work, repairs) == []
