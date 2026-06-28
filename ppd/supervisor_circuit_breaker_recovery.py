"""Deterministic recovery rules for supervisor termination storms.

The helper in this module is intentionally small and side-effect free so the
supervisor can validate circuit-breaker behavior without touching live crawl
state or daemon ledgers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class SupervisorTask:
    """Minimal task shape needed by circuit-breaker recovery tests."""

    task_id: str
    title: str
    state: str
    generated: bool = False
    reason: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class RecoveryTask:
    """Task appended after a vetted termination-storm recovery decision."""

    task_id: str
    title: str
    generated: bool
    vetted: bool
    reopens_blocked_cascade: bool
    storm_id: str
    source: str


@dataclass(frozen=True)
class RecoveryPlan:
    """Pure recovery result consumed by the supervisor."""

    restart_supervisor: bool
    appended_tasks: tuple[RecoveryTask, ...]
    preserved_blocked_generated_task_ids: tuple[str, ...]


@dataclass(frozen=True)
class TerminationStorm:
    """Circuit-breaker termination storm metadata."""

    storm_id: str
    terminated_task_ids: Sequence[str]
    expires_at: datetime

    def is_expired(self, now: datetime) -> bool:
        return _utc(now) >= _utc(self.expires_at)


def build_expired_storm_recovery_plan(
    *,
    storm: TerminationStorm,
    tasks: Iterable[SupervisorTask],
    now: datetime,
) -> RecoveryPlan:
    """Return the restart plan for an expired termination storm.

    Recovery is deliberately conservative: it appends one vetted manual-review
    task and one vetted restart task. It never reopens generated tasks that were
    blocked by cascade protection.
    """

    task_list = tuple(tasks)
    blocked_generated_ids = tuple(
        task.task_id
        for task in task_list
        if task.generated and task.state == "blocked" and task.reason == "blocked-cascade"
    )

    if not storm.is_expired(now):
        return RecoveryPlan(
            restart_supervisor=False,
            appended_tasks=(),
            preserved_blocked_generated_task_ids=blocked_generated_ids,
        )

    appended = (
        RecoveryTask(
            task_id=f"recovery-{storm.storm_id}-vet",
            title="Vet expired termination storm before restart",
            generated=False,
            vetted=True,
            reopens_blocked_cascade=False,
            storm_id=storm.storm_id,
            source="supervisor-circuit-breaker",
        ),
        RecoveryTask(
            task_id=f"recovery-{storm.storm_id}-restart",
            title="Restart supervisor after expired termination storm",
            generated=False,
            vetted=True,
            reopens_blocked_cascade=False,
            storm_id=storm.storm_id,
            source="supervisor-circuit-breaker",
        ),
    )

    return RecoveryPlan(
        restart_supervisor=True,
        appended_tasks=appended,
        preserved_blocked_generated_task_ids=blocked_generated_ids,
    )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
