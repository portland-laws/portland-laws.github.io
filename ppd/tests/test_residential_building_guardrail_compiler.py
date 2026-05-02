"""Fixture tests for residential building permit guardrail compiler output."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "residential_building_permit_guardrails.json"


class ResidentialBuildingGuardrailCompilerFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)
        self.guardrails: dict[str, dict[str, Any]] = {
            guardrail["id"]: guardrail for guardrail in self.fixture["guardrails"]
        }

    def test_fixture_is_residential_building_permit_compiler_output(self) -> None:
        self.assertEqual(self.fixture["schemaVersion"], 1)
        self.assertEqual(self.fixture["processId"], "residential-building-permit")
        self.assertTrue(self.fixture["compiledAt"].endswith("Z"))
        self.assertEqual(self.fixture["compiler"]["name"], "ppd.logic.guardrailCompiler.fixture")
        self.assertGreaterEqual(len(self.fixture["authoritySources"]), 3)
        self.assertEqual(len(self.guardrails), len(self.fixture["guardrails"]))

    def test_missing_fact_guardrails_are_source_backed_and_block_submission(self) -> None:
        expected_facts = {
            "property_identifier",
            "project_scope",
            "applicant_contact",
            "contractor_or_owner_role",
        }
        missing_fact_guardrails = [
            guardrail for guardrail in self.guardrails.values() if guardrail["kind"] == "missing_fact"
        ]
        self.assertEqual({guardrail["requiredFact"] for guardrail in missing_fact_guardrails}, expected_facts)
        for guardrail in missing_fact_guardrails:
            self.assertEqual(guardrail["severity"], "block_submission")
            self.assertIn("fact_missing", guardrail["predicate"])
            self.assertTrue(guardrail["sourceIds"])
            self.assertTrue(guardrail["message"].startswith("Ask"))

    def test_required_document_groups_cover_application_plans_and_supporting_documents(self) -> None:
        document_group_guardrails = [
            guardrail
            for guardrail in self.guardrails.values()
            if guardrail["kind"] == "required_document_group"
        ]
        groups = {guardrail["documentGroup"]["id"]: guardrail for guardrail in document_group_guardrails}
        self.assertEqual(set(groups), {"application_forms", "drawing_plans", "supporting_documents"})
        for group_id, guardrail in groups.items():
            with self.subTest(group_id=group_id):
                document_group = guardrail["documentGroup"]
                self.assertEqual(guardrail["severity"], "block_submission")
                self.assertEqual(document_group["minimumDocuments"], 1)
                self.assertEqual(document_group["acceptedFormats"], ["pdf"])
                self.assertGreaterEqual(len(document_group["examples"]), 1)
                self.assertTrue(guardrail["sourceIds"])

    def test_single_pdf_process_compatibility_is_explicit(self) -> None:
        guardrail = self.guardrails["rbp_single_pdf_drawings_compatible"]
        self.assertEqual(guardrail["kind"], "single_pdf_process_compatibility")
        self.assertEqual(guardrail["severity"], "block_submission")
        self.assertIn("single_pdf_process_applies", guardrail["predicate"])
        self.assertIn("exactly_one_pdf", guardrail["predicate"])
        rules = guardrail["compatibilityRules"]
        self.assertTrue(rules["drawingPlansMustBeOneSearchablePdf"])
        self.assertTrue(rules["applicationsCalculationsAndSupportingDocumentsMustBeSeparatePdfs"])
        self.assertTrue(rules["rejectMergedApplicationAndPlans"])
        self.assertTrue(rules["rejectMultipleDrawingPlanPdfsWhenSinglePdfProcessApplies"])
        self.assertEqual(guardrail["sourceIds"], ["single_pdf_process_guide"])

    def test_inspection_scheduling_is_a_consequential_stop_point(self) -> None:
        guardrail = self.guardrails["rbp_stop_before_inspection_scheduling"]
        self.assertEqual(guardrail["kind"], "action_gate")
        self.assertEqual(guardrail["action"], "schedule_inspection")
        self.assertEqual(guardrail["classification"], "potentially_consequential")
        self.assertEqual(guardrail["severity"], "stop_before_action")
        self.assertTrue(guardrail["requiresExactUserConfirmation"])
        self.assertFalse(guardrail["allowedWithoutConfirmation"])
        self.assertTrue(guardrail["auditEventRequired"])
        self.assertIn("permit_issued", guardrail["stagePreconditions"])

    def test_payment_is_a_financial_stop_point(self) -> None:
        guardrail = self.guardrails["rbp_stop_before_payment"]
        self.assertEqual(guardrail["kind"], "action_gate")
        self.assertEqual(guardrail["action"], "pay_fees")
        self.assertEqual(guardrail["classification"], "financial")
        self.assertEqual(guardrail["severity"], "stop_before_action")
        self.assertTrue(guardrail["requiresExactUserConfirmation"])
        self.assertFalse(guardrail["allowedWithoutConfirmation"])
        self.assertTrue(guardrail["auditEventRequired"])
        self.assertIn("fees_assessed", guardrail["stagePreconditions"])

    def test_compiled_scenarios_reference_existing_guardrails(self) -> None:
        scenario_ids = {scenario["id"] for scenario in self.fixture["compiledScenarios"]}
        self.assertEqual(
            scenario_ids,
            {
                "missing_facts_and_documents",
                "single_pdf_process_incompatible_multiple_plan_pdfs",
                "payment_requires_confirmation",
                "inspection_scheduling_requires_confirmation",
            },
        )
        for scenario in self.fixture["compiledScenarios"]:
            with self.subTest(scenario=scenario["id"]):
                self.assertTrue(scenario["expectedBlockingGuardrailIds"])
                for guardrail_id in scenario["expectedBlockingGuardrailIds"]:
                    self.assertIn(guardrail_id, self.guardrails)

    def test_fixture_contains_no_private_or_live_automation_artifacts(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        forbidden_fragments = (
            "password",
            "token",
            "cookie",
            "storage_state",
            "auth_state",
            "trace.zip",
            "screenshot",
            "ppd/data/private",
            "ppd/data/raw",
        )
        for fragment in forbidden_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment, serialized)


if __name__ == "__main__":
    unittest.main()
