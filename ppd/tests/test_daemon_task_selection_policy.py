from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path

from ppd.daemon.task_selection_policy import (
    AcceptedRepairRecord,
    TaskSelectionRecord,
    accepted_repairs_from_fixture,
    select_next_task,
    skipped_blocked_task_ids,
    tasks_from_fixture,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "daemon" / "task_selection_blocked_until_repair_or_reopen.json"


class DaemonTaskSelectionPolicyTest(unittest.TestCase):
    def load_fixture(self) -> dict[str, object]:
        with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual(data["schema_version"], 1)
        return data

    def test_blocked_tasks_are_skipped_when_no_new_repair_was_accepted(self) -> None:
        tasks = (
            TaskSelectionRecord(
                task_id="checkbox-178",
                title="blocked domain work",
                status="blocked",
                kind="domain",
                created_order=178,
                blocked_at="2026-05-03T08:00:00Z",
            ),
            TaskSelectionRecord(
                task_id="checkbox-190",
                title="new daemon repair coverage",
                status="open",
                kind="daemon_repair",
                created_order=190,
            ),
        )
        repairs = (
            AcceptedRepairRecord(
                task_id="checkbox-188",
                kind="daemon_repair",
                accepted_at="2026-05-03T07:59:00Z",
            ),
        )

        selected = select_next_task(tasks, repairs)

        self.assertIsNotNone(selected)
        self.assertEqual(selected.task_id, "checkbox-190")
        self.assertEqual(skipped_blocked_task_ids(tasks, repairs), ("checkbox-178",))

    def test_fixture_prefers_newest_non_blocked_repair_before_blocked_work(self) -> None:
        data = self.load_fixture()
        tasks = tasks_from_fixture(data)
        repairs = accepted_repairs_from_fixture(data)

        selected = select_next_task(tasks, repairs)

        self.assertIsNotNone(selected)
        self.assertEqual(selected.task_id, "checkbox-191")
        self.assertEqual(skipped_blocked_task_ids(tasks, repairs), ())

    def test_blocked_task_can_be_selected_after_new_repair_acceptance_when_no_open_repair_remains(self) -> None:
        tasks = (
            TaskSelectionRecord(
                task_id="checkbox-178",
                title="blocked domain work",
                status="blocked",
                kind="domain",
                created_order=178,
                blocked_at="2026-05-03T08:00:00Z",
            ),
        )
        repairs = (
            AcceptedRepairRecord(
                task_id="checkbox-190",
                kind="daemon_repair",
                accepted_at="2026-05-03T08:30:00Z",
            ),
        )

        selected = select_next_task(tasks, repairs)

        self.assertIsNotNone(selected)
        self.assertEqual(selected.task_id, "checkbox-178")
        self.assertEqual(skipped_blocked_task_ids(tasks, repairs), ())

    def test_human_reopen_makes_specific_blocked_task_selectable(self) -> None:
        data = self.load_fixture()
        tasks = tuple(task for task in tasks_from_fixture(data) if task.task_id == "checkbox-182")
        self.assertEqual(len(tasks), 1)
        reopened_task = replace(tasks[0], reopened_by_human_at="2026-05-03T08:20:00Z")

        selected = select_next_task((reopened_task,), ())

        self.assertIsNotNone(selected)
        self.assertEqual(selected.task_id, "checkbox-182")
        self.assertEqual(skipped_blocked_task_ids((reopened_task,), ()), ())


if __name__ == "__main__":
    unittest.main()
