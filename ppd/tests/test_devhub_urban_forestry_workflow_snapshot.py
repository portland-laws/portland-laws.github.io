"""Validate the Urban Forestry DevHub draft-review workflow fixture."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub_workflow_snapshots"
    / "urban_forestry_application_draft_review.json"
)

PRIVATE_VALUE_PATTERNS = (
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}", re.IGNORECASE),
    re.compile(r"\\b\\d{3}[-.]\\d{3}[-.]\\d{4}\\b"),
    re.compile(r"\\b\\d{1,6}\\s+[A-Za-z0-9 .'-]+\\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)\\b", re.IGNORECASE),
)

FORBIDDEN_KEYS = {
    "authorization",
    "authState",
    "body",
    "cookies",
    "credential",
    "documentPath",
    "downloadPath",
    "filePath",
    "html",
    "localPath",
    "password",
    "rawBody",
    "rawHtml",
    "screenshotPath",
    "sessionPath",
    "storageState",
    "token",
    "tracePath",
    "username",
}


class UrbanForestryWorkflowSnapshotTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)

    def test_fixture_identifies_mocked_urban_forestry_draft_review(self) -> None:
        workflow = self.fixture["workflow"]
        self.assertEqual(workflow["id"], "urban-forestry-application-draft-review")
        self.assertEqual(workflow["permitType"], "Urban Forestry permit")
        self.assertEqual(workflow["stateId"], "draft-review")
        self.assertFalse(workflow["privateSession"])
        self.assertFalse(workflow["liveAutomation"])
        self.assertFalse(workflow["rawCrawlOutput"])

    def test_semantic_selectors_do_not_depend_on_css_or_xpath(self) -> None:
        selectors = self.fixture["semanticSelectors"]
        self.assertGreaterEqual(len(selectors), 4)
        for selector in selectors:
            self.assertTrue(selector["selectorId"])
            self.assertTrue(selector["role"])
            self.assertTrue(selector["accessibleName"])
            self.assertTrue(selector["labelText"])
            self.assertTrue(selector["nearbyHeading"])
            self.assertTrue(selector["urlState"])
            self.assertIsNone(selector["fallbackCss"])
            self.assertIsNone(selector["fallbackXpath"])

    def test_required_fields_are_redacted_and_validation_backed(self) -> None:
        fields = self.fixture["requiredFields"]
        required_field_ids = {field["fieldId"] for field in fields if field["required"]}
        self.assertEqual(
            required_field_ids,
            {
                "property-site-address",
                "property-account-id",
                "applicant-contact-name",
                "applicant-contact-email",
                "tree-work-description",
                "tree-location-description",
            },
        )
        for field in fields:
            self.assertTrue(field["currentValue"].startswith("[REDACTED:"), field["fieldId"])
            self.assertTrue(field["validationMessage"], field["fieldId"])
            self.assertTrue(field["accessibleName"], field["fieldId"])
            self.assertTrue(field["labelText"], field["fieldId"])

    def test_upload_controls_capture_hints_without_private_document_paths(self) -> None:
        controls = self.fixture["uploadControls"]
        self.assertEqual({control["controlId"] for control in controls}, {"site-plan-upload", "tree-photos-upload"})
        required_controls = [control for control in controls if control["required"]]
        self.assertEqual([control["controlId"] for control in required_controls], ["site-plan-upload"])
        for control in controls:
            self.assertTrue(control["acceptedFileTypes"])
            self.assertTrue(control["fileSizeHint"])
            self.assertTrue(control["validationMessages"])
            self.assertTrue(control["currentFileName"].startswith("[REDACTED:"))
            self.assertFalse(control["officialUploadAction"])
            self.assertNotIn("documentPath", control)
            self.assertNotIn("localPath", control)

    def test_save_for_later_is_reversible_draft_state(self) -> None:
        save_state = self.fixture["saveForLaterState"]
        self.assertTrue(save_state["available"])
        self.assertEqual(save_state["classification"], "reversible_draft_edit")
        self.assertEqual(save_state["resumeStateId"], "urban-forestry-draft-resume")
        self.assertEqual(save_state["savedValues"], "redacted-only")
        self.assertFalse(save_state["confirmationRequired"])

    def test_confirmation_gates_are_exact_and_blocking(self) -> None:
        gates = {gate["gateId"]: gate for gate in self.fixture["confirmationGates"]}
        self.assertEqual(set(gates), {"urban-forestry-certification-acknowledgment", "urban-forestry-submit-application"})
        for gate in gates.values():
            self.assertEqual(gate["classification"], "potentially_consequential")
            self.assertTrue(gate["exactRequiredUserConfirmation"].startswith("I confirm "))
            self.assertTrue(gate["mustStopWithoutExactConfirmation"])
            self.assertFalse(gate["automationMayProceedWithoutConfirmation"])

    def test_navigation_edges_reference_confirmation_gate_for_submission(self) -> None:
        edges = self.fixture["navigationEdges"]
        submission_edges = [edge for edge in edges if edge["action"] == "submit_application"]
        self.assertEqual(len(submission_edges), 1)
        self.assertEqual(submission_edges[0]["classification"], "potentially_consequential")
        self.assertEqual(submission_edges[0]["requiresExactConfirmationGateId"], "urban-forestry-submit-application")

    def test_fixture_contains_only_redacted_values_and_no_private_artifacts(self) -> None:
        privacy = self.fixture["privacy"]
        self.assertTrue(privacy["redactedValuesOnly"])
        for flag in (
            "containsCredentials",
            "containsAuthState",
            "containsTrace",
            "containsScreenshot",
            "containsRawCrawlOutput",
            "containsDownloadedDocuments",
            "containsPrivateDevHubSessionPath",
        ):
            self.assertFalse(privacy[flag], flag)

        findings: list[str] = []
        self._walk(self.fixture, findings=findings)
        self.assertEqual(findings, [])

    def _walk(self, value: Any, *, path: str = "$", findings: list[str]) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in FORBIDDEN_KEYS:
                    findings.append(f"{path}.{key}: forbidden key")
                self._walk(child, path=f"{path}.{key}", findings=findings)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                self._walk(child, path=f"{path}[{index}]", findings=findings)
            return
        if isinstance(value, str):
            for pattern in PRIVATE_VALUE_PATTERNS:
                if pattern.search(value):
                    findings.append(f"{path}: private-looking value {value!r}")


if __name__ == "__main__":
    unittest.main()
