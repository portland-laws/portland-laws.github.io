"""Supervisor policy for resuming a blocked PP&D daemon task.

This module is intentionally small and fixture-friendly. It does not implement PP&D
crawl behavior; it only summarizes when the supervisor may hand a blocked task
back to a worker after recovery guardrails have been accepted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence


RECOVERY_CHECKBOXES = frozenset({112, 113, 114, 115, 116})
SYNTAX_FAILURE_KINDS = frozenset({"syntax_preflight", "py_compile", "ts_parse"})


@dataclass(frozen=True)
class ResumePolicyDecision:
    """A deterministic recommendation for the PP&D supervisor."""

    may_resume: bool
    reason: str
    target_task: str
    required_guardrails: tuple[str, ...]
    allowed_file_shapes: tuple[str, ...]


def completed_recovery_checkboxes(progress: Mapping[str, object]) -> frozenset[int]:
    """Return recovery checkbox numbers found in accepted recent progress."""

    completed: set[int] = set()
    recent_results = progress.get("recent_results", [])
    if not isinstance(recent_results, Sequence):
        return frozenset()

    for result in recent_results:
        if not isinstance(result, Mapping):
            continue
        if result.get("validation_passed") is not True:
            continue
        target = str(result.get("target_task", ""))
        for checkbox in RECOVERY_CHECKBOXES:
            token = f"checkbox-{checkbox}"
            if token in target:
                completed.add(checkbox)
    return frozenset(completed)


def recent_syntax_failure_count(recent_results: Iterable[Mapping[str, object]]) -> int:
    """Count recent parser/compile failures without inspecting patch contents."""

    count = 0
    for result in recent_results:
        failure_kind = str(result.get("failure_kind", ""))
        errors = "\n".join(str(error) for error in result.get("errors", []) if error)
        if failure_kind in SYNTAX_FAILURE_KINDS:
            count += 1
        elif "SyntaxError" in errors or "py_compile" in errors or "TS1005" in errors or "TS1109" in errors or "TS1128" in errors:
            count += 1
    return count


def recommend_resume_policy(runtime_status: Mapping[str, object], progress: Mapping[str, object]) -> ResumePolicyDecision:
    """Recommend whether the supervisor should resume the active blocked task.

    The recommendation only applies when there is exactly one blocked task, no
    selectable task remains, and recovery checkboxes 112 through 116 have already
    passed. The next worker still receives a constrained domain task; this module
    only defines the supervisor handoff conditions.
    """

    task_counts = progress.get("task_counts", {})
    if not isinstance(task_counts, Mapping):
        task_counts = {}

    blocked = int(task_counts.get("blocked", 0) or 0)
    needed = int(task_counts.get("needed", 0) or 0)
    in_progress = int(task_counts.get("in_progress", 0) or 0)
    target_task = str(runtime_status.get("active_target_task", ""))

    guardrails = (
        "Do not perform network access or write crawl output.",
        "Before returning JSON, mentally py_compile every changed Python file and keep edits syntax-small.",
        "Use exactly one syntactically valid Python source file, or one small JSON fixture plus one syntactically valid Python unittest file.",
        "Do not add broad contracts, live crawl code, authenticated DevHub automation, private session files, or raw crawl artifacts.",
    )
    shapes = (
        "one_python_source_file",
        "one_json_fixture_plus_one_python_unittest",
    )

    if blocked != 1 or needed != 0 or in_progress != 0:
        return ResumePolicyDecision(
            may_resume=False,
            reason="resume policy only applies when exactly one blocked task remains and no selectable work is active",
            target_task=target_task,
            required_guardrails=guardrails,
            allowed_file_shapes=shapes,
        )

    completed = completed_recovery_checkboxes(progress)
    missing = sorted(RECOVERY_CHECKBOXES.difference(completed))
    if missing:
        return ResumePolicyDecision(
            may_resume=False,
            reason="missing recovery checkbox guardrails: " + ", ".join(f"checkbox-{item}" for item in missing),
            target_task=target_task,
            required_guardrails=guardrails,
            allowed_file_shapes=shapes,
        )

    return ResumePolicyDecision(
        may_resume=True,
        reason="all recovery guardrails passed; resume the blocked task once with strict syntax-first file-shape limits",
        target_task=target_task,
        required_guardrails=guardrails,
        allowed_file_shapes=shapes,
    )
