from __future__ import annotations

import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "blocked_cascade"
    / "tranche2_item3_daemon_repair.json"
)


def _parked_work_ids(payload: dict, repair_attempts: list[dict]) -> list[str]:
    fresh_after = payload["fresh_after"]
    validated_repairs = {
        attempt["id"]
        for attempt in repair_attempts
        if attempt.get("kind") == "daemon-repair"
        and attempt.get("validated") is True
        and attempt.get("created_at", 0) > fresh_after
    }

    parked = []
    for work in payload["blocked_work"]:
        blocking_repair = work.get("blocked_by")
        if work.get("state") == "blocked" and blocking_repair not in validated_repairs:
            parked.append(work["id"])
    return parked


def test_blocked_ppd_work_stays_parked_without_repair_attempt() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert _parked_work_ids(payload, []) == [
        "ppd-tranche2-item3-normalize-devhub-guides",
        "ppd-tranche2-item3-refresh-permit-guide-index",
    ]


def test_blocked_ppd_work_stays_parked_for_stale_or_unvalidated_repair() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    stale_or_unvalidated = payload["repair_attempts"][:2]

    assert _parked_work_ids(payload, stale_or_unvalidated) == [
        "ppd-tranche2-item3-normalize-devhub-guides",
        "ppd-tranche2-item3-refresh-permit-guide-index",
    ]


def test_blocked_ppd_work_unparks_only_after_fresh_validated_repair() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert _parked_work_ids(payload, payload["repair_attempts"]) == []
