"""Focused validation for demolition permit requirement extraction fixtures."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from ppd.contracts.requirements import fixture_from_dict


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "requirement_extraction"
    / "demolition_permit_requirements.json"
)


class DemolitionRequirementExtractionFocusedTest(unittest.TestCase):
    def load_fixture(self) -> dict[str, Any]:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_demolition_extraction_has_only_expected_fixture_categories(self) -> None:
        data = self.load_fixture()
        parsed = fixture_from_dict(data)
        expected = set(data["expected_fixture_categories"])
        categories = {
            item["fixture_category"]
            for item in data["requirements"]
            if item.get("fixture_category") != "stop_gate"
        }

        self.assertEqual(parsed.process_id, "demolition-permit")
        self.assertEqual(categories, expected)
        self.assertEqual(len(categories), 7)

    def test_source_evidence_ids_are_exact_and_deduplicated_for_categories(self) -> None:
        data = self.load_fixture()
        expected_source_ids = set(data["expected_source_evidence_ids"])
        category_requirements = [
            item for item in data["requirements"] if item.get("fixture_category") != "stop_gate"
        ]
        observed_source_ids = {
            evidence["source_id"]
            for item in category_requirements
            for evidence in item["evidence"]
        }
        requirement_ids = [item["requirement_id"] for item in data["requirements"]]
        category_names = [item["fixture_category"] for item in category_requirements]

        self.assertEqual(observed_source_ids, expected_source_ids)
        self.assertEqual(len(requirement_ids), len(set(requirement_ids)))
        self.assertEqual(len(category_names), len(set(category_names)))

    def test_confidence_values_stay_inside_fixture_bounds(self) -> None:
        data = self.load_fixture()
        bounds = data["confidence_bounds"]
        minimum = float(bounds["minimum"])
        maximum = float(bounds["maximum"])

        for requirement in fixture_from_dict(data).requirements:
            self.assertGreaterEqual(requirement.confidence, minimum, requirement.requirement_id)
            self.assertLessEqual(requirement.confidence, maximum, requirement.requirement_id)

    def test_stop_gates_have_explicit_classifications(self) -> None:
        data = self.load_fixture()
        expected = data["expected_stop_gate_classifications"]
        observed = {
            item["requirement_id"]: item.get("stop_gate", {}).get("classification")
            for item in data["requirements"]
            if item.get("type") == "action_gate"
        }

        self.assertEqual(observed, expected)
        for item in data["requirements"]:
            if item.get("type") != "action_gate":
                continue
            self.assertTrue(
                item.get("stop_gate", {}).get("requires_exact_user_confirmation"),
                item["requirement_id"],
            )
            self.assertIn(
                item.get("stop_gate", {}).get("classification"),
                {"potentially_consequential", "financial"},
                item["requirement_id"],
            )


if __name__ == "__main__":
    unittest.main()
