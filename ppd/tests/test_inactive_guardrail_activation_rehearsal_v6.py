from __future__ import annotations

import copy
import unittest
from pathlib import Path

from ppd.agent_readiness.inactive_guardrail_activation_rehearsal_v6 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    PACKET_TYPE,
    build_inactive_guardrail_activation_rehearsal_v6_from_fixture,
    validate_inactive_guardrail_activation_rehearsal_v6,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "inactive_guardrail_activation_rehearsal_v6"
DECISION_PACKET_FIXTURE = FIXTURE_DIR / "post_recompile_release_decision_packet_v6_fixture.json"


class InactiveGuardrailActivationRehearsalV6Test(unittest.TestCase):
    def _packet(self) -> dict:
        return build_inactive_guardrail_activation_rehearsal_v6_from_fixture(DECISION_PACKET_FIXTURE)

    def test_builds_fixture_first_inactive_activation_rehearsal(self) -> None:
        packet = self._packet()

        self.assertEqual(packet["packet_type"], PACKET_TYPE)
        self.assertTrue(packet["fixture_first"])
        self.assertTrue(packet["inactive_rehearsal_only"])
        self.assertTrue(packet["post_recompile_release_decision_packet_v6_fixture_only"])
        self.assertFalse(packet["guardrails_activated"])
        self.assertFalse(packet["activation_executed"])
        self.assertFalse(packet["opens_devhub"])
        self.assertFalse(packet["crawls_live_sites"])
        self.assertFalse(packet["reads_private_documents"])
        self.assertFalse(packet["uploads"])
        self.assertFalse(packet["submits"])
        self.assertFalse(packet["certifies"])
        self.assertFalse(packet["pays"])
        self.assertFalse(packet["schedules"])
        self.assertFalse(packet["legal_or_permitting_guarantee"])
        self.assertEqual(packet["offline_validation_commands"], EXACT_OFFLINE_VALIDATION_COMMANDS)
        self.assertEqual(packet["validation_commands"], [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]])

    def test_stages_required_reviewer_controlled_rows(self) -> None:
        packet = self._packet()

        self.assertTrue(packet["reviewer_activation_checklist_rows"])
        self.assertTrue(packet["pre_activation_source_freshness_requirements"])
        self.assertTrue(packet["unresolved_hold_carry_forward_rules"])
        self.assertTrue(packet["smoke_replay_expectations"])
        self.assertTrue(packet["rollback_trigger_thresholds"])
        self.assertTrue(packet["agent_notification_placeholders"])
        self.assertTrue(packet["monitoring_watch_rows"])
        self.assertTrue(all(row["activation_allowed"] is False for row in packet["reviewer_activation_checklist_rows"]))
        self.assertTrue(all(row["carry_forward_required"] is True for row in packet["unresolved_hold_carry_forward_rules"]))
        self.assertTrue(all(row["sent"] is False for row in packet["agent_notification_placeholders"]))

    def test_validator_rejects_each_required_section_when_missing(self) -> None:
        sections = (
            "source_fixture_refs",
            "reviewer_activation_checklist_rows",
            "pre_activation_source_freshness_requirements",
            "unresolved_hold_carry_forward_rules",
            "smoke_replay_expectations",
            "rollback_trigger_thresholds",
            "agent_notification_placeholders",
            "monitoring_watch_rows",
            "offline_validation_commands",
            "validation_commands",
        )
        for section in sections:
            with self.subTest(section=section):
                packet = self._packet()
                packet[section] = []
                result = validate_inactive_guardrail_activation_rehearsal_v6(packet)
                self.assertFalse(result.valid)
                self.assertIn(f"{section} must be a non-empty list", result.problems)

    def test_validator_rejects_wrong_source_fixture_contract(self) -> None:
        packet = self._packet()
        packet["source_fixture_refs"] = [{"fixture_role": "other", "packet_type": "other", "path": "fixture.json"}]
        packet["consumes_only"] = {"post_recompile_release_decision_packet_v6_fixtures": False, "packet_type": "other"}
        result = validate_inactive_guardrail_activation_rehearsal_v6(packet)

        self.assertFalse(result.valid)
        self.assertIn("source_fixture_refs must include a post-recompile release decision packet v6 fixture reference", result.problems)
        self.assertIn("consumes_only must require post-recompile release decision packet v6 fixtures", result.problems)
        self.assertIn("consumes_only.packet_type must be ppd.post_recompile_release_decision_packet.v6", result.problems)

    def test_validator_rejects_row_status_mutations(self) -> None:
        packet = self._packet()
        packet["reviewer_activation_checklist_rows"][0] = copy.deepcopy(packet["reviewer_activation_checklist_rows"][0])
        packet["reviewer_activation_checklist_rows"][0]["reviewer_controlled"] = False
        packet["reviewer_activation_checklist_rows"][0]["activation_allowed"] = True
        packet["agent_notification_placeholders"][0]["sent"] = True
        packet["monitoring_watch_rows"][0]["watch_required"] = False
        result = validate_inactive_guardrail_activation_rehearsal_v6(packet)

        self.assertFalse(result.valid)
        self.assertIn("reviewer_activation_checklist_rows[0].reviewer_controlled must be True", result.problems)
        self.assertIn("reviewer_activation_checklist_rows[0].activation_allowed must be False", result.problems)
        self.assertIn("agent_notification_placeholders[0].sent must be False", result.problems)
        self.assertIn("monitoring_watch_rows[0].watch_required must be True", result.problems)

    def test_validator_rejects_active_live_private_official_and_guarantee_claims(self) -> None:
        forbidden_examples = (
            ("active guardrail claim", "guardrails activated"),
            ("live crawl or DevHub claim", "opened DevHub"),
            ("private artifact claim", "session token"),
            ("official-action completion claim", "submitted"),
            ("legal or permitting guarantee", "permit approval guaranteed"),
        )
        for label, text in forbidden_examples:
            with self.subTest(label=label):
                packet = self._packet()
                packet["reviewer_note"] = text
                result = validate_inactive_guardrail_activation_rehearsal_v6(packet)
                self.assertFalse(result.valid)
                self.assertTrue(any(label in problem for problem in result.problems), result.problems)

    def test_validator_rejects_private_or_auth_artifact_keys(self) -> None:
        packet = self._packet()
        packet["auth_state"] = {"stored": True}
        packet["raw_crawl_output"] = "artifact"
        result = validate_inactive_guardrail_activation_rehearsal_v6(packet)

        self.assertFalse(result.valid)
        self.assertIn("packet.auth_state must not include private, session, auth, raw, browser, trace, payment, or downloaded artifacts", result.problems)
        self.assertIn("packet.raw_crawl_output must not include private, session, auth, raw, browser, trace, payment, or downloaded artifacts", result.problems)


if __name__ == "__main__":
    unittest.main()
