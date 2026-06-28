from __future__ import annotations

import unittest

from ppd.daemon.ppd_daemon import parse_tasks, select_task
from ppd.daemon.ppd_supervisor import builtin_blocked_cascade_replenish_task_board


class GeneratedBlockedCascadeRecoveryTest(unittest.TestCase):
    def test_checkbox_215_fresh_repair_selected_while_blocked_ppd_work_stays_parked(self) -> None:
        board = "\n".join(
            (
                "- [!] Task checkbox-178: Blocked DevHub draft-readiness domain task.",
                "- [!] Task checkbox-210: Blocked daemon prompt-scope task.",
                "- [ ] Task checkbox-215: Add generated blocked-cascade daemon-repair coverage for tranche 1 item 1 proving blocked PP&D work stays parked until a fresh daemon repair task validates.",
            )
        )

        tasks = parse_tasks(board)
        selected = select_task(tasks, revisit_blocked=True)

        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(215, selected.checkbox_id)
        self.assertEqual("blocked", tasks[0].status)
        self.assertEqual("blocked", tasks[1].status)

    def test_checkbox_216_next_repair_selected_after_first_repair_validates(self) -> None:
        board = "\n".join(
            (
                "- [!] Task checkbox-178: Blocked DevHub draft-readiness domain task.",
                "- [x] Task checkbox-215: Add generated blocked-cascade daemon-repair coverage for tranche 1 item 1 proving blocked PP&D work stays parked until a fresh daemon repair task validates.",
                "- [ ] Task checkbox-216: Add generated blocked-cascade daemon-repair coverage for tranche 1 item 2 proving blocked PP&D work stays parked until a fresh daemon repair task validates.",
            )
        )

        tasks = parse_tasks(board)
        selected = select_task(tasks, revisit_blocked=True)

        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(216, selected.checkbox_id)
        self.assertEqual("blocked", tasks[0].status)

    def test_checkbox_217_protected_blocked_ppd_work_is_not_revisited_after_repairs_validate(self) -> None:
        board = "\n".join(
            (
                "- [!] Task checkbox-178: Blocked DevHub draft-readiness domain task.",
                "- [!] Task checkbox-209: Blocked repeated non-JSON diagnostics task.",
                "- [x] Task checkbox-215: Completed generated daemon repair.",
                "- [x] Task checkbox-216: Completed generated daemon repair.",
                "- [x] Task checkbox-217: Completed generated daemon repair.",
                "- [x] Task checkbox-218: Completed generated daemon repair.",
            )
        )

        selected = select_task(parse_tasks(board), revisit_blocked=True)

        self.assertIsNone(selected)

    def test_checkbox_218_followup_blocked_cascade_tranche_is_nonduplicate(self) -> None:
        board = "\n".join(
            (
                "- [!] Task checkbox-178: Blocked DevHub draft-readiness domain task.",
                "- [x] Task checkbox-188: Add supervisor blocked-cascade recovery coverage proving a board with only blocked domain/recovery tasks gets deterministic daemon-repair tasks without invoking the LLM repair path.",
                "- [x] Task checkbox-189: Add daemon blocked-task prompt-budget fixture coverage proving repeated llm_router exits summarize the target, compact errors, and next daemon-repair hint without retrying blocked domain work.",
                "- [x] Task checkbox-190: Add daemon task-selection coverage proving blocked tasks are skipped until a new non-blocked repair task is accepted or a human explicitly reopens the blocked task.",
                "- [!] Task checkbox-191: Add supervisor recovery-note compaction coverage proving repeated repair notes are summarized before future prompt construction so task-board context stays bounded.",
                "- [x] Task checkbox-211: Add one daemon-only unittest proving `select_task` does not choose blocked checkbox-178 when a fresh unchecked daemon-repair task exists, even if `revisit_blocked` is enabled.",
                "- [x] Task checkbox-212: Add one supervisor regression proving a blocked-only PP&D board appends a fresh daemon-repair tranche before restarting a worker with blocked revisits enabled.",
                "- [x] Task checkbox-213: Add one parser-clean prompt-scope unittest proving checkbox-178 retries stay blocked after three syntax_preflight failures until a daemon-repair task passes validation.",
                "- [x] Task checkbox-214: Add one task-board accounting unittest proving duplicate generated-status sections outside the managed marker are detected before daemon task selection.",
                "",
                "## Built-In Blocked Cascade Recovery Tranche",
                "",
                "- [!] Task checkbox-215: Add generated blocked-cascade daemon-repair coverage for tranche 1 item 1 proving blocked PP&D work stays parked until a fresh daemon repair task validates.",
                "- [!] Task checkbox-216: Add generated blocked-cascade daemon-repair coverage for tranche 1 item 2 proving blocked PP&D work stays parked until a fresh daemon repair task validates.",
                "- [!] Task checkbox-217: Add generated blocked-cascade daemon-repair coverage for tranche 1 item 3 proving blocked PP&D work stays parked until a fresh daemon repair task validates.",
                "- [!] Task checkbox-218: Add generated blocked-cascade daemon-repair coverage for tranche 1 item 4 proving blocked PP&D work stays parked until a fresh daemon repair task validates.",
            )
        )

        repaired, labels = builtin_blocked_cascade_replenish_task_board(board)
        selected = select_task(parse_tasks(repaired), revisit_blocked=True)

        self.assertEqual(("checkbox-219", "checkbox-220", "checkbox-221", "checkbox-222"), labels)
        self.assertIn("## Built-In Blocked Cascade Recovery Tranche 2", repaired)
        self.assertIn("tranche 2 item 1", repaired)
        self.assertNotIn("- [ ] Task checkbox-219: Add one daemon-only unittest proving `select_task`", repaired)
        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(219, selected.checkbox_id)


if __name__ == "__main__":
    unittest.main()
