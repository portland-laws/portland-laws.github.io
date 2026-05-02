"""Validate the minimal Urban Forestry requirement expected-output fixture."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_extraction"
    / "urban_forestry_expected_output.json"
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

PRIVATE_MARKERS = [
    "password",
    "credential",
    "auth_state",
    "bearer ",
    "access_token",
    "refresh_token",
    "sessionid",
    "trace.zip",
    "screen capture",
    "raw response body",
    "downloaded document",
    "ppd/data/private",
    "devhub private",
]


class UrbanForestryRequirementExpectedOutputTest(unittest.TestCase):
    def load_fixture(self) -> dict[str, Any]:
        with FIXTURE_PATH.open(encoding="utf-8") as handle:
            return json.load(handle)

    def test_fixture_has_exactly_seven_expected_categories(self) -> None:
        fixture = self.load_fixture()
        records = fixture.get("records")

        self.assertEqual(fixture.get("schema_version"), 1)
        self.assertEqual(fixture.get("permit_type"), "urban_forestry_permit")
        self.assertEqual(fixture.get("redaction_status"), "redacted_public_fixture")
        self.assertIsInstance(records, list)
        self.assertEqual(len(records), 7)
        self.assertEqual([record.get("category") for record in records], EXPECTED_CATEGORIES)

    def test_each_category_record_is_source_backed(self) -> None:
        fixture = self.load_fixture()

        seen_requirement_ids: set[str] = set()
        for record in fixture["records"]:
            requirement_id = record.get("requirement_id")
            self.assertIsInstance(requirement_id, str)
            self.assertTrue(requirement_id.startswith("uf-"))
            self.assertNotIn(requirement_id, seen_requirement_ids)
            seen_requirement_ids.add(requirement_id)

            for field in (
                "requirement_type",
                "subject",
                "action",
                "object",
                "expected_agent_behavior",
            ):
                self.assertIsInstance(record.get(field), str, field)
                self.assertTrue(record[field].strip(), field)

            self.assertIsInstance(record.get("conditions"), list)
            self.assertGreaterEqual(len(record["conditions"]), 1)
            self.assertIsInstance(record.get("redactions"), list)
            self.assertGreaterEqual(len(record["redactions"]), 1)
            self.assertTrue(all("redacted" in item for item in record["redactions"]))

            source_refs = record.get("source_refs")
            self.assertIsInstance(source_refs, list)
            self.assertGreaterEqual(len(source_refs), 1)
            for source in source_refs:
                self.assertTrue(source.get("source_id"))
                self.assertTrue(source.get("title"))
                self.assertTrue(source.get("url"))
                self.assertTrue(
                    source["url"].startswith("https://www.portland.gov/")
                    or source["url"].startswith("docs/PORTLAND_PPD_SCRAPING_AUTOMATION_LOGIC_PLAN.md")
                )
                self.assertTrue(source.get("captured_at", "").endswith("Z"))
                self.assertTrue(source.get("evidence_summary"))

    def test_fixture_is_redacted_and_contains_no_private_artifacts(self) -> None:
        fixture = self.load_fixture()
        serialized = json.dumps(fixture, sort_keys=True).lower()

        for marker in PRIVATE_MARKERS:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, serialized)

        self.assertNotIn("@", serialized)
        self.assertNotIn("private_value", serialized)
        self.assertNotIn("unredacted", serialized)

    def test_action_gates_stop_consequential_and_financial_actions(self) -> None:
        fixture = self.load_fixture()
        records_by_category = {record["category"]: record for record in fixture["records"]}

        payment = records_by_category["fee/payment checkpoints"]
        self.assertEqual(payment["requirement_type"], "action_gate")
        self.assertIn("exact user confirmation", payment["conditions"][1])
        self.assertIn("payment", payment["expected_agent_behavior"].lower())

        confirmation = records_by_category["explicit-confirmation gates"]
        self.assertEqual(confirmation["requirement_type"], "action_gate")
        confirmation_text = json.dumps(confirmation, sort_keys=True).lower()
        for action in ("submit", "certify", "cancel", "schedule", "upload", "pay"):
            with self.subTest(action=action):
                self.assertIn(action, confirmation_text)


if __name__ == "__main__":
    unittest.main()
