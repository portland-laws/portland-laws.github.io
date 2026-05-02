"""Focused fixture validation for FCC wireless requirement extraction."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_extraction"
    / "fcc_wireless_application_requirements.json"
)

EXPECTED_CATEGORIES = {
    "application_intake",
    "submittal_documents",
    "site_information",
    "wireless_facility_details",
    "plan_review",
    "fees",
    "agent_stop_gates",
}

STOP_GATE_CLASSIFICATIONS = {
    "potentially_consequential",
    "financial",
}


class FccWirelessRequirementExtractionTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)
        self.requirements = self.fixture["requirements"]
        self.evidence_ids = {
            evidence["evidenceId"] for evidence in self.fixture["sourceEvidence"]
        }

    def test_fixture_uses_only_the_seven_expected_categories(self) -> None:
        categories = {requirement["category"] for requirement in self.requirements}
        self.assertEqual(EXPECTED_CATEGORIES, categories)

    def test_every_requirement_references_known_source_evidence_ids(self) -> None:
        self.assertTrue(self.evidence_ids)
        for requirement in self.requirements:
            evidence_ids = requirement.get("evidenceIds", [])
            self.assertTrue(evidence_ids, requirement["requirementId"])
            for evidence_id in evidence_ids:
                self.assertIn(evidence_id, self.evidence_ids, requirement["requirementId"])

    def test_confidence_values_are_bounded_probabilities(self) -> None:
        for requirement in self.requirements:
            confidence = requirement.get("confidence")
            self.assertIsInstance(confidence, float, requirement["requirementId"])
            self.assertGreaterEqual(confidence, 0.0, requirement["requirementId"])
            self.assertLessEqual(confidence, 1.0, requirement["requirementId"])

    def test_requirement_extraction_is_deduplicated(self) -> None:
        seen_ids = set()
        seen_semantic_keys = set()
        for requirement in self.requirements:
            requirement_id = requirement["requirementId"]
            self.assertNotIn(requirement_id, seen_ids)
            seen_ids.add(requirement_id)

            semantic_key = (
                requirement["category"],
                requirement["type"],
                requirement["subject"],
                requirement["action"],
                requirement["object"],
                tuple(requirement.get("conditions", [])),
            )
            self.assertNotIn(semantic_key, seen_semantic_keys)
            seen_semantic_keys.add(semantic_key)

    def test_action_gate_requirements_have_explicit_stop_gate_classifications(self) -> None:
        action_gates = [
            requirement
            for requirement in self.requirements
            if requirement["type"] == "action_gate"
        ]
        self.assertTrue(action_gates)
        for requirement in action_gates:
            stop_gate = requirement.get("stopGate")
            self.assertIsInstance(stop_gate, dict, requirement["requirementId"])
            self.assertIn(
                stop_gate.get("classification"),
                STOP_GATE_CLASSIFICATIONS,
                requirement["requirementId"],
            )
            self.assertIs(stop_gate.get("requiresExactUserConfirmation"), True)


if __name__ == "__main__":
    unittest.main()
