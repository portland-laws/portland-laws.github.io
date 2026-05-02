from __future__ import annotations

import unittest

from ppd.daemon.no_eligible_replanning import (
    NoEligibleTaskState,
    build_no_eligible_task_replanning_guidance,
)


class NoEligibleReplanningGuidanceTest(unittest.TestCase):
    def test_completed_board_with_expanded_goals_appends_fixture_first_tranche(self) -> None:
        guidance = build_no_eligible_task_replanning_guidance(
            NoEligibleTaskState(complete=75, task_count=75, expanded_goals_present=True)
        )

        self.assertIn("complete == task_count", guidance)
        self.assertIn("expanded goals", guidance)
        self.assertIn("Do not invoke repeated repair", guidance)
        self.assertIn("Append the next narrow fixture-first tranche", guidance)
        self.assertIn("ppd/daemon/task-board.md", guidance)
        self.assertIn("Do not run live crawls", guidance)
        self.assertIn("authenticated DevHub sessions", guidance)

    def test_incomplete_or_unexpanded_board_uses_diagnostic_guidance(self) -> None:
        guidance = build_no_eligible_task_replanning_guidance(
            NoEligibleTaskState(complete=74, task_count=75, expanded_goals_present=True)
        )

        self.assertIn("Inspect ppd/daemon/task-board.md", guidance)
        self.assertIn("parser drift", guidance)
        self.assertNotIn("Append the next narrow fixture-first tranche", guidance)


if __name__ == "__main__":
    unittest.main()
