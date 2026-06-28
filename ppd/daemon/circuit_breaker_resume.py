"""Deterministic resume selection helpers for PP&D daemon circuit-breaker recovery.

The daemon can receive model-generated cascade tasks after a circuit breaker parks
an unsafe or stale tranche. On resume, those generated cascade tasks must remain
skipped until a fresh vetted recovery task has been selected first. This module
keeps that ordering rule small and independently testable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


SKIPPED_GENERATED_CASCADE = "skipped_generated_cascade_after_circuit_breaker"
SELECTED_VETTED_RECOVERY = "selected_vetted_recovery_after_circuit_breaker"


@dataclass(frozen=True)
class ResumeTask:
    """Task metadata needed for circuit-breaker resume selection."""

    task_id: str
    status: str = "pending"
    generated: bool = False
    cascade: bool = False
    vetted_recovery: bool = False
    blocked: bool = False


@dataclass(frozen=True)
class ResumeDecision:
    """Selected task and generated cascade tasks intentionally skipped."""

    selected_task_id: str | None
    reason: str
    skipped_task_ids: tuple[str, ...]


def select_circuit_breaker_resume_task(tasks: Sequence[ResumeTask]) -> ResumeDecision:
    """Select the first vetted recovery task before generated cascade tasks.

    Rules:
    - Only pending, unblocked tasks are selectable.
    - Pending generated cascade tasks are skipped during circuit-breaker resume.
    - The first pending, unblocked vetted recovery task is selected before any
      ordinary pending task.
    - If no vetted recovery task exists, the first ordinary pending task is
      selected. Generated cascade tasks still remain skipped.
    """

    skipped_generated = tuple(
        task.task_id
        for task in tasks
        if _is_pending_unblocked(task) and task.generated and task.cascade
    )

    vetted = _first(
        task
        for task in tasks
        if _is_pending_unblocked(task)
        and task.vetted_recovery
        and not (task.generated and task.cascade)
    )
    if vetted is not None:
        return ResumeDecision(
            selected_task_id=vetted.task_id,
            reason=SELECTED_VETTED_RECOVERY,
            skipped_task_ids=skipped_generated,
        )

    ordinary = _first(
        task
        for task in tasks
        if _is_pending_unblocked(task) and not (task.generated and task.cascade)
    )
    if ordinary is not None:
        return ResumeDecision(
            selected_task_id=ordinary.task_id,
            reason="selected_ordinary_pending_after_circuit_breaker",
            skipped_task_ids=skipped_generated,
        )

    return ResumeDecision(
        selected_task_id=None,
        reason=SKIPPED_GENERATED_CASCADE,
        skipped_task_ids=skipped_generated,
    )


def _is_pending_unblocked(task: ResumeTask) -> bool:
    return task.status == "pending" and not task.blocked


def _first(tasks: Iterable[ResumeTask]) -> ResumeTask | None:
    for task in tasks:
        return task
    return None
