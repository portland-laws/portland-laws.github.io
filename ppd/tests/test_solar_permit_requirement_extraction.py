"""Focused validation for solar permit requirement extraction fixtures."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "solar_permit_requirement_extraction"
    / "seven_categories.json"
)

EXPECTED_CATEGORY_EVIDENCE_IDS = {
    "eligibility": {"solar-public-guide"},
    "required_facts": {"solar-public-guide", "solar-devhub-application-guide"},
    "required_documents": {"solar-public-guide", "solar-single-pdf-process"},
    "file_rules": {"solar-single-pdf-process"},
    "fee_payment_gates": {"solar-fee-payment-guide", "solar-devhub-application-guide"},
    "correction_upload_gates": {"solar-correction-upload-guide"},
    "inspection_scheduling_gates": {"solar-inspection-guide"},
}

EXPECTED_STOP_GATE_CLASSIFICATIONS = {
    "solar-fee-payment-stop-gate": "financial",
    "solar-correction-upload-stop-gate": "consequential",
    "solar-inspection-scheduling-stop-gate": "consequential",
}


class SolarPermitRequirementExtractionFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)

    def test_fixture_contains_only_the_seven_expected_categories(self) -> None:
        requirements = self.fixture["requirements"]
        categories = [requirement["category"] for requirement in requirements]

        self.assertEqual(set(EXPECTED_CATEGORY_EVIDENCE_IDS), set(categories))
        self.assertEqual(len(EXPECTED_CATEGORY_EVIDENCE_IDS), len(categories))

    def test_each_category_uses_the_expected_source_evidence_ids(self) -> None:
        available_evidence_ids = {
            evidence["id"] for evidence in self.fixture["sourceEvidence"]
        }

        for requirement in self.fixture["requirements"]:
            category = requirement["category"]
            expected_evidence_ids = EXPECTED_CATEGORY_EVIDENCE_IDS[category]
            actual_evidence_ids = set(requirement["evidenceIds"])

            self.assertEqual(expected_evidence_ids, actual_evidence_ids, category)
            self.assertTrue(
                actual_evidence_ids.issubset(available_evidence_ids),
                category,
            )

    def test_confidence_values_are_bounded_probabilities(self) -> None:
        for requirement in self.fixture["requirements"]:
            confidence = requirement["confidence"]

            self.assertIsInstance(confidence, (int, float), requirement["id"])
            self.assertGreaterEqual(confidence, 0.0, requirement["id"])
            self.assertLessEqual(confidence, 1.0, requirement["id"])

    def test_stop_gates_have_explicit_classifications_only_where_expected(self) -> None:
        requirements_by_id = {
            requirement["id"]: requirement
            for requirement in self.fixture["requirements"]
        }

        for requirement_id, expected_classification in EXPECTED_STOP_GATE_CLASSIFICATIONS.items():
            self.assertIn(requirement_id, requirements_by_id)
            self.assertEqual(
                expected_classification,
                requirements_by_id[requirement_id].get("stopGateClassification"),
            )

        non_stop_gate_requirements = [
            requirement
            for requirement in self.fixture["requirements"]
            if requirement["id"] not in EXPECTED_STOP_GATE_CLASSIFICATIONS
        ]
        self.assertTrue(non_stop_gate_requirements)
        for requirement in non_stop_gate_requirements:
            self.assertNotIn("stopGateClassification", requirement)


if __name__ == "__main__":
    unittest.main()
