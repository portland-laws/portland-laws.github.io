from __future__ import annotations

import unittest

from ppd.daemon.ppd_daemon import (
    count_unmanaged_generated_status_sections,
    parse_tasks,
    select_task,
    strip_unmanaged_generated_status_sections,
    update_generated_status,
)
from ppd.daemon.ppd_supervisor import (
    builtin_blocked_cascade_replenish_task_board,
    diagnose,
    SupervisorConfig,
)


class ManualTranche20RecoveryTest(unittest.TestCase):
    def test_revisit_blocked_still_prefers_fresh_daemon_repair_task(self) -> None:
        board = "\n".join(
            (
                "- [!] Task checkbox-178: Add a blocked DevHub draft-readiness matrix.",
                "- [ ] Task checkbox-211: Add one daemon-only unittest proving select_task skips blocked work.",
            )
        )

        selected = select_task(parse_tasks(board), revisit_blocked=True)

        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(211, selected.checkbox_id)
        self.assertIn("daemon-only unittest", selected.title)

    def test_protected_blocked_checkbox178_is_not_revisited_without_fresh_repair(self) -> None:
        board = "\n".join(
            (
                "- [!] Task checkbox-178: Add a blocked DevHub draft-readiness matrix.",
                "- [!] Task checkbox-210: Blocked daemon prompt-scope retry.",
            )
        )

        selected = select_task(parse_tasks(board), revisit_blocked=True)

        self.assertIsNone(selected)

    def test_blocked_cascade_appends_numbered_nonduplicate_followup_tranche(self) -> None:
        board = "\n".join(
            (
                "- [!] Task checkbox-178: Blocked domain task.",
                "- [x] Task checkbox-188: Add supervisor blocked-cascade recovery coverage proving a board with only blocked domain/recovery tasks gets deterministic daemon-repair tasks without invoking the LLM repair path.",
                "",
                "## Built-In Blocked Cascade Recovery Tranche",
                "",
                "- [!] Task checkbox-208: Add one daemon-only parser-clean unittest proving a blocked-only board with stale calling_llm for checkbox-178 produces a new unchecked daemon-repair task.",
                "- [!] Task checkbox-209: Add one narrow daemon helper or unittest proving repeated non-JSON LLM responses are persisted as compact diagnostics.",
                "- [!] Task checkbox-210: Add one parser-clean daemon prompt-scope unittest proving that after two syntax_preflight failures for checkbox-178, a retry prompt permits exactly one parser-bearing file.",
            )
        )

        repaired, labels = builtin_blocked_cascade_replenish_task_board(board)
        selected = select_task(parse_tasks(repaired), revisit_blocked=True)

        self.assertEqual(("checkbox-211", "checkbox-212", "checkbox-213", "checkbox-214"), labels)
        self.assertIn("## Built-In Blocked Cascade Recovery Tranche 2", repaired)
        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(211, selected.checkbox_id)
        self.assertNotEqual(178, selected.checkbox_id)

    def test_status_update_removes_unmanaged_generated_status_sections(self) -> None:
        board = "\n".join(
            (
                "- [x] Task checkbox-1: Done.",
                "",
                "## Generated Status",
                "",
                "Last updated: stale",
                "",
                "- Latest target: `stale`",
                "",
                "<!-- ppd-daemon-task-board:start -->",
                "## Generated Status",
                "",
                "Last updated: managed",
                "<!-- ppd-daemon-task-board:end -->",
            )
        )

        self.assertEqual(1, count_unmanaged_generated_status_sections(board))
        cleaned = strip_unmanaged_generated_status_sections(board)
        self.assertEqual(0, count_unmanaged_generated_status_sections(cleaned))
        self.assertIn("<!-- ppd-daemon-task-board:start -->", cleaned)
        self.assertNotIn("Latest target: `stale`", cleaned)

        updated = update_generated_status(
            board,
            latest={"target_task": "Task checkbox-1: Done.", "result": "accepted", "summary": "ok"},
            tasks=parse_tasks(board),
        )
        self.assertEqual(0, count_unmanaged_generated_status_sections(updated))
        self.assertEqual(1, updated.count("## Generated Status"))

    def test_diagnose_uses_blocked_cascade_before_dead_worker_restart(self) -> None:
        # This models the board failure that caused the daemon to restart with
        # --revisit-blocked and retry checkbox-178 instead of adding fresh work.
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            board_path = repo / "ppd" / "daemon" / "task-board.md"
            board_path.parent.mkdir(parents=True)
            board_path.write_text(
                "- [!] Task checkbox-178: Blocked domain task.\n"
                "- [!] Task checkbox-210: Blocked daemon repair task.\n",
                encoding="utf-8",
            )

            decision = diagnose(SupervisorConfig(repo_root=repo, pid_file=Path("ppd/daemon/missing.pid")))

        self.assertEqual("reconcile_blocked_cascade_and_restart", decision.action)
        self.assertTrue(decision.should_restart_daemon)
        self.assertFalse(decision.should_invoke_codex)


if __name__ == "__main__":
    unittest.main()
