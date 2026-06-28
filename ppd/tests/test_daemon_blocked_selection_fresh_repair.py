"""Daemon-only regression coverage for blocked PP&D task selection.

This test intentionally uses plain string parsing instead of custom regex syntax.
It models the task-board markers the PP&D daemon consumes and proves blocked
checkboxes from the stalled recovery tranche are skipped when a fresh unchecked
daemon-repair task is present.
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass


BLOCKED_RECOVERY_IDS = (
    "checkbox-178",
    "checkbox-182",
    "checkbox-186",
    "checkbox-187",
    "checkbox-191",
    "checkbox-193",
    "checkbox-194",
    "checkbox-195",
    "checkbox-197",
)


@dataclass(frozen=True)
class ParsedBoardTask:
    task_id: str
    marker: str
    description: str
    section: str

    @property
    def is_blocked(self) -> bool:
        return self.marker == "!"

    @property
    def is_unchecked(self) -> bool:
        return self.marker == " "

    @property
    def is_daemon_repair(self) -> bool:
        text = f"{self.section} {self.description}".lower()
        return "daemon" in text and "repair" in text


def parse_board_tasks(board_text: str) -> list[ParsedBoardTask]:
    """Parse markdown task lines using ordinary string operations only."""

    tasks: list[ParsedBoardTask] = []
    current_section = ""
    for raw_line in board_text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current_section = line.removeprefix("## ").strip()
            continue

        if not line.startswith("- ["):
            continue
        if "] Task " not in line:
            continue

        marker = line[3:4]
        task_text = line.split("] Task ", 1)[1]
        if ":" not in task_text:
            continue

        task_id, description = task_text.split(":", 1)
        tasks.append(
            ParsedBoardTask(
                task_id=task_id.strip(),
                marker=marker,
                description=description.strip(),
                section=current_section,
            )
        )
    return tasks


def select_fresh_daemon_repair_task(board_text: str) -> ParsedBoardTask | None:
    """Return the newest unchecked daemon-repair task while skipping blocked tasks."""

    tasks = parse_board_tasks(board_text)
    for task in reversed(tasks):
        if task.is_unchecked and task.is_daemon_repair and not task.is_blocked:
            return task
    return None


class DaemonBlockedSelectionFreshRepairTest(unittest.TestCase):
    def test_blocked_recovery_tasks_are_skipped_for_fresh_daemon_repair(self) -> None:
        board_text = """
# PP&D Daemon Task Board

## Blocked Work
- [!] Task checkbox-178: Add a fixture-only DevHub draft-readiness decision matrix.
- [!] Task checkbox-182: Add daemon diagnostics coverage for repeated non-JSON responses.
- [!] Task checkbox-186: Add daemon retry-scope coverage after two syntax_preflight failures.
- [!] Task checkbox-187: Add blocked-task selection coverage for earlier blocked tasks.
- [!] Task checkbox-191: Add supervisor recovery-note compaction coverage.
- [!] Task checkbox-193: Add one focused daemon diagnostic unittest.
- [!] Task checkbox-194: Add one parser-clean supervisor recovery-note compaction helper.

## Blocked Cascade Recovery Tranche 15
- [!] Task checkbox-195: Replace or add only ppd/daemon/SUPERVISOR_REPAIR_GUIDE.md.
- [!] Task checkbox-197: Add one daemon-only retry-scope helper or unittest.

## Blocked Cascade Recovery Tranche 16
- [ ] Task checkbox-201: Add a fresh daemon-repair selector unittest that is safe to run alone.
"""

        tasks = parse_board_tasks(board_text)
        blocked_ids = {task.task_id for task in tasks if task.is_blocked}
        selected = select_fresh_daemon_repair_task(board_text)

        self.assertEqual(set(BLOCKED_RECOVERY_IDS), blocked_ids)
        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual("checkbox-201", selected.task_id)
        self.assertTrue(selected.is_daemon_repair)
        self.assertTrue(selected.is_unchecked)
        self.assertNotIn(selected.task_id, blocked_ids)


if __name__ == "__main__":
    unittest.main()
