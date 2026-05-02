from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "guardrail_playwright_mapping.json"
REDACTED_VALUE_PREFIX = "[REDACTED_"


class GuardrailPlaywrightMappingFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_links_one_missing_fact_to_one_reversible_field_and_one_stop_gate(self) -> None:
        facts = self.fixture["missingInformationFacts"]
        field_mappings = self.fixture["playwrightFieldMappings"]
        stop_gates = self.fixture["explicitStopGates"]

        self.assertEqual(1, len(facts))
        self.assertEqual(1, len(field_mappings))
        self.assertEqual(1, len(stop_gates))

        fact = facts[0]
        field_mapping = field_mappings[0]
        stop_gate = stop_gates[0]

        self.assertEqual("missing", fact["status"])
        self.assertEqual(fact["id"], field_mapping["missingInformationFactId"])
        self.assertEqual(fact["id"], stop_gate["linkedMissingInformationFactId"])
        self.assertEqual("reversible_draft_edit", field_mapping["actionClass"])
        self.assertEqual("submit_application", stop_gate["blockedAction"])
        self.assertEqual("potentially_consequential", stop_gate["classification"])
        self.assertTrue(stop_gate["requiresExplicitUserConfirmation"])
        self.assertFalse(stop_gate["defaultConfirmed"])

    def test_uses_only_source_evidence_ids_declared_in_fixture(self) -> None:
        evidence_ids = {item["id"] for item in self.fixture["sourceEvidence"]}
        self.assertGreaterEqual(len(evidence_ids), 1)

        for collection_name in ("missingInformationFacts", "playwrightFieldMappings", "explicitStopGates"):
            for item in self.fixture[collection_name]:
                item_evidence_ids = item["sourceEvidenceIds"]
                self.assertGreaterEqual(len(item_evidence_ids), 1)
                self.assertTrue(set(item_evidence_ids).issubset(evidence_ids))

    def test_field_values_are_redacted_before_and_after_only(self) -> None:
        field_mapping = self.fixture["playwrightFieldMappings"][0]
        self.assertEqual({"beforeValue", "afterValue"}, {key for key in field_mapping if key.endswith("Value")})
        self.assertTrue(field_mapping["beforeValue"].startswith(REDACTED_VALUE_PREFIX))
        self.assertTrue(field_mapping["afterValue"].startswith(REDACTED_VALUE_PREFIX))
        self.assertNotEqual(field_mapping["beforeValue"], field_mapping["afterValue"])

    def test_selector_basis_is_accessible_and_does_not_require_browser_artifacts(self) -> None:
        selector_basis = self.fixture["playwrightFieldMappings"][0]["selectorBasis"]
        self.assertEqual("textbox", selector_basis["role"])
        self.assertEqual("Project description", selector_basis["accessibleName"])
        self.assertNotIn("css", selector_basis)
        self.assertNotIn("xpath", selector_basis)
        self.assertNotIn("screenshot", json.dumps(self.fixture).lower())
        self.assertNotIn("trace", json.dumps(self.fixture).lower())
        self.assertNotIn("storage_state", json.dumps(self.fixture).lower())


if __name__ == "__main__":
    unittest.main()
