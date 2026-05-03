from __future__ import annotations

import unittest

from ppd.daemon.ppd_daemon import parse_tasks


class DaemonTaskIdentityTest(unittest.TestCase):
    def test_task_label_uses_literal_checkbox_id_from_board_title(self) -> None:
        board = "\n".join(
            [
                "- [x] Task checkbox-01 through checkbox-171: Completed prior work.",
                "- [~] Task checkbox-176: Add public source lineage rollup.",
            ]
        )

        tasks = parse_tasks(board)

        self.assertEqual("Task checkbox-176: Add public source lineage rollup.", tasks[1].label)
        self.assertEqual(2, tasks[1].index)
        self.assertEqual(176, tasks[1].checkbox_id)


if __name__ == "__main__":
    unittest.main()
