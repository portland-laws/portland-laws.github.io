from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.agent_readiness.dry_run_promotion_sequence_packet import (
    build_dry_run_promotion_sequence_packet,
    validate_dry_run_promotion_sequence_packet,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "agent_readiness" / "dry_run_promotion_sequence_source_decision_packet.json"


class DryRunPromotionSequencePacketTest(unittest.TestCase):
    def load_fixture(self) -> dict:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            return json.load(fixture_file)

    def test_builds_ordered_fixture_first_sequence_from_offline_decision_packet(self) -> None:
        packet = build_dry_run_promotion_sequence_packet(self.load_fixture())

        result = validate_dry_run_promotion_sequence_packet(packet)
        self.assertTrue(result.valid, result.problems)
        self.assertEqual(packet["packet_type"], "ppd.dry_run_promotion_sequence_packet.v1")
        self.assertTrue(packet["fixture_only"])
        self.assertEqual(packet["source_packet_type"], "ppd.offline_release_decision_packet.v1")
        self.assertEqual(packet["sequence_status"], "blocked")

        sequences = [step["sequence"] for step in packet["ordered_synthetic_promotion_steps"]]
        self.assertEqual(sequences, list(range(1, len(sequences) + 1)))
        self.assertTrue(all(step["synthetic_only"] for step in packet["ordered_synthetic_promotion_steps"]))
        self.assertTrue(all(step["writes_active_state"] is False for step in packet["ordered_synthetic_promotion_steps"]))

        affected_ids = set(packet["affected_artifact_ids"])
        self.assertIn("fixture-offline-release-decision-packet", affected_ids)
        self.assertIn("candidate-guardrail-bundle-2026-05-29", affected_ids)
        self.assertIn("validation-command-self-test", affected_ids)

        owners = {owner["role"] for owner in packet["reviewer_owners"]}
        self.assertEqual(owners, {"ppd_release_operator", "ppd_guardrail_reviewer"})
        abort_ids = {condition["condition_id"] for condition in packet["abort_conditions"]}
        self.assertIn("abort-on-active-state-write-request", abort_ids)
        self.assertIn("abort-on-blocker-reviewer-approval-pending", abort_ids)

    def test_packet_declares_no_active_ppd_state_effects(self) -> None:
        packet = build_dry_run_promotion_sequence_packet(self.load_fixture())

        self.assertEqual(
            packet["active_state_effects"],
            {
                "writes_active_registries": False,
                "writes_active_manifests": False,
                "writes_active_requirements": False,
                "writes_active_process_models": False,
                "writes_active_guardrails": False,
                "writes_source_indexes": False,
                "writes_agent_consumer_state": False,
                "promotes_release": False,
                "uses_live_network": False,
            },
        )
        self.assertTrue(all(item["writes_active_state"] is False for item in packet["rollback_order"]))
        rollback_ids = [item["rollback_id"] for item in packet["rollback_order"]]
        self.assertEqual(rollback_ids[:2], ["stop-before-active-state", "discard-synthetic-sequence"])
        self.assertIn("rollback-before-agent-consumer-boundary", rollback_ids)

    def test_validator_rejects_active_write_step(self) -> None:
        packet = build_dry_run_promotion_sequence_packet(self.load_fixture())
        packet["ordered_synthetic_promotion_steps"][0]["writes_active_state"] = True

        result = validate_dry_run_promotion_sequence_packet(packet)
        self.assertFalse(result.valid)
        self.assertTrue(any("active mutation" in problem or "must not write active state" in problem for problem in result.problems))


if __name__ == "__main__":
    unittest.main()
