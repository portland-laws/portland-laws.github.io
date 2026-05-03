from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ppd.daemon.ppd_daemon import atomic_write_json
from ppd.daemon.ppd_supervisor import (
    SupervisorConfig,
    append_jsonl,
    builtin_dead_worker_task_board,
    builtin_repair_task_board,
    diagnose,
    read_supervisor_result_rows,
)


class SupervisorStaleStatusReplanningTest(unittest.TestCase):
    def test_completed_board_with_no_eligible_status_plans_next_tasks(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            board = repo / "ppd" / "daemon" / "task-board.md"
            board.parent.mkdir(parents=True)
            board.write_text("- [x] Task checkbox-1: Done.\n", encoding="utf-8")
            atomic_write_json(
                repo / "ppd" / "daemon" / "status.json",
                {
                    "updated_at": "2026-05-02T00:00:00Z",
                    "active_state": "no_eligible_tasks",
                    "state": "no_eligible_tasks",
                },
            )
            atomic_write_json(
                repo / "ppd" / "daemon" / "progress.json",
                {"latest": {"failure_kind": "no_eligible_tasks"}},
            )

            decision = diagnose(SupervisorConfig(repo_root=repo))

        self.assertEqual("plan_next_tasks", decision.action)
        self.assertTrue(decision.should_invoke_codex)

    def test_completed_board_with_stale_calling_llm_status_plans_next_tasks_first(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            board = repo / "ppd" / "daemon" / "task-board.md"
            board.parent.mkdir(parents=True)
            board.write_text("- [x] Task checkbox-1: Done.\n", encoding="utf-8")
            atomic_write_json(
                repo / "ppd" / "daemon" / "status.json",
                {
                    "updated_at": "2026-05-02T00:00:00Z",
                    "active_state": "calling_llm",
                    "active_state_started_at": "2026-05-02T00:00:00Z",
                    "active_target_task": "Task checkbox-1: Done.",
                },
            )

            decision = diagnose(SupervisorConfig(repo_root=repo))

        self.assertEqual("plan_next_tasks", decision.action)
        self.assertIn("all PP&D daemon tasks are complete", decision.reason)

    def test_dead_worker_calling_llm_status_resets_in_progress_task_before_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            board = repo / "ppd" / "daemon" / "task-board.md"
            board.parent.mkdir(parents=True)
            board.write_text(
                "- [~] Task checkbox-160: Add supervisor task-board de-duplication coverage.\n"
                "- [ ] Task checkbox-161: Add daemon stale-worker recovery coverage.\n",
                encoding="utf-8",
            )
            atomic_write_json(
                repo / "ppd" / "daemon" / "status.json",
                {
                    "updated_at": "2026-05-03T00:00:00Z",
                    "active_state": "calling_llm",
                    "active_state_started_at": "2026-05-03T00:00:00Z",
                    "active_target_task": "Task checkbox-160: Add supervisor task-board de-duplication coverage.",
                    "pid": 99999999,
                },
            )

            decision = diagnose(SupervisorConfig(repo_root=repo, pid_file=Path("ppd/daemon/missing.pid")))
            repaired, reset = builtin_dead_worker_task_board(
                board.read_text(encoding="utf-8"),
                "Task checkbox-160: Add supervisor task-board de-duplication coverage.",
            )

        self.assertEqual("reconcile_dead_worker_and_restart", decision.action)
        self.assertTrue(decision.should_restart_daemon)
        self.assertEqual(("Add supervisor task-board de-duplication coverage.",), reset)
        self.assertIn("- [ ] Task checkbox-160: Add supervisor task-board de-duplication coverage.", repaired)
        self.assertNotIn("- [~] Task checkbox-160", repaired)

    def test_repeated_durable_parse_diagnostics_trigger_repair_before_restart_loop(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            daemon_dir = repo / "ppd" / "daemon"
            daemon_dir.mkdir(parents=True)
            (daemon_dir / "task-board.md").write_text(
                "- [~] Task checkbox-160: Add supervisor task-board de-duplication coverage.\n",
                encoding="utf-8",
            )
            atomic_write_json(
                daemon_dir / "status.json",
                {
                    "updated_at": "2026-05-03T00:00:00Z",
                    "active_state": "calling_llm",
                    "active_target_task": "Task checkbox-160: Add supervisor task-board de-duplication coverage.",
                },
            )
            for _ in range(3):
                append_jsonl(
                    daemon_dir / "ppd-daemon.jsonl",
                    {
                        "stage": "before_validation",
                        "diagnostic": {
                            "failure_kind": "parse",
                            "target_task": "Task checkbox-160: Add supervisor task-board de-duplication coverage.",
                            "errors": ["LLM response did not contain a JSON object."],
                        },
                    },
                )

            rows = read_supervisor_result_rows(daemon_dir / "ppd-daemon.jsonl")
            decision = diagnose(SupervisorConfig(repo_root=repo, pid_file=Path("ppd/daemon/missing.pid")))

        self.assertEqual(3, len(rows))
        self.assertEqual("repair_daemon_programming", decision.action)
        self.assertIn("durable LLM parse/runtime diagnostics", decision.reason)

    def test_repeated_parse_diagnostics_park_stuck_task_in_builtin_repair(self) -> None:
        board = (
            "- [~] Task checkbox-160: Add supervisor task-board de-duplication coverage.\n"
            "- [ ] Task checkbox-161: Add daemon stale-worker recovery coverage.\n"
        )
        rows = [
            {
                "failure_kind": "parse",
                "target_task": "Task checkbox-160: Add supervisor task-board de-duplication coverage.",
                "errors": ["LLM response did not contain a JSON object."],
            }
            for _ in range(3)
        ]

        repaired, parked = builtin_repair_task_board(board, rows)

        self.assertEqual(("Add supervisor task-board de-duplication coverage.",), parked)
        self.assertIn("- [!] Task checkbox-160: Add supervisor task-board de-duplication coverage.", repaired)
        self.assertIn("- [ ] Task checkbox-161: Add daemon stale-worker recovery coverage.", repaired)


if __name__ == "__main__":
    unittest.main()
