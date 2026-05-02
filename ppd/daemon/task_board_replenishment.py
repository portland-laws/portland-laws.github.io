"""Task-board replenishment helpers for PP&D daemon supervision.

These helpers are intentionally small and deterministic. They operate on task-board
markdown only; they do not inspect live daemon state, run crawls, or write files.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


TASK_MARKER = "- [ ] Task "
DONE_MARKER = "- [x] Task "
BLOCKED_HEADING_MARKERS = (
    "## Blocked",
    "## Parked",
    "## Superseded or Parked",
)
SECTION_HEADING_PREFIX = "## "


@dataclass(frozen=True)
class ReplenishmentResult:
    """Result of appending a supervisor tranche to a task board."""

    board_text: str
    appended: bool
    preserved_completed_count: int
    parked_blocked_count: int


def append_supervisor_tranche_when_only_blocked_remains(
    board_text: str,
    supervisor_tasks: Iterable[str],
) -> ReplenishmentResult:
    """Append supervisor tasks when no selectable tasks remain.

    A selectable task is an unchecked markdown task outside a blocked or parked
    section. Blocked and parked unchecked tasks must remain in place so the
    daemon does not lose the reason they were deferred.
    """

    lines = board_text.splitlines()
    completed_count = _count_completed(lines)
    parked_blocked_count = _count_parked_blocked(lines)

    if _has_selectable_task(lines) or parked_blocked_count == 0:
        return ReplenishmentResult(
            board_text=board_text,
            appended=False,
            preserved_completed_count=completed_count,
            parked_blocked_count=parked_blocked_count,
        )

    tranche_lines = _normalize_supervisor_tasks(supervisor_tasks)
    if not tranche_lines:
        return ReplenishmentResult(
            board_text=board_text,
            appended=False,
            preserved_completed_count=completed_count,
            parked_blocked_count=parked_blocked_count,
        )

    suffix = ["", "## Supervisor Replenishment", "", *tranche_lines]
    replenished = "\n".join([*lines, *suffix]).rstrip() + "\n"
    return ReplenishmentResult(
        board_text=replenished,
        appended=True,
        preserved_completed_count=completed_count,
        parked_blocked_count=parked_blocked_count,
    )


def _count_completed(lines: Iterable[str]) -> int:
    return sum(1 for line in lines if line.startswith(DONE_MARKER))


def _count_parked_blocked(lines: Iterable[str]) -> int:
    blocked = False
    count = 0
    for line in lines:
        if line.startswith(SECTION_HEADING_PREFIX):
            blocked = line.startswith(BLOCKED_HEADING_MARKERS)
        if blocked and line.startswith(TASK_MARKER):
            count += 1
    return count


def _has_selectable_task(lines: Iterable[str]) -> bool:
    blocked = False
    for line in lines:
        if line.startswith(SECTION_HEADING_PREFIX):
            blocked = line.startswith(BLOCKED_HEADING_MARKERS)
        if not blocked and line.startswith(TASK_MARKER):
            return True
    return False


def _normalize_supervisor_tasks(supervisor_tasks: Iterable[str]) -> list[str]:
    normalized: list[str] = []
    for task in supervisor_tasks:
        stripped = task.strip()
        if not stripped:
            continue
        if not stripped.startswith(TASK_MARKER):
            raise ValueError(f"supervisor tranche entries must be unchecked task lines: {stripped}")
        normalized.append(stripped)
    return normalized
