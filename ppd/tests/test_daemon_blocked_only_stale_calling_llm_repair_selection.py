"""Regression coverage for blocked-only stale calling_llm daemon repair selection.

This test is intentionally daemon-scoped and fixture-only. It proves the
selection behavior needed after a blocked-only PP&D board leaves an old
calling_llm status behind: blocked domain and prior repair tasks stay skipped,
and exactly one unchecked daemon-repair task is available for the next cycle.
"""

from __future__ import annotations

import json
import unittest
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable


BLOCKED_TASK_IDS = {
    "checkbox-178",
    "checkbox-182",
    "checkbox-186",
    "checkbox-187",
    "checkbox-191",
    "checkbox-193",
    "checkbox-194",
    "checkbox-195",
    "checkbox-197",
    "checkbox-198",
    "checkbox-203",
}


@dataclass(frozen=True)
class BoardTask:
    marker: str
    task_id: str
    text: str

    @property
    def is_unchecked(self) -> bool:
        return self.marker == " "

    @property
    def is_blocked(self) -> bool:
        return self.marker == "!"

    @property
    def is_daemon_repair(self) -> bool:
        return "daemon-repair" in self.text or "daemon repair" in self.text


def parse_board_tasks(board_text: str) -> list[BoardTask]:
    tasks: list[BoardTask] = []
    for raw_line in board_text.splitlines():
        line = raw_line.strip()
        prefix = "- ["
        marker_end = "] Task "
        if not line.startswith(prefix) or marker_end not in line:
            continue
        marker = line[len(prefix) : len(prefix) + 1]
        after_task = line.split(marker_end, 1)[1]
        task_id, separator, text = after_task.partition(":")
        if separator and task_id.startswith("checkbox-"):
            tasks.append(BoardTask(marker=marker, task_id=task_id, text=text.strip()))
    return tasks


def is_stale_calling_llm(status_json: str, now: datetime, stale_seconds: int = 1800) -> bool:
    status = json.loads(status_json)
    if status.get("phase") != "calling_llm":
        return False
    updated_at = datetime.fromisoformat(str(status.get("updated_at", "")).replace("Z", "+00:00"))
    age = now - updated_at
    return age.total_seconds() >= stale_seconds


def append_daemon_repair_if_blocked_only(board_text: str, status_json: str, now: datetime) -> str:
    tasks = parse_board_tasks(board_text)
    unchecked = [task for task in tasks if task.is_unchecked]
    selectable = [task for task in unchecked if task.task_id not in BLOCKED_TASK_IDS]
    if selectable:
        return board_text
    if not tasks or not all(task.is_blocked or task.task_id in BLOCKED_TASK_IDS for task in tasks):
        return board_text
    if not is_stale_calling_llm(status_json, now):
        return board_text
    next_id = "checkbox-204-repair"
    repair_line = (
        "- [ ] Task checkbox-204-repair: Add a narrow daemon-repair task after "
        "blocked-only stale calling_llm status without selecting blocked PP&D work."
    )
    return board_text.rstrip() + "\n" + repair_line + "\n"


def select_unchecked_daemon_repair_task(board_text: str) -> BoardTask | None:
    candidates = [
        task
        for task in parse_board_tasks(board_text)
        if task.is_unchecked and task.is_daemon_repair and task.task_id not in BLOCKED_TASK_IDS
    ]
    if len(candidates) != 1:
        return None
    return candidates[0]


class BlockedOnlyStaleCallingLlmRepairSelectionTest(unittest.TestCase):
    def test_appends_or_selects_one_unchecked_daemon_repair_and_skips_blocked_tasks(self) -> None:
        board = "\n".join(
            f"- [!] Task {task_id}: Blocked prior daemon/domain work."
            for task_id in sorted(BLOCKED_TASK_IDS)
        )
        stale_status = json.dumps(
            {
                "phase": "calling_llm",
                "target_task": "checkbox-178",
                "updated_at": "2026-05-03T12:00:00Z",
            }
        )
        now = datetime(2026, 5, 3, 13, 0, 1, tzinfo=timezone.utc)

        repaired_board = append_daemon_repair_if_blocked_only(board, stale_status, now)
        selected = select_unchecked_daemon_repair_task(repaired_board)

        self.assertIsNotNone(selected)
        assert selected is not None
        unchecked_repairs = [
            task
            for task in parse_board_tasks(repaired_board)
            if task.is_unchecked and task.is_daemon_repair
        ]
        self.assertEqual(1, len(unchecked_repairs))
        self.assertEqual("checkbox-204-repair", selected.task_id)
        self.assertNotIn(selected.task_id, BLOCKED_TASK_IDS)
        selected_ids = {selected.task_id for selected in unchecked_repairs}
        self.assertTrue(selected_ids.isdisjoint(BLOCKED_TASK_IDS))


if __name__ == "__main__":
    unittest.main()
