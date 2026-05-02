"""Validate the fixture-only FCC wireless application permit process skeleton."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import unittest


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "permit_processes"
    / "fcc_wireless_application_process.json"
)


class FccWirelessApplicationProcessFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)
        self.process: dict[str, Any] = self.fixture["process"]
        self.source_ids = {
            source["id"] for source in self.fixture["sourceInventoryEvidence"]
        }

    def test_fixture_scope_is_existing_public_evidence_only(self) -> None:
        self.assertEqual("fcc_wireless_application", self.process["id"])
        self.assertEqual("FCC wireless application", self.process["permitType"])
        self.assertEqual(
            "fixture_only_existing_public_source_inventory_evidence",
            self.fixture["fixtureScope"],
        )
        basis = self.process["evidenceBasis"]
        self.assertTrue(basis["usesExistingPublicFixturesOnly"])
        self.assertFalse(basis["usesLiveCrawl"])
        self.assertFalse(basis["usesAuthenticatedDevhubSession"])
        self.assertFalse(basis["usesRawResponseBodies"])
        self.assertSetEqual(set(self.process["authoritySourceIds"]), self.source_ids)

    def test_stages_cover_fcc_wireless_workflow_skeleton(self) -> None:
        stage_ids = {stage["id"] for stage in self.process["stages"]}
        expected_stage_ids = {
            "pre_application_research",
            "account_setup",
            "property_lookup",
            "select_request_type",
            "eligibility_screening",
            "document_preparation",
            "application_data_entry",
            "upload_package",
            "acknowledgment_certification",
            "submission",
            "prescreen_intake",
            "fee_payment_gate",
            "plan_review",
            "corrections_checksheets",
            "approval_issuance",
            "inspections",
            "closeout_finalization",
        }
        self.assertTrue(expected_stage_ids.issubset(stage_ids))
        self._assert_all_evidence_is_source_inventory_backed(self.process["stages"])

    def test_required_facts_documents_and_file_rules_are_cited(self) -> None:
        fact_ids = {fact["id"] for fact in self.process["requiredFacts"]}
        self.assertTrue(
            {
                "site_property_identifier",
                "applicant_contact",
                "wireless_facility_scope",
                "responsible_party_authorization",
            }.issubset(fact_ids)
        )

        document_ids = {document["id"] for document in self.process["requiredDocuments"]}
        self.assertTrue(
            {
                "fcc_wireless_application_pdf",
                "wireless_drawing_plan_set",
                "supporting_calculations_reports",
                "authorization_or_signature_document",
            }.issubset(document_ids)
        )

        file_rule_ids = {rule["id"] for rule in self.process["fileRules"]}
        self.assertTrue(
            {
                "single_searchable_plan_pdf",
                "supporting_documents_pdf",
                "devhub_upload_preview_only",
            }.issubset(file_rule_ids)
        )

        self._assert_all_evidence_is_source_inventory_backed(self.process["requiredFacts"])
        self._assert_all_evidence_is_source_inventory_backed(self.process["requiredDocuments"])
        self._assert_all_evidence_is_source_inventory_backed(self.process["fileRules"])

    def test_payment_inspection_finalization_and_action_gates_fail_closed(self) -> None:
        financial_gates = self.process["feePaymentGates"]
        self.assertEqual(1, len(financial_gates))
        self.assertEqual("financial", financial_gates[0]["classification"])

        finalization_gate_ids = {
            gate["id"] for gate in self.process["inspectionFinalizationGates"]
        }
        self.assertIn("inspection_scheduling_requires_exact_confirmation", finalization_gate_ids)
        self.assertIn("finalization_status_requires_resolved_gates", finalization_gate_ids)

        action_gates = {gate["id"]: gate for gate in self.process["actionGates"]}
        for gate_id in (
            "official_upload_stop",
            "certification_stop",
            "submit_application_stop",
            "payment_stop",
            "correction_upload_stop",
            "inspection_schedule_stop",
        ):
            with self.subTest(gate_id=gate_id):
                gate = action_gates[gate_id]
                self.assertIn(gate["classification"], {"consequential", "financial"})
                self.assertTrue(gate["requiresExactUserConfirmation"])
                self.assertTrue(set(gate["evidence"]).issubset(self.source_ids))

        self.assertFalse(action_gates["read_public_guidance"]["requiresExactUserConfirmation"])
        self.assertFalse(action_gates["draft_reversible_fields"]["requiresExactUserConfirmation"])
        self.assertFalse(action_gates["preview_upload_package"]["requiresExactUserConfirmation"])

    def test_source_inventory_evidence_is_public_and_fixture_only(self) -> None:
        for source in self.fixture["sourceInventoryEvidence"]:
            with self.subTest(source_id=source["id"]):
                self.assertTrue(source["sourceInventoryOnly"])
                self.assertTrue(source["canonicalUrl"].startswith("https://www.portland.gov/"))
                self.assertTrue(source["authorityLabel"].strip())
                self.assertTrue(source["supports"])

    def test_fixture_does_not_embed_private_or_raw_artifacts(self) -> None:
        forbidden_value_fragments = (
            "ppd/data/private",
            "ppd\\data\\private",
            "storage_state",
            "storage-state",
            "auth_state",
            "auth-state",
            "cookies.json",
            "localstorage.json",
            "trace.zip",
            "/traces/",
            "\\traces\\",
            "/screenshots/",
            "\\screenshots\\",
            "screenshot.png",
            "screenshot.jpg",
            "/response-bodies/",
            "\\response-bodies\\",
            "raw_crawl_output",
            "download_path",
            "downloaded_document_path",
            "password=",
            "access_token",
            "refresh_token",
            "ssn",
        )
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for fragment in forbidden_value_fragments:
            with self.subTest(fragment=fragment):
                self.assertNotIn(fragment.lower(), serialized)

        forbidden_keys = {
            "body",
            "responseBody",
            "rawBody",
            "rawResponseBody",
            "htmlBody",
            "screenshotPath",
            "tracePath",
            "credentialPath",
            "sessionPath",
            "authStatePath",
        }
        self._assert_forbidden_keys_absent(self.fixture, forbidden_keys)

    def _assert_all_evidence_is_source_inventory_backed(
        self, entries: list[dict[str, Any]]
    ) -> None:
        for entry in entries:
            with self.subTest(entry_id=entry["id"]):
                evidence = set(entry["evidence"])
                self.assertTrue(evidence)
                self.assertTrue(evidence.issubset(self.source_ids))

    def _assert_forbidden_keys_absent(
        self, value: Any, forbidden_keys: set[str]
    ) -> None:
        if isinstance(value, dict):
            for key, nested_value in value.items():
                self.assertNotIn(key, forbidden_keys)
                self._assert_forbidden_keys_absent(nested_value, forbidden_keys)
        elif isinstance(value, list):
            for nested_value in value:
                self._assert_forbidden_keys_absent(nested_value, forbidden_keys)


if __name__ == "__main__":
    unittest.main()
