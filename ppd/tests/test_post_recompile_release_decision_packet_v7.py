from __future__ import annotations

import copy
import unittest
from pathlib import Path

from ppd.agent_readiness.post_recompile_release_decision_packet_v7 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    PACKET_TYPE,
    build_post_recompile_release_decision_packet_v7_from_fixture,
    validate_post_recompile_release_decision_packet_v7,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "post_recompile_release_decision_packet_v7"
REPLAY_FIXTURE = FIXTURE_DIR / "post_recompile_agent_readiness_replay_v7_fixture.json"


class PostRecompileReleaseDecisionPacketV7Test(unittest.TestCase):
    def _packet(self) -> dict:
        return build_post_recompile_release_decision_packet_v7_from_fixture(REPLAY_FIXTURE)

    def test_builds_fixture_first_release_decision_packet(self) -> None:
        packet = self._packet()

        self.assertEqual(packet["packet_type"], PACKET_TYPE)
        self.assertTrue(packet["fixture_first"])
        self.assertTrue(packet["post_recompile_replay_fixture_only"])
        self.assertFalse(packet["active_mutation"])
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

    def test_assembles_required_reviewer_sections(self) -> None:
        packet = self._packet()

        self.assertGreaterEqual(len(packet["go_no_go_rows"]), 7)
        self.assertTrue(packet["source_fixture_refs"])
        self.assertTrue(packet["unresolved_hold_inventory"])
        self.assertTrue(packet["citation_continuity_summaries"])
        self.assertTrue(packet["agent_compatibility_notes"])
        self.assertTrue(packet["inactive_guardrail_promotion_eligibility_placeholders"])
        self.assertTrue(packet["rollback_owner_placeholders"])
        self.assertTrue(packet["monitoring_handoff_reminders"])
        self.assertTrue(packet["reviewer_signoff_placeholders"])
        self.assertIn(packet["overall_recommendation"], {"NO_GO", "GO_WITH_CAVEATS"})
        self.assertTrue(all(row["activation_allowed"] is False for row in packet["go_no_go_rows"]))
        self.assertTrue(all(row["promotion_blocked"] is True for row in packet["unresolved_hold_inventory"]))
        self.assertTrue(all(row["signoff_required"] is True for row in packet["reviewer_signoff_placeholders"]))

    def test_validator_rejects_each_required_section_when_missing(self) -> None:
        required_sections = (
            "source_fixture_refs",
            "go_no_go_rows",
            "unresolved_hold_inventory",
            "citation_continuity_summaries",
            "agent_compatibility_notes",
            "inactive_guardrail_promotion_eligibility_placeholders",
            "rollback_owner_placeholders",
            "monitoring_handoff_reminders",
            "reviewer_signoff_placeholders",
            "offline_validation_commands",
            "validation_commands",
        )
        for section in required_sections:
            with self.subTest(section=section):
                packet = self._packet()
                packet[section] = []
                result = validate_post_recompile_release_decision_packet_v7(packet)
                self.assertFalse(result.valid)
                self.assertIn(f"{section} must be a non-empty list", result.problems)

    def test_validator_rejects_missing_readiness_replay_reference(self) -> None:
        packet = self._packet()
        packet["source_fixture_refs"] = [{"fixture_role": "other", "path": "fixture.json", "replay": "other"}]
        packet["consumes_only"] = {"post_recompile_agent_readiness_replay_v7_fixtures": False, "replay": "other"}
        result = validate_post_recompile_release_decision_packet_v7(packet)

        self.assertFalse(result.valid)
        self.assertIn("source_fixture_refs must include a post-recompile agent readiness replay v7 reference", result.problems)
        self.assertIn("consumes_only must require post-recompile agent readiness replay v7 fixtures", result.problems)
        self.assertIn("consumes_only.replay must be post_recompile_agent_readiness_replay_v7", result.problems)

    def test_validator_rejects_invalid_go_no_go_rows(self) -> None:
        packet = self._packet()
        packet["go_no_go_rows"][0] = copy.deepcopy(packet["go_no_go_rows"][0])
        packet["go_no_go_rows"][0]["activation_allowed"] = True
        packet["go_no_go_rows"][0]["manual_reviewer_decision_required"] = False
        packet["go_no_go_rows"][0]["recommendation"] = "GO"
        result = validate_post_recompile_release_decision_packet_v7(packet)

        self.assertFalse(result.valid)
        self.assertIn("go_no_go_rows[0].activation_allowed must be false", result.problems)
        self.assertIn("go_no_go_rows[0].manual_reviewer_decision_required must be true", result.problems)
        self.assertIn("go_no_go_rows[0].recommendation must be NO_GO or GO_WITH_CAVEATS", result.problems)

    def test_validator_rejects_required_placeholder_status_mutations(self) -> None:
        packet = self._packet()
        packet["unresolved_hold_inventory"][0]["promotion_blocked"] = False
        packet["citation_continuity_summaries"][0]["requires_manual_review"] = False
        packet["agent_compatibility_notes"][0]["requires_manual_review"] = False
        packet["inactive_guardrail_promotion_eligibility_placeholders"][0]["activation_allowed"] = True
        packet["rollback_owner_placeholders"][0]["active_state_changed"] = True
        packet["monitoring_handoff_reminders"][0]["handoff_required"] = False
        packet["reviewer_signoff_placeholders"][0]["signoff_required"] = False
        result = validate_post_recompile_release_decision_packet_v7(packet)

        self.assertFalse(result.valid)
        self.assertIn("unresolved_hold_inventory[0].promotion_blocked must be True", result.problems)
        self.assertIn("citation_continuity_summaries[0].requires_manual_review must be True", result.problems)
        self.assertIn("agent_compatibility_notes[0].requires_manual_review must be True", result.problems)
        self.assertIn("inactive_guardrail_promotion_eligibility_placeholders[0].activation_allowed must be False", result.problems)
        self.assertIn("rollback_owner_placeholders[0].active_state_changed must be False", result.problems)
        self.assertIn("monitoring_handoff_reminders[0].handoff_required must be True", result.problems)
        self.assertIn("reviewer_signoff_placeholders[0].signoff_required must be True", result.problems)

    def test_validator_rejects_active_activation_and_mutation_flags(self) -> None:
        packet = self._packet()
        packet["activation_executed"] = True
        packet["active_mutation"] = True
        packet["nested"] = {"active_mutation_flag": True}
        result = validate_post_recompile_release_decision_packet_v7(packet)

        self.assertFalse(result.valid)
        self.assertIn("activation_executed must be false", result.problems)
        self.assertIn("active_mutation must be false", result.problems)
        self.assertIn("packet.nested.active_mutation_flag contains an active mutation flag", result.problems)

    def test_validator_rejects_live_private_official_and_guarantee_claims(self) -> None:
        forbidden_examples = (
            ("active activation claim", "release is active"),
            ("live crawl execution claim", "ran live crawl"),
            ("private/session/auth artifact claim", "session token"),
            ("official-action completion claim", "submitted"),
            ("legal or permitting guarantee", "permit approval guaranteed"),
            ("active mutation claim", "active state changed"),
        )
        for label, text in forbidden_examples:
            with self.subTest(label=label):
                packet = self._packet()
                packet["reviewer_note"] = text
                result = validate_post_recompile_release_decision_packet_v7(packet)
                self.assertFalse(result.valid)
                self.assertTrue(any(label in problem for problem in result.problems), result.problems)

    def test_validator_rejects_private_or_auth_artifact_keys(self) -> None:
        packet = self._packet()
        packet["auth_state"] = {"stored": True}
        packet["raw_crawl_output"] = "artifact"
        result = validate_post_recompile_release_decision_packet_v7(packet)

        self.assertFalse(result.valid)
        self.assertIn("packet.auth_state must not include private, session, auth, raw, browser, trace, payment, or downloaded artifacts", result.problems)
        self.assertIn("packet.raw_crawl_output must not include private, session, auth, raw, browser, trace, payment, or downloaded artifacts", result.problems)


if __name__ == "__main__":
    unittest.main()
