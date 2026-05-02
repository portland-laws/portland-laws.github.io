"""Tests for daemon task-selection recovery validation."""

from __future__ import annotations

import unittest

from ppd.daemon.task_selection_validation import (
    TaskSelectionFixture,
    TaskState,
    eligible_task_ids,
    tasks_requiring_supersession_reconciliation,
    validate_blocked_superseded_domain_task_selection,
    validate_blocked_syntax_preflight_selection,
)


class DaemonTaskSelectionValidationTest(unittest.TestCase):
    def test_blocked_syntax_preflight_task_is_not_reselected(self) -> None:
        self.assertEqual(validate_blocked_syntax_preflight_selection(), [])

    def test_unchecked_supervisor_recovery_task_remains_available(self) -> None:
        tasks = (
            TaskSelectionFixture(
                checkbox_id="checkbox-112",
                title="Blocked syntax-preflight retry",
                state=TaskState.BLOCKED,
                failure_kind="syntax_preflight",
            ),
            TaskSelectionFixture(
                checkbox_id="checkbox-117",
                title="Unchecked supervisor recovery validation",
                state=TaskState.UNCHECKED,
                recovery_kind="supervisor_recovery",
            ),
        )

        self.assertEqual(eligible_task_ids(tasks), ("checkbox-117",))

    def test_blocked_domain_task_with_unrecorded_supersession_is_not_selected(self) -> None:
        self.assertEqual(validate_blocked_superseded_domain_task_selection(), [])

    def test_supersession_reconciliation_detects_only_unrecorded_domain_tasks(self) -> None:
        tasks = (
            TaskSelectionFixture(
                checkbox_id="checkbox-108",
                title="Blocked domain task with accepted supersession evidence",
                state=TaskState.BLOCKED,
                task_kind="domain",
                accepted_supersession_evidence=True,
                task_board_supersession_note_appended=False,
            ),
            TaskSelectionFixture(
                checkbox_id="checkbox-130",
                title="Blocked domain task already reconciled on the board",
                state=TaskState.BLOCKED,
                task_kind="domain",
                accepted_supersession_evidence=True,
                task_board_supersession_note_appended=True,
            ),
            TaskSelectionFixture(
                checkbox_id="checkbox-132",
                title="Unchecked daemon reconciliation task",
                state=TaskState.UNCHECKED,
                task_kind="daemon",
                recovery_kind="task_board_supersession_reconciliation",
            ),
        )

        self.assertEqual(tasks_requiring_supersession_reconciliation(tasks), ("checkbox-108",))
        self.assertEqual(eligible_task_ids(tasks), ("checkbox-132",))


if __name__ == "__main__":
    unittest.main()
