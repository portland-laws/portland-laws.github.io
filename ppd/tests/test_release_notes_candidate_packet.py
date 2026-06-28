from __future__ import annotations

from copy import deepcopy
import json
import unittest
from pathlib import Path

from ppd.agent_consumer_regression import build_agent_consumer_regression_rerun_plan
from ppd.agent_readiness.dry_run_promotion_sequence_packet import build_dry_run_promotion_sequence_packet
from ppd.agent_readiness.post_promotion_smoke_test_plan import build_post_promotion_smoke_test_plan
from ppd.agent_readiness.release_notes_candidate_packet import (
    build_release_notes_candidate_packet,
    validate_release_notes_candidate_packet,
)

FIXTURES = Path(__file__).parent / "fixtures"
EXPECTATIONS = FIXTURES / "agent_readiness" / "release_notes_candidate_expectations.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _source_packets() -> tuple[dict, dict, dict]:
    offline = _load_json(FIXTURES / "agent_readiness" / "dry_run_promotion_sequence_source_decision_packet.json")
    dry_run = build_dry_run_promotion_sequence_packet(offline)
    regression = build_agent_consumer_regression_rerun_plan(
        _load_json(FIXTURES / "agent_consumer_regression" / "guardrail_bundle_update_candidates.json"),
        _load_json(FIXTURES / "agent_consumer_regression" / "safe_action_regression_matrix.json"),
    )
    smoke_plan = build_post_promotion_smoke_test_plan(dry_run, regression)
    return offline, dry_run, smoke_plan


class ReleaseNotesCandidatePacketTest(unittest.TestCase):
    def test_builds_fixture_first_release_notes_candidate_packet(self) -> None:
        packet = build_release_notes_candidate_packet(*_source_packets())
        expected = _load_json(EXPECTATIONS)

        result = validate_release_notes_candidate_packet(packet)
        self.assertTrue(result.valid, result.problems)
        self.assertEqual(packet["packet_type"], "ppd.release_notes_candidate_packet.v1")
        self.assertEqual(packet["candidate_status"], "draft_operator_notes_not_published")
        self.assertEqual(packet["publication_policy"], expected["publication_policy"])
        self.assertEqual(
            {item["note_id"] for item in packet["operator_facing_change_notes"]},
            set(expected["required_change_note_ids"]),
        )
        self.assertTrue(packet["known_limitations"])
        self.assertTrue(packet["validation_evidence_references"])
        self.assertTrue(packet["rollback_notes"])
        self.assertTrue(packet["manual_handoff_reminders"])

    def test_sections_are_cited_to_source_packets_and_evidence(self) -> None:
        packet = build_release_notes_candidate_packet(*_source_packets())

        for section_name in (
            "operator_facing_change_notes",
            "known_limitations",
            "rollback_notes",
            "manual_handoff_reminders",
        ):
            for item in packet[section_name]:
                self.assertTrue(item["source_packet_refs"], section_name)
                self.assertTrue(item["source_evidence_ids"], section_name)

        source_refs = {item["source_packet_ref"] for item in packet["validation_evidence_references"]}
        self.assertIn("offline_release_decision_packet", source_refs)
        self.assertIn("dry_run_promotion_sequence_packet", source_refs)
        self.assertIn("post_promotion_smoke_test_plan", source_refs)

    def test_validator_rejects_publication_or_active_artifact_claims(self) -> None:
        packet = build_release_notes_candidate_packet(*_source_packets())
        packet["publication_policy"]["publishes_release_notes"] = True
        packet["operator_facing_change_notes"][0]["body"] = "Release notes published for active artifacts."

        result = validate_release_notes_candidate_packet(packet)
        self.assertFalse(result.valid)
        joined = "; ".join(result.problems)
        self.assertIn("publishes_release_notes", joined)
        self.assertIn("publication", joined)

    def test_validator_rejects_uncited_sections_and_private_artifacts(self) -> None:
        packet = build_release_notes_candidate_packet(*_source_packets())
        altered = deepcopy(packet)
        altered["known_limitations"][0]["source_evidence_ids"] = []
        altered["private_path"] = "/tmp/private-release-note.txt"

        result = validate_release_notes_candidate_packet(altered)
        self.assertFalse(result.valid)
        joined = "; ".join(result.problems)
        self.assertIn("known_limitations", joined)
        self.assertIn("private", joined)
        self.assertTrue(validate_release_notes_candidate_packet(packet).valid)


if __name__ == "__main__":
    unittest.main()
