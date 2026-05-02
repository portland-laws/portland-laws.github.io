from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "process_comparison"
    / "permit_process_comparison_scenario.json"
)

FORBIDDEN_ACTIONS = {
    "upload_official_document",
    "submit_application",
    "certify_statement",
    "pay_fee",
    "cancel_request",
    "schedule_inspection",
}
FORBIDDEN_MARKERS = (
    "ppd/data/private",
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
    "cookie",
    "password",
    "token",
)


class PermitProcessComparisonScenarioTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_processes_preserve_separate_legal_and_ui_surfaces(self) -> None:
        self.assertEqual("permit_process_comparison_scenario", self.fixture["fixtureKind"])
        evidence_ids = {item["sourceEvidenceId"] for item in self.fixture["sourceEvidence"]}
        process_types = {process["processType"] for process in self.fixture["processes"]}

        self.assertEqual({"residential_building_permit", "trade_permit_with_plan_review"}, process_types)
        for process in self.fixture["processes"]:
            self.assertTrue(set(process["sourceEvidenceIds"]).issubset(evidence_ids))
            self.assertTrue(process["legalObligations"])
            self.assertTrue(process["operationalUiHints"])
            self.assertTrue(process["documentPlaceholders"])
            self.assertTrue(process["feeNotices"])
            for obligation in process["legalObligations"]:
                self.assertTrue(obligation["citationRequired"])
                self.assertEqual("provide_required_user_fact", obligation["kind"])
            for hint in process["operationalUiHints"]:
                self.assertTrue(hint["citationRequired"])

    def test_document_placeholders_fee_notices_and_confirmation_gates_fail_closed(self) -> None:
        for process in self.fixture["processes"]:
            for placeholder in process["documentPlaceholders"]:
                self.assertTrue(placeholder["requiredBeforeOfficialSubmission"])
                self.assertEqual("[REDACTED_DOCUMENT_PLACEHOLDER]", placeholder["redactedPlaceholder"])
            for fee in process["feeNotices"]:
                self.assertTrue(fee["noticeOnly"])
                self.assertTrue(fee["exactConfirmationRequiredBeforePayment"])
            self.assertIn("submit_application", process["exactConfirmationGates"])
            self.assertIn("pay_fee", process["exactConfirmationGates"])

        self.assertTrue(FORBIDDEN_ACTIONS.issubset(set(self.fixture["forbiddenAutomation"])))

    def test_comparison_keeps_requirements_and_documents_separate(self) -> None:
        comparison = self.fixture["comparison"]
        self.assertEqual(["submit_application", "pay_fee"], comparison["sharedExactConfirmationGates"])
        self.assertEqual(
            ["project.site_address", "contractor.license_identifier"],
            comparison["separateRequirementKeys"],
        )
        self.assertEqual(
            ["documents.site_plan", "documents.trade_plan_review"],
            comparison["separateDocumentPlaceholders"],
        )
        self.assertEqual(
            "keep_process_requirements_separate_and_fail_closed_before_official_actions",
            comparison["agentPlanningOutcome"],
        )

    def test_private_runtime_artifacts_are_absent(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)
        for evidence in self.fixture["sourceEvidence"]:
            self.assertTrue(evidence["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertTrue(evidence["citation"]["locator"])
            self.assertTrue(evidence["citation"]["paraphrase"])


if __name__ == "__main__":
    unittest.main()
