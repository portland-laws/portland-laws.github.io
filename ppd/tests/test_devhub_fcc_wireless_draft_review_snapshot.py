"""Validate the mocked DevHub FCC wireless draft-review snapshot fixture."""

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
    / "fcc_wireless_application_draft_review_snapshot.json"
)

FORBIDDEN_KEYS = {
    "authorization",
    "authState",
    "auth_state",
    "body",
    "content",
    "cookie",
    "cookies",
    "html",
    "password",
    "rawBody",
    "raw_body",
    "rawHtml",
    "raw_html",
    "screenshot",
    "storageState",
    "storage_state",
    "token",
    "trace",
    "username",
}

FORBIDDEN_TEXT_PATTERNS = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b"),
    re.compile(r"\b\d{1,6}\s+(?:SW|SE|NE|NW|N)\s+[A-Za-z0-9 .]+\b"),
    re.compile(r"ppd/data/private", re.IGNORECASE),
    re.compile(r"storage[_-]?state", re.IGNORECASE),
    re.compile(r"trace\.zip", re.IGNORECASE),
    re.compile(r"screenshots?[/\\]", re.IGNORECASE),
    re.compile(r"downloads?[/\\]", re.IGNORECASE),
)


class DevhubFccWirelessDraftReviewSnapshotTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.snapshot = self.fixture["snapshot"]

    def test_fixture_is_mocked_and_redacted(self) -> None:
        self.assertEqual(self.fixture["captureMode"], "mocked_fixture_only")
        self.assertFalse(self.fixture["urlState"]["containsPrivateSessionPath"])
        for key, value in self.fixture["privacyAssertions"].items():
            self.assertFalse(value, key)
        self.assertEqual([], list(_privacy_findings(self.fixture)))

    def test_records_semantic_selectors_for_review_state(self) -> None:
        selectors = self.snapshot["semanticSelectors"]
        self.assertGreaterEqual(len(selectors), 3)
        for selector in selectors:
            self.assertIn(selector["role"], {"button", "heading", "textbox", "combobox"})
            self.assertTrue(selector["accessibleName"])
            self.assertTrue(selector["labelText"])
            self.assertTrue(selector["nearbyHeading"])
            self.assertEqual(selector["state"], "devhub:fcc-wireless-application:draft-review")
            self.assertIsNone(selector["fallbackCss"])
            self.assertIsNone(selector["fallbackXPath"])

    def test_required_fields_are_present_and_redacted(self) -> None:
        fields = self.snapshot["requiredFields"]
        field_ids = {field["id"] for field in fields}
        self.assertEqual(
            {
                "project-site-address",
                "property-id",
                "applicant-contact",
                "wireless-facility-type",
                "project-description",
            },
            field_ids,
        )
        for field in fields:
            self.assertTrue(field["required"])
            self.assertRegex(field["value"], r"^\[REDACTED_[A-Z0-9_]+\]$")
            self.assert_selector_basis(field["selectorBasis"])

    def test_upload_controls_and_validation_messages_are_explicit(self) -> None:
        uploads = self.snapshot["uploadControls"]
        upload_ids = {upload["id"] for upload in uploads}
        self.assertEqual(
            {"application-packet-upload", "site-plan-upload", "supporting-documents-upload"},
            upload_ids,
        )
        required_uploads = {upload["id"] for upload in uploads if upload["required"]}
        self.assertEqual({"application-packet-upload", "site-plan-upload"}, required_uploads)
        for upload in uploads:
            self.assertEqual(upload["acceptedFileTypes"], ["application/pdf"])
            self.assertRegex(upload["fileSizeHint"], r"^\[REDACTED_[A-Z0-9_]+\]$")
            self.assertRegex(upload["fileNamingHint"], r"^\[REDACTED_[A-Z0-9_]+\]$")
            self.assert_selector_basis(upload["selectorBasis"])
        messages = self.snapshot["validationMessages"]
        self.assertTrue(any(message["severity"] == "error" for message in messages))
        self.assertTrue(any(message["fieldOrControlId"] == "site-plan-upload" for message in messages))

    def test_save_for_later_state_and_navigation_edges_are_recorded(self) -> None:
        draft_status = self.snapshot["draftStatus"]
        self.assertEqual(draft_status["state"], "saved_for_later_available")
        self.assertEqual(draft_status["resumeState"], "devhub:fcc-wireless-application:draft-review")
        edge_by_id = {edge["id"]: edge for edge in self.snapshot["navigationEdges"]}
        self.assertEqual(edge_by_id["save-for-later"]["classification"], "reversible_draft_edit")
        self.assertFalse(edge_by_id["save-for-later"]["requiresExactConfirmation"])
        self.assertEqual(edge_by_id["continue-to-certification"]["classification"], "potentially_consequential")
        self.assertTrue(edge_by_id["continue-to-certification"]["requiresExactConfirmation"])

    def test_exact_confirmation_gates_block_consequential_and_financial_actions(self) -> None:
        gates = {gate["action"]: gate for gate in self.snapshot["confirmationGates"]}
        self.assertEqual({"continue_to_certification", "submit_application", "pay_fees"}, set(gates))
        for action in ("continue_to_certification", "submit_application", "pay_fees"):
            gate = gates[action]
            self.assertFalse(gate["mayExecuteWithoutConfirmation"])
            self.assertIn("this DevHub session", gate["requiredExactConfirmation"])
            self.assertGreaterEqual(len(gate["requiredExactConfirmation"].split()), 8)
        self.assertEqual(gates["pay_fees"]["classification"], "financial")

    def assert_selector_basis(self, selector_basis: dict[str, Any]) -> None:
        self.assertTrue(selector_basis["accessibleName"])
        self.assertTrue(selector_basis["labelText"])
        self.assertTrue(selector_basis["nearbyHeading"])
        self.assertEqual(selector_basis["state"], "devhub:fcc-wireless-application:draft-review")


def _privacy_findings(value: Any, path: str = "$", key: str | None = None) -> list[str]:
    findings: list[str] = []
    if key in FORBIDDEN_KEYS:
        findings.append(f"{path}: forbidden key {key}")
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            findings.extend(_privacy_findings(child_value, f"{path}.{child_key}", str(child_key)))
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            findings.extend(_privacy_findings(child_value, f"{path}[{index}]", key))
    elif isinstance(value, str):
        for pattern in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                findings.append(f"{path}: forbidden private value pattern {pattern.pattern}")
    return findings


if __name__ == "__main__":
    unittest.main()
