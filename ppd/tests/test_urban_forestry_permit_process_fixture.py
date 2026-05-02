"""Validate the fixture-only Urban Forestry permit process skeleton."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "permit_processes"
    / "urban_forestry_permit_process.json"
)


class UrbanForestryPermitProcessFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)

    def test_fixture_is_public_redacted_and_fixture_only(self) -> None:
        self.assertTrue(self.fixture["fixtureOnly"])
        self.assertEqual(
            self.fixture["generatedFrom"],
            "existing_public_fixture_source_inventory_evidence_only",
        )
        privacy = self.fixture["privacy"]
        for key, value in privacy.items():
            self.assertFalse(value, key)

    def test_core_process_sections_are_present(self) -> None:
        self.assertEqual(self.fixture["permitType"], "Urban Forestry permit")
        self.assertGreaterEqual(len(self.fixture["authoritySources"]), 5)
        self.assertGreaterEqual(len(self.fixture["requiredFacts"]), 5)
        self.assertGreaterEqual(len(self.fixture["requiredDocuments"]), 5)
        self.assertGreaterEqual(len(self.fixture["fileRules"]), 3)
        self.assertGreaterEqual(len(self.fixture["stages"]), 10)
        self.assertGreaterEqual(len(self.fixture["actionGates"]), 10)

    def test_all_process_items_are_citation_backed(self) -> None:
        evidence_ids = {source["evidenceId"] for source in self.fixture["authoritySources"]}
        self.assertIn("uf-src-004", evidence_ids)
        self.assertIn("uf-src-005", evidence_ids)

        for source in self.fixture["authoritySources"]:
            self.assertTrue(source["canonicalUrl"].startswith("https://www.portland.gov/"))
            self.assertTrue(source["authorityLabel"].strip())
            self.assertTrue(source["sourceInventoryCategory"].strip())
            self.assertTrue(source["sourceIndexRef"].startswith("fixture_public_source_inventory_"))

        for section_name in ("requiredFacts", "requiredDocuments", "fileRules", "stages", "actionGates"):
            for item in self.fixture[section_name]:
                evidence = item.get("evidence") or item.get("entryEvidence")
                self.assertIsInstance(evidence, list, section_name)
                self.assertTrue(evidence, item)
                self.assertTrue(set(evidence).issubset(evidence_ids), item)

    def test_required_gates_cover_payment_inspection_finalization_and_confirmations(self) -> None:
        gates = {gate["gateId"]: gate for gate in self.fixture["actionGates"]}
        self.assertEqual(self.fixture["feePaymentGates"], ["uf-gate-008"])
        self.assertEqual(self.fixture["inspectionFinalizationGates"], ["uf-gate-010", "uf-gate-011"])

        payment_gate = gates["uf-gate-008"]
        self.assertEqual(payment_gate["classification"], "financial")
        self.assertTrue(payment_gate["requiresExactUserConfirmation"])

        stopped_gate_ids = {"uf-gate-006", "uf-gate-007", "uf-gate-008", "uf-gate-009", "uf-gate-010"}
        for gate_id in stopped_gate_ids:
            with self.subTest(gate_id=gate_id):
                self.assertTrue(gates[gate_id]["requiresExactUserConfirmation"])
                self.assertIn(
                    gates[gate_id]["classification"],
                    {"potentially_consequential", "financial"},
                )
                self.assertTrue(gates[gate_id]["evidence"])

    def test_file_rules_are_document_linked_and_pdf_aware(self) -> None:
        document_ids = {document["documentId"] for document in self.fixture["requiredDocuments"]}
        for rule in self.fixture["fileRules"]:
            self.assertTrue(rule["ruleId"].startswith("uf-file-"))
            self.assertTrue(rule["description"].strip())
            self.assertTrue(rule["predicate"].strip())
            if rule["ruleId"] != "uf-file-003":
                self.assertTrue(set(rule["appliesTo"]).issubset(document_ids))

        plan_document = next(
            document for document in self.fixture["requiredDocuments"] if document["documentId"] == "uf-doc-002"
        )
        self.assertIn("pdf", plan_document["acceptableFormats"])


if __name__ == "__main__":
    unittest.main()
