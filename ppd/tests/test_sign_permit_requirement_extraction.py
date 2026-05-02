"""Focused fixture validation for sign permit requirement extraction.

This test intentionally checks only the narrow behavior needed for the sign
permit extraction fixture: seven categories, source evidence IDs, confidence
bounds, deduplication, and explicit stop-gate classifications.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_extraction"
    / "sign_permit_requirements.json"
)

EXPECTED_CATEGORIES = {
    "permit_type_selection",
    "project_scope_description",
    "site_plan_and_location",
    "sign_drawings_and_dimensions",
    "structural_or_attachment_details",
    "property_owner_authorization",
    "fee_and_submission_gates",
}

EXPECTED_STOP_GATE_CLASSIFICATIONS = {
    "sign-gate-upload-official-documents": "potentially_consequential",
    "sign-gate-certify-application": "potentially_consequential",
    "sign-gate-submit-request": "potentially_consequential",
    "sign-gate-pay-fees": "financial",
}

MIN_CONFIDENCE = 0.7
MAX_CONFIDENCE = 0.95


class SignPermitRequirementExtractionFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)

    def test_fixture_has_exactly_the_seven_sign_permit_categories(self) -> None:
        requirements = self.fixture["requirements"]
        categories = {requirement["category"] for requirement in requirements}

        self.assertEqual(EXPECTED_CATEGORIES, categories)
        self.assertEqual(7, len(requirements))

    def test_requirement_evidence_ids_are_declared_source_ids(self) -> None:
        declared_source_ids = {source["id"] for source in self.fixture["source_evidence"]}

        for requirement in self.fixture["requirements"]:
            evidence_ids = requirement.get("evidence_ids", [])
            self.assertTrue(evidence_ids, requirement["requirement_id"])
            self.assertTrue(set(evidence_ids).issubset(declared_source_ids), requirement)

    def test_confidence_values_are_within_focused_bounds(self) -> None:
        for requirement in self.fixture["requirements"]:
            confidence = requirement.get("confidence")
            self.assertIsInstance(confidence, float, requirement["requirement_id"])
            self.assertGreaterEqual(confidence, MIN_CONFIDENCE, requirement["requirement_id"])
            self.assertLessEqual(confidence, MAX_CONFIDENCE, requirement["requirement_id"])

    def test_requirements_are_deduplicated_by_extraction_signature(self) -> None:
        signatures = []
        for requirement in self.fixture["requirements"]:
            signatures.append(
                (
                    requirement["category"],
                    requirement["type"],
                    requirement["subject"],
                    requirement["action"],
                    requirement["object"],
                    tuple(requirement.get("conditions", [])),
                )
            )

        self.assertEqual(len(signatures), len(set(signatures)))

    def test_stop_gates_have_explicit_classification_and_confirmation(self) -> None:
        declared_source_ids = {source["id"] for source in self.fixture["source_evidence"]}
        stop_gates = self.fixture["stop_gates"]
        actual_classifications = {
            gate["gate_id"]: gate["classification"] for gate in stop_gates
        }

        self.assertEqual(EXPECTED_STOP_GATE_CLASSIFICATIONS, actual_classifications)
        for gate in stop_gates:
            self.assertTrue(gate["requires_exact_confirmation"], gate["gate_id"])
            self.assertTrue(gate.get("evidence_ids"), gate["gate_id"])
            self.assertTrue(set(gate["evidence_ids"]).issubset(declared_source_ids), gate)


if __name__ == "__main__":
    unittest.main()
