from __future__ import annotations

import copy
import unittest
from pathlib import Path

from ppd.agent_readiness.guardrail_bundle_recompile_candidate_v4 import REQUIRED_CHANGE_CATEGORIES
from ppd.agent_readiness.guardrail_recompile_reviewer_packet_v5 import (
    OFFLINE_VALIDATION_COMMANDS,
    REQUIRED_ATTESTATIONS,
    load_guardrail_recompile_reviewer_packet_v5_manifest,
    validate_guardrail_recompile_reviewer_packet_v5,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "guardrail_recompile_reviewer_packet_v5"
MANIFEST = FIXTURE_DIR / "input_manifest.json"


class GuardrailRecompileReviewerPacketV5Test(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = load_guardrail_recompile_reviewer_packet_v5_manifest(MANIFEST)

    def test_builds_v5_review_packet_from_candidate_fixture_reference(self) -> None:
        self.assertEqual(self.packet["packet_type"], "ppd.guardrail_recompile_reviewer_packet.v5")
        self.assertEqual(self.packet["packet_version"], "v5")
        self.assertEqual(self.packet["candidate_packet_type"], "ppd.guardrail_bundle_recompile_candidate.v4")
        self.assertEqual(set(self.packet["consumes"]), {"guardrail_bundle_recompile_candidate_v4_fixture"})
        self.assertEqual(self.packet["attestations"], REQUIRED_ATTESTATIONS)
        result = validate_guardrail_recompile_reviewer_packet_v5(self.packet)
        self.assertTrue(result.valid, result.problems)

    def test_reviewer_ready_rows_and_source_evidence_refs_are_required(self) -> None:
        rows = self.packet["reviewer_predicate_rows"]
        self.assertEqual(tuple(row["category"] for row in rows), REQUIRED_CHANGE_CATEGORIES)
        for row in rows:
            self.assertEqual(row["review_status"], "pending_human_review")
            self.assertEqual(row["reviewer_hold_status"], "unresolved")
            self.assertFalse(row["active_bundle_mutation"])
            self.assertTrue(row["reviewer_ready_predicate"])
            self.assertTrue(row["source_evidence_refs"])
            self.assertGreater(row["process_impact_reference_count"], 0)

    def test_packet_has_v5_required_review_sections(self) -> None:
        for section in (
            "candidate_guardrail_bundle_ids",
            "source_evidence_references",
            "source_freshness_caveats",
            "stale_source_hold_summaries",
            "exact_confirmation_checkpoint_summaries",
            "refused_action_summaries",
            "rollback_owner_placeholders",
            "reviewer_decision_placeholders",
        ):
            self.assertTrue(self.packet[section], section)

    def test_validation_commands_are_exact_offline_commands_only(self) -> None:
        self.assertEqual(self.packet["offline_validation_commands"], OFFLINE_VALIDATION_COMMANDS)
        self.assertEqual(self.packet["validation_status"]["validation_commands"], OFFLINE_VALIDATION_COMMANDS)
        self.assertFalse(self.packet["validation_status"]["active_bundle_mutation"])

    def test_validator_rejects_missing_required_top_level_sections(self) -> None:
        required_sections = (
            "candidate_guardrail_bundle_ids",
            "source_evidence_references",
            "source_freshness_caveats",
            "stale_source_hold_summaries",
            "exact_confirmation_checkpoint_summaries",
            "refused_action_summaries",
            "rollback_owner_placeholders",
            "reviewer_decision_placeholders",
            "offline_validation_commands",
        )
        for section in required_sections:
            with self.subTest(section=section):
                broken = copy.deepcopy(self.packet)
                broken[section] = []
                result = validate_guardrail_recompile_reviewer_packet_v5(broken)
                self.assertFalse(result.valid)

    def test_validator_rejects_missing_consumed_candidate_reference(self) -> None:
        broken = copy.deepcopy(self.packet)
        broken["consumes"] = {}
        result = validate_guardrail_recompile_reviewer_packet_v5(broken)
        self.assertFalse(result.valid)
        self.assertIn("consumes must contain only guardrail_bundle_recompile_candidate_v4_fixture", result.problems)

    def test_validator_rejects_incomplete_reviewer_rows_and_evidence_refs(self) -> None:
        cases = (
            ("reviewer_ready_predicate", ""),
            ("source_evidence_refs", []),
            ("reviewer_hold_status", "resolved"),
            ("active_bundle_mutation", True),
        )
        for key, value in cases:
            with self.subTest(key=key):
                broken = copy.deepcopy(self.packet)
                broken["reviewer_predicate_rows"][0][key] = value
                result = validate_guardrail_recompile_reviewer_packet_v5(broken)
                self.assertFalse(result.valid)

    def test_validator_rejects_incomplete_summaries_and_placeholders(self) -> None:
        cases = (
            ("source_evidence_references", 0, "citation_refs", []),
            ("source_freshness_caveats", 0, "predicate", ""),
            ("stale_source_hold_summaries", 0, "citation_refs", []),
            ("exact_confirmation_checkpoint_summaries", 0, "boundary", ""),
            ("refused_action_summaries", 0, "predicate", ""),
            ("rollback_owner_placeholders", 0, "rollback_owner_placeholder", ""),
            ("reviewer_decision_placeholders", 0, "release_state", "released"),
        )
        for section, index, key, value in cases:
            with self.subTest(section=section, key=key):
                broken = copy.deepcopy(self.packet)
                broken[section][index][key] = value
                result = validate_guardrail_recompile_reviewer_packet_v5(broken)
                self.assertFalse(result.valid)

    def test_validator_rejects_active_mutation_private_completion_and_guarantee_claims(self) -> None:
        cases = (
            ("active_guardrail_mutation", True),
            ("active_mutation", True),
            ("guardrail_mutation_claim", True),
            ("session_state_path", "private/session.json"),
            ("auth_state", "auth.json"),
            ("review_note", "official action completed"),
            ("legal_note", "permit will be approved"),
            ("mutation_note", "active guardrail mutation applied"),
        )
        for key, value in cases:
            with self.subTest(key=key):
                broken = copy.deepcopy(self.packet)
                broken[key] = value
                result = validate_guardrail_recompile_reviewer_packet_v5(broken)
                self.assertFalse(result.valid)

    def test_fixture_path_is_local_to_ppd_tests(self) -> None:
        self.assertEqual(FIXTURE_DIR, Path(__file__).parent / "fixtures" / "guardrail_recompile_reviewer_packet_v5")


if __name__ == "__main__":
    unittest.main()
