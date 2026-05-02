"""Validate the minimal demolition permit requirement extraction fixture."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_extraction"
    / "demolition_permit_expected_output.json"
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

FORBIDDEN_PRIVACY_TERMS = (
    "password",
    "token",
    "cookie",
    "storage_state",
    "auth_state",
    "trace.zip",
    "screenshot",
    "rawHtml",
    "raw_html",
    "responseBody",
    "response_body",
)


class DemolitionPermitRequirementExpectedOutputTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)

    def test_has_exactly_seven_expected_category_records(self) -> None:
        records = self.fixture["categoryRecords"]
        self.assertEqual(7, len(records))
        self.assertEqual(EXPECTED_CATEGORIES, [record["category"] for record in records])
        self.assertEqual(len(EXPECTED_CATEGORIES), len({record["category"] for record in records}))

    def test_every_record_is_source_backed_and_redacted(self) -> None:
        for record in self.fixture["categoryRecords"]:
            self.assertTrue(record["recordId"].startswith("demo-"))
            self.assertIn(record["requirementType"], {"precondition", "dependency", "obligation", "action_gate"})
            self.assertTrue(record["expectedExtraction"].strip())
            self.assertTrue(record["redactedUserFacts"])
            self.assertTrue(all("" in fact for fact in record["redactedUserFacts"]))
            self.assertTrue(record["evidence"], record["recordId"])
            for evidence in record["evidence"]:
                self.assertTrue(evidence["url"].startswith("https://www.portland.gov/"), evidence)
                self.assertTrue(evidence["sourceTitle"].strip())
                self.assertTrue(evidence["anchor"].strip())
                self.assertTrue(evidence["supports"].strip())

    def test_fixture_contains_no_private_artifact_markers(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True)
        for forbidden in FORBIDDEN_PRIVACY_TERMS:
            self.assertNotIn(forbidden, serialized)
        self.assertTrue(self.fixture["privacy"]["redacted"])
        self.assertFalse(self.fixture["privacy"]["containsPrivateDevhubSession"])
        self.assertFalse(self.fixture["privacy"]["containsRawCrawlOutput"])
        self.assertFalse(self.fixture["privacy"]["containsDownloadedDocuments"])
        self.assertFalse(self.fixture["privacy"]["containsCredentials"])
        self.assertFalse(self.fixture["privacy"]["containsPersonalData"])


if __name__ == "__main__":
    unittest.main()
