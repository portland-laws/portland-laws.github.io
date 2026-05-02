"""Validate the fixture-only online trade permit purchase workflow skeleton."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "permit_processes" / "online_trade_permit_purchase.json"


class OnlineTradePermitPurchaseFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)

    def test_fixture_is_public_fixture_only(self) -> None:
        self.assertTrue(self.fixture["fixtureOnly"])
        self.assertEqual(
            self.fixture["sourceMode"],
            "existing_public_fixture_and_source_inventory_evidence_only",
        )
        private_policy = self.fixture["privateDataPolicy"]
        self.assertFalse(private_policy["containsPrivateDevhubSession"])
        self.assertFalse(private_policy["containsCredentials"])
        self.assertFalse(private_policy["containsRawResponseBodies"])
        self.assertFalse(private_policy["containsDownloadedDocuments"])
        self.assertFalse(private_policy["containsScreenshotsOrTraces"])
        self.assertFalse(private_policy["liveCrawlRequired"])

    def test_required_sources_are_public_and_citation_targets_exist(self) -> None:
        sources = {source["sourceId"]: source for source in self.fixture["authoritySources"]}
        self.assertGreaterEqual(len(sources), 3)
        for source in sources.values():
            self.assertTrue(source["canonicalUrl"].startswith("https://www.portland.gov/ppd"))
            self.assertTrue(source["authorityLabel"].startswith("PP&D"))
            self.assertTrue(source["fixtureEvidenceOnly"])

        citation_holders = []
        citation_holders.extend(self.fixture["eligibilityFacts"])
        citation_holders.extend(self.fixture["requiredLicenseOrContractorFacts"])
        citation_holders.extend(self.fixture["stages"])
        citation_holders.extend(self.fixture["feePaymentGates"])
        citation_holders.extend(self.fixture["inspectionSchedulingStopPoints"])
        citation_holders.extend(self.fixture["citationBackedActionGates"])
        citation_holders.append(self.fixture["tradeScope"])
        for item in citation_holders:
            citation_ids = item.get("citationIds", [])
            self.assertTrue(citation_ids, item)
            for citation_id in citation_ids:
                self.assertIn(citation_id, sources)

    def test_eligibility_trade_scope_and_license_facts_are_present(self) -> None:
        eligibility_ids = {fact["factId"] for fact in self.fixture["eligibilityFacts"]}
        self.assertIn("project_property_identifier", eligibility_ids)
        self.assertIn("trade_permit_kind", eligibility_ids)
        self.assertIn("no_plan_review_required", eligibility_ids)
        self.assertIn("applicant_role", eligibility_ids)

        trade_kind = next(fact for fact in self.fixture["eligibilityFacts"] if fact["factId"] == "trade_permit_kind")
        self.assertEqual(trade_kind["allowedValues"], ["electrical", "mechanical", "plumbing"])

        excluded_scope = set(self.fixture["tradeScope"]["excluded"])
        self.assertIn("Trade permits with plan review", excluded_scope)
        self.assertIn("CAPTCHA, MFA, account creation, password recovery, or payment entry automation", excluded_scope)

        license_fact_ids = {fact["factId"] for fact in self.fixture["requiredLicenseOrContractorFacts"]}
        self.assertIn("contractor_business_name_or_owner_attestation", license_fact_ids)
        self.assertIn("contractor_license_identifier", license_fact_ids)
        self.assertIn("authorization_to_act", license_fact_ids)

    def test_payment_and_inspection_stop_points_fail_closed(self) -> None:
        payment_stop = next(gate for gate in self.fixture["feePaymentGates"] if gate["gateId"] == "payment_entry_stop")
        self.assertEqual(payment_stop["classification"], "financial")
        self.assertFalse(payment_stop["agentMayProceed"])
        self.assertTrue(payment_stop["requiresExactUserConfirmation"])

        inspection_stop = self.fixture["inspectionSchedulingStopPoints"][0]
        self.assertEqual(inspection_stop["classification"], "potentially_consequential")
        self.assertFalse(inspection_stop["agentMayProceed"])
        self.assertTrue(inspection_stop["requiresExactUserConfirmation"])

    def test_citation_backed_action_gates_cover_required_stops(self) -> None:
        gates = {gate["gateId"]: gate for gate in self.fixture["citationBackedActionGates"]}
        for gate_id in (
            "select_trade_permit_type_gate",
            "certification_stop_gate",
            "purchase_submission_stop_gate",
            "payment_stop_gate",
            "inspection_scheduling_stop_gate",
        ):
            self.assertIn(gate_id, gates)
            self.assertTrue(gates[gate_id]["citationIds"])

        for gate_id in (
            "certification_stop_gate",
            "purchase_submission_stop_gate",
            "payment_stop_gate",
            "inspection_scheduling_stop_gate",
        ):
            self.assertFalse(gates[gate_id]["agentMayProceed"])
            self.assertTrue(gates[gate_id]["requiresExactUserConfirmation"])


if __name__ == "__main__":
    unittest.main()
