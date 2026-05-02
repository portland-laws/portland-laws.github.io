"""Validate the FCC wireless application expected-output fixture."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlparse


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "expected_outputs"
    / "fcc_wireless_application_requirements.json"
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

ALLOWED_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}

FORBIDDEN_KEYS = {
    "body",
    "raw_body",
    "rawBody",
    "response_body",
    "responseBody",
    "html",
    "screenshot",
    "trace",
    "cookie",
    "password",
    "token",
    "secret",
}

FORBIDDEN_VALUE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"BEGIN PRIVATE KEY",
        r"sk-[a-z0-9]",
        r"password\s*[:=]",
        r"cookie\s*[:=]",
        r"bearer\s+[a-z0-9._-]+",
        r"\b\d{3}-\d{2}-\d{4}\b",
        r"\b(?:\d[ -]*?){13,19}\b",
        r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
    )
]


class FccWirelessApplicationExpectedOutputTest(unittest.TestCase):
    maxDiff = None

    def load_fixture(self):
        with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_fixture_has_exactly_seven_ordered_categories(self):
        fixture = self.load_fixture()
        records = fixture["records"]

        self.assertEqual(7, len(records))
        self.assertEqual(EXPECTED_CATEGORIES, [record["category"] for record in records])
        self.assertEqual(len(EXPECTED_CATEGORIES), len({record["category"] for record in records}))

    def test_records_are_source_backed(self):
        fixture = self.load_fixture()

        for record in fixture["records"]:
            with self.subTest(category=record["category"]):
                self.assertTrue(record["requirement_id"].startswith("fcc-wireless-"))
                self.assertIn(record["type"], {"action_gate", "dependency", "obligation", "precondition"})
                self.assertTrue(record["requirement_text"].strip())
                self.assertGreaterEqual(len(record.get("evidence", [])), 1)
                for evidence in record["evidence"]:
                    parsed = urlparse(evidence["source_url"])
                    self.assertEqual("https", parsed.scheme)
                    self.assertIn(parsed.netloc, ALLOWED_HOSTS)
                    self.assertTrue(evidence["source_title"].strip())
                    self.assertTrue(evidence["source_detail"].strip())
                    self.assertRegex(evidence["captured_at"], r"^2026-05-01T00:00:00Z$")

    def test_fixture_is_redacted_and_commit_safe(self):
        fixture = self.load_fixture()
        self.assertEqual(
            "No applicant, property, account, contact, project, credential, browser, payment-card, or portal-state values are present.",
            fixture["redaction_policy"],
        )

        self.assert_no_forbidden_keys_or_values(fixture)
        for record in fixture["records"]:
            with self.subTest(category=record["category"]):
                self.assertGreaterEqual(len(record.get("redacted_values", [])), 1)
                for value in record["redacted_values"]:
                    self.assertRegex(value, r"^[a-z0-9_]+$")

    def test_explicit_confirmation_gate_stops_consequential_actions(self):
        fixture = self.load_fixture()
        gate = fixture["records"][-1]

        self.assertEqual("explicit-confirmation gates", gate["category"])
        self.assertEqual("action_gate", gate["type"])
        self.assertEqual("agent", gate["subject"])
        for required_phrase in (
            "official submission",
            "certification",
            "correction upload",
            "inspection scheduling",
            "cancellation",
            "payment",
            "exact approval",
        ):
            self.assertIn(required_phrase, gate["requirement_text"])

    def assert_no_forbidden_keys_or_values(self, value, path="fixture"):
        if isinstance(value, dict):
            for key, item in value.items():
                self.assertNotIn(key, FORBIDDEN_KEYS, f"forbidden key at {path}.{key}")
                self.assert_no_forbidden_keys_or_values(item, f"{path}.{key}")
            return

        if isinstance(value, list):
            for index, item in enumerate(value):
                self.assert_no_forbidden_keys_or_values(item, f"{path}[{index}]")
            return

        if isinstance(value, str):
            for pattern in FORBIDDEN_VALUE_PATTERNS:
                self.assertIsNone(pattern.search(value), f"forbidden private-looking value at {path}")


if __name__ == "__main__":
    unittest.main()
