"""Focused validation for Urban Forestry permit requirement extraction fixtures."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_extraction"
    / "urban_forestry_permit_requirements.json"
)

EXPECTED_CATEGORIES = {
    "permit_type_selection",
    "property_and_tree_location",
    "tree_work_description",
    "site_plan_or_map",
    "supporting_documents",
    "fee_payment_checkpoint",
    "official_submission_certification",
}

EXPECTED_STOP_GATES = {
    "permit_type_selection": "read_only",
    "property_and_tree_location": "draft_edit",
    "tree_work_description": "draft_edit",
    "site_plan_or_map": "draft_edit",
    "supporting_documents": "draft_edit",
    "fee_payment_checkpoint": "financial",
    "official_submission_certification": "consequential",
}

ALLOWED_STOP_GATES = {"read_only", "draft_edit", "consequential", "financial"}


class UrbanForestryRequirementExtractionFixtureTest(unittest.TestCase):
    """Validate only the narrow fixture properties required by checkbox-106."""

    @classmethod
    def setUpClass(cls) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            cls.fixture = json.load(fixture_file)

    def test_fixture_covers_exactly_the_seven_urban_forestry_categories(self) -> None:
        requirements = self.fixture["requirements"]
        categories = {requirement["category"] for requirement in requirements}

        self.assertEqual(EXPECTED_CATEGORIES, categories)
        self.assertEqual(7, len(requirements))

    def test_every_requirement_uses_declared_source_evidence_ids(self) -> None:
        source_ids = {source["id"] for source in self.fixture["sources"]}

        self.assertGreaterEqual(len(source_ids), 3)
        for requirement in self.fixture["requirements"]:
            evidence_ids = requirement.get("sourceEvidenceIds", [])
            self.assertGreaterEqual(
                len(evidence_ids),
                1,
                f"{requirement['requirementId']} must cite at least one source evidence id",
            )
            self.assertTrue(
                set(evidence_ids).issubset(source_ids),
                f"{requirement['requirementId']} cites unknown source evidence ids",
            )

    def test_confidence_values_are_bounded(self) -> None:
        for requirement in self.fixture["requirements"]:
            confidence = requirement.get("confidence")
            self.assertIsInstance(confidence, float)
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)

    def test_requirement_ids_and_normalized_keys_are_deduplicated(self) -> None:
        requirements = self.fixture["requirements"]
        requirement_ids = [requirement["requirementId"] for requirement in requirements]
        normalized_keys = [requirement["normalizedKey"] for requirement in requirements]

        self.assertEqual(len(requirement_ids), len(set(requirement_ids)))
        self.assertEqual(len(normalized_keys), len(set(normalized_keys)))

    def test_stop_gate_classifications_are_explicit_and_expected(self) -> None:
        for requirement in self.fixture["requirements"]:
            category = requirement["category"]
            stop_gate = requirement.get("stopGateClassification")

            self.assertIn(stop_gate, ALLOWED_STOP_GATES)
            self.assertEqual(
                EXPECTED_STOP_GATES[category],
                stop_gate,
                f"{requirement['requirementId']} has an unexpected stop-gate classification",
            )


if __name__ == "__main__":
    unittest.main()
