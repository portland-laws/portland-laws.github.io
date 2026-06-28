from __future__ import annotations

import copy
import unittest
from pathlib import Path

from ppd.agent_readiness.inactive_guardrail_bundle_promotion_candidate_v1 import (
    OFFLINE_VALIDATION_COMMANDS,
    build_inactive_guardrail_bundle_promotion_candidate_v1_from_fixture,
    validate_inactive_guardrail_bundle_promotion_candidate_v1,
)


FIXTURE = Path(__file__).parent / "fixtures" / "agent_readiness" / "synthetic_guardrail_reviewer_packet_v1.json"


class InactiveGuardrailBundlePromotionCandidateV1Tests(unittest.TestCase):
    def _valid_packet(self) -> dict:
        return build_inactive_guardrail_bundle_promotion_candidate_v1_from_fixture(FIXTURE)

    def _assert_invalid_with(self, packet: dict, expected: str) -> None:
        result = validate_inactive_guardrail_bundle_promotion_candidate_v1(packet)
        self.assertFalse(result.valid)
        self.assertIn(expected, "; ".join(result.problems))

    def test_fixture_builds_valid_inactive_candidate_packet(self) -> None:
        packet = self._valid_packet()
        result = validate_inactive_guardrail_bundle_promotion_candidate_v1(packet)
        self.assertTrue(result.valid, result.problems)
        self.assertEqual(packet["offline_validation_commands"], OFFLINE_VALIDATION_COMMANDS)
        self.assertEqual(packet["reviewer_approval_references"][0]["approval_status"], "approved_by_synthetic_reviewer_packet")
        self.assertFalse(packet["reviewer_approval_references"][0]["activation_allowed"])

    def test_rejects_missing_required_review_and_inventory_sections(self) -> None:
        required_sections = (
            "reviewer_approval_references",
            "inactive_bundle_metadata",
            "source_evidence_placeholder_references",
            "deterministic_predicate_inventory",
            "deontic_predicate_inventory",
            "temporal_predicate_inventory",
            "reversible_gate_inventory",
            "refused_gate_inventory",
            "exact_confirmation_gate_inventory",
            "agent_facing_explanation_inventory",
            "release_blocker_notes",
            "rollback_notes",
            "offline_validation_commands",
        )
        for section in required_sections:
            with self.subTest(section=section):
                packet = self._valid_packet()
                packet.pop(section)
                self._assert_invalid_with(packet, f"{section} must be a non-empty list")

    def test_rejects_missing_reviewer_approval_cross_reference(self) -> None:
        packet = self._valid_packet()
        packet["inactive_bundle_metadata"][0].pop("reviewer_approval_ref")
        self._assert_invalid_with(packet, "inactive_bundle_metadata[0].reviewer_approval_ref is required")

    def test_rejects_missing_source_evidence_placeholder_contents(self) -> None:
        packet = self._valid_packet()
        packet["source_evidence_placeholder_references"][0]["source_evidence_ids"] = []
        self._assert_invalid_with(packet, "source_evidence_placeholder_references[0].source_evidence_ids must be non-empty")

    def test_rejects_missing_predicate_inventory_contents(self) -> None:
        packet = self._valid_packet()
        packet["deterministic_predicate_inventory"][0]["predicate_id"] = ""
        self._assert_invalid_with(packet, "deterministic_predicate_inventory[0].predicate_id is required")

    def test_rejects_missing_action_gate_inventory_contents(self) -> None:
        packet = self._valid_packet()
        packet["exact_confirmation_gate_inventory"][0]["gate_id"] = ""
        self._assert_invalid_with(packet, "exact_confirmation_gate_inventory[0].gate_id is required")

    def test_rejects_missing_explanation_release_blocker_and_rollback_contents(self) -> None:
        cases = (
            ("agent_facing_explanation_inventory", "template", "agent_facing_explanation_inventory[0].template is required"),
            ("release_blocker_notes", "note", "release_blocker_notes[0].note is required"),
            ("rollback_notes", "note", "rollback_notes[0].note is required"),
        )
        for section, field, expected in cases:
            with self.subTest(section=section, field=field):
                packet = self._valid_packet()
                packet[section][0][field] = ""
                self._assert_invalid_with(packet, expected)

    def test_rejects_private_raw_downloaded_artifact_references(self) -> None:
        cases = (
            ("raw crawl payload stored"),
            ("downloaded document archived"),
            ("private artifact retained"),
        )
        for value in cases:
            with self.subTest(value=value):
                packet = self._valid_packet()
                packet["release_blocker_notes"][0]["note"] = value
                self._assert_invalid_with(packet, "must not reference private artifacts")

    def test_rejects_live_crawl_devhub_and_activation_claims(self) -> None:
        cases = (
            "live crawl completed",
            "DevHub observed this workflow",
            "active guardrail activated",
        )
        for value in cases:
            with self.subTest(value=value):
                packet = self._valid_packet()
                packet["rollback_notes"][0]["note"] = value
                self._assert_invalid_with(packet, "must not reference private artifacts")

    def test_rejects_official_action_completion_and_legal_or_permitting_guarantees(self) -> None:
        cases = (
            "official action completed",
            "permit will be approved",
            "legal guarantee provided",
        )
        for value in cases:
            with self.subTest(value=value):
                packet = self._valid_packet()
                packet["agent_facing_explanation_inventory"][0]["template"] = value
                self._assert_invalid_with(packet, "must not guarantee outcomes or authorize consequential actions")

    def test_rejects_active_mutation_flags(self) -> None:
        packet = self._valid_packet()
        packet["active_guardrail_mutation"] = True
        self._assert_invalid_with(packet, "active_guardrail_mutation must be false")

        packet = self._valid_packet()
        packet["active_custom_mutation"] = True
        self._assert_invalid_with(packet, "active_custom_mutation must not set active mutation flags")

    def test_validation_does_not_mutate_packet(self) -> None:
        packet = self._valid_packet()
        before = copy.deepcopy(packet)
        validate_inactive_guardrail_bundle_promotion_candidate_v1(packet)
        self.assertEqual(packet, before)


if __name__ == "__main__":
    unittest.main()
