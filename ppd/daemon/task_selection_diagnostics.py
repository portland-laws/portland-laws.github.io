"""Small deterministic diagnostics for PP&D supervisor task selection.

The helper in this module is intentionally side-effect free.  It accepts already
loaded task records and returns a compact explanation of the first selectable
candidate, or why no candidate should be run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


DEFAULT_RETRY_LIMIT = 3


@dataclass(frozen=True)
class TaskSelectionDiagnostic:
    """Result of validating task-selection candidates."""

    selected_task_id: str | None
    reason: str
    checked: int
    skipped: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "selected_task_id": self.selected_task_id,
            "reason": self.reason,
            "checked": self.checked,
            "skipped": list(self.skipped),
        }


def _task_id(task: Mapping[str, Any], fallback_index: int) -> str:
    value = task.get("id") or task.get("task_id") or task.get("checkbox")
    if value is None:
        return f"index:{fallback_index}"
    return str(value)


def _retry_count(task: Mapping[str, Any]) -> int:
    value = task.get("retries", task.get("retry_count", 0))
    try:
        count = int(value)
    except (TypeError, ValueError):
        return DEFAULT_RETRY_LIMIT
    return max(count, 0)


def _is_complete(task: Mapping[str, Any]) -> bool:
    status = str(task.get("status", "")).strip().lower()
    return bool(task.get("complete") or task.get("completed") or status in {"done", "complete", "completed"})


def _is_blocked(task: Mapping[str, Any]) -> bool:
    status = str(task.get("status", "")).strip().lower()
    return bool(task.get("blocked") or status == "blocked")


def diagnose_task_selection(
    tasks: Sequence[Mapping[str, Any]],
    *,
    retry_limit: int = DEFAULT_RETRY_LIMIT,
) -> TaskSelectionDiagnostic:
    """Return the first validation-passing candidate and skipped-task reasons.

    The selector is deliberately conservative: completed, blocked, invalid, and
    retry-exhausted tasks are reported before any task is selected.
    """

    bounded_retry_limit = max(int(retry_limit), 0)
    skipped: list[str] = []

    for index, task in enumerate(tasks):
        task_id = _task_id(task, index)

        if not isinstance(task, Mapping):
            skipped.append(f"{task_id}: invalid task record")
            continue

        if _is_complete(task):
            skipped.append(f"{task_id}: already complete")
            continue

        if _is_blocked(task):
            skipped.append(f"{task_id}: blocked")
            continue

        retries = _retry_count(task)
        if retries >= bounded_retry_limit:
            skipped.append(f"{task_id}: retry limit reached ({retries}/{bounded_retry_limit})")
            continue

        if task.get("requires_live_crawl") and not task.get("fixture_validated"):
            skipped.append(f"{task_id}: live crawl gated until fixture validation passes")
            continue

        return TaskSelectionDiagnostic(
            selected_task_id=task_id,
            reason="selected first validation-passing task",
            checked=index + 1,
            skipped=tuple(skipped),
        )

    return TaskSelectionDiagnostic(
        selected_task_id=None,
        reason="no validation-passing task candidates",
        checked=len(tasks),
        skipped=tuple(skipped),
    )
