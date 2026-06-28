from __future__ import annotations

import copy
import unittest

from ppd.agent_readiness.release_notes_candidate_packet import validate_release_notes_candidate_packet


class ReleaseNotesCandidatePacketValidationTest(unittest.TestCase):
    def test_valid_minimal_candidate_packet_passes(self) -> None:
        result = validate_release_notes_candidate_packet(_valid_packet())
        self.assertTrue(result.valid, result.problems)

    def test_rejects_uncited_change_claim(self) -> None:
        packet = _valid_packet()
        packet["operator_facing_change_notes"][0]["source_evidence_ids"] = []
        result = validate_release_notes_candidate_packet(packet)
        self.assertFalse(result.valid)
        self.assertTrue(any("uncited change claim" in problem or "lacks source_evidence_ids" in problem for problem in result.problems))

    def test_rejects_legal_or_permitting_outcome_guarantee(self) -> None:
        packet = _valid_packet()
        packet["operator_facing_change_notes"][0]["body"] = "This guarantees permit approval."
        result = validate_release_notes_candidate_packet(packet)
        self.assertFalse(result.valid)
        self.assertTrue(any("legal or permitting outcome guarantee" in problem for problem in result.problems))

    def test_rejects_missing_limitations_rollback_and_validation_references(self) -> None:
        for key in ("known_limitations", "rollback_notes", "validation_evidence_references"):
            packet = _valid_packet()
            packet[key] = []
            result = validate_release_notes_candidate_packet(packet)
            self.assertFalse(result.valid)
            self.assertIn(f"{key} must be a non-empty list", result.problems)

    def test_rejects_private_authenticated_and_raw_references(self) -> None:
        unsafe_values = [
            "https://devhub.portlandoregon.gov/login?token=secret",
            "file:///home/user/private-case.pdf",
            "/Users/person/Downloads/raw-crawl-output.warc.gz",
            "Use the raw archive reference from the crawl output.",
        ]
        for unsafe_value in unsafe_values:
            packet = _valid_packet()
            packet["validation_evidence_references"][0]["description"] = unsafe_value
            result = validate_release_notes_candidate_packet(packet)
            self.assertFalse(result.valid, unsafe_value)

    def test_rejects_live_publication_claims_and_active_mutation_flags(self) -> None:
        packet = _valid_packet()
        packet["operator_facing_change_notes"][0]["body"] = "Release notes published and active artifacts changed."
        result = validate_release_notes_candidate_packet(packet)
        self.assertFalse(result.valid)
        self.assertTrue(any("publication" in problem or "active mutation" in problem for problem in result.problems))

        packet = _valid_packet()
        packet["active_artifact_mutation_enabled"] = True
        result = validate_release_notes_candidate_packet(packet)
        self.assertFalse(result.valid)
        self.assertTrue(any("active artifact mutation flag" in problem for problem in result.problems))


def _valid_packet() -> dict[str, object]:
    return copy.deepcopy(
        {
            "packet_type": "ppd.release_notes_candidate_packet.v1",
            "packet_id": "fixture-release-notes-candidate",
            "fixture_only": True,
            "candidate_status": "draft_operator_notes_not_published",
            "source_packet_ids": {
                "offline_release_decision_packet": "offline-release-decision",
                "dry_run_promotion_sequence_packet": "dry-run-promotion",
                "post_promotion_smoke_test_plan": "post-promotion-smoke",
            },
            "publication_policy": {
                "fixtures_only": True,
                "publishes_release_notes": False,
                "changes_active_artifacts": False,
                "writes_active_state": False,
                "promotes_release": False,
                "uses_live_network": False,
                "invokes_devhub": False,
                "invokes_agents": False,
                "invokes_crawlers": False,
                "invokes_processors": False,
                "reads_private_case_files": False,
            },
            "operator_facing_change_notes": [
                {
                    "note_id": "change-note",
                    "title": "Candidate notes remain fixture-only",
                    "body": "Operators must review this cited draft before any release decision.",
                    "source_packet_refs": ["offline_release_decision_packet"],
                    "source_evidence_ids": ["evidence-release-note"],
                }
            ],
            "known_limitations": [
                {
                    "limitation_id": "limitation-fixture-only",
                    "summary": "Fixture-only candidate notes do not prove production readiness.",
                    "source_packet_refs": ["dry_run_promotion_sequence_packet"],
                    "source_evidence_ids": ["evidence-limitation"],
                }
            ],
            "validation_evidence_references": [
                {
                    "reference_id": "validation-self-test",
                    "source_packet_ref": "post_promotion_smoke_test_plan",
                    "description": "Deterministic validation reference for the fixture packet.",
                    "source_evidence_ids": ["evidence-validation"],
                }
            ],
            "rollback_notes": [
                {
                    "rollback_note_id": "rollback-discard-candidate",
                    "summary": "Discard the candidate packet without changing active artifacts.",
                    "source_packet_refs": ["dry_run_promotion_sequence_packet"],
                    "source_evidence_ids": ["evidence-rollback"],
                }
            ],
            "manual_handoff_reminders": [
                {
                    "reminder_id": "operator-review",
                    "summary": "Operator review is required before publication.",
                    "source_packet_refs": ["offline_release_decision_packet"],
                    "source_evidence_ids": ["evidence-handoff"],
                }
            ],
            "no_publication_attestations": [
                {
                    "attestation_id": "candidate-only",
                    "attested": True,
                    "summary": "This is not a publication event.",
                    "source_evidence_ids": ["evidence-attestation"],
                }
            ],
        }
    )


if __name__ == "__main__":
    unittest.main()
