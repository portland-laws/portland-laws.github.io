from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub"
    / "upload_readiness_checklist.json"
)

FORBIDDEN_ACTIONS = {
    "upload_official_document",
    "submit_application",
    "certify_statement",
    "pay_fee",
    "cancel_request",
    "schedule_inspection",
    "captcha",
    "mfa",
    "account_creation",
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


class DevhubUploadReadinessChecklistTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_boundary_is_fixture_only_and_refuses_official_upload_surface(self) -> None:
        boundary = self.fixture["boundary"]
        self.assertEqual("devhub_upload_readiness_checklist", self.fixture["fixtureKind"])
        self.assertTrue(boundary["fixtureOnly"])
        self.assertFalse(boundary["liveDevhubAccess"])
        self.assertFalse(boundary["browserLaunchRequested"])
        self.assertFalse(boundary["officialUploadAllowed"])
        self.assertFalse(boundary["officialSubmissionAllowed"])
        self.assertFalse(boundary["storesPrivateFileContents"])

    def test_document_placeholders_link_public_evidence_to_redacted_inventory(self) -> None:
        evidence_ids = {item["sourceEvidenceId"] for item in self.fixture["publicEvidence"]}
        inventory_ids = {item["fileInventoryId"] for item in self.fixture["redactedUserFileInventory"]}

        for item in self.fixture["publicEvidence"]:
            self.assertTrue(item["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertTrue(item["citation"]["locator"])
            self.assertTrue(item["citation"]["paraphrase"])

        for placeholder in self.fixture["requiredDocumentPlaceholders"]:
            self.assertTrue(set(placeholder["sourceEvidenceIds"]).issubset(evidence_ids))
            self.assertIn(placeholder["linkedFileInventoryId"], inventory_ids)
            self.assertIn(placeholder["readiness"], {"metadata_present_needs_human_review", "missing_ask_user"})

        for file_item in self.fixture["redactedUserFileInventory"]:
            self.assertTrue(file_item["metadataOnly"])
            self.assertFalse(file_item["byteLengthStored"])
            self.assertFalse(file_item["contentStored"])
            self.assertTrue(str(file_item["redactedFilename"]).startswith("[REDACTED_"))

    def test_stop_gates_refuse_upload_submission_payment_and_account_actions(self) -> None:
        official_gate = next(gate for gate in self.fixture["stopGates"] if gate["gateId"] == "gate-official-upload-actions")
        self.assertEqual("refuse", official_gate["defaultOutcome"])
        self.assertTrue(official_gate["requiresExactConfirmation"])
        self.assertFalse(official_gate["exactConfirmationPresent"])
        self.assertTrue(FORBIDDEN_ACTIONS.issubset(set(official_gate["blockedActions"])))

        missing_gate = next(gate for gate in self.fixture["stopGates"] if gate["gateId"] == "gate-missing-required-document")
        self.assertEqual("ask_user", missing_gate["defaultOutcome"])
        self.assertTrue(missing_gate["blocksOfficialUpload"])

    def test_planner_outcome_and_private_artifacts_fail_closed(self) -> None:
        outcome = self.fixture["plannerOutcome"]
        self.assertEqual("ask_user_for_missing_document_metadata", outcome["nextAgentAction"])
        self.assertFalse(outcome["draftPreviewAllowed"])
        self.assertFalse(outcome["officialUploadAllowed"])
        self.assertFalse(outcome["officialSubmissionAllowed"])
        self.assertTrue(outcome["humanReviewRequiredBeforeUpload"])

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)
        self.assertEqual([], find_unredacted_values(self.fixture))


def find_unredacted_values(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in {"rawvalue", "privatevalue", "knownvalue", "filecontents"}:
                findings.append(f"{path}.{key}")
            findings.extend(find_unredacted_values(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_unredacted_values(child, f"{path}[{index}]"))
    elif isinstance(value, str) and "real user" in value.lower():
        findings.append(path)
    return findings


if __name__ == "__main__":
    unittest.main()
