import copy
import json
import unittest
from pathlib import Path

from ppd.guardrail_consumer_contract_audit import (
    assert_valid_guardrail_consumer_contract_audit_packet,
    validate_guardrail_consumer_contract_audit_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "guardrail_consumer_contract_audit"


class GuardrailConsumerContractAuditValidationTest(unittest.TestCase):
    def setUp(self):
        with (FIXTURE_DIR / "valid_packet.json").open(encoding="utf-8") as handle:
            self.packet = json.load(handle)

    def finding_codes(self, packet):
        return {finding.code for finding in validate_guardrail_consumer_contract_audit_packet(packet)}

    def test_fixture_packet_is_valid(self):
        self.assertEqual([], validate_guardrail_consumer_contract_audit_packet(self.packet))
        assert_valid_guardrail_consumer_contract_audit_packet(self.packet)

    def test_rejects_uncited_contract_gap(self):
        packet = copy.deepcopy(self.packet)
        packet["contract_gaps"][0].pop("source_evidence_ids")

        self.assertIn("uncited_contract_gap", self.finding_codes(packet))

    def test_rejects_private_case_facts(self):
        packet = copy.deepcopy(self.packet)
        packet["private_case_facts"] = {"owner_phone": "private value"}

        self.assertIn("private_case_fact", self.finding_codes(packet))

    def test_rejects_local_private_paths(self):
        packet = copy.deepcopy(self.packet)
        packet["debug"] = {"source_path": "/home/alex/.config/devhub/auth_state.json"}

        self.assertIn("local_private_path", self.finding_codes(packet))

    def test_rejects_stale_current_claim_without_acknowledgement(self):
        packet = copy.deepcopy(self.packet)
        packet["current_claims"][1].pop("staleness_acknowledged")

        self.assertIn("stale_current_claim_without_acknowledgement", self.finding_codes(packet))

    def test_rejects_blocked_action_downgrade(self):
        packet = copy.deepcopy(self.packet)
        packet["next_safe_actions"].append(
            {
                "action_id": "submit_application",
                "classification": "reversible",
                "source_evidence_ids": ["ppd-devhub-guide-2026-05-08"],
            }
        )

        self.assertIn("blocked_action_downgrade", self.finding_codes(packet))

    def test_rejects_missing_manual_handoff_expectation(self):
        packet = copy.deepcopy(self.packet)
        packet["blocked_actions"][0].pop("manual_handoff_expectation")

        self.assertIn("missing_manual_handoff_expectation", self.finding_codes(packet))

    def test_rejects_live_llm_execution_claim(self):
        packet = copy.deepcopy(self.packet)
        packet["execution_claims"].append({"executor": "llm", "mode": "live", "status": "executed"})

        self.assertIn("live_execution_claim", self.finding_codes(packet))

    def test_rejects_live_devhub_execution_text_claim(self):
        packet = copy.deepcopy(self.packet)
        packet["notes"] = "DevHub executed the final upload during this audit."

        self.assertIn("live_execution_claim", self.finding_codes(packet))

    def test_rejects_enabled_consequential_controls(self):
        packet = copy.deepcopy(self.packet)
        packet["controls"][0]["enabled"] = True

        self.assertIn("enabled_consequential_control", self.finding_codes(packet))


if __name__ == "__main__":
    unittest.main()
