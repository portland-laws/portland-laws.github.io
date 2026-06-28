import copy
import json
import unittest
from pathlib import Path
from typing import Any

from ppd.logic.stale_guardrail_audit import build_stale_guardrail_audit_packet
from ppd.validation.stale_guardrail_audit_packet import (
    finding_codes,
    require_valid_stale_guardrail_audit_packet,
    validate_stale_guardrail_audit_packet,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "stale_guardrail_audit"
    / "source_registry_invalidation_packet.json"
)


class StaleGuardrailAuditTests(unittest.TestCase):
    def load_fixture(self) -> dict[str, Any]:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def build_packet(self) -> dict[str, Any]:
        return build_stale_guardrail_audit_packet(self.load_fixture())

    def test_builds_packet_without_recompiling_active_guardrails(self):
        fixture = self.load_fixture()
        original_active_bundle = copy.deepcopy(fixture["active_guardrail_bundle_inputs"])

        packet = build_stale_guardrail_audit_packet(fixture)

        self.assertEqual(packet["audit_mode"], "fixture_first_no_recompile")
        self.assertFalse(packet["recompiled_active_guardrails"])
        self.assertEqual(packet["guardrail_bundle_id"], "single_pdf_process_guardrails_active_v1")
        self.assertEqual(fixture["active_guardrail_bundle_inputs"], original_active_bundle)

    def test_lists_stale_predicates_explanations_refusals_and_confirmation_gates(self):
        packet = self.build_packet()

        self.assertEqual(
            [item["id"] for item in packet["stale_predicates"]],
            ["pred-fee-review-before-payment", "pred-single-pdf-required"],
        )
        self.assertEqual(
            [item["id"] for item in packet["stale_explanations"]],
            ["explain-fee-payment-gate", "explain-single-pdf-required"],
        )
        self.assertEqual(
            [item["id"] for item in packet["stale_refused_action_rules"]],
            ["refuse-submit-application", "refuse-submit-payment"],
        )
        self.assertEqual(
            [item["id"] for item in packet["stale_exact_confirmation_gates"]],
            ["confirm-submit-application", "confirm-submit-payment"],
        )

    def test_excludes_current_sources_from_stale_output(self):
        packet = self.build_packet()
        all_stale_ids = {
            item["id"]
            for group_name in (
                "stale_predicates",
                "stale_explanations",
                "stale_refused_action_rules",
                "stale_exact_confirmation_gates",
            )
            for item in packet[group_name]
        }

        self.assertNotIn("pred-property-address-known", all_stale_ids)
        self.assertEqual(
            {source["source_id"] for source in packet["changed_sources"]},
            {"src-fee-payment-guide", "src-submit-plans-online"},
        )

    def test_reports_required_human_review_by_changed_source(self):
        packet = self.build_packet()
        review_by_source = {item["source_id"]: item for item in packet["required_human_review"]}

        self.assertEqual(set(review_by_source), {"src-fee-payment-guide", "src-submit-plans-online"})
        self.assertIn("pred-single-pdf-required", review_by_source["src-submit-plans-online"]["stale_item_ids"])
        self.assertIn("confirm-submit-payment", review_by_source["src-fee-payment-guide"]["stale_item_ids"])
        self.assertIn("human review", review_by_source["src-submit-plans-online"]["review_reason"])

    def test_valid_stale_guardrail_audit_packet_passes_validation(self):
        packet = self.build_packet()

        findings = validate_stale_guardrail_audit_packet(packet)

        self.assertEqual(findings, [])
        require_valid_stale_guardrail_audit_packet(packet)

    def test_validation_rejects_missing_source_to_predicate_dependency_links(self):
        packet = self.build_packet()
        packet["stale_predicates"][0]["source_evidence_ids"] = []

        codes = finding_codes(validate_stale_guardrail_audit_packet(packet))

        self.assertIn("missing_source_dependency_link", codes)

    def test_validation_rejects_uncited_stale_claims(self):
        packet = self.build_packet()
        packet["stale_explanations"][0]["staleness_reasons"] = []

        codes = finding_codes(validate_stale_guardrail_audit_packet(packet))

        self.assertIn("uncited_stale_claim", codes)

    def test_validation_rejects_private_case_facts(self):
        packet = self.build_packet()
        packet["known_case_facts"] = {"applicant_name": "PRIVATE_VALUE_Jane Example"}

        codes = finding_codes(validate_stale_guardrail_audit_packet(packet))

        self.assertIn("private_case_fact", codes)

    def test_validation_rejects_unresolved_blockers_marked_current(self):
        packet = self.build_packet()
        packet["changed_sources"][0]["freshness_status"] = "current"
        packet["changed_sources"][0]["unresolved_blockers"] = ["Human review blocker is unresolved."]

        codes = finding_codes(validate_stale_guardrail_audit_packet(packet))

        self.assertIn("unresolved_blocker_marked_current", codes)

    def test_validation_rejects_consequential_action_enablement(self):
        packet = self.build_packet()
        packet["enabled_actions"] = ["submit_application"]

        codes = finding_codes(validate_stale_guardrail_audit_packet(packet))

        self.assertIn("consequential_action_enablement", codes)

    def test_validation_rejects_active_bundle_mutation(self):
        packet = self.build_packet()
        packet["recompiled_active_guardrails"] = True

        findings = validate_stale_guardrail_audit_packet(packet)
        codes = finding_codes(findings)

        self.assertIn("active_bundle_mutation", codes)
        with self.assertRaises(ValueError):
            require_valid_stale_guardrail_audit_packet(packet)


if __name__ == "__main__":
    unittest.main()
