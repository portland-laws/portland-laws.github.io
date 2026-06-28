"""Fixture coverage for blocked-task prompt-budget compaction.

This test is intentionally fixture-only. It proves the daemon prompt context can
represent repeated llm_router exits without persisting raw responses or retrying
blocked PP&D domain work.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "daemon" / "blocked_task_prompt_budget.json"


class BlockedTaskPromptBudgetFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)

    def test_repeated_router_exits_are_compacted_without_raw_responses(self) -> None:
        exits = self.fixture["llm_router_exits"]
        budget = self.fixture["prompt_budget_summary"]

        self.assertGreaterEqual(len(exits), 2)
        for expected_attempt, exit_record in enumerate(exits, start=1):
            self.assertEqual(exit_record["attempt"], expected_attempt)
            self.assertEqual(exit_record["failure_kind"], "llm_router_exit")
            self.assertLessEqual(
                len(exit_record["compact_error_summary"]),
                budget["max_compact_error_summary_chars"],
            )
            self.assertIs(exit_record["raw_response_persisted"], False)
            self.assertNotIn("raw_response", exit_record)
            self.assertNotIn("response_body", exit_record)

    def test_target_and_next_daemon_repair_hint_fit_prompt_budget(self) -> None:
        target = self.fixture["target_task"]
        budget = self.fixture["prompt_budget_summary"]

        self.assertEqual(target["checkbox_id"], "checkbox-178")
        self.assertEqual(target["task_kind"], "domain")
        self.assertIs(target["blocked"], True)
        self.assertIs(target["retry_allowed"], False)
        self.assertIn(target["checkbox_id"], budget["target_summary"])
        self.assertIn("daemon repair", budget["next_action_hint"])
        self.assertLessEqual(
            len(budget["next_action_hint"]),
            budget["max_next_action_hint_chars"],
        )

    def test_blocked_domain_work_is_not_retried(self) -> None:
        decision = self.fixture["selection_decision"]
        omitted_context = set(self.fixture["prompt_budget_summary"]["omitted_context"])

        self.assertIs(decision["blocked_domain_retry_attempted"], False)
        self.assertEqual(decision["selected_task_kind"], "daemon_repair")
        self.assertEqual(decision["selected_checkbox_id"], "checkbox-189")
        self.assertIn("raw llm responses", omitted_context)
        self.assertIn("private DevHub session data", omitted_context)
        self.assertIn("browser traces", omitted_context)
        self.assertIn("raw crawl output", omitted_context)
        self.assertIn("downloaded documents", omitted_context)


if __name__ == "__main__":
    unittest.main()
