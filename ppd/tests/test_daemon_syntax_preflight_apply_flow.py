from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ppd.daemon.ppd_daemon import Config, Proposal, apply_files_with_validation
from ppd.daemon.syntax_preflight import run_apply_flow_syntax_preflight


class DaemonSyntaxPreflightApplyFlowTests(unittest.TestCase):
    def test_no_syntax_bearing_changed_files_runs_no_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_apply_flow_syntax_preflight(
                Path(temp_dir),
                ["ppd/tests/fixtures/crawler/public_crawl_dry_run_plan.json"],
            )

        self.assertTrue(result.ok)
        self.assertEqual(result.failure_kind, "")
        self.assertEqual(result.errors, ())
        self.assertEqual(result.validation_results, ())

    def test_python_syntax_failure_rolls_back_before_full_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            target = repo_root / "ppd/generated/bad_replacement.py"
            proposal = Proposal(
                summary="Exercise syntax preflight rollback.",
                files=[
                    {
                        "path": "ppd/generated/bad_replacement.py",
                        "content": "def broken(:\n    return 1\n",
                    }
                ],
            )
            config = Config(
                repo_root=repo_root,
                validation_commands=(("python3", "-c", "raise SystemExit(99)"),),
            )

            result = apply_files_with_validation(proposal, config)

            self.assertFalse(result.applied)
            self.assertEqual(result.failure_kind, "syntax_preflight")
            self.assertFalse(target.exists())
            self.assertEqual(len(result.validation_results), 1)
            self.assertEqual(result.validation_results[0].command[:3], ("python3", "-m", "py_compile"))
            self.assertIn("Syntax preflight failed", result.errors[0])
            failed_manifests = list((repo_root / "ppd/daemon/failed-patches").glob("*syntax_preflight*.json"))
            self.assertEqual(len(failed_manifests), 1)


if __name__ == "__main__":
    unittest.main()
