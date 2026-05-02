from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "permit-processes" / "solar_permit_workflow.json"
ALLOWED_SOURCE_IDS = {
    "ppd-devhub-application-guidance",
    "ppd-devhub-faq",
    "ppd-single-pdf-process-guidance",
}
CONSEQUENTIAL_CLASSIFICATIONS = {"potentially_consequential", "financial"}
PRIVATE_TEXT_MARKERS = (
    "password",
    "token",
    "cookie",
    "credential",
    "storage-state",
    "auth-state",
    "trace.zip",
    "screenshot",
    "ppd/data/private",
    "ppd/data/raw",
)


class SolarPermitProcessFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.process = self.fixture["process"]
        self.stage_ids = {stage["id"] for stage in self.process["stages"]}
        self.document_ids = {document["id"] for document in self.process["requiredDocuments"]}

    def test_fixture_is_existing_public_source_backed_solar_skeleton(self) -> None:
        self.assertEqual(self.fixture["fixtureKind"], "permit_process")
        self.assertEqual(self.fixture["schemaVersion"], 1)
        self.assertEqual(self.fixture["sourceMode"], "existing_public_fixtures_only")
        self.assertEqual(self.process["id"], "solar-permit-workflow")
        self.assertIn("Solar permits", self.process["permitTypes"])
        self.assertEqual(set(self.process["sourceIds"]), ALLOWED_SOURCE_IDS)

    def test_stages_cover_solar_workflow_without_unknown_edges(self) -> None:
        kinds = [stage["kind"] for stage in self.process["stages"]]
        expected_kinds = {
            "permit_type_selection",
            "eligibility_screening",
            "document_preparation",
            "application_data_entry",
            "upload",
            "acknowledgment_certification",
            "fee_payment",
            "corrections",
            "inspections",
        }
        self.assertTrue(expected_kinds.issubset(set(kinds)))
        self.assertEqual([stage["sequence"] for stage in self.process["stages"]], list(range(len(self.process["stages"]))))
        for stage in self.process["stages"]:
            for next_stage_id in stage.get("nextStageIds", []):
                self.assertIn(next_stage_id, self.stage_ids)
            self.assertEvidence(stage)

    def test_required_facts_documents_file_rules_and_gates_are_source_backed(self) -> None:
        fact_ids = {fact["id"] for fact in self.process["requiredFacts"]}
        self.assertTrue(
            {
                "solar-property-identifier",
                "solar-project-scope",
                "solar-applicant-contact",
                "solar-contractor-or-installer",
                "solar-project-valuation",
            }.issubset(fact_ids)
        )
        for fact in self.process["requiredFacts"]:
            self.assertTrue(fact["required"])
            self.assertStageReferences(fact)
            self.assertEvidence(fact)

        self.assertTrue(
            {
                "solar-permit-application-pdf",
                "solar-drawing-plan-pdf",
                "solar-structural-or-electrical-supporting-pdf",
                "solar-correction-response-pdf",
                "solar-fee-payment-notice",
            }.issubset(self.document_ids)
        )
        for document in self.process["requiredDocuments"]:
            self.assertIn("application/pdf", document["acceptedFileTypes"])
            self.assertStageReferences(document)
            self.assertEvidence(document)

        rule_ids = {rule["id"] for rule in self.process["fileRules"]}
        self.assertTrue(
            {
                "solar-plans-one-searchable-pdf",
                "solar-application-and-supporting-documents-separate-pdfs",
                "solar-official-actions-require-user-confirmation",
            }.issubset(rule_ids)
        )
        for rule in self.process["fileRules"]:
            self.assertTrue(rule["required"])
            self.assertIn("application/pdf", rule["acceptedFileTypes"])
            self.assertTrue(set(rule["appliesToDocumentIds"]).issubset(self.document_ids))
            self.assertEvidence(rule)

        gate_ids = {gate["id"] for gate in self.process["actionGates"]}
        self.assertTrue(
            {
                "solar-official-upload-gate",
                "solar-certification-gate",
                "solar-submission-gate",
                "solar-payment-gate",
                "solar-correction-upload-gate",
                "solar-inspection-scheduling-gate",
            }.issubset(gate_ids)
        )
        payment_gate = next(gate for gate in self.process["actionGates"] if gate["id"] == "solar-payment-gate")
        self.assertEqual(payment_gate["classification"], "financial")
        for gate in self.process["actionGates"]:
            self.assertStageReferences(gate)
            self.assertEvidence(gate)
            if gate["classification"] in CONSEQUENTIAL_CLASSIFICATIONS:
                self.assertTrue(gate["prohibitedWithoutConfirmation"])
                self.assertIn("User explicitly confirms", gate["requiredConfirmation"])

    def test_fixture_contains_no_private_or_live_artifacts(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in PRIVATE_TEXT_MARKERS:
            self.assertNotIn(marker, serialized)

    def assertStageReferences(self, item: dict[str, Any]) -> None:
        for stage_id in item.get("sourceStageIds", []):
            self.assertIn(stage_id, self.stage_ids)

    def assertEvidence(self, item: dict[str, Any]) -> None:
        evidence = item.get("evidence")
        self.assertIsInstance(evidence, list)
        self.assertGreater(len(evidence), 0)
        for evidence_ref in evidence:
            self.assertIn(evidence_ref["sourceId"], ALLOWED_SOURCE_IDS)
            self.assertIn(evidence_ref["sourceId"], self.process["sourceIds"])
            source_url = evidence_ref["sourceUrl"]
            parsed = urlparse(source_url)
            self.assertEqual(parsed.scheme, "https")
            self.assertIn(parsed.netloc, {"www.portland.gov"})
            self.assertTrue(evidence_ref["anchorId"].strip())
            self.assertTrue(evidence_ref["capturedAt"].endswith("Z"))
            self.assertTrue(evidence_ref["note"].strip())


if __name__ == "__main__":
    unittest.main()
