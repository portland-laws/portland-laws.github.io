from __future__ import annotations

import unittest

from ppd.daemon.ppd_supervisor import builtin_replenish_goal_tasks


class SupervisorAdaptiveSlicePolicyTest(unittest.TestCase):
    def test_completed_board_level_recovery_tranche_enables_broader_nonduplicate_slices(self) -> None:
        board = "\n".join(
            [
                "- [x] Task checkbox-1: Bootstrap PP&D work.",
                "",
                "## Built-In Goal Replenishment Tranche",
                "",
                "- [x] Task checkbox-2: Add a fixture-only processor archive integration manifest that maps PP&D public source URLs.",
                "- [x] Task checkbox-3: Add validation for the processor archive integration manifest.",
                "- [x] Task checkbox-4: Add a mocked Playwright draft-fill plan fixture for one PP&D form.",
                "- [x] Task checkbox-5: Add validation for the Playwright draft-fill plan fixture.",
                "- [x] Task checkbox-6: Add a fixture-only formal-logic guardrail bundle.",
                "- [x] Task checkbox-7: Add validation for formal-logic guardrail bundles.",
            ]
        )

        replenished, labels = builtin_replenish_goal_tasks(board, rows=[])

        self.assertEqual(("checkbox-8", "checkbox-9", "checkbox-10", "checkbox-11"), labels)
        self.assertIn("## Built-In Goal Replenishment Tranche 2", replenished)
        self.assertIn("Slice policy: `broad_integrated_after_green_streak`", replenished)
        self.assertIn("end-to-end fixture-only handoff scenario plus focused validation", replenished)
        self.assertIn("user gap-resolution scenario plus focused validation", replenished)
        self.assertIn("supervisor adaptive-slice regression coverage", replenished)
        self.assertIn("offline Playwright draft transcript fixture plus focused validation", replenished)
        self.assertNotIn("Add validation for the processor archive integration manifest proving", replenished)

    def test_incomplete_recovery_tranche_does_not_append_more_tasks(self) -> None:
        board = "\n".join(
            [
                "- [x] Task checkbox-1: Bootstrap PP&D work.",
                "",
                "## Built-In Goal Replenishment Tranche",
                "",
                "- [x] Task checkbox-2: Completed recovery slice.",
                "- [ ] Task checkbox-3: Remaining recovery slice.",
            ]
        )

        replenished, labels = builtin_replenish_goal_tasks(board, rows=[])

        self.assertEqual((), labels)
        self.assertEqual(board, replenished)

    def test_later_completed_tranches_rotate_to_new_goal_titles(self) -> None:
        board = "\n".join(
            [
                "- [x] Task checkbox-1: Bootstrap PP&D work.",
                "",
                "## Built-In Goal Replenishment Tranche",
                "- [x] Task checkbox-2: Initial completed recovery slice.",
                "",
                "## Built-In Goal Replenishment Tranche 2",
                "- [x] Task checkbox-3: Add an end-to-end fixture-only handoff scenario plus focused validation.",
                "- [x] Task checkbox-4: Add a fixture-only user gap-resolution scenario plus focused validation.",
                "- [x] Task checkbox-5: Add supervisor adaptive-slice regression coverage.",
                "- [x] Task checkbox-6: Add an offline Playwright draft transcript fixture plus focused validation.",
            ]
        )

        replenished, labels = builtin_replenish_goal_tasks(board, rows=[])

        self.assertEqual(("checkbox-7", "checkbox-8", "checkbox-9", "checkbox-10"), labels)
        self.assertIn("## Built-In Goal Replenishment Tranche 3", replenished)
        self.assertIn("source-change impact scenario plus focused validation", replenished)
        self.assertIn("agent work-order scenario plus focused validation", replenished)
        self.assertIn("parse-failure recovery coverage", replenished)
        self.assertIn("permit-process comparison scenario plus focused validation", replenished)
        self.assertNotIn("offline Playwright draft transcript fixture plus focused validation proving future agents", replenished)


if __name__ == "__main__":
    unittest.main()
