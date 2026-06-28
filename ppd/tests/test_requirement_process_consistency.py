from pathlib import Path
import unittest

from ppd.logic.requirement_process_consistency import (
    check_consistency,
    check_consistency_files,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "requirement_process_consistency"


class RequirementProcessConsistencyTest(unittest.TestCase):
    def test_public_source_fixture_matches_process_model(self):
        report = check_consistency_files(
            FIXTURE_DIR / "source_requirements_valid.json",
            FIXTURE_DIR / "process_models_valid.json",
        )

        self.assertTrue(report.passed)
        self.assertEqual(report.checked_requirement_count, 4)
        self.assertEqual(report.checked_process_count, 1)
        self.assertEqual([], report.to_dict()["issues"])

    def test_missing_required_document_file_rule_fee_trigger_and_unsupported_path_are_reported(self):
        report = check_consistency_files(
            FIXTURE_DIR / "source_requirements_valid.json",
            FIXTURE_DIR / "process_models_missing_coverage.json",
        )

        self.assertFalse(report.passed)
        issues = report.to_dict()["issues"]
        missing = [issue for issue in issues if issue["issue_type"] == "missing_model_coverage"]
        self.assertEqual(4, len(missing))
        self.assertEqual(
            [
                "fee_trigger",
                "file_rule",
                "required_document",
                "unsupported_path",
            ],
            sorted(issue["category"] for issue in missing),
        )

    def test_process_model_entries_without_source_requirement_are_reported(self):
        report = check_consistency_files(
            FIXTURE_DIR / "source_requirements_valid.json",
            FIXTURE_DIR / "process_models_with_orphan_entry.json",
        )

        orphan_issues = [
            issue
            for issue in report.to_dict()["issues"]
            if issue["issue_type"] == "model_entry_without_source_requirement"
        ]
        self.assertEqual(1, len(orphan_issues))
        self.assertEqual("extra_unverified_upload", orphan_issues[0]["key"])
        self.assertEqual("required_document", orphan_issues[0]["category"])

    def test_unsupported_requirement_categories_do_not_affect_targeted_check(self):
        report = check_consistency(
            {
                "requirements": [
                    {
                        "requirement_id": "REQ-SYNTH-DEADLINE-001",
                        "process_id": "building-plan-review",
                        "permit_type": "building_plan_review",
                        "category": "deadline",
                        "key": "example_deadline",
                    }
                ]
            },
            {"process_models": []},
        )

        self.assertTrue(report.passed)
        self.assertEqual(0, report.checked_requirement_count)


if __name__ == "__main__":
    unittest.main()
