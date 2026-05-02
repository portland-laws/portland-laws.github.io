"""Validate the mocked DevHub demolition draft-review workflow snapshot."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "demolition_application_draft_review_snapshot.json"
REDACTED_PATTERN = re.compile(r"^\[REDACTED_[A-Z0-9_]+\]$")
FORBIDDEN_KEYS = {
    "authorization",
    "auth_state",
    "body",
    "cookie",
    "credentials",
    "download_path",
    "html",
    "password",
    "raw_body",
    "raw_html",
    "screenshot_path",
    "storage_state",
    "token",
    "trace_path",
    "username",
}
FORBIDDEN_VALUE_FRAGMENTS = (
    "ppd/data/private",
    "storage_state",
    "auth_state",
    "trace.zip",
    "/traces/",
    "/screenshots/",
    "/downloads/",
    "BEGIN PRIVATE",
)


class DevHubDemolitionDraftReviewSnapshotTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
            self.snapshot: dict[str, Any] = json.load(handle)

    def test_snapshot_identity_and_privacy_flags(self) -> None:
        self.assertEqual(self.snapshot["workflow"], "demolition_application_draft_review")
        self.assertEqual(self.snapshot["capturedMode"], "mocked_fixture_only")
        privacy = self.snapshot["privacy"]
        for key in (
            "containsCredentials",
            "containsAuthState",
            "containsTrace",
            "containsScreenshot",
            "containsRawCrawlOutput",
            "containsDownloadedDocuments",
        ):
            self.assertIs(privacy[key], False, key)

    def test_semantic_selectors_are_accessibility_first(self) -> None:
        selectors = self.snapshot["semanticSelectors"]
        self.assertGreaterEqual(len(selectors), 5)
        for selector in selectors:
            self.assertTrue(selector["role"].strip())
            self.assertTrue(selector["accessibleName"].strip())
            self.assertTrue(selector["labelText"].strip())
            self.assertTrue(selector["nearbyHeading"].strip())
            self.assertTrue(selector["urlState"].strip())
            self.assertIsNone(selector["fallbackCss"])

    def test_required_fields_record_redacted_values_and_validation(self) -> None:
        fields = {field["fieldId"]: field for field in self.snapshot["requiredFields"]}
        for field_id in (
            "project_address",
            "property_owner",
            "applicant_contact",
            "demolition_scope",
            "structure_type",
            "contractor_license",
        ):
            self.assertIn(field_id, fields)
            field = fields[field_id]
            self.assertTrue(field["required"])
            self.assertIn("semanticSelector", field)
            self.assertRegex(field["redactedValue"], REDACTED_PATTERN)
        self.assertTrue(fields["applicant_contact"]["validationMessages"])
        self.assertTrue(fields["contractor_license"]["validationMessages"])

    def test_upload_controls_and_messages_are_recorded_without_documents(self) -> None:
        controls = {control["controlId"]: control for control in self.snapshot["uploadControls"]}
        self.assertIn("demolition_application_pdf", controls)
        self.assertIn("site_plan_pdf", controls)
        required_upload = controls["demolition_application_pdf"]
        self.assertTrue(required_upload["required"])
        self.assertEqual(required_upload["acceptedFileTypes"], ["application/pdf"])
        self.assertRegex(required_upload["redactedFileName"], REDACTED_PATTERN)
        self.assertTrue(required_upload["validationMessages"])
        blocking = [message for message in self.snapshot["validationMessages"] if message["blocksSubmission"]]
        self.assertGreaterEqual(len(blocking), 4)

    def test_save_for_later_and_navigation_edges_are_explicit(self) -> None:
        save_for_later = self.snapshot["state"]["saveForLater"]
        self.assertTrue(save_for_later["available"])
        self.assertEqual(save_for_later["resultingState"], "draft_saved_not_submitted")
        self.assertEqual(save_for_later["storedValues"], "redacted")
        edges = {edge["edgeId"]: edge for edge in self.snapshot["navigationEdges"]}
        self.assertEqual(edges["review_save_for_later"]["classification"], "reversible_draft_edit")
        self.assertFalse(edges["review_save_for_later"]["confirmationRequired"])
        self.assertTrue(edges["review_submit_application"]["confirmationRequired"])
        self.assertTrue(edges["review_submit_application"]["blockedUntilValidationClears"])

    def test_confirmation_gates_require_exact_session_specific_confirmation(self) -> None:
        gates = {gate["gateId"]: gate for gate in self.snapshot["confirmationGates"]}
        for gate_id in (
            "certify_demolition_application",
            "official_upload_demolition_application_pdf",
            "submit_demolition_application",
        ):
            self.assertIn(gate_id, gates)
            gate = gates[gate_id]
            self.assertEqual(gate["classification"], "potentially_consequential")
            self.assertIs(gate["agentMayProceedWithoutExactConfirmation"], False)
            self.assertIn("this DevHub", gate["exactRequiredUserConfirmation"])
            self.assertTrue(gate["semanticSelector"].startswith("getBy"))

    def test_fixture_contains_no_private_artifact_markers_or_unredacted_secret_keys(self) -> None:
        findings: list[str] = []
        self._walk(self.snapshot, "$", findings)
        self.assertEqual(findings, [])

    def _walk(self, value: Any, path: str, findings: list[str]) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized_key = str(key).lower().replace("-", "_")
                if normalized_key in FORBIDDEN_KEYS:
                    findings.append(f"{path}.{key}: forbidden key")
                self._walk(child, f"{path}.{key}", findings)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                self._walk(child, f"{path}[{index}]", findings)
            return
        if isinstance(value, str):
            lowered = value.lower()
            for fragment in FORBIDDEN_VALUE_FRAGMENTS:
                if fragment.lower() in lowered:
                    findings.append(f"{path}: forbidden value fragment {fragment}")


if __name__ == "__main__":
    unittest.main()
