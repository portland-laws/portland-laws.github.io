"""Validate the redacted DevHub draft audit ledger fixture."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "draft_audit_ledger.json"
FORBIDDEN_FIXTURE_FRAGMENTS = (
    "screenshot",
    "trace.zip",
    "cookies.json",
    "storage_state",
    "storage-state",
    "auth_state",
    "auth-state",
    "localstorage",
    "raw_browser_storage",
    "rawbrowserstorage",
    "password",
    "credential_value",
)
BLOCKED_ACTIONS = {
    "official_upload",
    "submit_application",
    "certify_statement",
    "pay_fee",
    "cancel_request",
    "schedule_inspection",
}


class DraftAuditLedgerFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_is_preview_only_and_not_live_automation_output(self) -> None:
        self.assertEqual(self.fixture["schemaVersion"], 1)
        self.assertTrue(self.fixture["ledgerId"].startswith("ppd-devhub-draft-audit-ledger-"))
        workflow_state = self.fixture["workflowState"]
        self.assertEqual(workflow_state["mode"], "preview_only")
        self.assertFalse(workflow_state["liveBrowserUsed"])
        self.assertFalse(workflow_state["portalWriteAttempted"])

        retained_policy = self.fixture["retainedArtifactPolicy"]
        self.assertTrue(retained_policy["publicEvidenceIdsOnly"])
        self.assertTrue(retained_policy["redactedFieldValuesOnly"])
        self.assertTrue(retained_policy["semanticSelectorBasisOnly"])
        self.assertFalse(retained_policy["binaryPageArtifactsStored"])
        self.assertFalse(retained_policy["credentialMaterialStored"])
        self.assertFalse(retained_policy["browserPersistenceStored"])
        self.assertFalse(retained_policy["networkPayloadsStored"])

    def test_events_link_public_evidence_guardrails_and_selector_confidence(self) -> None:
        evidence_ids = {item["evidenceId"] for item in self.fixture["publicSourceEvidence"]}
        guardrail_ids = {item["guardrailId"] for item in self.fixture["guardrails"]}
        selector_ids = {item["selectorId"] for item in self.fixture["selectorConfidence"]}

        self.assertGreaterEqual(len(evidence_ids), 2)
        for evidence in self.fixture["publicSourceEvidence"]:
            self.assertTrue(evidence["sourceUrl"].startswith("https://www.portland.gov/"))
            self.assertTrue(evidence["capturedAt"].endswith("Z"))
            self.assertTrue(evidence["anchor"])
            self.assertNotIn("body", evidence)
            self.assertNotIn("html", evidence)

        for event in self.fixture["events"]:
            self.assertTrue(event["processRequirementId"])
            self.assertTrue(set(event["sourceEvidenceIds"]).issubset(evidence_ids))
            self.assertTrue(set(event["guardrailIds"]).issubset(guardrail_ids))
            self.assertIn(event["selectorConfidenceId"], selector_ids)
            confirmation_state = event["userConfirmationState"]
            self.assertFalse(confirmation_state["exactActionConfirmation"])
            self.assertIn("confirmationRequired", confirmation_state)

    def test_selector_confidence_uses_stable_accessible_basis(self) -> None:
        for selector in self.fixture["selectorConfidence"]:
            self.assertEqual(selector["strategy"], "semantic_accessible_selector")
            self.assertGreaterEqual(selector["score"], 0.8)
            self.assertLessEqual(selector["score"], 1.0)
            basis = selector["basis"]
            for key in ("role", "accessibleName", "labelText", "nearbyHeading", "required", "stableUrlState"):
                self.assertIn(key, basis)
            self.assertNotIn("cssPath", selector)
            self.assertNotIn("xpath", selector)
            self.assertNotIn("cssPath", basis)
            self.assertNotIn("xpath", basis)

    def test_reversible_mutations_are_redacted_previews_only(self) -> None:
        reversible_events = [event for event in self.fixture["events"] if event["actionClass"] == "reversible_draft_edit"]
        self.assertTrue(reversible_events)
        for event in reversible_events:
            self.assertFalse(event["userConfirmationState"]["exactActionConfirmation"])
            self.assertTrue(event["mutations"])
            for mutation in event["mutations"]:
                self.assertEqual(mutation["fieldAction"], "fill")
                self.assertTrue(mutation["previewOnly"])
                self.assertTrue(mutation["reversible"])
                self.assertFalse(mutation["appliedToLivePage"])
                self.assertFalse(mutation["persistedToPortal"])
                self.assertTrue(mutation["beforeValue"].startswith("[REDACTED:"))
                self.assertTrue(mutation["afterValue"].startswith("[REDACTED:"))
                self.assertNotEqual(mutation["beforeValue"], mutation["afterValue"])

    def test_consequential_and_financial_actions_are_blocked_by_default(self) -> None:
        blocked_defaults = {item["action"]: item for item in self.fixture["blockedActionDefaults"]}
        self.assertEqual(set(blocked_defaults), BLOCKED_ACTIONS)
        for action in BLOCKED_ACTIONS:
            self.assertFalse(blocked_defaults[action]["defaultAllowed"])
            self.assertTrue(blocked_defaults[action]["requiresExactUserConfirmation"])

    def test_fixture_does_not_store_private_browser_artifacts(self) -> None:
        flattened = "\n".join(_walk_strings(self.fixture)).lower()
        for forbidden in FORBIDDEN_FIXTURE_FRAGMENTS:
            self.assertNotIn(forbidden, flattened)


def _walk_strings(value: object) -> list[str]:
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            strings.append(str(key))
            strings.extend(_walk_strings(item))
        return strings
    if isinstance(value, list):
        strings = []
        for item in value:
            strings.extend(_walk_strings(item))
        return strings
    if isinstance(value, str):
        return [value]
    return []


if __name__ == "__main__":
    unittest.main()
