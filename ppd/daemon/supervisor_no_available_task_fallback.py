"""Deterministic supervisor fallback for no-available-task planning gaps.

The PP&D daemon should not spin when all known tasks are complete and Codex
planning cannot provide the next tranche. This helper keeps the recovery path
small, fixture-first, and free of live DevHub or crawl side effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping
import re


FALLBACK_PLANNING_STATUSES = frozenset({"codex_planning_failed", "codex_planning_timed_out"})
DEFAULT_FALLBACK_TASK_ID = "checkbox-91"
DEFAULT_SOURCE_TASK_ID = "checkbox-86"
DEFAULT_FALLBACK_TITLE = (
    "Add supervisor no-available-task fallback validation proving the supervisor "
    "can append a deterministic fixture-first tranche if Codex planning fails or times out."
)


@dataclass(frozen=True)
class SupervisorNoAvailableTaskState:
    complete_count: int
    task_count: int
    no_available_task: bool
    planning_status: str


def state_from_mapping(data: Mapping[str, object]) -> SupervisorNoAvailableTaskState:
    """Build a compact state object from daemon progress-like fixture data."""

    return SupervisorNoAvailableTaskState(
        complete_count=int(data.get("completeCount", data.get("complete_count", 0))),
        task_count=int(data.get("taskCount", data.get("task_count", 0))),
        no_available_task=bool(data.get("noAvailableTask", data.get("no_available_task", False))),
        planning_status=str(data.get("planningStatus", data.get("planning_status", ""))),
    )


def should_append_fixture_first_tranche(state: SupervisorNoAvailableTaskState) -> bool:
    """Return true only for exhausted task boards with failed or timed-out planning."""

    return (
        state.no_available_task
        and state.task_count > 0
        and state.complete_count >= state.task_count
        and state.planning_status in FALLBACK_PLANNING_STATUSES
    )


def build_fallback_task_line(
    task_id: str = DEFAULT_FALLBACK_TASK_ID,
    source_task_id: str = DEFAULT_SOURCE_TASK_ID,
    title: str = DEFAULT_FALLBACK_TITLE,
) -> str:
    """Return the stable task-board line used by the supervisor fallback."""

    clean_task_id = task_id.strip()
    clean_source_task_id = source_task_id.strip()
    clean_title = title.strip()
    if not clean_task_id:
        raise ValueError("fallback task_id is required")
    if not clean_source_task_id:
        raise ValueError("fallback source_task_id is required")
    if not clean_title:
        raise ValueError("fallback title is required")
    return f"- [ ] Task {clean_task_id}: Task {clean_source_task_id}: {clean_title}"


def build_fixture_first_tranche(
    task_id: str = DEFAULT_FALLBACK_TASK_ID,
    source_task_id: str = DEFAULT_SOURCE_TASK_ID,
    title: str = DEFAULT_FALLBACK_TITLE,
) -> str:
    """Return a deterministic, narrow fallback tranche for task-board appends."""

    task_line = build_fallback_task_line(task_id=task_id, source_task_id=source_task_id, title=title)
    return "\n".join(
        (
            task_line,
            "  - Fixture-first scope: use ppd/daemon/ helpers and ppd/tests/fixtures/daemon/ validation only.",
            "  - Validation: python3 ppd/daemon/ppd_daemon.py --self-test.",
            "  - Forbidden actions: no live DevHub sessions, browser traces, auth state, raw crawl output, uploads, submissions, payments, CAPTCHA, MFA, account creation, cancellation, certification, or inspection scheduling.",
        )
    )


def append_fixture_first_tranche_if_needed(
    board_text: str,
    state: SupervisorNoAvailableTaskState,
    task_id: str = DEFAULT_FALLBACK_TASK_ID,
    source_task_id: str = DEFAULT_SOURCE_TASK_ID,
    title: str = DEFAULT_FALLBACK_TITLE,
) -> str:
    """Append the fallback tranche when the daemon has no task and planning failed.

    The operation is idempotent: an existing fallback task is left unchanged.
    """

    if not should_append_fixture_first_tranche(state):
        return board_text

    task_pattern = re.compile(rf"Task\s+{re.escape(task_id)}\s*:")
    if task_pattern.search(board_text):
        return board_text

    tranche = build_fixture_first_tranche(task_id=task_id, source_task_id=source_task_id, title=title)
    stripped_board = board_text.rstrip()
    heading = "## Next Goal-Aligned Tranche"
    if heading in stripped_board:
        return f"{stripped_board}\n\n{tranche}\n"
    return f"{stripped_board}\n\n{heading}\n\n{tranche}\n"
