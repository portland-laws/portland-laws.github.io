"""Fixture-only recovery policy for repeated non-JSON daemon proposals."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParseFailureAttempt:
    task_label: str
    failure_kind: str
    changed_files: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ParseFailureRecoveryDecision:
    action: str
    reason: str
    should_retry_task: bool
    should_park_task: bool
    should_mark_superseded: bool


def count_recent_non_json_failures(
    attempts: tuple[ParseFailureAttempt, ...],
    task_label: str,
) -> int:
    """Count the newest contiguous non-JSON failures for one task."""

    count = 0
    for attempt in reversed(attempts):
        if attempt.task_label != task_label:
            if count:
                break
            continue
        if attempt.failure_kind != "parse":
            break
        if attempt.changed_files:
            break
        count += 1
    return count


def decide_parse_failure_recovery(
    attempts: tuple[ParseFailureAttempt, ...],
    *,
    task_label: str,
    completed_task_labels: frozenset[str],
    manually_satisfied_task_labels: frozenset[str],
    threshold: int = 2,
) -> ParseFailureRecoveryDecision:
    """Return how the daemon/supervisor should handle repeated parse failures.

    Completed or manually satisfied tasks should not be retried after stale
    non-JSON LLM responses. Active unfinished tasks get one retry window, then
    are parked so a daemon-programming recovery task can be selected instead.
    """

    if task_label in completed_task_labels:
        return ParseFailureRecoveryDecision(
            action="supersede_completed_task_parse_failures",
            reason="target task is already complete on the task board",
            should_retry_task=False,
            should_park_task=False,
            should_mark_superseded=True,
        )
    if task_label in manually_satisfied_task_labels:
        return ParseFailureRecoveryDecision(
            action="supersede_manually_satisfied_task_parse_failures",
            reason="target task was manually satisfied by validated recovery work",
            should_retry_task=False,
            should_park_task=False,
            should_mark_superseded=True,
        )

    count = count_recent_non_json_failures(attempts, task_label)
    if count >= threshold:
        return ParseFailureRecoveryDecision(
            action="park_repeated_parse_failure_task",
            reason=f"{count} contiguous non-JSON LLM responses without changed files",
            should_retry_task=False,
            should_park_task=True,
            should_mark_superseded=False,
        )

    return ParseFailureRecoveryDecision(
        action="retry_with_json_only_prompt",
        reason=f"{count} recent non-JSON response(s), below threshold {threshold}",
        should_retry_task=True,
        should_park_task=False,
        should_mark_superseded=False,
    )
