"""Fixture-first validation for supervisor no-available-task fallback behavior."""

from __future__ import annotations

import json
from pathlib import Path
import unittest

from ppd.daemon.supervisor_no_available_task_fallback import (
    append_fixture_first_tranche_if_needed,
    build_fallback_task_line,
    state_from_mapping,
    should_append_fixture_first_tranche,
)


class SupervisorNoAvailableTaskFallbackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        fixture_path = Path(__file__).parent / "fixtures" / "daemon" / "no_available_task_fallback.json"
        cls.fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    def test_fallback_is_limited_to_codex_planning_failure_or_timeout(self) -> None:
        for state_data in self.fixture["states"]:
            with self.subTest(state=state_data["name"]):
                state = state_from_mapping(state_data)
                self.assertIs(should_append_fixture_first_tranche(state), state_data["shouldAppend"])

    def test_fallback_task_line_is_deterministic(self) -> None:
        self.assertEqual(build_fallback_task_line(), self.fixture["expectedTaskLine"])

    def test_supervisor_appends_fixture_first_tranche_when_planning_fails(self) -> None:
        state_data = next(item for item in self.fixture["states"] if item["planningStatus"] == "codex_planning_failed")
        board_after = append_fixture_first_tranche_if_needed(
            self.fixture["boardBefore"],
            state_from_mapping(state_data),
        )

        self.assertIn(self.fixture["expectedTaskLine"], board_after)
        for expected_text in self.fixture["expectedGuidanceContains"]:
            self.assertIn(expected_text, board_after)

    def test_supervisor_appends_same_tranche_for_timeout(self) -> None:
        failed_state = next(item for item in self.fixture["states"] if item["planningStatus"] == "codex_planning_failed")
        timeout_state = next(item for item in self.fixture["states"] if item["planningStatus"] == "codex_planning_timed_out")

        failed_board = append_fixture_first_tranche_if_needed(
            self.fixture["boardBefore"],
            state_from_mapping(failed_state),
        )
        timeout_board = append_fixture_first_tranche_if_needed(
            self.fixture["boardBefore"],
            state_from_mapping(timeout_state),
        )

        self.assertEqual(failed_board, timeout_board)

    def test_fallback_append_is_idempotent(self) -> None:
        state_data = next(item for item in self.fixture["states"] if item["planningStatus"] == "codex_planning_failed")
        state = state_from_mapping(state_data)
        once = append_fixture_first_tranche_if_needed(self.fixture["boardBefore"], state)
        twice = append_fixture_first_tranche_if_needed(once, state)

        self.assertEqual(once, twice)
        self.assertEqual(once.count(self.fixture["expectedTaskLine"]), 1)


if __name__ == "__main__":
    unittest.main()
