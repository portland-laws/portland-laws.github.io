"""Deterministic blocked-cascade repair gating helpers for PP&D daemon coverage."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class BlockedWork:
    """A blocked PP&D work item waiting on daemon repair validation."""

    work_id: str
    blocked_at: datetime
    blocked_by: str
    state: str = "blocked"


@dataclass(frozen=True)
class RepairTask:
    """A daemon repair task that may validate blocked work."""

    task_id: str
    validates: str
    state: str
    validated_at: datetime | None = None


@dataclass(frozen=True)
class CascadeDecision:
    """Decision for whether blocked work remains parked or may resume."""

    work_id: str
    parked: bool
    reason: str
    repair_task_id: str | None = None


def parse_utc(value: str | None) -> datetime | None:
    """Parse a stable UTC timestamp used by deterministic fixtures."""

    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def blocked_work_from_mapping(data: Mapping[str, object]) -> BlockedWork:
    return BlockedWork(
        work_id=str(data["work_id"]),
        blocked_at=parse_utc(str(data["blocked_at"])) or datetime.min.replace(tzinfo=timezone.utc),
        blocked_by=str(data["blocked_by"]),
        state=str(data.get("state", "blocked")),
    )


def repair_task_from_mapping(data: Mapping[str, object]) -> RepairTask:
    raw_validated_at = data.get("validated_at")
    return RepairTask(
        task_id=str(data["task_id"]),
        validates=str(data["validates"]),
        state=str(data["state"]),
        validated_at=parse_utc(str(raw_validated_at)) if raw_validated_at is not None else None,
    )


def decide_blocked_cascade(
    work: BlockedWork,
    repair_tasks: Sequence[RepairTask],
    previous_validated_repair_ids: Iterable[str] = (),
) -> CascadeDecision:
    """Keep blocked work parked until a fresh matching repair validates."""

    previous_ids = set(previous_validated_repair_ids)
    matching_repairs = [task for task in repair_tasks if task.validates == work.blocked_by]
    validated_repairs = [
        task
        for task in matching_repairs
        if task.state == "validated" and task.validated_at is not None
    ]
    fresh_repairs = [
        task
        for task in validated_repairs
        if task.task_id not in previous_ids and task.validated_at > work.blocked_at
    ]

    if work.state != "blocked":
        return CascadeDecision(work_id=work.work_id, parked=False, reason="not-blocked")
    if not matching_repairs:
        return CascadeDecision(work_id=work.work_id, parked=True, reason="no-repair-task")
    if not validated_repairs:
        return CascadeDecision(work_id=work.work_id, parked=True, reason="repair-not-validated")
    if not fresh_repairs:
        return CascadeDecision(work_id=work.work_id, parked=True, reason="no-fresh-validated-repair")

    newest = max(fresh_repairs, key=lambda task: task.validated_at or datetime.min.replace(tzinfo=timezone.utc))
    return CascadeDecision(
        work_id=work.work_id,
        parked=False,
        reason="fresh-validated-repair",
        repair_task_id=newest.task_id,
    )
