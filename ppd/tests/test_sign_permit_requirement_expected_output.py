"""Validate the minimal sign permit requirement extraction expected-output fixture."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "sign_permit_requirement_extraction"
    / "expected_output.json"
)

EXPECTED_CATEGORIES = [
    "eligibility",
    "plan-review applicability",
    "upload requirements",
    "fee/payment checkpoints",
    "corrections",
    "inspections/finalization",
    "explicit-confirmation gates",
]

PRIVATE_VALUE_PATTERNS = (
    re.compile(r"\b\d{3}[-. ]\d{2}[-. ]\d{4}\b"),
    re.compile(r"\b\d{16}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b(?:password|credential|auth[_-]?state|storage[_-]?state|session[_-]?cookie|bearer\s+[a-z0-9._-]+)\b", re.IGNORECASE),
)

FORBIDDEN_STRINGS = (
    "ppd/data/private",
    "ppd/data/raw",
    "trace.zip",
    "playwright-report",
    "screenshot.png",
    "cookies.json",
    "localstorage.json",
)


class SignPermitRequirementExpectedOutputTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)

    def test_fixture_has_exactly_seven_expected_categories(self) -> None:
        records = self.fixture["category_records"]
        self.assertEqual(7, len(records))
        self.assertEqual(EXPECTED_CATEGORIES, [record["category"] for record in records])

    def test_each_record_is_source_backed_and_redacted(self) -> None:
        for record in self.fixture["category_records"]:
            with self.subTest(category=record["category"]):
                self.assertTrue(record["requirement_id"].startswith("sign-permit-"))
                self.assertEqual("redacted_public_fixture", record["redaction_status"])
                self.assertGreaterEqual(len(record.get("conditions", [])), 1)
                self.assertTrue(record.get("expected_agent_output"))
                evidence_items = record.get("evidence", [])
                self.assertGreaterEqual(len(evidence_items), 1)
                for evidence in evidence_items:
                    self.assertTrue(evidence["source_url"].startswith("https://www.portland.gov/ppd/"))
                    self.assertTrue(evidence["source_title"])
                    self.assertTrue(evidence["source_anchor"])
                    self.assertTrue(evidence["evidence_note"])

    def test_fixture_contains_no_private_values_or_artifact_paths(self) -> None:
        fixture_text = json.dumps(self.fixture, sort_keys=True)
        lowered = fixture_text.lower()
        for forbidden in FORBIDDEN_STRINGS:
            self.assertNotIn(forbidden, lowered)
        for pattern in PRIVATE_VALUE_PATTERNS:
            self.assertIsNone(pattern.search(fixture_text))


if __name__ == "__main__":
    unittest.main()
