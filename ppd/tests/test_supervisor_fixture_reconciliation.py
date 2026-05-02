from __future__ import annotations

import unittest

from ppd.daemon.supervisor_fixture_reconciliation import (
    AcceptedValidationTask,
    BlockedValidationTask,
    FixtureShape,
    accepted_task_from_dict,
    blocked_task_from_dict,
    reconcile_blocked_fixture_shape,
)


class SupervisorFixtureReconciliationTests(unittest.TestCase):
    def test_reports_accepted_validation_task_satisfying_blocked_fixture_shape(self) -> None:
        blocked = BlockedValidationTask(
            task_id="checkbox-115",
            summary="blocked crawl-plan validator retry",
            fixture_shape=FixtureShape(
                fixture_path="ppd/tests/fixtures/crawler/public_crawl_dry_run_plan.json",
                required_fields=("seedUrls", "allowlistDecisions", "robotsPreflight"),
            ),
        )
        accepted = AcceptedValidationTask(
            task_id="checkbox-119",
            summary="accepted narrower crawl-plan validator",
            fixture_shape=FixtureShape(
                fixture_path="ppd/tests/fixtures/crawler/public_crawl_dry_run_plan.json",
                required_fields=(
                    "schemaVersion",
                    "seedUrls",
                    "allowlistDecisions",
                    "robotsPreflight",
                    "skippedUrlReasonCodes",
                ),
            ),
        )

        diagnostic = reconcile_blocked_fixture_shape(blocked, [accepted])

        self.assertIsNotNone(diagnostic)
        assert diagnostic is not None
        self.assertEqual(diagnostic.blocked_task_id, "checkbox-115")
        self.assertEqual(diagnostic.accepted_task_id, "checkbox-119")
        self.assertEqual(diagnostic.recommendation, "supersede_blocked_or_resume_one_file")
        self.assertEqual(
            diagnostic.matched_fields,
            ("seedUrls", "allowlistDecisions", "robotsPreflight"),
        )
        self.assertEqual(
            diagnostic.as_dict()["fixturePath"],
            "ppd/tests/fixtures/crawler/public_crawl_dry_run_plan.json",
        )

    def test_does_not_report_for_different_fixture_paths(self) -> None:
        blocked = BlockedValidationTask(
            task_id="checkbox-115",
            summary="blocked process validator retry",
            fixture_shape=FixtureShape(
                fixture_path="ppd/tests/fixtures/processes/public_process.json",
                required_fields=("processId",),
            ),
        )
        accepted = AcceptedValidationTask(
            task_id="checkbox-119",
            summary="accepted crawl-plan validator",
            fixture_shape=FixtureShape(
                fixture_path="ppd/tests/fixtures/crawler/public_crawl_dry_run_plan.json",
                required_fields=("processId",),
            ),
        )

        self.assertIsNone(reconcile_blocked_fixture_shape(blocked, [accepted]))

    def test_parses_daemon_style_dicts(self) -> None:
        blocked = blocked_task_from_dict(
            {
                "taskId": "checkbox-115",
                "summary": "blocked fixture task",
                "fixtureShape": {
                    "fixturePath": "ppd/tests/fixtures/devhub/form_state.json",
                    "requiredFields": ["fields", "sourceEvidenceIds"],
                },
            }
        )
        accepted = accepted_task_from_dict(
            {
                "task_id": "checkbox-118",
                "summary": "accepted DevHub form-state validation",
                "fixture_shape": {
                    "fixture_path": "ppd/tests/fixtures/devhub/form_state.json",
                    "required_fields": ["fields", "sourceEvidenceIds", "redactedValuesOnly"],
                },
            }
        )

        diagnostic = reconcile_blocked_fixture_shape(blocked, [accepted])

        self.assertIsNotNone(diagnostic)
        assert diagnostic is not None
        self.assertEqual(diagnostic.as_dict()["recommendation"], "supersede_blocked_or_resume_one_file")


if __name__ == "__main__":
    unittest.main()
