from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ppd.daemon.ppd_daemon import (
    Config,
    Task,
    append_jsonl,
    build_prompt,
    call_llm,
    effective_prompt_limit,
    should_use_compact_prompt,
)


class DaemonCompactPromptRetryTest(unittest.TestCase):
    def test_repeated_parse_or_llm_failures_enable_compact_prompt(self) -> None:
        failures = [
            {"failure_kind": "parse"},
            {"failure_kind": "llm"},
        ]

        self.assertTrue(should_use_compact_prompt(failures))
        self.assertFalse(should_use_compact_prompt([{"failure_kind": "validation"}]))

    def test_compact_prompt_uses_diagnostic_rows_and_omits_workspace_dump(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            daemon_dir = repo / "ppd" / "daemon"
            daemon_dir.mkdir(parents=True)
            (repo / "ppd" / "tests").mkdir(parents=True)
            (repo / "docs").mkdir()
            (repo / "docs" / "PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md").write_text(
                "Plan\n" + ("long plan\n" * 1000),
                encoding="utf-8",
            )
            (daemon_dir / "task-board.md").write_text(
                "- [~] Task checkbox-1: Add compact retry coverage.\n",
                encoding="utf-8",
            )
            (repo / "ppd" / "README.md").write_text("README\n" + ("long readme\n" * 500), encoding="utf-8")
            (repo / "ppd" / "tests" / "huge_context.py").write_text("# context\n" + ("x = 1\n" * 2000), encoding="utf-8")
            target = "Task checkbox-1: Add compact retry coverage."
            for kind in ("parse", "llm"):
                append_jsonl(
                    daemon_dir / "ppd-daemon.jsonl",
                    {
                        "stage": "before_validation",
                        "diagnostic": {
                            "failure_kind": kind,
                            "target_task": target,
                            "errors": ["LLM response did not contain a JSON object."],
                        },
                    },
                )

            prompt = build_prompt(
                Config(repo_root=repo, max_prompt_chars=60000),
                Task(index=1, title="Add compact retry coverage.", status="in-progress", checkbox_id=1),
            )

        self.assertLessEqual(len(prompt), 4300)
        self.assertIn("Compact retry mode", prompt)
        self.assertIn("LLM response did not contain a JSON object", prompt)
        self.assertIn("Recent failure context", prompt)
        self.assertNotIn("--- ppd/tests/huge_context.py ---", prompt)

    def test_compact_prompt_keeps_json_only_recovery_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            daemon_dir = repo / "ppd" / "daemon"
            daemon_dir.mkdir(parents=True)
            (repo / "docs").mkdir()
            (repo / "docs" / "PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md").write_text("Plan\n", encoding="utf-8")
            (daemon_dir / "task-board.md").write_text(
                "- [~] Task checkbox-1: Add JSON recovery coverage.\n",
                encoding="utf-8",
            )
            target = "Task checkbox-1: Add JSON recovery coverage."
            for _ in range(2):
                append_jsonl(
                    daemon_dir / "ppd-daemon.jsonl",
                    {
                        "stage": "before_validation",
                        "diagnostic": {
                            "failure_kind": "parse",
                            "target_task": target,
                            "errors": ["LLM response did not contain a JSON object."],
                        },
                    },
                )

            prompt = build_prompt(
                Config(repo_root=repo),
                Task(index=1, title="Add JSON recovery coverage.", status="in-progress", checkbox_id=1),
            )

        self.assertIn("Return ONLY one JSON object", prompt)
        self.assertIn("no prose outside JSON", prompt)
        self.assertIn("complete file replacements", prompt)
        self.assertIn("smallest useful JSON file replacements", prompt)
        self.assertIn("one fixture and one focused test", prompt)

    def test_compact_prompt_respects_named_budget_before_llm_router_child(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            repo = Path(tempdir)
            daemon_dir = repo / "ppd" / "daemon"
            daemon_dir.mkdir(parents=True)
            (repo / "docs").mkdir()
            (repo / "docs" / "PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md").write_text(
                "Plan\n" + ("x" * 5000),
                encoding="utf-8",
            )
            (daemon_dir / "task-board.md").write_text(
                "- [~] Task checkbox-1: Add budget coverage.\n",
                encoding="utf-8",
            )
            target = "Task checkbox-1: Add budget coverage."
            for _ in range(2):
                append_jsonl(
                    daemon_dir / "ppd-daemon.jsonl",
                    {
                        "stage": "before_validation",
                        "diagnostic": {
                            "failure_kind": "llm",
                            "target_task": target,
                            "errors": ["llm_router child exited with code -15:"],
                        },
                    },
                )
            config = Config(repo_root=repo, max_prompt_chars=60000, max_compact_prompt_chars=3600)

            prompt = build_prompt(config, Task(index=1, title="Add budget coverage.", status="in-progress", checkbox_id=1))

        self.assertLessEqual(len(prompt), effective_prompt_limit(config, compact_prompt=True) + len("\n\n[truncated]\n"))

    def test_call_llm_rejects_over_budget_prompt_before_child_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            config = Config(repo_root=Path(tempdir), max_prompt_chars=20)

            with self.assertRaisesRegex(RuntimeError, "exceeds configured budget"):
                call_llm("x" * 100, config)


if __name__ == "__main__":
    unittest.main()
