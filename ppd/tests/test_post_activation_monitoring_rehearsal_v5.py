from __future__ import annotations

from pathlib import Path
import unittest

from ppd.agent_readiness.post_activation_monitoring_rehearsal_v5 import (
    VALIDATION_COMMANDS,
    build_post_activation_monitoring_rehearsal_v5,
    load_post_activation_monitoring_rehearsal_v5_fixture,
    validate_post_activation_monitoring_rehearsal_v5,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "post_activation_monitoring_rehearsal_v5" / "source_fixture.json"


class PostActivationMonitoringRehearsalV5Test(unittest.TestCase):
    def test_loads_fixture_first_monitoring_rehearsal(self) -> None:
        packet = load_post_activation_monitoring_rehearsal_v5_fixture(FIXTURE_PATH)
        result = validate_post_activation_monitoring_rehearsal_v5(packet)

        self.assertTrue(result.valid, result.problems)
        self.assertEqual(packet["packet_type"], "ppd.post_activation_monitoring_rehearsal.v5")
        self.assertEqual(packet["consumes_only"], {"inactive_activation_checklist_v5_fixtures": True})
        self.assertEqual(packet["validation_commands"], VALIDATION_COMMANDS)
        self.assertEqual(packet["boundaries"]["live_monitoring_enabled"], False)
        self.assertEqual(packet["boundaries"]["guardrail_activation_enabled"], False)
        self.assertEqual(packet["boundaries"]["devhub_opened"], False)
        self.assertEqual(packet["boundaries"]["live_site_crawl_enabled"], False)
        self.assertEqual(packet["boundaries"]["financial_action_enabled"], False)
        self.assertEqual(packet["attestations"]["legal_or_permitting_guarantees_made"], False)

        required_sections = (
            "guardrail_lookup_health_rows",
            "stale_source_stop_gate_rows",
            "exact_confirmation_gate_behavior_rows",
            "refused_consequential_and_financial_action_rows",
            "rollback_trigger_threshold_rows",
            "reviewer_escalation_routing_rows",
            "agent_notification_routing_rows",
            "exact_offline_validation_command_rows",
        )
        for section in required_sections:
            self.assertEqual(len(packet[section]), 1, section)

    def test_rejects_live_or_active_claims(self) -> None:
        packet = load_post_activation_monitoring_rehearsal_v5_fixture(FIXTURE_PATH)
        packet["boundaries"] = dict(packet["boundaries"])
        packet["boundaries"]["guardrail_activation_enabled"] = True

        result = validate_post_activation_monitoring_rehearsal_v5(packet)

        self.assertFalse(result.valid)
        self.assertTrue(any("boundaries" in problem or "guardrail_activation_enabled" in problem for problem in result.problems))

    def test_rejects_non_checklist_sources(self) -> None:
        source = {
            "inactive_activation_checklist_v5_fixtures": [
                {
                    "packet_type": "ppd.inactive_activation_checklist.v4",
                    "packet_version": "v4",
                    "packet_id": "wrong-version",
                    "validation_commands": VALIDATION_COMMANDS,
                }
            ]
        }

        with self.assertRaises(ValueError):
            build_post_activation_monitoring_rehearsal_v5(source)


if __name__ == "__main__":
    unittest.main()
