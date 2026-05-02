"""Fixture-only schema validation for public PP&D process models.

These tests validate required process-model fields only. They do not crawl public
sites, open DevHub, authenticate, submit, upload, pay, or execute browser
automation.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "process-models" / "residential-building-permit-process.json"
REQUIRED_TOP_LEVEL_FIELDS = {
    "processId",
    "sourceEvidenceIds",
    "stages",
    "requiredInputs",
    "requiredDocuments",
    "stopGates",
    "lastReviewed",
}
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ProcessModelSchemaTest(unittest.TestCase):
    def test_public_permit_process_fixture_has_required_schema_fields(self) -> None:
        process = self._load_fixture()

        missing = REQUIRED_TOP_LEVEL_FIELDS.difference(process)
        self.assertEqual(set(), missing)
        self.assert_non_empty_string(process["processId"], "processId")
        self.assert_non_empty_string_list(process["sourceEvidenceIds"], "sourceEvidenceIds")
        self.assertRegex(process["lastReviewed"], ISO_DATE_RE)

        evidence_ids = set(process["sourceEvidenceIds"])
        self.assert_required_record_list(process["stages"], "stages", evidence_ids)
        self.assert_required_record_list(process["requiredInputs"], "requiredInputs", evidence_ids)
        self.assert_required_record_list(process["requiredDocuments"], "requiredDocuments", evidence_ids)
        self.assert_required_record_list(process["stopGates"], "stopGates", evidence_ids)

    def _load_fixture(self) -> dict[str, Any]:
        with FIXTURE_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertIsInstance(data, dict)
        return data

    def assert_required_record_list(self, value: Any, field: str, evidence_ids: set[str]) -> None:
        self.assertIsInstance(value, list, f"{field} must be a list")
        self.assertGreater(len(value), 0, f"{field} must not be empty")
        seen_ids: set[str] = set()
        for index, record in enumerate(value):
            label = f"{field}[{index}]"
            self.assertIsInstance(record, dict, f"{label} must be an object")
            self.assert_non_empty_string(record.get("id"), f"{label}.id")
            self.assertNotIn(record["id"], seen_ids, f"{label}.id must be unique")
            seen_ids.add(record["id"])
            self.assert_non_empty_string_list(record.get("sourceEvidenceIds"), f"{label}.sourceEvidenceIds")
            unknown = set(record["sourceEvidenceIds"]).difference(evidence_ids)
            self.assertEqual(set(), unknown, f"{label}.sourceEvidenceIds must cite top-level sourceEvidenceIds")

    def assert_non_empty_string(self, value: Any, field: str) -> None:
        self.assertIsInstance(value, str, f"{field} must be a string")
        self.assertTrue(value.strip(), f"{field} must not be blank")

    def assert_non_empty_string_list(self, value: Any, field: str) -> None:
        self.assertIsInstance(value, list, f"{field} must be a list")
        self.assertGreater(len(value), 0, f"{field} must not be empty")
        for index, item in enumerate(value):
            self.assert_non_empty_string(item, f"{field}[{index}]")


if __name__ == "__main__":
    unittest.main()
