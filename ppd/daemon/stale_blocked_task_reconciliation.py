"""Reconcile stale blocked PP&D daemon tasks.

Blocked recovery tasks can become stale when a later accepted task explicitly
supersedes and satisfies the same recovery goal. This helper keeps that logic
small and deterministic so daemon task-selection tests can cover it without
requiring a live daemon cycle.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Optional, Protocol


SATISFIED_BY_RE = re.compile(
    r"\b(?:superseded\s+and\s+satisfied\s+by|satisfied\s+by)\s+checkbox-(?P\d+)\b",
    re.IGNORECASE,
)


class TaskLike(Protocol):
    index: int
    title: str
    status: str


@dataclass(frozen=True)
class BlockedTaskReconciliation:
    task_index: int
    satisfied_by_index: int
    reason: str


def satisfied_by_indexes(title: str) -> tuple[int, ...]:
    """Return checkbox indexes that a task title says satisfy this task."""

    indexes: list[int] = []
    for match in SATISFIED_BY_RE.finditer(title):
        try:
            indexes.append(int(match.group("index")))
        except ValueError:
            continue
    return tuple(indexes)


def stale_blocked_reconciliation(
    task: TaskLike,
    completed_indexes: set[int],
) -> Optional[BlockedTaskReconciliation]:
    """Return reconciliation details when a blocked task is already satisfied."""

    if task.status != "blocked":
        return None
    for satisfied_by_index in satisfied_by_indexes(task.title):
        if satisfied_by_index in completed_indexes:
            return BlockedTaskReconciliation(
                task_index=task.index,
                satisfied_by_index=satisfied_by_index,
                reason=(
                    f"blocked task checkbox-{task.index} is superseded by "
                    f"accepted checkbox-{satisfied_by_index}"
                ),
            )
    return None


def reconciled_blocked_tasks(tasks: Iterable[TaskLike]) -> tuple[BlockedTaskReconciliation, ...]:
    """Find blocked tasks whose recovery goal is already satisfied."""

    task_list = list(tasks)
    completed_indexes = {task.index for task in task_list if task.status == "complete"}
    reconciliations: list[BlockedTaskReconciliation] = []
    for task in task_list:
        reconciliation = stale_blocked_reconciliation(task, completed_indexes)
        if reconciliation is not None:
            reconciliations.append(reconciliation)
    return tuple(reconciliations)


def first_reselectable_blocked_task(tasks: Iterable[TaskLike]) -> Optional[TaskLike]:
    """Return the first blocked task that has not been superseded by completion."""

    task_list = list(tasks)
    completed_indexes = {task.index for task in task_list if task.status == "complete"}
    for task in task_list:
        if task.status != "blocked":
            continue
        if stale_blocked_reconciliation(task, completed_indexes) is None:
            return task
    return None
