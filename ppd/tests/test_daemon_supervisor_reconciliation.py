import json
import unittest
from pathlib import Path

from ppd.daemon.ppd_daemon import CHECKBOX_RE, parse_tasks, select_task


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "daemon" / "supervisor_reconciliation_blocked_recovery.json"


class DaemonSupervisorReconciliationTests(unittest.TestCase):
    def test_superseded_blocked_task_is_not_selectable(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        board = fixture["boardMarkdown"]
        blocked_title = fixture["supersededBlockedTaskTitle"]
        recovery_title = fixture["acceptedRecoveryTitle"]
        expected_selected_title = fixture["expectedSelectedTitle"]

        tasks = parse_tasks(board)
        titles = [task.title for task in tasks]

        self.assertIn(blocked_title, board)
        self.assertNotIn(blocked_title, titles)
        for line in board.splitlines():
            if blocked_title in line:
                self.assertIsNone(CHECKBOX_RE.match(line))

        recovery = [task for task in tasks if task.title == recovery_title]
        self.assertEqual(len(recovery), 1)
        self.assertEqual(recovery[0].status, "complete")

        selected = select_task(tasks)
        self.assertIsNotNone(selected)
        self.assertEqual(selected.title, expected_selected_title)
        self.assertEqual(selected.status, "needed")


if __name__ == "__main__":
    unittest.main()
