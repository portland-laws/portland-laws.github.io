"""No-eligible-task replanning guidance for the PP&D daemon.

This module is intentionally small and fixture-first. It only builds prompt
text for the daemon supervisor when parsed progress has no selectable task.
It does not edit the task board, run crawlers, open DevHub, or touch runtime
ledger state.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NoEligibleTaskState:
    """Parsed progress state used to decide the daemon's next guidance."""

    complete: int
    task_count: int
    expanded_goals_present: bool
    stale_progress_label: str = "complete == task_count"

    def is_completed_board_with_expanded_goals(self) -> bool:
        return self.task_count > 0 and self.complete == self.task_count and self.expanded_goals_present


def build_no_eligible_task_replanning_guidance(state: NoEligibleTaskState) -> str:
    """Return deterministic supervisor guidance for no-eligible-task states.

    When all parsed tasks are complete but the task board has expanded goals,
    repeated repair is stale work. The useful next action is to append a small
    fixture-first tranche and let the daemon select from that fresh backlog.
    """

    if state.is_completed_board_with_expanded_goals():
        return "\n".join(
            (
                "No eligible unchecked PP&D task was found, but progress reports "
                f"{state.stale_progress_label} and the task board contains expanded goals.",
                "Do not invoke repeated repair against stale completed progress.",
                "Append the next narrow fixture-first tranche to ppd/daemon/task-board.md, "
                "then select the first unchecked task from that new tranche in the next cycle.",
                "Keep the tranche deterministic, validation-first, and limited to PP&D fixtures, "
                "daemon prompt/preflight helpers, or mocked DevHub planning contracts.",
                "Do not run live crawls, authenticated DevHub sessions, uploads, submissions, "
                "payments, CAPTCHA, MFA, account creation, cancellation, certification, or inspection scheduling.",
            )
        )

    return "\n".join(
        (
            "No eligible unchecked PP&D task was found.",
            "Inspect ppd/daemon/task-board.md and ppd/daemon/progress.json for parser drift, "
            "blocked-task state, or stale progress before proposing repair work.",
            "Keep any repair narrow, fixture-first, and limited to PP&D daemon supervision files.",
        )
    )


__all__ = ["NoEligibleTaskState", "build_no_eligible_task_replanning_guidance"]
