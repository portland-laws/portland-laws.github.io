"""Validate the minimal solar permit requirement expected-output fixture."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_extraction"
    / "solar_permit_expected_output.json"
)

EXPECTED_CATEGORIES = [
    "eligibility",
    "plan-review applicability",
    "upload requirements",
    "fee/payment checkpoints",
    "corrections",
    "inspections",
    "explicit-confirmation gates",
]

ALLOWED_SOURCE_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}

PRIVATE_VALUE_PATTERNS = [
    re.compile(r"\b\d{3}[-. ]?\d{2}[-. ]?\d{4}\b"),
    re.compile(r"\b\d{16}\b"),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\bpassword\b", re.IGNORECASE),
    re.compile(r"\btoken\b", re.IGNORECASE),
    re.compile(r"\bauth[_ -]?state\b", re.IGNORECASE),
    re.compile(r"\bstorage[_ -]?state\b", re.IGNORECASE),
    re.compile(r"\bcookie\b", re.IGNORECASE),
    re.compile(r"\btrace\.zip\b", re.IGNORECASE),
    re.compile(r"\bscreenshot\b", re.IGNORECASE),
    re.compile(r"ppd/data/private", re.IGNORECASE),
    re.compile(r"ppd/data/raw", re.IGNORECASE),
]


class SolarRequirementExpectedOutputTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_has_exactly_seven_required_categories(self) -> None:
        records = self.fixture.get("records")
        self.assertIsInstance(records, list)
        self.assertEqual(7, len(records))
        self.assertEqual(EXPECTED_CATEGORIES, [record.get("category") for record in records])
        self.assertEqual(len(EXPECTED_CATEGORIES), len({record.get("category") for record in records}))

    def test_records_are_source_backed_and_redacted(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True)
        for pattern in PRIVATE_VALUE_PATTERNS:
            self.assertIsNone(pattern.search(serialized), pattern.pattern)

        seen_ids: set[str] = set()
        for record in self.fixture["records"]:
            requirement_id = record.get("requirement_id")
            self.assertIsInstance(requirement_id, str)
            self.assertTrue(requirement_id.startswith("solar-"))
            self.assertNotIn(requirement_id, seen_ids)
            seen_ids.add(requirement_id)

            self.assertIn(record.get("type"), {"obligation", "precondition", "dependency", "action_gate", "prohibition"})
            self.assertIn(record.get("subject"), {"applicant", "agent"})
            self.assertTrue(record.get("action"))
            self.assertTrue(record.get("object"))
            self.assertIsInstance(record.get("conditions"), list)
            self.assertGreaterEqual(len(record["conditions"]), 1)
            self.assertTrue(record.get("deadline_or_temporal_scope"))
            self.assertEqual("redacted", record.get("redaction_status"))
            self.assertIn(record.get("confidence"), {"low", "medium", "high"})
            self.assertEqual("fixture_expected_output", record.get("formalization_status"))

            evidence = record.get("evidence")
            self.assertIsInstance(evidence, list)
            self.assertGreaterEqual(len(evidence), 1)
            for source in evidence:
                self.assert_source_backed(source)

    def assert_source_backed(self, source: object) -> None:
        self.assertIsInstance(source, dict)
        source_url = str(source.get("source_url", ""))
        self.assertTrue(source_url)
        if source_url.startswith("docs/"):
            self.assertEqual("docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md", source_url)
        else:
            parsed = urlparse(source_url)
            self.assertEqual("https", parsed.scheme)
            self.assertIn(parsed.netloc, ALLOWED_SOURCE_HOSTS)
        self.assertTrue(source.get("source_title"))
        self.assertTrue(source.get("source_locator"))
        self.assertTrue(source.get("source_excerpt"))
        self.assertTrue(str(source.get("captured_at", "")).endswith("Z"))


if __name__ == "__main__":
    unittest.main()
