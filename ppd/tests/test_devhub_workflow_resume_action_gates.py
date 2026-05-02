"""Validate mocked DevHub workflow-resume action gates.

These tests stay fixture-only: they do not launch Playwright, authenticate,
inspect live DevHub, upload documents, submit applications, or pay fees.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "workflow_resume_action_gates.json"

ALLOWED_CLASSIFICATIONS = {"safe_read_only_inspection", "reversible_draft_preview"}
REFUSED_CLASSIFICATIONS = {"potentially_consequential", "financial"}
FORBIDDEN_ALLOWED_OPERATIONS = {
    "account_creation",
    "captcha",
    "cancel_request",
    "certify_statement",
    "mfa",
    "password_recovery",
    "pay_fees",
    "payment_entry",
    "schedule_inspection",
    "submit_application",
    "upload_official_correction",
}
PRIVATE_ARTIFACT_KEYS = {
    "authState",
    "auth_state",
    "cookie",
    "cookies",
    "downloadPath",
    "password",
    "rawHtml",
    "raw_html",
    "screenshotPath",
    "sessionState",
    "storageState",
    "tracePath",
    "username",
}


class DevhubWorkflowResumeActionGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = _load_fixture()

    def test_fixture_is_mocked_and_contains_no_private_artifacts(self) -> None:
        self.assertEqual(self.fixture["schemaVersion"], 1)
        workflow_resume = self.fixture["workflowResume"]
        self.assertTrue(workflow_resume["mockedFixtureOnly"])
        self.assertTrue(workflow_resume["accountScoped"])
        self.assertFalse(workflow_resume["privateArtifactsPresent"])
        self.assertFalse(_find_private_artifact_keys(self.fixture))

    def test_allowed_resume_actions_are_read_only_or_reversible_previews(self) -> None:
        allowed_actions = self.fixture["allowedActions"]
        self.assertGreaterEqual(len(allowed_actions), 1)

        for action in allowed_actions:
            with self.subTest(action=action["id"]):
                self.assertIn(action["classification"], ALLOWED_CLASSIFICATIONS)
                self.assertNotIn(action["operation"], FORBIDDEN_ALLOWED_OPERATIONS)
                self.assertFalse(action["executesLiveAction"])
                self.assertFalse(action["mutatesWorkflow"])
                self.assertFalse(action["exactConfirmationRequired"])
                self.assertFalse(action["confirmationProvided"])
                self.assertFalse(action["refusedByDefault"])
                self.assert_source_evidence(action)

                if action["classification"] == "reversible_draft_preview":
                    self.assertTrue(action["previewOnly"])
                    self.assert_redacted_value(action["beforeValue"])
                    self.assert_redacted_value(action["afterValue"])
                    self.assert_selector_basis(action["selectorBasis"])

    def test_consequential_and_financial_resume_actions_are_refused_by_default(self) -> None:
        refused_actions = self.fixture["refusedActions"]
        refused_classifications = {action["classification"] for action in refused_actions}
        self.assertEqual(refused_classifications, REFUSED_CLASSIFICATIONS)

        for action in refused_actions:
            with self.subTest(action=action["id"]):
                self.assertIn(action["classification"], REFUSED_CLASSIFICATIONS)
                self.assertFalse(action["executesLiveAction"])
                self.assertFalse(action["mutatesWorkflow"])
                self.assertTrue(action["exactConfirmationRequired"])
                self.assertFalse(action["confirmationProvided"])
                self.assertTrue(action["refusedByDefault"])
                self.assertIn(action["id"], action["exactConfirmationPhrase"])
                self.assertGreaterEqual(len(action["exactConfirmationPhrase"].split()), 3)
                self.assertTrue(action["refusalReason"].strip())
                self.assert_source_evidence(action)

    def test_never_automate_actions_are_not_allowed_resume_actions(self) -> None:
        never_automate = set(self.fixture["neverAutomateActions"])
        allowed_operations = {action["operation"] for action in self.fixture["allowedActions"]}
        self.assertFalse(never_automate.intersection(allowed_operations))

    def assert_source_evidence(self, action: dict[str, Any]) -> None:
        known_evidence_ids = {evidence["id"] for evidence in self.fixture["sourceEvidence"]}
        self.assertGreaterEqual(len(action["sourceEvidenceIds"]), 1)
        self.assertTrue(set(action["sourceEvidenceIds"]).issubset(known_evidence_ids))

    def assert_selector_basis(self, selector_basis: dict[str, str]) -> None:
        self.assertEqual(selector_basis["role"], "textbox")
        self.assertTrue(selector_basis["accessibleName"].strip())
        self.assertTrue(selector_basis["labelText"].strip())
        self.assertTrue(selector_basis["nearbyHeading"].strip())

    def assert_redacted_value(self, value: str) -> None:
        self.assertTrue(value.startswith("REDACTED_"), value)


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)
    if not isinstance(data, dict):
        raise AssertionError("workflow resume fixture must be a JSON object")
    return data


def _find_private_artifact_keys(value: Any) -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in PRIVATE_ARTIFACT_KEYS:
                findings.append(key)
            findings.extend(_find_private_artifact_keys(child))
    elif isinstance(value, list):
        for child in value:
            findings.extend(_find_private_artifact_keys(child))
    return findings


if __name__ == "__main__":
    unittest.main()
