from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from ppd.agent_readiness.inactive_guardrail_bundle_promotion_candidate_v5 import (
    OFFLINE_VALIDATION_COMMANDS,
    VALIDATION_COMMANDS,
    build_inactive_guardrail_bundle_promotion_candidate_v5_from_replay_fixtures,
    load_inactive_guardrail_bundle_promotion_candidate_v5,
    validate_inactive_guardrail_bundle_promotion_candidate_v5,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "inactive_guardrail_bundle_promotion_candidate_v5"
REPLAY_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_readiness_replay_v5"
VALID_PACKET = FIXTURE_DIR / "valid_packet.json"
REVIEWER_PACKET = REPLAY_FIXTURE_DIR / "guardrail_recompile_reviewer_packet_v5.json"
SYNTHETIC_REQUESTS = REPLAY_FIXTURE_DIR / "synthetic_agent_requests_v5.json"


class InactiveGuardrailBundlePromotionCandidateV5Tests(unittest.TestCase):
    def test_valid_fixture_loads(self) -> None:
        packet = load_inactive_guardrail_bundle_promotion_candidate_v5(VALID_PACKET)
        result = validate_inactive_guardrail_bundle_promotion_candidate_v5(packet)

        self.assertTrue(result.valid, result.problems)
        self.assertEqual(packet["packet_type"], "ppd.inactive_guardrail_promotion_candidate.v5")
        self.assertEqual(packet["offline_validation_commands"], OFFLINE_VALIDATION_COMMANDS)
        self.assertEqual(packet["validation_commands"], VALIDATION_COMMANDS)
        self.assertEqual(len(packet["inactive_promotion_rows"]), 3)
        self.assertTrue(all(row["candidate_status"] == "inactive_candidate_only" for row in packet["inactive_promotion_rows"]))
        self.assertTrue(all(row["activation_allowed"] is False for row in packet["inactive_promotion_rows"]))

    def test_builder_consumes_only_replay_v5_fixtures(self) -> None:
        packet = build_inactive_guardrail_bundle_promotion_candidate_v5_from_replay_fixtures(
            REVIEWER_PACKET,
            SYNTHETIC_REQUESTS,
        )

        self.assertEqual(packet["replay_source_versions"], ["guardrail_recompile_reviewer_packet_v5", "synthetic_agent_requests_v5"])
        self.assertTrue(packet["post_recompile_agent_readiness_replay_v5_fixtures_only"])
        self.assertEqual(
            [row["source_replay_response_id"] for row in packet["inactive_promotion_rows"]],
            ["missing-info-draft-only", "stale-and-conflicting-evidence", "confirmation-and-refusals"],
        )
        self.assertEqual(packet["unresolved_hold_inventory"][1]["stale_evidence_block"], True)
        self.assertEqual(packet["unresolved_hold_inventory"][2]["refused_actions_present"], True)

    def test_rejects_missing_required_sections(self) -> None:
        for key in (
            "replay_fixture_inputs",
            "inactive_promotion_rows",
            "activation_prerequisites",
            "unresolved_hold_inventory",
            "reviewer_signoff_placeholders",
            "source_freshness_clearance_criteria",
            "rollback_checkpoint_rows",
            "post_promotion_smoke_checks",
            "agent_notification_notes",
            "offline_validation_commands",
            "validation_commands",
        ):
            packet = self._valid_packet()
            packet.pop(key)

            result = validate_inactive_guardrail_bundle_promotion_candidate_v5(packet)

            self.assertFalse(result.valid, key)
            self.assertIn(f"{key} must be a non-empty list", result.problems)

    def test_rejects_activation_or_promotion_claims(self) -> None:
        cases = (
            ("active_guardrail_mutation", True),
            ("active_guardrail_bundle_mutation", True),
            ("guardrails_changed", True),
            ("promotion_executed", True),
            ("activation_executed", True),
            ("opens_devhub", True),
            ("reads_private_documents", True),
            ("uploads", True),
            ("submits", True),
            ("certifies", True),
            ("pays", True),
            ("schedules", True),
            ("legal_or_permitting_guarantee", True),
        )
        for key, value in cases:
            packet = self._valid_packet()
            packet[key] = value

            result = validate_inactive_guardrail_bundle_promotion_candidate_v5(packet)

            self.assertFalse(result.valid, key)
            self.assertIn(f"{key} must be false", result.problems)

    def test_rejects_invalid_row_statuses_and_clearance_claims(self) -> None:
        packet = self._valid_packet()
        packet["inactive_promotion_rows"][0]["candidate_status"] = "active"
        packet["inactive_promotion_rows"][0]["activation_allowed"] = True
        packet["activation_prerequisites"][0]["activation_allowed"] = True
        packet["unresolved_hold_inventory"][0]["promotion_blocked"] = False
        packet["reviewer_signoff_placeholders"][0]["signoff_status"] = "approved"
        packet["source_freshness_clearance_criteria"][0]["activation_allowed"] = True
        packet["rollback_checkpoint_rows"][0]["active_state_changed"] = True
        packet["post_promotion_smoke_checks"][0]["requires_separate_post_promotion_task"] = False
        packet["agent_notification_notes"][0]["notification_status"] = "sent"

        result = validate_inactive_guardrail_bundle_promotion_candidate_v5(packet)

        self.assertFalse(result.valid)
        self.assertIn("inactive_promotion_rows[0].candidate_status must remain inactive_candidate_only", result.problems)
        self.assertIn("inactive_promotion_rows[0].activation_allowed must be false", result.problems)
        self.assertIn("activation_prerequisites[0].activation_allowed must be False", result.problems)
        self.assertIn("unresolved_hold_inventory[0].promotion_blocked must be True", result.problems)
        self.assertIn("reviewer_signoff_placeholders[0].signoff_status must be 'pending_manual_review'", result.problems)
        self.assertIn("source_freshness_clearance_criteria[0].activation_allowed must be False", result.problems)
        self.assertIn("rollback_checkpoint_rows[0].active_state_changed must be False", result.problems)
        self.assertIn("post_promotion_smoke_checks[0].requires_separate_post_promotion_task must be True", result.problems)
        self.assertIn("agent_notification_notes[0].notification_status must be 'draft_note_only'", result.problems)

    def test_rejects_private_artifacts_official_actions_and_guarantees(self) -> None:
        forbidden_examples = (
            ("session_token", "private-token"),
            ("payment_details", {"card": "not allowed"}),
            ("operator_note", "opened DevHub and submitted the application"),
            ("legal_note", "legal advice and guarantee approval"),
            ("guardrail_note", "activated guardrail after review"),
        )
        for key, value in forbidden_examples:
            packet = self._valid_packet()
            packet[key] = value

            result = validate_inactive_guardrail_bundle_promotion_candidate_v5(packet)

            self.assertFalse(result.valid, key)

    def test_validation_does_not_mutate_packet(self) -> None:
        packet = self._valid_packet()
        before = copy.deepcopy(packet)

        validate_inactive_guardrail_bundle_promotion_candidate_v5(packet)

        self.assertEqual(packet, before)

    def _valid_packet(self) -> dict[str, object]:
        return copy.deepcopy(json.loads(VALID_PACKET.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
