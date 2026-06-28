from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "daemon_repair"
    / "blocked_cascade_tranche6_item2.json"
)


@dataclass(frozen=True)
class BlockedWork:
    item_id: str
    blocked_at: datetime
    parked: bool


@dataclass(frozen=True)
class RepairTask:
    task_id: str
    target: str
    created_at: datetime
    validated: bool


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.astimezone(timezone.utc)


def _load_fixture() -> tuple[BlockedWork, list[RepairTask]]:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    blocked = payload["blocked_item"]
    repairs = payload["repairs"]
    return (
        BlockedWork(
            item_id=blocked["id"],
            blocked_at=_parse_utc(blocked["blocked_at"]),
            parked=bool(blocked["parked"]),
        ),
        [
            RepairTask(
                task_id=repair["id"],
                target=repair["target"],
                created_at=_parse_utc(repair["created_at"]),
                validated=bool(repair["validated"]),
            )
            for repair in repairs
        ],
    )


def _is_fresh_validating_repair(blocked: BlockedWork, repair: RepairTask) -> bool:
    return (
        repair.target == blocked.item_id
        and repair.validated
        and repair.created_at > blocked.blocked_at
    )


def _cascade_state_after_repairs(
    blocked: BlockedWork, repairs: list[RepairTask]
) -> list[tuple[str, str]]:
    parked = blocked.parked
    states: list[tuple[str, str]] = []
    for repair in repairs:
        if parked and _is_fresh_validating_repair(blocked, repair):
            parked = False
        states.append((repair.task_id, "parked" if parked else "ready"))
    return states


def test_blocked_ppd_work_stays_parked_until_fresh_daemon_repair_validates() -> None:
    blocked, repairs = _load_fixture()

    assert _cascade_state_after_repairs(blocked, repairs) == [
        ("repair-stale", "parked"),
        ("repair-failed", "parked"),
        ("repair-fresh-valid", "ready"),
    ]


def test_stale_or_failed_repairs_do_not_unpark_blocked_work() -> None:
    blocked, repairs = _load_fixture()

    parked_only_repairs = repairs[:2]

    assert _cascade_state_after_repairs(blocked, parked_only_repairs) == [
        ("repair-stale", "parked"),
        ("repair-failed", "parked"),
    ]
