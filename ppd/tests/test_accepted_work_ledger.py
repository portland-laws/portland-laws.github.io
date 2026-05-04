import json
import tempfile
import unittest
from pathlib import Path

from ppd.daemon.accepted_work_ledger import (
    AcceptedWorkArtifacts,
    append_accepted_work_ledger,
    build_accepted_work_ledger_entry,
)


class AcceptedWorkLedgerTests(unittest.TestCase):
    def test_builds_stable_success_entry_without_raw_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            artifacts = AcceptedWorkArtifacts(
                manifest=repo_root / "ppd/daemon/accepted-work/round.json",
                patch=repo_root / "ppd/daemon/accepted-work/round.patch",
                stat=repo_root / "ppd/daemon/accepted-work/round.stat.txt",
            )
            entry = build_accepted_work_ledger_entry(
                repo_root=repo_root,
                target_task="Task checkbox-17: Add append-only accepted-work ledger generation for successful PP&D daemon rounds.",
                summary="Add accepted ledger",
                impact="Makes successful daemon rounds auditable.",
                changed_files=["ppd/tests/example.py", "ppd/daemon/example.py"],
                transport="temporary_worktree",
                artifacts=artifacts,
                validation_results=[{"command": ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"], "returncode": 0, "stdout": "raw output ignored"}],
                created_at="2026-05-01T00:00:00Z",
            )

        self.assertEqual(entry["schema_version"], 1)
        self.assertTrue(entry["validation_passed"])
        self.assertEqual(entry["transport"], "temporary_worktree")
        self.assertEqual(entry["changed_files"], ["ppd/daemon/example.py", "ppd/tests/example.py"])
        self.assertEqual(entry["artifacts"]["manifest"], "ppd/daemon/accepted-work/round.json")
        self.assertNotIn("stdout", entry["validation_results"][0])

    def test_appends_jsonl_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            accepted_dir = Path(tmp) / "ppd/daemon/accepted-work"
            first = {"created_at": "2026-05-01T00:00:00Z", "summary": "first"}
            second = {"created_at": "2026-05-01T00:01:00Z", "summary": "second"}

            ledger_path = append_accepted_work_ledger(accepted_dir, first)
            append_accepted_work_ledger(accepted_dir, second)

            rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(rows, [first, second])


if __name__ == "__main__":
    unittest.main()
