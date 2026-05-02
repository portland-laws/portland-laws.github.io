"""Fixture-backed PP&D supervisor self-test helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable, Optional


CHECKBOX_RE = re.compile(r"^(?P\s*-\s+\[)(?P[ xX~!])(?P\]\s+)(?P.+)$")


class SupervisorFixtureError(ValueError):
    """Raised when a supervisor self-test fixture is internally inconsistent."""


class FixtureTask:
    def __init__(self, index: int, title: str, status: str) -> None:
        self.index = index
        self.title = title
        self.status = status

    @property
    def label(self) -> str:
        return f"Task checkbox-{self.index}: {self.title}"


def validate_stale_blocked_retry_fixture(path: Path) -> list[str]:
    """Validate that a stale blocked retry is parked and task selection advances."""

    errors: list[str] = []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"missing supervisor self-test fixture: {path.as_posix()}"]
    except json.JSONDecodeError as exc:
        return [f"supervisor self-test fixture is invalid JSON: {exc}"]

    if not isinstance(data, dict):
        return ["supervisor self-test fixture must contain a JSON object"]

    stale_retry = data.get("stale_retry")
    if not isinstance(stale_retry, dict):
        errors.append("fixture stale_retry must be an object")
        stale_retry = {}

    required_true_flags = (
        "size_guard_passed",
        "malformed_comparison_diagnostic_passed",
        "parked_after_diagnostics",
    )
    for key in required_true_flags:
        if stale_retry.get(key) is not True:
            errors.append(f"stale_retry.{key} must be true")

    if stale_retry.get("previous_status") != "blocked":
        errors.append("stale_retry.previous_status must be blocked")
    if stale_retry.get("retry_state") != "stale":
        errors.append("stale_retry.retry_state must be stale")
    if stale_retry.get("selectable_checkbox_expected") is not False:
        errors.append("stale_retry.selectable_checkbox_expected must be false")
    if "size_guard" not in str(stale_retry.get("parked_reason", "")):
        errors.append("stale_retry.parked_reason must mention the size guard")
    if "malformed_comparison" not in str(stale_retry.get("parked_reason", "")):
        errors.append("stale_retry.parked_reason must mention the malformed-comparison diagnostic")

    board_lines = data.get("fixture_task_board_lines")
    if not isinstance(board_lines, list) or not all(isinstance(line, str) for line in board_lines):
        errors.append("fixture_task_board_lines must be a list of strings")
        board_lines = []
    board = "\n".join(board_lines) + "\n"
    tasks = _parse_tasks(board)

    expected = data.get("expected")
    if not isinstance(expected, dict):
        errors.append("fixture expected must be an object")
        expected = {}

    blocked_title = str(expected.get("blocked_task_title", ""))
    matching_blocked = [task for task in tasks if task.title == blocked_title]
    if not matching_blocked:
        errors.append("fixture board must include the stale retry as a blocked checkbox")
    elif matching_blocked[0].status != "blocked":
        errors.append("stale retry checkbox must be blocked")

    parked_lines = [line for line in board_lines if "Parked stale retry:" in line]
    if not parked_lines:
        errors.append("fixture must include a parked stale retry note")
    for line in parked_lines:
        if CHECKBOX_RE.match(line):
            errors.append("parked stale retry note must not be in selectable checkbox form")

    selected = _select_task(tasks, revisit_blocked=bool(expected.get("revisit_blocked", False)))
    if selected is None:
        errors.append("fixture unexpectedly produced no eligible task")
    else:
        expected_label = str(expected.get("next_selected_label", ""))
        if selected.label != expected_label:
            errors.append(f"expected selected task {expected_label!r}, got {selected.label!r}")
        if selected.status not in {"needed", "in-progress"}:
            errors.append("selected task must be a needed or in-progress task")
        if blocked_title and selected.title == blocked_title:
            errors.append("stale blocked retry was selected instead of being parked")

    if expected.get("no_eligible_tasks") is not False:
        errors.append("expected.no_eligible_tasks must be false")

    return errors


def _parse_tasks(markdown: str) -> list[FixtureTask]:
    tasks: list[FixtureTask] = []
    for line in markdown.splitlines():
        match = CHECKBOX_RE.match(line)
        if not match:
            continue
        mark = match.group("mark")
        status = "needed"
        if mark.lower() == "x":
            status = "complete"
        elif mark == "~":
            status = "in-progress"
        elif mark == "!":
            status = "blocked"
        tasks.append(FixtureTask(index=len(tasks) + 1, title=match.group("title").strip(), status=status))
    return tasks


def _select_task(tasks: Iterable[FixtureTask], *, revisit_blocked: bool = False) -> Optional[FixtureTask]:
    task_list = list(tasks)
    for task in task_list:
        if task.status in {"needed", "in-progress"}:
            return task
    if revisit_blocked:
        for task in task_list:
            if task.status == "blocked":
                return task
    return None
