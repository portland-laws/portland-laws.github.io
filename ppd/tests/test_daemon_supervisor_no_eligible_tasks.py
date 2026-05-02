"""Regression tests for PP&D daemon supervisor no_eligible_tasks states."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.daemon.supervisor_no_eligible_tasks import (
    EXPECTED_ERROR,
    PROGRAMMING_ERROR_KIND,
    assert_no_eligible_tasks_supervisor_error,
    classify_no_eligible_tasks_fixture,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "daemon_supervisor"
    / "no_eligible_tasks_stale_retry_without_fixture_first.json"
)


class SupervisorNoEligibleTasksRegressionTest(unittest.TestCase):
    def test_no_eligible_tasks_after_only_parked_stale_retry_is_programming_error(self) -> None:
        fixture = _load_fixture()

        result = assert_no_eligible_tasks_supervisor_error(fixture)

        self.assertEqual(PROGRAMMING_ERROR_KIND, result["classification"])
        self.assertEqual(EXPECTED_ERROR, result["error"])
        self.assertTrue(result["is_supervisor_programming_error"])
        self.assertEqual(fixture["expected_classification"], result["classification"])
        self.assertEqual(fixture["expected_error"], result["error"])
        self.assertEqual(fixture["expected_required_repair"], result["required_repair"])
        self.assertEqual(["checkbox-parked-stale-retry-example"], result["parked_task_ids"])

    def test_new_fixture_first_task_prevents_programming_error(self) -> None:
        fixture = _load_fixture()
        fixture = dict(fixture)
        fixture["appended_tasks"] = [
            {
                "task_id": "checkbox-new-fixture-first-recovery",
                "checkbox_state": "[ ]",
                "task_style": "fixture_first",
                "selectable": True,
                "appended_after_stale_retry_parking": True,
            }
        ]

        result = classify_no_eligible_tasks_fixture(fixture)

        self.assertEqual("not_programming_error", result["classification"])
        self.assertFalse(result["is_supervisor_programming_error"])


def _load_fixture() -> dict[str, object]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise AssertionError("supervisor regression fixture must be a JSON object")
    return data


if __name__ == "__main__":
    unittest.main()
