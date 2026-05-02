"""Focused fixture validation for online trade permit purchase extraction.

This test intentionally checks only the selected daemon task surface:
seven fixture categories, source evidence IDs, confidence bounds,
deduplication, and explicit stop-gate classifications.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "online_trade_permit_purchase"
    / "requirements.json"
)

EXPECTED_CATEGORIES = {
    "devhub_account_access",
    "online_trade_permit_scope",
    "permit_type_selection",
    "project_and_property_facts",
    "contractor_or_owner_responsibility",
    "purchase_payment_stop_gate",
    "inspection_scheduling_stop_gate",
}

EXPECTED_STOP_GATES = {
    "purchase_payment_stop_gate": "financial",
    "inspection_scheduling_stop_gate": "consequential",
}


class OnlineTradePermitPurchaseExtractionFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)

    def test_fixture_has_exactly_the_seven_expected_categories(self) -> None:
        categories = [item.get("category") for item in self.fixture["requirements"]]

        self.assertEqual(EXPECTED_CATEGORIES, set(categories))
        self.assertEqual(7, len(categories))
        self.assertEqual(7, len(self.fixture.get("expected_categories", [])))
        self.assertEqual(EXPECTED_CATEGORIES, set(self.fixture["expected_categories"]))

    def test_every_requirement_uses_declared_source_evidence_ids(self) -> None:
        declared_evidence_ids = {
            source["evidence_id"] for source in self.fixture.get("sources", [])
        }
        self.assertTrue(declared_evidence_ids)

        for requirement in self.fixture["requirements"]:
            evidence_ids = requirement.get("evidence_ids", [])
            self.assertTrue(evidence_ids, requirement["requirement_id"])
            self.assertTrue(
                set(evidence_ids).issubset(declared_evidence_ids),
                requirement["requirement_id"],
            )

    def test_confidence_values_stay_within_fixture_bounds(self) -> None:
        bounds = self.fixture["confidence_bounds"]
        minimum = bounds["minimum"]
        maximum = bounds["maximum"]

        self.assertGreaterEqual(minimum, 0.0)
        self.assertLessEqual(maximum, 1.0)
        self.assertLessEqual(minimum, maximum)

        for requirement in self.fixture["requirements"]:
            confidence = requirement.get("confidence")
            self.assertIsInstance(confidence, (int, float), requirement["requirement_id"])
            self.assertGreaterEqual(confidence, minimum, requirement["requirement_id"])
            self.assertLessEqual(confidence, maximum, requirement["requirement_id"])

    def test_requirements_are_deduplicated_by_id_and_extraction_signature(self) -> None:
        seen_ids: set[str] = set()
        seen_signatures: set[tuple[str, str, str, tuple[str, ...]]] = set()

        for requirement in self.fixture["requirements"]:
            requirement_id = requirement["requirement_id"]
            signature = (
                requirement["category"],
                requirement["action"],
                requirement["object"],
                tuple(sorted(requirement["evidence_ids"])),
            )

            self.assertNotIn(requirement_id, seen_ids)
            self.assertNotIn(signature, seen_signatures)
            seen_ids.add(requirement_id)
            seen_signatures.add(signature)

    def test_stop_gate_classifications_are_explicit_and_only_on_stop_gate_categories(self) -> None:
        for requirement in self.fixture["requirements"]:
            category = requirement["category"]
            classification = requirement.get("stop_gate_classification")
            self.assertIn(
                classification,
                {"none", "consequential", "financial"},
                requirement["requirement_id"],
            )

            if category in EXPECTED_STOP_GATES:
                self.assertEqual(EXPECTED_STOP_GATES[category], classification)
                self.assertEqual("action_gate", requirement.get("type"))
            else:
                self.assertEqual("none", classification, requirement["requirement_id"])


if __name__ == "__main__":
    unittest.main()
