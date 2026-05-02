"""Validate the mocked DevHub correction upload review snapshot fixture."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub"
    / "correction_upload_review_snapshot.json"
)

REDACTED_TOKEN_PATTERN = re.compile(r"\[REDACTED_[A-Z0-9_]+\]")
PRIVATE_VALUE_PATTERNS = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b"),
    re.compile(r"\b\d{1,6}\s+[A-Za-z0-9.'-]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)\b"),
)
FORBIDDEN_KEYS = {
    "authorization",
    "authState",
    "auth_state",
    "cookie",
    "cookies",
    "password",
    "sessionCookie",
    "session_cookie",
    "storageState",
    "storage_state",
    "token",
    "tracePath",
    "trace_path",
    "screenshotPath",
    "screenshot_path",
    "downloadPath",
    "download_path",
    "rawBody",
    "raw_body",
}
FORBIDDEN_PATH_MARKERS = (
    "ppd/data/private",
    "ppd\\data\\private",
    "storage_state",
    "storage-state",
    "auth_state",
    "auth-state",
    "trace.zip",
    "playwright-report",
    "/screenshots/",
    "\\screenshots\\",
    "/downloads/",
    "\\downloads\\",
)


class DevhubCorrectionUploadReviewSnapshotTest(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_snapshot_records_review_state_without_live_automation(self) -> None:
        self.assertEqual(self.snapshot["schemaVersion"], 1)
        self.assertTrue(self.snapshot["fixtureOnly"])
        self.assertEqual(self.snapshot["source"]["workflow"], "correction_upload_review")
        self.assertEqual(self.snapshot["workflowState"]["stateId"], "correction_upload_review")
        self.assertFalse(self.snapshot["source"]["liveAutomationPerformed"])
        self.assertFalse(self.snapshot["draftState"]["officialUploadPerformed"])
        self.assertFalse(self.snapshot["draftState"]["certificationPerformed"])
        self.assertFalse(self.snapshot["draftState"]["submissionPerformed"])

    def test_upload_controls_include_accepted_file_hints_and_semantic_selectors(self) -> None:
        controls = self.snapshot["uploadControls"]
        self.assertGreaterEqual(len(controls), 3)
        required_controls = [control for control in controls if control["required"]]
        self.assertGreaterEqual(len(required_controls), 2)

        for control in controls:
            self.assertIn("controlId", control)
            self.assertIn("label", control)
            self.assertIn("accessibleName", control)
            self.assertIn("nearbyHeading", control)
            self.assertIn("selectorBasis", control)
            self.assertEqual(control["selectorBasis"]["role"], "button")
            self.assertIn(".pdf", control["acceptedFileHints"]["extensions"])
            self.assertIn("application/pdf", control["acceptedFileHints"]["mimeTypes"])
            self.assertNotEqual(control["acceptedFileHints"]["maxSizeHint"], "")

    def test_validation_messages_cover_required_files_pdf_type_draft_and_review(self) -> None:
        messages = self.snapshot["validationMessages"]
        message_ids = {message["messageId"] for message in messages}
        self.assertIn("missing_required_response_letter", message_ids)
        self.assertIn("pdf_required", message_ids)
        self.assertIn("draft_not_official", message_ids)
        self.assertIn("review_before_upload", message_ids)

        severities = {message["severity"] for message in messages}
        self.assertIn("error", severities)
        self.assertIn("warning", severities)
        self.assertIn("info", severities)

    def test_exact_confirmation_gates_block_official_upload_and_certification(self) -> None:
        gates = {gate["gateId"]: gate for gate in self.snapshot["confirmationGates"]}
        official_upload = gates["gate-official-upload"]
        certification = gates["gate-certification"]
        preview = gates["gate-preview-only"]

        self.assertFalse(preview["exactConfirmationRequired"])
        self.assertTrue(preview["allowedWithoutConfirmation"])

        for gate in (official_upload, certification):
            self.assertEqual(gate["classification"], "potentially_consequential")
            self.assertTrue(gate["required"])
            self.assertTrue(gate["exactConfirmationRequired"])
            self.assertTrue(gate["sessionSpecific"])
            self.assertTrue(gate["blockedWithoutExactConfirmation"])
            self.assertRegex(gate["exactConfirmationPhrase"], REDACTED_TOKEN_PATTERN)

        actions = {action["actionId"]: action for action in self.snapshot["workflowState"]["availableActions"]}
        self.assertFalse(actions["official_upload_corrections"]["enabled"])
        self.assertFalse(actions["certify_correction_upload"]["enabled"])
        self.assertEqual(actions["official_upload_corrections"]["blockedUntilGateId"], "gate-official-upload")
        self.assertEqual(actions["certify_correction_upload"]["blockedUntilGateId"], "gate-certification")

    def test_fixture_contains_only_redacted_private_values_and_no_private_artifacts(self) -> None:
        privacy = self.snapshot["privacy"]
        self.assertFalse(privacy["containsCredentials"])
        self.assertFalse(privacy["containsAuthState"])
        self.assertFalse(privacy["containsTrace"])
        self.assertFalse(privacy["containsScreenshot"])
        self.assertFalse(privacy["containsRawCrawlOutput"])
        self.assertFalse(privacy["containsDownloadedDocument"])
        self.assertFalse(privacy["containsPrivateDevhubSessionPath"])

        findings = list(_walk_forbidden_values(self.snapshot))
        self.assertEqual(findings, [])


def _walk_forbidden_values(value: Any, path: str = "$", key: str = "") -> list[str]:
    findings: list[str] = []
    if key in FORBIDDEN_KEYS:
        findings.append(f"{path}: forbidden key {key}")

    if isinstance(value, dict):
        for child_key, child_value in value.items():
            findings.extend(_walk_forbidden_values(child_value, f"{path}.{child_key}", str(child_key)))
        return findings

    if isinstance(value, list):
        for index, child_value in enumerate(value):
            findings.extend(_walk_forbidden_values(child_value, f"{path}[{index}]", key))
        return findings

    if isinstance(value, str):
        lowered = value.lower()
        for marker in FORBIDDEN_PATH_MARKERS:
            if marker.lower() in lowered:
                findings.append(f"{path}: forbidden artifact marker {marker}")
        unredacted = REDACTED_TOKEN_PATTERN.sub("", value)
        for pattern in PRIVATE_VALUE_PATTERNS:
            if pattern.search(unredacted):
                findings.append(f"{path}: possible unredacted private value")
    return findings


if __name__ == "__main__":
    unittest.main()
