from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "agent_planning" / "reversible_draft_only_plan.json"
FORBIDDEN_ACTIONS = {
    "account_creation",
    "captcha",
    "cancel_request",
    "certify_statement",
    "mfa",
    "official_upload",
    "password_recovery",
    "pay_fee",
    "schedule_inspection",
    "submit_application",
}
FORBIDDEN_TEXT_MARKERS = (
    "storage_state",
    "auth_state",
    "cookies.json",
    "localstorage.json",
    "trace.zip",
    "playwright-report",
    "screenshot.png",
    "ppd/data/private",
    "ppd/data/raw",
)


class AgentPlanningReversibleDraftOnlyFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)
        self.evidence_ids = {item["sourceEvidenceId"] for item in self.fixture["sourceEvidence"]}

    def test_fixture_is_draft_only_and_fixture_only(self) -> None:
        self.assertEqual(self.fixture["schemaVersion"], 1)
        self.assertEqual(self.fixture["planType"], "reversible_draft_only_agent_plan")
        self.assertTrue(self.fixture["fixtureOnly"])
        self.assertTrue(self.fixture["draftOnly"])
        self.assertFalse(self.fixture["browserLaunched"])
        self.assertFalse(self.fixture["liveDevHubSession"])
        audit_preview = self.fixture["auditPreview"]
        self.assertTrue(audit_preview["recordsOnlyPlannedActions"])
        self.assertFalse(audit_preview["recordsExecutedActions"])
        self.assertFalse(audit_preview["containsScreenshots"])
        self.assertFalse(audit_preview["containsTraces"])
        self.assertFalse(audit_preview["containsAuthState"])
        self.assertFalse(audit_preview["containsPrivateValues"])

    def test_every_source_evidence_item_is_public_and_referenced(self) -> None:
        self.assertGreaterEqual(len(self.fixture["sourceEvidence"]), 3)
        referenced_ids: set[str] = set(self.fixture["processRef"]["sourceEvidenceIds"])
        for collection_name in ("missingInformation", "playwrightDraftPreviews", "guardrailStopGates"):
            for item in self.fixture[collection_name]:
                referenced_ids.update(item["sourceEvidenceIds"])
        self.assertEqual(referenced_ids, self.evidence_ids)
        for evidence in self.fixture["sourceEvidence"]:
            self.assertTrue(evidence["publicOnly"])
            self.assertTrue(evidence["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertTrue(evidence["capturedAt"].endswith("Z"))
            self.assertGreater(len(evidence["supports"]), 0)

    def test_missing_information_links_to_requirements_and_evidence(self) -> None:
        missing_information = self.fixture["missingInformation"]
        self.assertGreaterEqual(len(missing_information), 2)
        for item in missing_information:
            self.assertTrue(item["missingFactId"].startswith("fact-"))
            self.assertTrue(item["requirementId"].startswith("req-"))
            self.assertIn(item["currentValue"], {"UNKNOWN", "REDACTED_EMPTY"})
            self.assertTrue(item["prompt"].strip())
            self.assertTrue(set(item["sourceEvidenceIds"]).issubset(self.evidence_ids))

    def test_playwright_previews_are_reversible_redacted_draft_edits(self) -> None:
        previews = self.fixture["playwrightDraftPreviews"]
        self.assertGreaterEqual(len(previews), 1)
        missing_fact_ids = {item["missingFactId"] for item in self.fixture["missingInformation"]}
        for preview in previews:
            self.assertNotIn(preview["actionType"], FORBIDDEN_ACTIONS)
            self.assertEqual(preview["actionClass"], "reversible_draft_edit")
            self.assertTrue(preview["previewOnly"])
            self.assertFalse(preview["browserLaunched"])
            self.assertTrue(preview["beforeValue"].startswith("REDACTED"))
            self.assertTrue(preview["afterValue"].startswith("REDACTED"))
            self.assertTrue(set(preview["sourceEvidenceIds"]).issubset(self.evidence_ids))
            self.assertIn(preview["fieldRef"]["missingFactId"], missing_fact_ids)
            selector_basis = preview["selectorBasis"]
            self.assertEqual(selector_basis["stableSelectorBasis"], "role+accessibleName+labelText")
            self.assertTrue(selector_basis["role"].strip())
            self.assertTrue(selector_basis["accessibleName"].strip())
            self.assertTrue(selector_basis["labelText"].strip())
            self.assertTrue(selector_basis["nearbyHeading"].strip())

    def test_stop_gates_block_irreversible_or_financial_actions_by_default(self) -> None:
        gates = self.fixture["guardrailStopGates"]
        stopped_actions = {gate["stopBeforeAction"] for gate in gates}
        self.assertTrue({"official_upload", "submit_application", "pay_fee"}.issubset(stopped_actions))
        for gate in gates:
            self.assertIn(gate["actionClass"], {"consequential", "financial"})
            self.assertTrue(gate["explicitConfirmationRequired"])
            self.assertFalse(gate["exactConfirmationPresent"])
            self.assertFalse(gate["confirmationDefault"])
            self.assertTrue(gate["reason"].strip())
            self.assertTrue(set(gate["sourceEvidenceIds"]).issubset(self.evidence_ids))

    def test_fixture_contains_no_private_artifact_markers(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_TEXT_MARKERS:
            self.assertNotIn(marker, serialized)


if __name__ == "__main__":
    unittest.main()
