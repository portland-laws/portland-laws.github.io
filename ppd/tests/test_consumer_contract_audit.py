from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.agent_readiness.consumer_contract_audit import (
    AUDIT_CATEGORIES,
    build_consumer_contract_audit_packet,
    validate_consumer_contract_audit_packet,
)


class ConsumerContractAuditTests(unittest.TestCase):
    def _fixture(self) -> dict:
        fixture_path = Path(__file__).parent / "fixtures" / "agent_readiness" / "guardrail_consumer_contract_audit_fixture.json"
        return json.loads(fixture_path.read_text(encoding="utf-8"))

    def test_builds_fixture_first_consumer_contract_gap_packet(self) -> None:
        fixture = self._fixture()
        packet = build_consumer_contract_audit_packet(
            consumer_integration_checklist=fixture["consumer_integration_checklist"],
            post_release_audit_findings=fixture["post_release_audit_findings"],
        )

        self.assertEqual(packet["packet_type"], "ppd.guardrail_consumer_contract_audit.v1")
        self.assertIs(packet["fixture_first"], True)
        self.assertIs(packet["metadata_only"], True)
        self.assertIs(packet["live_services_called"], False)
        self.assertIs(packet["consumers_invoked"], False)
        self.assertIs(packet["active_guardrail_bundles_changed"], False)
        self.assertEqual(packet["audit_categories"], list(AUDIT_CATEGORIES))

        gaps = packet["consumer_contract_gaps"]
        self.assertEqual([gap["category"] for gap in gaps], list(AUDIT_CATEGORIES))
        self.assertEqual(len(gaps), 7)
        for gap in gaps:
            self.assertTrue(gap["source_evidence_ids"])
            self.assertIn("consumer-contract-gap:", gap["gap_id"])
            self.assertTrue(gap["consumer_contract_gap"])
            self.assertTrue(gap["required_consumer_behavior"])

    def test_packet_citations_are_normalized_and_known(self) -> None:
        fixture = self._fixture()
        packet = build_consumer_contract_audit_packet(
            consumer_integration_checklist=fixture["consumer_integration_checklist"],
            post_release_audit_findings=fixture["post_release_audit_findings"],
        )

        evidence_ids = {item["source_evidence_id"] for item in packet["normalized_source_evidence"]}
        self.assertEqual(len(evidence_ids), 7)
        for gap in packet["consumer_contract_gaps"]:
            self.assertLessEqual(set(gap["source_evidence_ids"]), evidence_ids)

        validation = validate_consumer_contract_audit_packet(packet)
        self.assertTrue(validation.ready, validation.problems)

    def test_rejects_live_or_consumer_invoking_packet(self) -> None:
        fixture = self._fixture()
        packet = build_consumer_contract_audit_packet(
            consumer_integration_checklist=fixture["consumer_integration_checklist"],
            post_release_audit_findings=fixture["post_release_audit_findings"],
        )
        packet["consumers_invoked"] = True
        packet["live_services_called"] = True

        validation = validate_consumer_contract_audit_packet(packet)
        self.assertFalse(validation.ready)
        self.assertIn("consumers_invoked must be False", validation.problems)
        self.assertIn("live_services_called must be False", validation.problems)


if __name__ == "__main__":
    unittest.main()
