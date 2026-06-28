from __future__ import annotations

import copy
import unittest
from pathlib import Path

from ppd.agent_readiness.inactive_guardrail_promotion_rehearsal_v7 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    PACKET_TYPE,
    build_inactive_guardrail_promotion_rehearsal_v7_from_fixture,
    validate_inactive_guardrail_promotion_rehearsal_v7,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "inactive_guardrail_promotion_rehearsal_v7"
RELEASE_DECISION_FIXTURE = FIXTURE_DIR / "post_recompile_release_decision_packet_v7.json"


class InactiveGuardrailPromotionRehearsalV7Test(unittest.TestCase):
    def _packet(self) -> dict:
        return build_inactive_guardrail_promotion_rehearsal_v7_from_fixture(RELEASE_DECISION_FIXTURE)

    def test_builds_fixture_first_rehearsal_from_release_decision_v7_only(self) -> None:
        packet = self._packet()

        self.assertEqual(packet["packet_type"], PACKET_TYPE)
        self.assertTrue(packet["fixture_first"])
        self.assertTrue(packet["inactive_guardrail_promotion_rehearsal_only"])
        self.assertTrue(packet["post_recompile_release_decision_packet_v7_fixtures_only"])
        self.assertEqual(
            packet["consumes_only"],
            {
                "post_recompile_release_decision_packet_v7_fixtures": True,
                "packet_type": "ppd.post_recompile_release_decision_packet.v7",
                "packet_version": "v7",
            },
        )
        self.assertEqual(
            packet["source_fixture_refs"],
            [{"fixture_role": "post_recompile_release_decision_packet_v7", "path": RELEASE_DECISION_FIXTURE.as_posix()}],
        )

    def test_assembles_reviewer_controlled_rows_and_carry_forward_sections(self) -> None:
        packet = self._packet()

        self.assertGreaterEqual(len(packet["reviewer_controlled_promotion_checklist_rows"]), 2)
        self.assertTrue(packet["unresolved_hold_carry_forward_conditions"])
        self.assertTrue(packet["pre_promotion_source_freshness_reminders"])
        self.assertTrue(packet["agent_notification_placeholders"])
        self.assertTrue(packet["rollback_checkpoint_references"])
        self.assertTrue(packet["monitoring_watch_rows"])
        self.assertTrue(all(row["reviewer_controlled"] is True for row in packet["reviewer_controlled_promotion_checklist_rows"]))
        self.assertTrue(all(row["promotion_allowed"] is False for row in packet["reviewer_controlled_promotion_checklist_rows"]))
        self.assertTrue(all(row["activation_allowed"] is False for row in packet["reviewer_controlled_promotion_checklist_rows"]))
        self.assertTrue(all(row["promotion_blocked"] is True for row in packet["unresolved_hold_carry_forward_conditions"]))
        self.assertTrue(all(row["all_sources_confirmed_fresh"] is False for row in packet["pre_promotion_source_freshness_reminders"]))
        self.assertTrue(all(row["active_agent_change_allowed"] is False for row in packet["agent_notification_placeholders"]))
        self.assertTrue(all(row["active_state_changed"] is False for row in packet["rollback_checkpoint_references"]))
        self.assertTrue(all(row["watch_status"] == "planned_offline_watch_only" for row in packet["monitoring_watch_rows"]))

    def test_keeps_boundary_flags_and_validation_commands_offline(self) -> None:
        packet = self._packet()

        self.assertEqual(packet["offline_validation_commands"], EXACT_OFFLINE_VALIDATION_COMMANDS)
        self.assertEqual(packet["validation_commands"], [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]])
        flattened = " ".join(part for command in packet["offline_validation_commands"] for part in command).lower()
        for forbidden in ["curl", "wget", "playwright", "devhub", "captcha", "mfa"]:
            self.assertNotIn(forbidden, flattened)

        for flag in [
            "active_guardrail_mutation",
            "active_guardrail_bundle_mutation",
            "active_prompt_mutation",
            "active_process_model_mutation",
            "active_requirement_mutation",
            "active_source_mutation",
            "active_devhub_surface_mutation",
            "active_release_state_mutation",
            "active_mutation",
            "guardrails_changed",
            "guardrail_bundles_changed",
            "promotion_executed",
            "activation_executed",
            "opens_devhub",
            "crawls_live_sites",
            "reads_private_documents",
            "uploads",
            "submits",
            "certifies",
            "pays",
            "schedules",
            "legal_or_permitting_guarantee",
        ]:
            self.assertFalse(packet[flag], flag)

        result = validate_inactive_guardrail_promotion_rehearsal_v7(packet)
        self.assertTrue(result.valid, result.problems)
        self.assertEqual(result.problems, ())

    def test_rejects_missing_required_sections(self) -> None:
        required_sections = (
            "source_fixture_refs",
            "reviewer_controlled_promotion_checklist_rows",
            "unresolved_hold_carry_forward_conditions",
            "pre_promotion_source_freshness_reminders",
            "agent_notification_placeholders",
            "rollback_checkpoint_references",
            "monitoring_watch_rows",
            "offline_validation_commands",
            "validation_commands",
        )
        for section in required_sections:
            with self.subTest(section=section):
                packet = self._packet()
                packet[section] = []
                result = validate_inactive_guardrail_promotion_rehearsal_v7(packet)
                self.assertFalse(result.valid)
                self.assertIn(f"{section} must be a non-empty list", result.problems)

    def test_rejects_row_mutations_that_would_allow_promotion_or_activation(self) -> None:
        packet = self._packet()
        packet["reviewer_controlled_promotion_checklist_rows"][0]["promotion_allowed"] = True
        packet["reviewer_controlled_promotion_checklist_rows"][0]["activation_allowed"] = True
        packet["unresolved_hold_carry_forward_conditions"][0]["promotion_blocked"] = False
        packet["pre_promotion_source_freshness_reminders"][0]["all_sources_confirmed_fresh"] = True
        packet["agent_notification_placeholders"][0]["active_agent_change_allowed"] = True
        packet["rollback_checkpoint_references"][0]["active_state_changed"] = True
        packet["monitoring_watch_rows"][0]["watch_status"] = "running"
        result = validate_inactive_guardrail_promotion_rehearsal_v7(packet)

        self.assertFalse(result.valid)
        self.assertIn("reviewer_controlled_promotion_checklist_rows[0].promotion_allowed must be false", result.problems)
        self.assertIn("reviewer_controlled_promotion_checklist_rows[0].activation_allowed must be false", result.problems)
        self.assertIn("unresolved_hold_carry_forward_conditions[0].promotion_blocked must be true", result.problems)
        self.assertIn("pre_promotion_source_freshness_reminders[0].all_sources_confirmed_fresh must be false", result.problems)
        self.assertIn("agent_notification_placeholders[0].active_agent_change_allowed must be false", result.problems)
        self.assertIn("rollback_checkpoint_references[0].active_state_changed must be false", result.problems)
        self.assertIn("monitoring_watch_rows[0].watch_status must be planned_offline_watch_only", result.problems)

    def test_rejects_live_private_official_and_guarantee_claims(self) -> None:
        forbidden_examples = (
            ("activation claim", "release is active"),
            ("live system claim", "live crawl"),
            ("artifact claim", "session token"),
            ("official action claim", "paid fee"),
            ("guarantee claim", "permit approval guaranteed"),
        )
        for label, text in forbidden_examples:
            with self.subTest(label=label):
                packet = self._packet()
                packet["reviewer_note"] = text
                result = validate_inactive_guardrail_promotion_rehearsal_v7(packet)
                self.assertFalse(result.valid)
                self.assertTrue(any(label in problem for problem in result.problems), result.problems)

    def test_rejects_private_or_auth_artifact_keys(self) -> None:
        packet = self._packet()
        packet["auth_state"] = {"stored": True}
        packet["raw_crawl_output"] = "artifact"
        result = validate_inactive_guardrail_promotion_rehearsal_v7(packet)

        self.assertFalse(result.valid)
        self.assertIn("packet.auth_state must not include private, session, auth, raw, browser, trace, payment, or downloaded artifacts", result.problems)
        self.assertIn("packet.raw_crawl_output must not include private, session, auth, raw, browser, trace, payment, or downloaded artifacts", result.problems)

    def test_rejects_wrong_source_fixture_family(self) -> None:
        packet = self._packet()
        packet["source_fixture_refs"] = [{"fixture_role": "post_recompile_agent_readiness_replay_v7", "path": "fixture.json"}]
        packet["consumes_only"] = {"post_recompile_release_decision_packet_v7_fixtures": False}
        result = validate_inactive_guardrail_promotion_rehearsal_v7(packet)

        self.assertFalse(result.valid)
        self.assertIn("source_fixture_refs must include a post-recompile release decision packet v7 fixture path", result.problems)
        self.assertIn("consumes_only must require post-recompile release decision packet v7 fixtures", result.problems)


if __name__ == "__main__":
    unittest.main()
