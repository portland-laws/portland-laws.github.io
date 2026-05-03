from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from ppd.daemon.ppd_daemon import (
    Config,
    Daemon,
    Proposal,
    should_skip_validation_for_no_file_failure,
    terminate_process_group,
)


class DaemonLlmResultDurabilityTest(unittest.TestCase):
    def test_parse_failure_diagnostic_is_written_before_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            (repo / "ppd" / "daemon").mkdir(parents=True)
            (repo / "ppd" / "daemon" / "task-board.md").write_text(
                "- [~] Task checkbox-1: Synthetic task.\n",
                encoding="utf-8",
            )
            daemon = Daemon(Config(repo_root=repo, apply=True))
            proposal = Proposal(
                errors=["LLM response did not contain a JSON object."],
                failure_kind="parse",
                target_task="Task checkbox-1: Synthetic task.",
            )
            proposal.dry_run = False

            daemon.write_progress([proposal])
            daemon.write_cycle_diagnostic(proposal, stage="before_validation")

            progress = json.loads((repo / "ppd" / "daemon" / "progress.json").read_text(encoding="utf-8"))
            rows = [
                json.loads(line)
                for line in (repo / "ppd" / "daemon" / "ppd-daemon.jsonl").read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual("parse", progress["latest"]["failure_kind"])
        self.assertEqual("before_validation", rows[0]["stage"])
        self.assertEqual("parse", rows[0]["diagnostic"]["failure_kind"])

    def test_timeout_interrupted_and_vanished_child_diagnostics_are_durable(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            (repo / "ppd" / "daemon").mkdir(parents=True)
            (repo / "ppd" / "daemon" / "task-board.md").write_text(
                "- [~] Task checkbox-1: Synthetic task.\n",
                encoding="utf-8",
            )
            daemon = Daemon(Config(repo_root=repo, apply=True))
            for message in (
                "llm_router child timed out after 330 seconds",
                "llm_router child exited with code -9",
                "validation command interrupted before final result",
            ):
                proposal = Proposal(
                    summary="LLM proposal failed.",
                    errors=[message],
                    failure_kind="llm",
                    target_task="Task checkbox-1: Synthetic task.",
                )
                daemon.write_cycle_diagnostic(proposal, stage="before_validation")

            rows = [
                json.loads(line)
                for line in (repo / "ppd" / "daemon" / "ppd-daemon.jsonl").read_text(encoding="utf-8").splitlines()
            ]

        self.assertEqual(3, len(rows))
        self.assertTrue(all(row["diagnostic"]["failure_kind"] == "llm" for row in rows))
        self.assertIn("timed out", rows[0]["diagnostic"]["errors"][0])
        self.assertIn("code -9", rows[1]["diagnostic"]["errors"][0])
        self.assertIn("interrupted", rows[2]["diagnostic"]["errors"][0])

    def test_no_file_llm_failures_skip_full_validation_after_durable_diagnostic(self) -> None:
        self.assertTrue(
            should_skip_validation_for_no_file_failure(
                Proposal(summary="LLM proposal failed.", failure_kind="llm")
            )
        )
        self.assertTrue(
            should_skip_validation_for_no_file_failure(
                Proposal(errors=["LLM response did not contain a JSON object."], failure_kind="parse")
            )
        )
        self.assertFalse(
            should_skip_validation_for_no_file_failure(
                Proposal(
                    summary="Has files",
                    failure_kind="llm",
                    files=[{"path": "ppd/example.py", "content": "print('ok')\n"}],
                )
            )
        )
        self.assertFalse(should_skip_validation_for_no_file_failure(Proposal(summary="Needs validation")))

    def test_llm_timeout_cleanup_terminates_descendant_processes(self) -> None:
        process = subprocess.Popen(
            ["bash", "-lc", "sleep 30 & echo $!; wait"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        assert process.stdout is not None
        child_pid = int(process.stdout.readline().strip())

        terminate_process_group(process, grace_seconds=0.2)
        time.sleep(0.1)

        self.assertIsNotNone(process.poll())
        with self.assertRaises(ProcessLookupError):
            os.kill(child_pid, 0)


if __name__ == "__main__":
    unittest.main()
