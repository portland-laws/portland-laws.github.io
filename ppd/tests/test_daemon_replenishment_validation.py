from __future__ import annotations

import unittest

from ppd.daemon.replenishment_validation import (
    ReplenishmentTask,
    build_replenishment_fixture,
    validate_replenishment_fixture,
)
from ppd.daemon.ppd_supervisor import (
    is_syntax_or_compile_failure,
    recent_syntax_failure_count,
)


class DaemonReplenishmentValidationTest(unittest.TestCase):
    def test_completed_board_can_append_goal_aligned_tranche(self) -> None:
        result = validate_replenishment_fixture(build_replenishment_fixture())

        self.assertTrue(result.ok, result.errors)
        self.assertEqual(2, result.before_task_count)
        self.assertEqual(4, result.after_task_count)
        self.assertEqual(
            (
                "accepted-agent-planning-reversible-draft-only",
                "accepted-processor-archive-provenance",
            ),
            result.preserved_accepted_work_ids,
        )
        self.assertEqual(("checkbox-82", "checkbox-83"), result.appended_task_ids)
        self.assertEqual("checkbox-82", result.next_selectable_task_id)
        self.assertEqual(0, result.stale_repair_count_after)

    def test_replenishment_rejects_reused_completed_task_ids(self) -> None:
        fixture = build_replenishment_fixture()
        fixture["appended_tasks"] = [
            {
                "checkbox_id": "checkbox-80",
                "title": "bad reused task id",
                "style": "fixture_first",
                "status": "needed",
            }
        ]

        result = validate_replenishment_fixture(fixture)

        self.assertFalse(result.ok)
        self.assertIn("appended task ids must not reuse completed task ids", result.errors)

    def test_replenishment_rejects_non_fixture_or_validation_first_tasks(self) -> None:
        fixture = build_replenishment_fixture()
        fixture["appended_tasks"] = [
            ReplenishmentTask(
                checkbox_id="checkbox-82",
                title="live DevHub automation",
                style="live_devhub",
            ).__dict__
        ]

        result = validate_replenishment_fixture(fixture)

        self.assertFalse(result.ok)
        self.assertIn("appended task checkbox-82 has unsupported style 'live_devhub'", result.errors)

    def test_supervisor_counts_syntax_preflight_as_syntax_failure(self) -> None:
        proposal = {
            "failure_kind": "syntax_preflight",
            "target_task": "Task checkbox-81: replenishment",
            "validation_results": [
                {
                    "command": ["python3", "-m", "py_compile", "ppd/daemon/replenishment_validation.py"],
                    "returncode": 1,
                    "stderr": "SyntaxError: invalid syntax",
                }
            ],
        }

        self.assertTrue(is_syntax_or_compile_failure(proposal))
        self.assertEqual(2, recent_syntax_failure_count([proposal, proposal]))


if __name__ == "__main__":
    unittest.main()
