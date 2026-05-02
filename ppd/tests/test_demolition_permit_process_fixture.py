import json
import unittest
from pathlib import Path
from urllib.parse import urlparse


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "permit_processes" / "demolition_permit_process_skeleton.json"


class DemolitionPermitProcessFixtureTest(unittest.TestCase):
    def setUp(self):
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)
        self.process = self.fixture["process"]
        self.source_ids = {source["source_id"] for source in self.process["authority_sources"]}

    def test_fixture_is_deterministic_and_public_only(self):
        self.assertEqual(self.fixture["generated_from"], "fixture_only_public_source_inventory")
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        forbidden_markers = (
            "ppd/data/private",
            "storage_state",
            "auth_state",
            "cookies.json",
            "localstorage.json",
            "raw_response_body",
            "response_body",
            "password",
            "secret",
            "token",
            "trace.zip",
            "playwright-report",
            "downloaded_documents",
        )
        for marker in forbidden_markers:
            self.assertNotIn(marker, serialized)

        for source in self.process["authority_sources"]:
            parsed = urlparse(source["url"])
            self.assertEqual(parsed.scheme, "https")
            self.assertIn(parsed.netloc, {"www.portland.gov", "devhub.portlandoregon.gov", "www.portlandoregon.gov"})
            self.assertEqual(source["captured_as"], "public_fixture_reference")
            self.assertTrue(source["authority_label"])
            self.assertTrue(source["source_inventory_category"])

    def test_has_demolition_stages_required_facts_documents_and_file_rules(self):
        self.assertEqual(self.process["permit_type"], "demolition_permit")
        stage_kinds = [stage["kind"] for stage in self.process["stages"]]
        expected_stage_kinds = {
            "pre_application_research",
            "account_setup",
            "document_preparation",
            "upload",
            "submission",
            "fee_payment",
            "plan_review_or_corrections",
            "inspection_or_finalization",
        }
        self.assertTrue(expected_stage_kinds.issubset(set(stage_kinds)))

        required_fact_ids = {fact["id"] for fact in self.process["required_user_facts"] if fact["required"]}
        self.assertTrue(
            {
                "demolition_property_identifier",
                "demolition_project_scope",
                "demolition_applicant_contact",
                "demolition_owner_or_authorized_agent",
                "demolition_utility_disconnect_status",
            }.issubset(required_fact_ids)
        )

        required_document_ids = {document["id"] for document in self.process["required_documents"] if document["required"]}
        self.assertTrue(
            {
                "demolition_application_form",
                "demolition_site_plan_or_scope_document",
                "demolition_supporting_reports_or_clearances",
                "demolition_contract_license_documentation",
            }.issubset(required_document_ids)
        )

        file_rule_ids = {rule["id"] for rule in self.process["file_rules"]}
        self.assertIn("demolition_files_pdf_only", file_rule_ids)
        self.assertIn("demolition_drawings_single_searchable_pdf_when_applicable", file_rule_ids)

    def test_fee_finalization_and_action_gates_are_confirmation_backed(self):
        payment_gates = self.process["fee_payment_gates"]
        self.assertEqual(len(payment_gates), 1)
        self.assertEqual(payment_gates[0]["classification"], "financial")
        self.assertIn("exact user confirmation", payment_gates[0]["stop_condition"])

        finalization_actions = {gate["action"] for gate in self.process["inspection_or_finalization_gates"]}
        self.assertIn("schedule_or_request_demolition_inspection", finalization_actions)
        self.assertIn("finalize_cancel_or_close_demolition_request", finalization_actions)

        gates = self.process["action_gates"]
        gate_actions = {gate["action"] for gate in gates}
        self.assertTrue(
            {
                "submit_demolition_permit_request",
                "accept_or_certify_demolition_application_statement",
                "upload_official_demolition_corrections",
                "pay_demolition_permit_fees",
            }.issubset(gate_actions)
        )
        for gate in gates:
            self.assertTrue(gate["requires_exact_user_confirmation"])
            self.assertTrue(gate["requires_action_preview"])
            self.assertIn(gate["classification"], {"consequential", "financial"})
            self.assertTrue(gate["citation_source_ids"])
            self.assertTrue(set(gate["citation_source_ids"]).issubset(self.source_ids))

    def test_all_process_requirements_are_citation_backed(self):
        for collection_name in ("required_user_facts", "required_documents", "file_rules", "stages", "fee_payment_gates", "inspection_or_finalization_gates"):
            for item in self.process[collection_name]:
                with self.subTest(collection=collection_name, item=item["id"]):
                    evidence = item.get("evidence", [])
                    self.assertTrue(evidence)
                    self.assertTrue(set(evidence).issubset(self.source_ids))


if __name__ == "__main__":
    unittest.main()
