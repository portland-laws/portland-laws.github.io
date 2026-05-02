"""Validate the fixture-only PP&D sign permit workflow skeleton."""

from __future__ import annotations

import json
from pathlib import Path
import unittest


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "permit_processes" / "sign_permit_process.json"


class SignPermitWorkflowFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
            self.fixture = json.load(handle)

    def test_fixture_is_public_source_inventory_only(self) -> None:
        self.assertEqual(self.fixture["processId"], "ppd_sign_permit_fixture_v1")
        self.assertEqual(self.fixture["permitType"], "sign_permit")
        self.assertTrue(self.fixture["fixtureOnly"])
        self.assertTrue(self.fixture["sourceInventoryOnly"])
        self.assertEqual(self.fixture["generatedFrom"], "existing_public_fixture_source_inventory")
        self.assertGreaterEqual(len(self.fixture["authoritySources"]), 5)
        for source in self.fixture["authoritySources"]:
            self.assertTrue(source["sourceId"].startswith("source_inventory_"))
            self.assertTrue(source["canonicalUrl"].startswith("https://www.portland.gov/ppd"))
            self.assertIn("authorityLabel", source)
            self.assertIn("recrawlCadenceHint", source)
            self.assertIn("evidenceUse", source)

    def test_required_facts_documents_and_file_rules_are_source_backed(self) -> None:
        source_ids = {source["sourceId"] for source in self.fixture["authoritySources"]}
        self.assertGreaterEqual(len(self.fixture["requiredFacts"]), 5)
        self.assertGreaterEqual(len(self.fixture["requiredDocuments"]), 5)
        self.assertGreaterEqual(len(self.fixture["fileRules"]), 3)

        for section_name in ("requiredFacts", "requiredDocuments", "fileRules"):
            for item in self.fixture[section_name]:
                self.assertIn("id", item)
                self.assertIn("evidence", item)
                self.assertTrue(item["evidence"])
                self.assertTrue(set(item["evidence"]).issubset(source_ids))

        document_ids = {document["id"] for document in self.fixture["requiredDocuments"]}
        self.assertIn("doc_sign_permit_application", document_ids)
        self.assertIn("doc_site_or_location_plan", document_ids)
        self.assertIn("doc_sign_drawings", document_ids)
        self.assertIn("doc_structural_or_engineering_support", document_ids)

    def test_stages_cover_sign_permit_workflow_gates(self) -> None:
        source_ids = {source["sourceId"] for source in self.fixture["authoritySources"]}
        stage_ids = [stage["id"] for stage in self.fixture["stages"]]
        expected_stage_ids = [
            "pre_application_research",
            "account_setup",
            "property_lookup",
            "permit_type_selection",
            "eligibility_screening",
            "document_preparation",
            "application_data_entry",
            "upload",
            "acknowledgment_certification",
            "submission",
            "prescreen_intake",
            "fee_payment",
            "plan_review_and_corrections",
            "approval_and_issuance",
            "inspections",
            "finalization_closeout",
        ]
        self.assertEqual(stage_ids, expected_stage_ids)

        for stage in self.fixture["stages"]:
            self.assertIn("kind", stage)
            self.assertIn("label", stage)
            self.assertIn("actionGates", stage)
            self.assertIn("evidence", stage)
            self.assertTrue(stage["evidence"])
            self.assertTrue(set(stage["evidence"]).issubset(source_ids))

    def test_action_gates_include_financial_consequential_and_read_only_stop_points(self) -> None:
        source_ids = {source["sourceId"] for source in self.fixture["authoritySources"]}
        gates = {gate["id"]: gate for gate in self.fixture["actionGates"]}
        gates.update({gate["id"]: gate for gate in self.fixture["feePaymentGates"]})
        gates.update({gate["id"]: gate for gate in self.fixture["inspectionFinalizationGates"]})

        required_gate_ids = {
            "gate_payment_confirmation",
            "gate_inspection_scheduling_confirmation",
            "gate_submission_confirmation",
            "gate_official_upload_confirmation",
            "gate_certification_confirmation",
            "gate_correction_upload_confirmation",
            "gate_finalization_status_review",
            "gate_status_is_read_only",
        }
        self.assertTrue(required_gate_ids.issubset(gates))
        self.assertEqual(gates["gate_payment_confirmation"]["classification"], "financial")
        self.assertEqual(gates["gate_inspection_scheduling_confirmation"]["classification"], "potentially_consequential")
        self.assertEqual(gates["gate_finalization_status_review"]["classification"], "safe_read_only")

        for gate in gates.values():
            self.assertIn("requiredCondition", gate)
            self.assertIn("evidence", gate)
            self.assertTrue(gate["evidence"])
            self.assertTrue(set(gate["evidence"]).issubset(source_ids))

        stop_points = set(self.fixture["agentStopPoints"])
        self.assertIn("pay_fees_or_enter_payment_details", stop_points)
        self.assertIn("official_correction_upload", stop_points)
        self.assertIn("schedule_inspection", stop_points)
        self.assertIn("submit_sign_permit_request", stop_points)

    def test_fixture_contains_no_private_or_live_crawl_artifacts(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        disallowed_markers = [
            "ppd/data/private",
            "storage_state",
            "storage-state",
            "auth_state",
            "auth-state",
            "cookies.json",
            "localstorage.json",
            "raw_crawl",
            "raw-crawl",
            "crawl_output",
            "crawl-output",
            "response body",
            "response_body",
            "trace.zip",
            "playwright-report",
            "/screenshots/",
            "screenshot.png",
            "/downloads/",
            "downloaded_documents",
            "password",
            "secret",
            "token",
            "mfa code",
            "captcha solution",
        ]
        for marker in disallowed_markers:
            self.assertNotIn(marker.lower(), serialized)

        policy = self.fixture["privateArtifactPolicy"]
        self.assertTrue(policy["fixtureContainsOnlyPublicMetadata"])
        self.assertTrue(policy["noLiveCrawlData"])
        self.assertTrue(policy["noPrivateAccountData"])
        self.assertTrue(policy["noDownloadedDocuments"])
        self.assertTrue(policy["noBrowserArtifacts"])
        self.assertTrue(policy["noResponseBodies"])


if __name__ == "__main__":
    unittest.main()
