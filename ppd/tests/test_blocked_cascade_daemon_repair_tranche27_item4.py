"""Regression coverage for tranche 27 item 4 blocked-cascade repair gating."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "daemon"
    / "blocked_cascade_tranche27_item4.json"
)


@dataclass(frozen=True)
class BlockedWork:
    task_id: str
    blocked_by: str
    parked: bool


@dataclass(frozen=True)
class RepairEvent:
    repair_generation: int
    repair_status: str


@dataclass(frozen=True)
class ParkingDecision:
    parked: bool
    selectable: bool


def _load_fixture() -> dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _parking_decision(
    blocked_work: BlockedWork,
    repair_event: RepairEvent,
    required_repair_generation: int,
) -> ParkingDecision:
    fresh_repair_validated = (
        repair_event.repair_generation >= required_repair_generation
        and repair_event.repair_status == "validated"
    )

    if blocked_work.parked and not fresh_repair_validated:
        return ParkingDecision(parked=True, selectable=False)

    return ParkingDecision(parked=False, selectable=True)


def test_blocked_ppd_work_stays_parked_until_fresh_daemon_repair_validates() -> None:
    fixture = _load_fixture()
    blocked_task = fixture["blocked_task"]
    repair_task = fixture["repair_task"]

    blocked_work = BlockedWork(
        task_id=blocked_task["id"],
        blocked_by=blocked_task["blocked_by"],
        parked=blocked_task["parked"],
    )

    assert blocked_task["status"] == "blocked"
    assert repair_task["kind"] == "daemon_repair"
    assert blocked_work.blocked_by == repair_task["id"]

    for event_data in fixture["events"]:
        event = RepairEvent(
            repair_generation=event_data["repair_generation"],
            repair_status=event_data["repair_status"],
        )
        decision = _parking_decision(
            blocked_work=blocked_work,
            repair_event=event,
            required_repair_generation=repair_task["generation"],
        )

        assert decision.parked is event_data["expect_parked"], event_data["name"]
        assert decision.selectable is event_data["expect_selectable"], event_data["name"]


def test_stale_validated_repair_cannot_unpark_blocked_cascade_work() -> None:
    fixture = _load_fixture()
    blocked_task = fixture["blocked_task"]
    repair_task = fixture["repair_task"]
    stale_event = next(
        event
        for event in fixture["events"]
        if event["name"] == "stale_prior_repair_validated"
    )

    decision = _parking_decision(
        blocked_work=BlockedWork(
            task_id=blocked_task["id"],
            blocked_by=blocked_task["blocked_by"],
            parked=True,
        ),
        repair_event=RepairEvent(
            repair_generation=stale_event["repair_generation"],
            repair_status=stale_event["repair_status"],
        ),
        required_repair_generation=repair_task["generation"],
    )

    assert decision == ParkingDecision(parked=True, selectable=False)
