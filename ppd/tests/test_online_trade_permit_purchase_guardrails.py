from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.logic.online_trade_permit_purchase_guardrails import compile_online_trade_purchase_guardrails


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrail_compiler" / "online_trade_permit_purchase.json"


class OnlineTradePermitPurchaseGuardrailTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.report = compile_online_trade_purchase_guardrails(self.fixture)

    def test_reports_missing_core_project_facts_from_fixture_only(self) -> None:
        missing_ids = {item["id"] for item in self.report["missing_facts"]}
        self.assertIn("property_identifier", missing_ids)
        self.assertIn("trade_work_scope", missing_ids)
        self.assertIn("fixture_or_equipment_count", missing_ids)
        self.assertIn("job_valuation", missing_ids)

    def test_reports_required_license_and_contractor_facts(self) -> None:
        missing_by_id = {item["id"]: item for item in self.report["missing_facts"]}
        self.assertEqual("license", missing_by_id["contractor_license_number"]["category"])
        self.assertEqual("contractor", missing_by_id["contractor_business_name"]["category"])
        self.assertEqual("license", missing_by_id["license_active_attestation"]["category"])

    def test_reports_required_document_acknowledgment_and_decision_gaps(self) -> None:
        self.assertEqual(["contractor_license_evidence"], [item["id"] for item in self.report["missing_documents"]])
        self.assertEqual(["online_purchase_terms_reviewed"], [item["id"] for item in self.report["missing_acknowledgments"]])
        self.assertEqual(["owner_or_contractor_purchase_authority"], [item["id"] for item in self.report["missing_decisions"]])

    def test_payment_stop_points_are_financial_and_blocked(self) -> None:
        gates = {gate["id"]: gate for gate in self.report["action_gates"]}
        self.assertEqual("financial", gates["enter_payment_details"]["classification"])
        self.assertEqual("blocked", gates["enter_payment_details"]["status"])
        self.assertEqual("financial", gates["pay_permit_fees"]["classification"])
        self.assertEqual("blocked", gates["pay_permit_fees"]["status"])

    def test_inspection_scheduling_cancellation_and_finalization_are_blocked(self) -> None:
        gates = {gate["id"]: gate for gate in self.report["action_gates"]}
        for gate_id in ("schedule_inspection", "cancel_permit_purchase", "finalize_purchase"):
            with self.subTest(gate_id=gate_id):
                self.assertEqual("consequential", gates[gate_id]["classification"])
                self.assertEqual("blocked", gates[gate_id]["status"])
                self.assertIn("missing exact session-specific user confirmation", gates[gate_id]["reasons"])

    def test_every_requested_item_and_action_gate_is_citation_backed(self) -> None:
        self.assertEqual([], self.report["citation_errors"])
        requested_groups = (
            self.report["missing_facts"],
            self.report["missing_documents"],
            self.report["missing_acknowledgments"],
            self.report["missing_decisions"],
        )
        for group in requested_groups:
            for item in group:
                with self.subTest(item=item["id"]):
                    self.assertTrue(item["citations"])
                    self.assertTrue(item["citations"][0].startswith("fixture://"))
        for gate in self.report["action_gates"]:
            with self.subTest(gate=gate["id"]):
                self.assertTrue(gate["citations"])
                self.assertTrue(gate["citations"][0].startswith("fixture://"))


if __name__ == "__main__":
    unittest.main()
