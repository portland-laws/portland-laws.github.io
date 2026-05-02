"""Validate the fixture-only redacted PP&D user-case-state contract."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "user_case_state" / "redacted_user_case_state.json"
REDACTED_TOKEN = "[REDACTED]"
FORBIDDEN_KEYS = {
    "accountId",
    "accountIdentifier",
    "authState",
    "cardNumber",
    "contentHash",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "downloadPath",
    "filePath",
    "localPath",
    "password",
    "payment",
    "paymentMethod",
    "rawDocument",
    "screenshot",
    "sessionState",
    "storageState",
    "trace",
    "tracePath",
    "uploadPath",
    "userId",
}
FORBIDDEN_VALUE_FRAGMENTS = (
    "ppd/data/private",
    "storage_state",
    "auth_state",
    "cookies.json",
    "trace.zip",
    "screenshots/",
    "downloaded_documents",
    "devhub/session",
    "card number",
)


class RedactedUserCaseStateContractTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)

    def test_contract_links_case_inventory_questions_files_status_and_evidence(self) -> None:
        evidence_ids = {item["evidenceId"] for item in self.fixture["sourceEvidence"]}
        fact_ids = {item["factId"] for item in self.fixture["projectFactInventory"]}
        requirement_ids = {item["requirementId"] for item in self.fixture["projectFactInventory"]}
        requirement_ids.update(item["requirementId"] for item in self.fixture["uploadedFilePlaceholders"])

        self.assertEqual(1, self.fixture["schemaVersion"])
        self.assertTrue(self.fixture["fixtureOnly"])
        self.assertTrue(self.fixture["redactionPolicy"]["usesSyntheticValuesOnly"])
        self.assertFalse(self.fixture["redactionPolicy"]["privateDocumentsStored"])
        self.assertFalse(self.fixture["redactionPolicy"]["liveDevHubStateStored"])
        self.assertEqual("draft_not_submitted", self.fixture["projectCase"]["draftStatus"]["state"])
        self.assertFalse(self.fixture["projectCase"]["draftStatus"]["submitted"])

        for evidence_id in self.fixture["projectCase"]["draftStatus"]["sourceEvidenceIds"]:
            self.assertIn(evidence_id, evidence_ids)

        for fact in self.fixture["projectFactInventory"]:
            self.assertIn(fact["valueState"], {"known_redacted", "missing", "unknown"})
            self.assertTrue(fact["sourceEvidenceIds"])
            for evidence_id in fact["sourceEvidenceIds"]:
                self.assertIn(evidence_id, evidence_ids)

        for question in self.fixture["missingInformationQuestions"]:
            self.assertIn(question["factId"], fact_ids)
            self.assertIn(question["requirementId"], requirement_ids)
            self.assertEqual("unanswered", question["answerState"])
            for evidence_id in question["sourceEvidenceIds"]:
                self.assertIn(evidence_id, evidence_ids)

        for placeholder in self.fixture["uploadedFilePlaceholders"]:
            self.assertIn(placeholder["requirementId"], requirement_ids)
            for evidence_id in placeholder["sourceEvidenceIds"]:
                self.assertIn(evidence_id, evidence_ids)

    def test_uploaded_file_placeholders_store_no_private_documents_or_paths(self) -> None:
        for placeholder in self.fixture["uploadedFilePlaceholders"]:
            self.assertFalse(placeholder["fileStored"])
            self.assertFalse(placeholder["contentHashStored"])
            self.assertTrue(placeholder["redactedDisplayName"].startswith("[REDACTED_"))
            self.assertNotIn("filePath", placeholder)
            self.assertNotIn("localPath", placeholder)
            self.assertNotIn("downloadPath", placeholder)
            self.assertNotIn("uploadPath", placeholder)
            self.assertNotIn("contentHash", placeholder)
            self.assertNotIn("rawDocument", placeholder)

    def test_fixture_does_not_store_private_devhub_state_or_sensitive_identifiers(self) -> None:
        findings: list[str] = []
        self._collect_forbidden_entries(self.fixture, "$", findings)
        self.assertEqual([], findings)

    def test_known_values_are_redacted_or_missing(self) -> None:
        for fact in self.fixture["projectFactInventory"]:
            if fact["valueState"] == "known_redacted":
                self.assertEqual(REDACTED_TOKEN, fact["redactedValue"])
            if fact["valueState"] == "missing":
                self.assertIsNone(fact["redactedValue"])

    def _collect_forbidden_entries(self, value: Any, path: str, findings: list[str]) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if key in FORBIDDEN_KEYS:
                    findings.append(child_path)
                self._collect_forbidden_entries(child, child_path, findings)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                self._collect_forbidden_entries(child, f"{path}[{index}]", findings)
            return
        if isinstance(value, str):
            normalized = value.lower()
            for fragment in FORBIDDEN_VALUE_FRAGMENTS:
                if fragment in normalized:
                    findings.append(path)


if __name__ == "__main__":
    unittest.main()
