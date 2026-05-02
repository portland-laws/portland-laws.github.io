"""Deterministic validation for PP&D daemon task selection recovery cases.

This module is intentionally standalone and fixture-only. It models narrow
selection invariants needed after failed daemon rounds:

- blocked tasks are not eligible for reselection.
- unchecked supervisor recovery tasks remain available.
- accepted supersession evidence for a blocked domain task requires a task-board
  reconciliation task before the domain task can be revisited.

The implementation avoids regular-expression task-board parsing on purpose. The
recent daemon failures were syntax/preflight-sensitive, so these guardrails use
small typed fixtures that can be validated by py_compile and unittest without
live crawling, authenticated automation, or task-board mutation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskState(str, Enum):
    CHECKED = "checked"
    UNCHECKED = "unchecked"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class TaskSelectionFixture:
    checkbox_id: str
    title: str
    state: TaskState
    failure_kind: str | None = None
    recovery_kind: str | None = None
    task_kind: str = "daemon"
    accepted_supersession_evidence: bool = False
    task_board_supersession_note_appended: bool = False


def eligible_task_ids(tasks: tuple[TaskSelectionFixture, ...]) -> tuple[str, ...]:
    """Return task ids the daemon may select for the next cycle."""

    eligible: list[str] = []
    for task in tasks:
        if task.state != TaskState.UNCHECKED:
            continue
        eligible.append(task.checkbox_id)
    return tuple(eligible)


def tasks_requiring_supersession_reconciliation(
    tasks: tuple[TaskSelectionFixture, ...],
) -> tuple[str, ...]:
    """Return blocked domain tasks whose accepted supersession evidence is unrecorded.

    A blocked domain task with accepted supersession evidence is not a domain-work
    candidate. Until the task board records the supersession note, the daemon
    should select a narrow board-reconciliation task instead.
    """

    requiring_reconciliation: list[str] = []
    for task in tasks:
        if task.state != TaskState.BLOCKED:
            continue
        if task.task_kind != "domain":
            continue
        if not task.accepted_supersession_evidence:
            continue
        if task.task_board_supersession_note_appended:
            continue
        requiring_reconciliation.append(task.checkbox_id)
    return tuple(requiring_reconciliation)


def validate_blocked_syntax_preflight_selection() -> list[str]:
    """Validate blocked syntax-preflight tasks are skipped but recovery remains."""

    tasks = (
        TaskSelectionFixture(
            checkbox_id="checkbox-112",
            title="Resume syntax-sensitive fixture validator after failed parser rollback",
            state=TaskState.BLOCKED,
            failure_kind="syntax_preflight",
        ),
        TaskSelectionFixture(
            checkbox_id="checkbox-116",
            title="Add supervisor recovery task after repeated syntax-preflight failures",
            state=TaskState.UNCHECKED,
            recovery_kind="supervisor_recovery",
        ),
        TaskSelectionFixture(
            checkbox_id="checkbox-111",
            title="Previously accepted daemon preflight guardrail",
            state=TaskState.CHECKED,
        ),
    )

    selected = eligible_task_ids(tasks)
    errors: list[str] = []

    if "checkbox-112" in selected:
        errors.append("blocked syntax-preflight task checkbox-112 must not be reselected")
    if "checkbox-116" not in selected:
        errors.append("unchecked supervisor recovery task checkbox-116 must remain eligible")
    if selected != ("checkbox-116",):
        errors.append(f"expected only checkbox-116 to be eligible, got {selected!r}")

    return errors


def validate_blocked_superseded_domain_task_selection() -> list[str]:
    """Validate accepted supersession evidence forces board reconciliation first."""

    tasks = (
        TaskSelectionFixture(
            checkbox_id="checkbox-108",
            title="Implement crawl frontier decision contract fixtures",
            state=TaskState.BLOCKED,
            failure_kind="superseded_by_accepted_evidence",
            task_kind="domain",
            accepted_supersession_evidence=True,
            task_board_supersession_note_appended=False,
        ),
        TaskSelectionFixture(
            checkbox_id="checkbox-132",
            title="Record checkbox-108 supersession on the task board before domain retry",
            state=TaskState.UNCHECKED,
            recovery_kind="task_board_supersession_reconciliation",
            task_kind="daemon",
        ),
        TaskSelectionFixture(
            checkbox_id="checkbox-131",
            title="Accepted supersession evidence validation",
            state=TaskState.CHECKED,
            task_kind="daemon",
        ),
    )

    selected = eligible_task_ids(tasks)
    reconciliation_required = tasks_requiring_supersession_reconciliation(tasks)
    errors: list[str] = []

    if reconciliation_required != ("checkbox-108",):
        errors.append(
            "expected checkbox-108 to require task-board supersession reconciliation, "
            f"got {reconciliation_required!r}"
        )
    if "checkbox-108" in selected:
        errors.append("blocked superseded domain task checkbox-108 must not be reselected")
    if selected != ("checkbox-132",):
        errors.append(f"expected only checkbox-132 to be eligible, got {selected!r}")

    return errors


def run_self_test() -> None:
    errors = []
    errors.extend(validate_blocked_syntax_preflight_selection())
    errors.extend(validate_blocked_superseded_domain_task_selection())
    if errors:
        raise AssertionError("; ".join(errors))


if __name__ == "__main__":
    run_self_test()
