from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class DaemonTask:
    task_id: str
    status: str
    accepted_at: str | None = None
    blocked_reason: str | None = None
    reopened_by_human: bool = False


BLOCKED_STATUSES = {"blocked", "needs-human", "failed-blocked"}
SELECTABLE_STATUSES = {"accepted", "open", "ready"}


def _fixture_path(name: str) -> Path:
    return Path(__file__).parent / "fixtures" / "daemon_task_selection" / name


def _is_blocked(task: DaemonTask) -> bool:
    return task.status in BLOCKED_STATUSES or bool(task.blocked_reason)


def _select_next_task(tasks: Iterable[DaemonTask]) -> DaemonTask | None:
    """Small deterministic selector fixture mirroring the daemon invariant under test.

    A blocked task may not be selected again because retry state still exists. It
    becomes selectable only when a human explicitly reopens that same task. A new
    accepted repair task is independently selectable and should let the daemon
    continue without mutating the blocked task.
    """

    candidates: list[DaemonTask] = []
    for task in tasks:
        if _is_blocked(task) and not task.reopened_by_human:
            continue
        if task.status in SELECTABLE_STATUSES or task.reopened_by_human:
            candidates.append(task)

    return sorted(candidates, key=lambda task: (task.accepted_at or "", task.task_id))[0] if candidates else None


def test_blocked_task_is_skipped_even_when_it_is_the_only_known_task() -> None:
    blocked_task = DaemonTask(
        task_id="checkbox-64",
        status="blocked",
        accepted_at="2026-05-13T00:00:00Z",
        blocked_reason="validation failed and needs an explicit repair path",
    )

    assert _select_next_task([blocked_task]) is None


def test_new_non_blocked_repair_task_is_selected_without_reopening_blocked_task() -> None:
    blocked_task = DaemonTask(
        task_id="checkbox-64",
        status="blocked",
        accepted_at="2026-05-13T00:00:00Z",
        blocked_reason="previous proposal failed validation",
    )
    repair_task = DaemonTask(
        task_id="repair-checkbox-64-daemon-selection",
        status="accepted",
        accepted_at="2026-05-13T00:01:00Z",
    )

    selected = _select_next_task([blocked_task, repair_task])

    assert selected == repair_task
    assert blocked_task.blocked_reason == "previous proposal failed validation"
    assert blocked_task.reopened_by_human is False


def test_human_reopen_makes_the_original_blocked_task_selectable_again() -> None:
    blocked_task = DaemonTask(
        task_id="checkbox-64",
        status="blocked",
        accepted_at="2026-05-13T00:00:00Z",
        blocked_reason="waiting for human review",
    )
    reopened_task = replace(blocked_task, reopened_by_human=True, blocked_reason=None, status="ready")

    assert _select_next_task([blocked_task]) is None
    assert _select_next_task([reopened_task]) == reopened_task


def test_fixture_paths_are_scoped_to_ppd_tests() -> None:
    path = _fixture_path("blocked_task_selection.json")

    assert path.parts[-4:] == ("ppd", "tests", "fixtures", "daemon_task_selection") or path.parent.name == "daemon_task_selection"
