"""Tests for daemon task-selection recovery validation."""

from __future__ import annotations

from ppd.daemon.task_selection_validation import (
    TaskSelectionFixture,
    TaskState,
    eligible_task_ids,
    validate_blocked_syntax_preflight_selection,
)


def test_blocked_syntax_preflight_task_is_not_reselected() -> None:
    assert validate_blocked_syntax_preflight_selection() == []


def test_unchecked_supervisor_recovery_task_remains_available() -> None:
    tasks = (
        TaskSelectionFixture(
            checkbox_id="checkbox-112",
            title="Blocked syntax-preflight retry",
            state=TaskState.BLOCKED,
            failure_kind="syntax_preflight",
        ),
        TaskSelectionFixture(
            checkbox_id="checkbox-117",
            title="Unchecked supervisor recovery validation",
            state=TaskState.UNCHECKED,
            recovery_kind="supervisor_recovery",
        ),
    )

    assert eligible_task_ids(tasks) == ("checkbox-117",)
