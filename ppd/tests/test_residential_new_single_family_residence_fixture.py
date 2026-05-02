import json
import unittest
from pathlib import Path
from urllib.parse import urlparse


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "permit_processes"
    / "residential_new_single_family_residence.json"
)


class ResidentialNewSingleFamilyResidenceFixtureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            cls.fixture = json.load(fixture_file)
        cls.process = cls.fixture["process"]

    def test_fixture_identifies_residential_building_process(self):
        self.assertEqual("residential_new_single_family_residence", self.process["id"])
        self.assertIn("building_permit", self.process["permitTypes"])
        self.assertIn("new_single_family_residence", self.process["permitTypes"])
        self.assertGreaterEqual(len(self.process["sourceIds"]), 4)

    def test_stages_cover_residential_lifecycle_in_order(self):
        stages = self.process["stages"]
        kinds = [stage["kind"] for stage in stages]
        expected_kinds = [
            "pre_application_research",
            "document_preparation",
            "account_setup",
            "permit_type_selection",
            "application_data_entry",
            "upload",
            "submission",
            "prescreen_intake",
            "fee_payment",
            "plan_review",
            "corrections",
            "approval_issuance",
            "inspections",
            "expiration_extension_reactivation",
        ]
        for kind in expected_kinds:
            self.assertIn(kind, kinds)

        sequences = [stage["sequence"] for stage in stages]
        self.assertEqual(sorted(sequences), sequences)
        self.assertEqual(len(sequences), len(set(sequences)))

        stage_ids = {stage["id"] for stage in stages}
        for stage in stages:
            for next_stage_id in stage.get("nextStageIds", []):
                self.assertIn(next_stage_id, stage_ids)

    def test_required_facts_include_case_specific_inputs(self):
        facts = {fact["id"]: fact for fact in self.process["requiredFacts"]}
        required_fact_ids = {
            "property-address-or-r-number",
            "project-description-and-scope",
            "applicant-contact",
            "owner-information",
            "estimated-project-valuation",
        }
        self.assertLessEqual(required_fact_ids, set(facts))
        self.assertTrue(facts["contractor-license-if-contractor"]["appliesWhen"])
        for fact_id in required_fact_ids:
            self.assertTrue(facts[fact_id]["required"])
            self.assertTrue(facts[fact_id]["sourceStageIds"])
            self.assertTrue(facts[fact_id]["evidence"])

    def test_required_documents_and_file_rules_include_single_pdf_process(self):
        documents = {document["id"]: document for document in self.process["requiredDocuments"]}
        self.assertTrue(documents["building-permit-application-pdf"]["required"])
        self.assertTrue(documents["single-drawing-plan-pdf"]["required"])
        self.assertEqual(
            "one_searchable_drawing_plan_pdf",
            documents["single-drawing-plan-pdf"]["singlePdfProcessRole"],
        )
        self.assertIn("application/pdf", documents["single-drawing-plan-pdf"]["acceptedFileTypes"])
        self.assertFalse(documents["structural-calculations-pdf"]["required"])
        self.assertIn("corrections_requested", documents["correction-response-pdf"]["appliesWhen"])

        rules = {rule["id"]: rule for rule in self.process["fileRules"]}
        plan_rule = rules["plans-one-searchable-pdf"]
        self.assertTrue(plan_rule["mustBeSearchable"])
        self.assertEqual(["application/pdf"], plan_rule["allowedMimeTypes"])
        self.assertIn("single-drawing-plan-pdf", plan_rule["appliesToDocumentIds"])
        self.assertIn("building-permit-application-pdf", plan_rule["mustBeSeparateFromDocumentIds"])

        support_rule = rules["applications-calculations-supporting-documents-separate-pdfs"]
        self.assertFalse(support_rule["mustBeSearchable"])
        self.assertIn("single-drawing-plan-pdf", support_rule["mustBeSeparateFromDocumentIds"])

    def test_fee_and_action_gates_stop_financial_and_consequential_actions(self):
        fee_gates = {gate["id"]: gate for gate in self.process["feePaymentGates"]}
        self.assertEqual("financial", fee_gates["fee-notice-before-payment"]["classification"])
        self.assertIn("fee_notice_available", fee_gates["fee-notice-before-payment"]["blocksUntil"])
        self.assertIn("confirm", fee_gates["fee-notice-before-payment"]["requiredConfirmation"].lower())

        action_gates = {gate["id"]: gate for gate in self.process["actionGates"]}
        for gate_id in (
            "official-document-upload-confirmation",
            "submit-application-confirmation",
            "payment-confirmation",
            "inspection-scheduling-confirmation",
        ):
            gate = action_gates[gate_id]
            self.assertTrue(gate["prohibitedWithoutConfirmation"])
            self.assertTrue(gate["requiredConfirmation"])

        self.assertEqual("financial", action_gates["payment-confirmation"]["classification"])
        self.assertEqual(
            "potentially_consequential",
            action_gates["inspection-scheduling-confirmation"]["classification"],
        )
        self.assertFalse(action_gates["draft-field-entry-preview"]["prohibitedWithoutConfirmation"])

    def test_every_requirement_like_item_has_public_citation_evidence(self):
        evidence_bearing_collections = (
            "stages",
            "requiredFacts",
            "requiredDocuments",
            "fileRules",
            "feePaymentGates",
            "actionGates",
        )
        for collection_name in evidence_bearing_collections:
            for item in self.process[collection_name]:
                self.assertTrue(item.get("evidence"), f"{collection_name} {item['id']} lacks evidence")
                for evidence in item["evidence"]:
                    self.assertIn(evidence["sourceId"], self.process["sourceIds"])
                    parsed = urlparse(evidence["sourceUrl"])
                    self.assertEqual("https", parsed.scheme)
                    self.assertIn(parsed.netloc, {"www.portland.gov", "devhub.portlandoregon.gov"})
                    self.assertTrue(evidence["capturedAt"].endswith("Z"))
                    self.assertTrue(evidence.get("note"))

    def test_fixture_contains_no_private_or_live_crawl_artifacts(self):
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        forbidden_fragments = (
            "ppd/data/private",
            "storage_state",
            "auth_state",
            "cookies.json",
            "localstorage.json",
            "trace.zip",
            "playwright-report",
            "/downloads/",
            "downloaded_documents",
            "raw_body",
            "response_body",
            "password",
            "bearer ",
            "api_key",
            "client_secret",
        )
        for fragment in forbidden_fragments:
            self.assertNotIn(fragment, serialized)


if __name__ == "__main__":
    unittest.main()
