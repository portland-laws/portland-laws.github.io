from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass(frozen=True)
class BlockedWork:
    item_id: str
    blocked_by: str
    blocked_at_generation: int


@dataclass(frozen=True)
class DaemonRepair:
    repair_id: str
    target: str
    issued_at_generation: int
    validated: bool


def _fixture_path() -> Path:
    return Path(__file__).parent / "fixtures" / "blocked_cascade" / "tranche_13_item_3.json"


def _load_fixture() -> tuple[BlockedWork, List[DaemonRepair]]:
    payload = json.loads(_fixture_path().read_text(encoding="utf-8"))
    blocked = payload["blocked_work"]
    repairs = payload["repairs"]
    return (
        BlockedWork(
            item_id=blocked["id"],
            blocked_by=blocked["blocked_by"],
            blocked_at_generation=blocked["blocked_at_generation"],
        ),
        [
            DaemonRepair(
                repair_id=repair["id"],
                target=repair["target"],
                issued_at_generation=repair["issued_at_generation"],
                validated=repair["validated"],
            )
            for repair in repairs
        ],
    )


def _is_fresh_validating_repair(blocked: BlockedWork, repair: DaemonRepair) -> bool:
    return (
        repair.target == blocked.blocked_by
        and repair.issued_at_generation > blocked.blocked_at_generation
        and repair.validated
    )


def _is_still_parked(blocked: BlockedWork, repairs: Iterable[DaemonRepair]) -> bool:
    return not any(_is_fresh_validating_repair(blocked, repair) for repair in repairs)


def test_blocked_ppd_work_stays_parked_until_fresh_daemon_repair_validates() -> None:
    blocked, repairs = _load_fixture()

    assert blocked.item_id == "ppd-work-tranche-13-item-3"
    assert _is_still_parked(blocked, [])
    assert _is_still_parked(blocked, repairs[:1])
    assert _is_still_parked(blocked, repairs[:2])
    assert not _is_still_parked(blocked, repairs)


def test_stale_validated_repair_is_not_enough_to_unpark_blocked_work() -> None:
    blocked, repairs = _load_fixture()
    stale_repair = repairs[0]

    assert stale_repair.validated
    assert stale_repair.issued_at_generation == blocked.blocked_at_generation
    assert not _is_fresh_validating_repair(blocked, stale_repair)


def test_fresh_unvalidated_repair_is_not_enough_to_unpark_blocked_work() -> None:
    blocked, repairs = _load_fixture()
    failed_repair = repairs[1]

    assert failed_repair.issued_at_generation > blocked.blocked_at_generation
    assert not failed_repair.validated
    assert not _is_fresh_validating_repair(blocked, failed_repair)
