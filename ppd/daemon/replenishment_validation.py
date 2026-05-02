"""Deterministic completed-board replenishment validation for PP&D tasks.

The worker daemon should be able to move from a fully accepted task board to a
new goal-aligned tranche without losing accepted-work history or carrying stale
repair pressure forward. This module models that transition without launching
the daemon, calling an LLM, opening DevHub, or touching runtime artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


@dataclass(frozen=True)
class CompletedTask:
    checkbox_id: str
    title: str
    accepted_work_id: str


@dataclass(frozen=True)
class ReplenishmentTask:
    checkbox_id: str
    title: str
    style: str
    status: str = "needed"


@dataclass(frozen=True)
class SupervisorRepairState:
    target_task: str
    consecutive_failures: int
    stale_repair_count: int


@dataclass(frozen=True)
class ReplenishmentResult:
    before_task_count: int
    after_task_count: int
    preserved_accepted_work_ids: tuple[str, ...]
    appended_task_ids: tuple[str, ...]
    next_selectable_task_id: str
    stale_repair_count_after: int
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_completed_board_replenishment(
    completed_tasks: Sequence[CompletedTask],
    accepted_work_ids: Iterable[str],
    appended_tasks: Sequence[ReplenishmentTask],
    supervisor_state: SupervisorRepairState,
) -> ReplenishmentResult:
    """Validate that a completed PP&D board can receive a fresh task tranche."""

    errors: list[str] = []
    accepted = tuple(accepted_work_ids)
    completed_ids = tuple(task.checkbox_id for task in completed_tasks)
    completed_accepted_ids = tuple(task.accepted_work_id for task in completed_tasks)
    appended_ids = tuple(task.checkbox_id for task in appended_tasks)

    if not completed_tasks:
        errors.append("completed board snapshot must contain at least one task")
    if len(set(completed_ids)) != len(completed_ids):
        errors.append("completed task checkbox ids must be unique")
    if len(set(appended_ids)) != len(appended_ids):
        errors.append("appended task checkbox ids must be unique")
    if set(completed_ids).intersection(appended_ids):
        errors.append("appended task ids must not reuse completed task ids")
    if not set(completed_accepted_ids).issubset(set(accepted)):
        errors.append("accepted-work history must preserve every completed task artifact")
    if not appended_tasks:
        errors.append("a replenishment transition must append at least one task")

    selectable = tuple(task for task in appended_tasks if task.status == "needed")
    if not selectable:
        errors.append("new tranche must include a needed task selectable by the daemon")

    allowed_styles = {"fixture_first", "validation_first", "daemon_supervision"}
    for task in appended_tasks:
        if task.status != "needed":
            errors.append(f"appended task {task.checkbox_id} must start as needed")
        if task.style not in allowed_styles:
            errors.append(f"appended task {task.checkbox_id} has unsupported style {task.style!r}")

    next_selectable = selectable[0].checkbox_id if selectable else ""
    if supervisor_state.target_task in completed_ids and supervisor_state.consecutive_failures:
        errors.append("stale supervisor failures must not remain attached to completed tasks")

    stale_repair_count_after = 0
    return ReplenishmentResult(
        before_task_count=len(completed_tasks),
        after_task_count=len(completed_tasks) + len(appended_tasks),
        preserved_accepted_work_ids=completed_accepted_ids,
        appended_task_ids=appended_ids,
        next_selectable_task_id=next_selectable,
        stale_repair_count_after=stale_repair_count_after,
        errors=tuple(errors),
    )


def build_replenishment_fixture() -> dict[str, object]:
    """Return a compact fixture dict used by tests and supervisor prompts."""

    return {
        "completed_tasks": [
            {
                "checkbox_id": "checkbox-79",
                "title": "reversible draft-only agent plan fixture",
                "accepted_work_id": "accepted-agent-planning-reversible-draft-only",
            },
            {
                "checkbox_id": "checkbox-80",
                "title": "processor archive provenance fixture",
                "accepted_work_id": "accepted-processor-archive-provenance",
            },
        ],
        "accepted_work_ids": [
            "accepted-agent-planning-reversible-draft-only",
            "accepted-processor-archive-provenance",
        ],
        "appended_tasks": [
            {
                "checkbox_id": "checkbox-82",
                "title": "formal guardrail planner integration fixture",
                "style": "fixture_first",
                "status": "needed",
            },
            {
                "checkbox_id": "checkbox-83",
                "title": "processor archive manifest validation",
                "style": "validation_first",
                "status": "needed",
            },
        ],
        "supervisor_state": {
            "target_task": "checkbox-80",
            "consecutive_failures": 0,
            "stale_repair_count": 2,
        },
    }


def validate_replenishment_fixture(fixture: Mapping[str, object]) -> ReplenishmentResult:
    """Validate a JSON-like fixture for completed-board replenishment."""

    completed = tuple(
        CompletedTask(
            checkbox_id=str(item.get("checkbox_id", "")),
            title=str(item.get("title", "")),
            accepted_work_id=str(item.get("accepted_work_id", "")),
        )
        for item in _object_list(fixture.get("completed_tasks"))
    )
    appended = tuple(
        ReplenishmentTask(
            checkbox_id=str(item.get("checkbox_id", "")),
            title=str(item.get("title", "")),
            style=str(item.get("style", "")),
            status=str(item.get("status", "")),
        )
        for item in _object_list(fixture.get("appended_tasks"))
    )
    state_data = fixture.get("supervisor_state")
    state_map = state_data if isinstance(state_data, Mapping) else {}
    state = SupervisorRepairState(
        target_task=str(state_map.get("target_task", "")),
        consecutive_failures=int(state_map.get("consecutive_failures", 0)),
        stale_repair_count=int(state_map.get("stale_repair_count", 0)),
    )
    accepted_ids = tuple(str(item) for item in _string_list(fixture.get("accepted_work_ids")))
    return validate_completed_board_replenishment(completed, accepted_ids, appended, state)


def _object_list(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _string_list(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


__all__ = [
    "CompletedTask",
    "ReplenishmentResult",
    "ReplenishmentTask",
    "SupervisorRepairState",
    "build_replenishment_fixture",
    "validate_completed_board_replenishment",
    "validate_replenishment_fixture",
]
