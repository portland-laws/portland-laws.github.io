from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.agent_readiness.release_acceptance_review_packet import (
    PACKET_TYPE,
    ReleaseAcceptanceReviewPacketError,
    assert_valid_release_acceptance_review_packet,
    build_release_acceptance_review_packet,
    validate_release_acceptance_review_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "release_acceptance_review" / "input_packets.json"


class ReleaseAcceptanceReviewPacketTest(unittest.TestCase):
    def _inputs(self) -> dict[str, object]:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def _packet(self) -> dict[str, object]:
        return build_release_acceptance_review_packet(self._inputs())

    def test_builds_fixture_first_release_acceptance_review_packet(self) -> None:
        packet = self._packet()

        self.assertEqual(PACKET_TYPE, packet["packet_type"])
        self.assertTrue(packet["fixture_first"])
        self.assertEqual("pending_reviewer_acceptance", packet["review_status"])
        self.assertEqual([], list(validate_release_acceptance_review_packet(packet).problems))
        assert_valid_release_acceptance_review_packet(packet)

    def test_packet_consumes_all_required_source_packets(self) -> None:
        packet = self._packet()
        consumed = packet["consumed_packets"]

        self.assertEqual(
            {
                "source_registry_schedule_update_candidate",
                "requirement_rerun_work_queue_packet",
                "process_model_impact_review_packet",
                "devhub_surface_registry_reviewer_approval_packet",
                "agent_prompt_regression_dry_run_packet",
                "release_rollback_drill_outcome_review_packet",
            },
            set(consumed),
        )
        for consumed_packet in consumed.values():
            self.assertTrue(consumed_packet["packet_id"])
            self.assertTrue(consumed_packet["source_evidence_ids"])

    def test_packet_contains_cited_checklist_blockers_signoffs_and_reruns(self) -> None:
        packet = self._packet()

        checklist = packet["go_no_go_checklist_items"]
        self.assertEqual(6, len(checklist))
        self.assertTrue(all(item["source_evidence_ids"] for item in checklist))
        self.assertEqual({"go_pending_signoff"}, {item["go_no_go"] for item in checklist})

        blockers = packet["open_blocker_dispositions"]
        self.assertTrue(blockers)
        self.assertTrue(all(item["owner"] for item in blockers))
        self.assertTrue(all(item["source_evidence_ids"] for item in blockers))

        signoffs = packet["reviewer_owner_signoff_slots"]
        self.assertEqual(6, len(signoffs))
        self.assertEqual({"pending"}, {item["status"] for item in signoffs})
        self.assertTrue(all(item["source_evidence_ids"] for item in signoffs))

        reruns = packet["validation_rerun_expectations"]
        self.assertTrue(any(item["validation_id"] == "ppd-daemon-self-test" for item in reruns))
        self.assertTrue(all(item["writes_active_artifacts"] is False for item in reruns))

    def test_packet_attests_no_publication_or_artifact_mutation(self) -> None:
        packet = self._packet()

        attestations = packet["no_publication_no_artifact_mutation_attestations"]
        for key in (
            "no_publication_performed",
            "no_registry_mutation",
            "no_manifest_mutation",
            "no_requirement_mutation",
            "no_process_model_mutation",
            "no_guardrail_mutation",
            "no_prompt_mutation",
            "no_release_notes_mutation",
            "no_schedule_mutation",
            "no_agent_state_mutation",
            "no_artifact_mutation",
        ):
            self.assertTrue(attestations[key])

        effects = packet["release_effects"]
        self.assertTrue(effects)
        self.assertTrue(all(value is False for value in effects.values()))

    def test_validator_rejects_missing_citation_and_mutation_effect(self) -> None:
        packet = self._packet()
        packet["go_no_go_checklist_items"][0]["source_evidence_ids"] = []
        packet["release_effects"]["publishes_release"] = True

        result = validate_release_acceptance_review_packet(packet)

        self.assertFalse(result.valid)
        self.assertIn("go_no_go_checklist_items[0].source_evidence_ids is required", result.problems)
        self.assertIn("release_effects.publishes_release must be false", result.problems)
        with self.assertRaises(ReleaseAcceptanceReviewPacketError):
            assert_valid_release_acceptance_review_packet(packet)


if __name__ == "__main__":
    unittest.main()
