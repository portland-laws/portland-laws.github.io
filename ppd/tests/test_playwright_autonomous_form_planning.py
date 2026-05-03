from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "playwright_autonomous_form_planning.json"
REFUSED_ACTIONS = {
    "upload_official_document",
    "submit_application",
    "pay_fee",
    "certify_statement",
    "cancel_request",
    "mfa",
    "captcha",
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


class PlaywrightAutonomousFormPlanningTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_boundary_is_fixture_only_and_no_live_browser_is_launched(self) -> None:
        self.assertEqual("playwright_autonomous_form_planning", self.fixture["fixtureKind"])
        boundary = self.fixture["boundary"]
        self.assertTrue(boundary["fixtureOnly"])
        self.assertFalse(boundary["playwrightLaunched"])
        self.assertFalse(boundary["liveDevhubAccess"])
        self.assertFalse(boundary["officialUploadAllowed"])
        self.assertFalse(boundary["officialSubmissionAllowed"])
        self.assertFalse(boundary["paymentAutomationAllowed"])
        self.assertFalse(boundary["privateArtifactStored"])

    def test_reversible_draft_fill_steps_are_source_linked_and_redacted(self) -> None:
        evidence_ids = {source["sourceEvidenceId"] for source in self.fixture["sourceEvidence"]}
        facts = {fact["factId"]: fact for fact in self.fixture["redactedUserFacts"]}

        for fact in facts.values():
            self.assertTrue(fact["redactedValue"].startswith("[REDACTED_"))
            self.assertEqual("user_document_store", fact["source"])
            self.assertEqual("current", fact["freshness"])

        for step in self.fixture["draftFillPlan"]:
            self.assertEqual("reversible_draft_fill", step["actionClass"])
            self.assertTrue(step["allowedAutonomous"])
            self.assertFalse(step["requiresExactConfirmation"])
            self.assertIn(step["inputFactId"], facts)
            selector = step["selectorPlan"]
            self.assertIn(selector["role"], {"textbox", "combobox", "checkbox"})
            self.assertGreaterEqual(selector["confidence"], 0.9)
            self.assertTrue(set(selector["sourceEvidenceIds"]).issubset(evidence_ids))

    def test_consequential_security_and_financial_actions_are_refused(self) -> None:
        actions = {action["actionId"]: action for action in self.fixture["refusedActions"]}
        self.assertEqual(REFUSED_ACTIONS, set(actions))
        for action in actions.values():
            self.assertTrue(action["requiresExactConfirmation"])
            self.assertFalse(action["exactConfirmationPresent"])
            self.assertIn(action["defaultOutcome"], {"refuse", "human_review"})

    def test_public_evidence_and_planner_outcome_stay_draft_only(self) -> None:
        for source in self.fixture["sourceEvidence"]:
            self.assertTrue(source["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertTrue(source["citation"]["locator"])
            self.assertTrue(source["citation"]["paraphrase"])

        outcome = self.fixture["plannerOutcome"]
        self.assertTrue(outcome["mayFillReversibleDraftFields"])
        self.assertFalse(outcome["mayLaunchLiveBrowser"])
        self.assertFalse(outcome["mayPerformOfficialActions"])
        self.assertEqual("prepare_reversible_draft_preview_plan", outcome["nextAgentAction"])

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)


if __name__ == "__main__":
    unittest.main()
