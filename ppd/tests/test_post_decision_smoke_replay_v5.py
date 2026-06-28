from __future__ import annotations

import copy
import unittest

from ppd.agent_readiness.post_decision_smoke_replay_v5 import (
    VALIDATION_COMMANDS,
    build_post_decision_smoke_replay_v5,
    validate_post_decision_smoke_replay_v5,
)


def _source_fixture() -> dict:
    return {
        "release_decision_packet_v5_refs": ["ppd/tests/fixtures/release_decision_packet_v5.json"],
        "inactive_guardrail_placeholder_fixture_refs": ["ppd/tests/fixtures/inactive_placeholder.json"],
        "release_decision_packet_v5": {
            "packet_version": "v5",
            "fixture_first": True,
            "inactive_candidate_fixture_only": True,
            "active_mutation": False,
            "active_guardrail_mutation": False,
            "active_release_state_mutation": False,
            "activation_executed": False,
            "opens_devhub": False,
            "reads_private_documents": False,
            "uploads": False,
            "submits": False,
            "certifies": False,
            "pays": False,
            "schedules": False,
            "legal_or_permitting_guarantee": False,
            "reviewer_go_no_go_recommendation": [
                {
                    "recommendation_id": "reviewer-release-decision-v5",
                    "recommendation": "NO_GO",
                    "activation_allowed": False,
                    "manual_reviewer_final_decision_required": True,
                }
            ],
            "unresolved_hold_inventory": [
                {
                    "hold_id": "hold-public-source-freshness",
                    "candidate_id": "candidate-fixture",
                    "promotion_blocked": True,
                }
            ],
            "source_freshness_clearance_status": [
                {
                    "clearance_id": "freshness-caveat-public-source",
                    "candidate_id": "candidate-fixture",
                    "activation_allowed": False,
                }
            ],
            "agent_api_compatibility_caveats": [
                {
                    "caveat_id": "agent-api-caveat::candidate-fixture",
                    "candidate_id": "candidate-fixture",
                    "requires_manual_review": True,
                }
            ],
            "rollback_owner_placeholders": [
                {
                    "rollback_owner_placeholder_id": "owner::candidate-fixture",
                    "candidate_id": "candidate-fixture",
                    "owner_assignment_status": "pending_manual_assignment",
                    "active_state_changed": False,
                }
            ],
            "agent_notification_notes": [
                {
                    "note_id": "agent-note-candidate-fixture",
                    "candidate_id": "candidate-fixture",
                    "notification_status": "draft_note_only",
                }
            ],
        },
        "inactive_guardrail_placeholder_fixtures": [
            {
                "fixture_kind": "inactive_guardrail_placeholder_fixture",
                "placeholder_id": "placeholder-candidate-fixture",
                "guardrail_bundle_id": "guardrail-bundle-placeholder",
                "placeholder_status": "inactive_placeholder_only",
                "activation_allowed": False,
            }
        ],
    }


class PostDecisionSmokeReplayV5Test(unittest.TestCase):
    def test_builds_valid_fixture_first_packet(self) -> None:
        packet = build_post_decision_smoke_replay_v5(_source_fixture())
        result = validate_post_decision_smoke_replay_v5(packet)
        self.assertTrue(result.valid, result.problems)
        self.assertEqual(packet["validation_commands"], VALIDATION_COMMANDS)

    def test_rejects_missing_required_references_and_rows(self) -> None:
        packet = build_post_decision_smoke_replay_v5(_source_fixture())
        packet["required_source_references"] = {
            "release_decision_packet_v5_refs": [],
            "inactive_guardrail_placeholder_fixture_refs": [],
        }
        for key in (
            "go_no_go_outcome_checks",
            "inactive_guardrail_placeholder_checks",
            "unresolved_hold_propagation",
            "source_freshness_caveat_checks",
            "agent_api_compatibility_checks",
            "rollback_owner_placeholders",
            "manual_handoff_reminders",
            "agent_notification_rows",
        ):
            packet[key] = []

        problems = validate_post_decision_smoke_replay_v5(packet).problems
        joined = "\n".join(problems)
        self.assertIn("required_source_references.release_decision_packet_v5_refs must be non-empty", joined)
        self.assertIn("required_source_references.inactive_guardrail_placeholder_fixture_refs must be non-empty", joined)
        self.assertIn("go_no_go_outcome_checks must be a non-empty list", joined)
        self.assertIn("inactive_guardrail_placeholder_checks must be a non-empty list", joined)
        self.assertIn("unresolved_hold_propagation must be a non-empty list", joined)
        self.assertIn("source_freshness_caveat_checks must be a non-empty list", joined)
        self.assertIn("agent_api_compatibility_checks must be a non-empty list", joined)
        self.assertIn("rollback_owner_placeholders must be a non-empty list", joined)
        self.assertIn("manual_handoff_reminders must be a non-empty list", joined)
        self.assertIn("agent_notification_rows must be a non-empty list", joined)

    def test_rejects_missing_validation_commands(self) -> None:
        packet = build_post_decision_smoke_replay_v5(_source_fixture())
        packet["validation_commands"] = []
        problems = validate_post_decision_smoke_replay_v5(packet).problems
        self.assertIn("validation_commands must contain only the PP&D daemon self-test command", problems)

    def test_rejects_prohibited_claims_and_artifacts(self) -> None:
        packet = build_post_decision_smoke_replay_v5(_source_fixture())
        packet["active_mutation"] = True
        packet["active_activation"] = True
        packet["session_state"] = {"path": "state.json"}
        packet["agent_notification_rows"][0]["message"] = "official action completed"
        packet["manual_handoff_reminders"][0]["reminder"] = "permit will be approved"

        problems = "\n".join(validate_post_decision_smoke_replay_v5(packet).problems)
        self.assertIn("active_mutation must not be true", problems)
        self.assertIn("active_activation must not be true", problems)
        self.assertIn("session_state must not contain private", problems)
        self.assertIn("official-action", problems)
        self.assertIn("guarantee", problems)

    def test_rejects_nested_active_mutation_flags(self) -> None:
        packet = build_post_decision_smoke_replay_v5(_source_fixture())
        nested = copy.deepcopy(packet)
        nested["go_no_go_outcome_checks"][0]["active_guardrail_mutation"] = True
        problems = "\n".join(validate_post_decision_smoke_replay_v5(nested).problems)
        self.assertIn("active_guardrail_mutation must not be true", problems)


if __name__ == "__main__":
    unittest.main()
