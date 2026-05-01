"""Validate the first fixture-backed Single PDF Process permit model."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.contracts.processes import (
    ActionGate,
    ActionGateClassification,
    ActionGateKind,
    EvidenceRef,
    PermitProcess,
    ProcessStage,
    ProcessStageKind,
    RequiredDocument,
    RequiredDocumentKind,
    RequiredFact,
    RequiredFactKind,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "permit-processes" / "single_pdf_process.json"


class SinglePdfProcessFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        cls.process = cls.fixture["process"]

    def test_fixture_metadata_is_scoped_and_versioned(self) -> None:
        self.assertEqual(self.fixture["fixtureKind"], "permit_process")
        self.assertEqual(self.fixture["schemaVersion"], 1)
        self.assertTrue(self.fixture["generatedAt"].endswith("Z"))
        self.assertEqual(self.process["id"], "single-pdf-process")
        self.assertIn("ppd-single-pdf-process-guidance", self.process["sourceIds"])

    def test_process_contract_accepts_core_fixture_shape(self) -> None:
        permit_process = PermitProcess(
            id=self.process["id"],
            name=self.process["name"],
            permit_types=tuple(self.process["permitTypes"]),
            source_ids=tuple(self.process["sourceIds"]),
            stages=tuple(self._stage(stage) for stage in self.process["stages"]),
            required_facts=tuple(self._fact(fact) for fact in self.process["requiredFacts"]),
            required_documents=tuple(self._document(document) for document in self.process["requiredDocuments"]),
            action_gates=tuple(self._gate(gate) for gate in self.process["actionGates"]),
            formal_requirement_ids=tuple(self.process["formalRequirementIds"]),
        )
        self.assertEqual(permit_process.validate(), [])

    def test_stage_sequence_covers_single_pdf_workflow(self) -> None:
        stages = self.process["stages"]
        self.assertEqual([stage["sequence"] for stage in stages], list(range(len(stages))))
        kinds = {stage["kind"] for stage in stages}
        expected_kinds = {
            "pre_application_research",
            "document_preparation",
            "application_data_entry",
            "upload",
            "acknowledgment_certification",
            "submission",
            "prescreen_intake",
            "plan_review",
        }
        self.assertTrue(expected_kinds.issubset(kinds))
        stage_ids = {stage["id"] for stage in stages}
        for stage in stages:
            for next_stage_id in stage["nextStageIds"]:
                self.assertIn(next_stage_id, stage_ids)
            self.assertEvidence(stage["evidence"], f"stage {stage['id']}")

    def test_required_documents_capture_single_pdf_roles_and_pdf_rules(self) -> None:
        documents = {document["id"]: document for document in self.process["requiredDocuments"]}
        self.assertIn("single-searchable-drawing-plan-pdf", documents)
        self.assertIn("permit-application-pdf", documents)
        self.assertIn("calculations-and-supporting-documents-pdf", documents)

        plan = documents["single-searchable-drawing-plan-pdf"]
        self.assertEqual(plan["kind"], "drawing_plan")
        self.assertTrue(plan["required"])
        self.assertEqual(plan["singlePdfProcessRole"], "single_searchable_plan_pdf")

        separate_roles = {
            documents["permit-application-pdf"]["singlePdfProcessRole"],
            documents["calculations-and-supporting-documents-pdf"]["singlePdfProcessRole"],
        }
        self.assertEqual(separate_roles, {"separate_application_pdf", "separate_supporting_pdf"})

        for document in documents.values():
            self.assertEqual(document["acceptedFileTypes"], ["application/pdf"])
            self.assertEvidence(document["evidence"], f"document {document['id']}")

    def test_file_rules_are_citation_backed_and_constrain_pdf_submittals(self) -> None:
        rules = {rule["id"]: rule for rule in self.process["fileRules"]}
        self.assertIn("plans-one-searchable-pdf", rules)
        self.assertIn("applications-and-supporting-documents-separate-pdfs", rules)
        self.assertIn("official-actions-require-user-confirmation", rules)

        plan_rule = rules["plans-one-searchable-pdf"]
        self.assertEqual(plan_rule["acceptedFileTypes"], ["application/pdf"])
        self.assertIn("single-searchable-drawing-plan-pdf", plan_rule["appliesToDocumentIds"])
        self.assertIn("multiple_plan_pdf_files_for_same_initial_submittal", plan_rule["prohibitedPatterns"])

        separate_rule = rules["applications-and-supporting-documents-separate-pdfs"]
        self.assertIn("permit-application-pdf", separate_rule["appliesToDocumentIds"])
        self.assertIn("calculations-and-supporting-documents-pdf", separate_rule["appliesToDocumentIds"])
        self.assertIn("application_pages_embedded_in_plan_pdf", separate_rule["prohibitedPatterns"])

        for rule in rules.values():
            self.assertTrue(rule["required"])
            self.assertEqual(rule["acceptedFileTypes"], ["application/pdf"])
            self.assertEvidence(rule["evidence"], f"file rule {rule['id']}")

    def test_action_gates_stop_before_consequential_devhub_actions(self) -> None:
        gates = {gate["id"]: gate for gate in self.process["actionGates"]}
        self.assertEqual(set(gates), {"official-upload-gate", "certification-gate", "submission-gate"})
        for gate in gates.values():
            self.assertEqual(gate["classification"], "potentially_consequential")
            self.assertTrue(gate["prohibitedWithoutConfirmation"])
            self.assertIn("explicitly confirms", gate["requiredConfirmation"])
            self.assertEvidence(gate["evidence"], f"action gate {gate['id']}")

    def test_no_private_or_runtime_artifacts_are_embedded(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        forbidden = ("password", "cookie", "auth-state", "storage-state", "trace.zip", "session token")
        for marker in forbidden:
            self.assertNotIn(marker, serialized)

    def assertEvidence(self, evidence: list[dict], context: str) -> None:
        self.assertTrue(evidence, f"{context} must include evidence")
        source_ids = set(self.process["sourceIds"])
        for item in evidence:
            self.assertIn(item["sourceId"], source_ids, context)
            self.assertTrue(item["sourceUrl"].startswith("https://"), context)
            self.assertTrue(item["capturedAt"].endswith("Z"), context)
            self.assertTrue(item["note"].strip(), context)

    def _evidence(self, items: list[dict]) -> tuple[EvidenceRef, ...]:
        return tuple(
            EvidenceRef(
                source_id=item["sourceId"],
                source_url=item.get("sourceUrl"),
                anchor_id=item.get("anchorId"),
                page_number=item.get("pageNumber"),
                captured_at=item.get("capturedAt"),
                note=item.get("note"),
            )
            for item in items
        )

    def _stage(self, stage: dict) -> ProcessStage:
        return ProcessStage(
            id=stage["id"],
            name=stage["name"],
            kind=ProcessStageKind(stage["kind"]),
            sequence=stage["sequence"],
            description=stage["description"],
            entry_conditions=tuple(stage["entryConditions"]),
            exit_conditions=tuple(stage["exitConditions"]),
            next_stage_ids=tuple(stage["nextStageIds"]),
            evidence=self._evidence(stage["evidence"]),
        )

    def _fact(self, fact: dict) -> RequiredFact:
        return RequiredFact(
            id=fact["id"],
            label=fact["label"],
            kind=RequiredFactKind(fact["kind"]),
            required=fact["required"],
            description=fact["description"],
            applies_when=tuple(fact["appliesWhen"]),
            source_stage_ids=tuple(fact["sourceStageIds"]),
            validation_hint=fact.get("validationHint"),
            contains_private_or_user_specific_data=fact["containsPrivateOrUserSpecificData"],
            evidence=self._evidence(fact["evidence"]),
        )

    def _document(self, document: dict) -> RequiredDocument:
        return RequiredDocument(
            id=document["id"],
            name=document["name"],
            kind=RequiredDocumentKind(document["kind"]),
            required=document["required"],
            description=document["description"],
            applies_when=tuple(document["appliesWhen"]),
            accepted_file_types=tuple(document["acceptedFileTypes"]),
            source_stage_ids=tuple(document["sourceStageIds"]),
            single_pdf_process_role=document.get("singlePdfProcessRole"),
            requires_signature=document["requiresSignature"],
            evidence=self._evidence(document["evidence"]),
        )

    def _gate(self, gate: dict) -> ActionGate:
        return ActionGate(
            id=gate["id"],
            name=gate["name"],
            kind=ActionGateKind(gate["kind"]),
            classification=ActionGateClassification(gate["classification"]),
            description=gate["description"],
            required_confirmation=gate["requiredConfirmation"],
            blocks_until=tuple(gate["blocksUntil"]),
            prohibited_without_confirmation=gate["prohibitedWithoutConfirmation"],
            source_stage_ids=tuple(gate["sourceStageIds"]),
            evidence=self._evidence(gate["evidence"]),
        )


if __name__ == "__main__":
    unittest.main()
