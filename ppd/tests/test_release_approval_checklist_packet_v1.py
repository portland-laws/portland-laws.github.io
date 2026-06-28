from __future__ import annotations

import copy
from pathlib import Path
import unittest

from ppd.agent_readiness.release_approval_checklist_packet_v1 import (
    VALIDATION_COMMAND,
    load_release_approval_checklist_packet_v1,
    validate_release_approval_checklist_packet_v1,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "release_approval_checklist_packet_v1" / "valid_packet.json"


def _valid_packet() -> dict:
    return load_release_approval_checklist_packet_v1(FIXTURE_PATH)


def _codes(packet: dict) -> set[str]:
    return {issue["code"] for issue in validate_release_approval_checklist_packet_v1(packet)}


class ReleaseApprovalChecklistPacketV1Tests(unittest.TestCase):
    def test_valid_fixture_passes(self) -> None:
        packet = _valid_packet()
        self.assertEqual(packet["packet_type"], "ppd.release_approval_checklist_packet.v1")
        self.assertEqual(packet["mode"], "fixture-first-offline-only")
        self.assertEqual(packet["validation_commands"], [VALIDATION_COMMAND])
        self.assertEqual(validate_release_approval_checklist_packet_v1(packet), [])

    def test_rejects_missing_required_approval_sections_and_validation_commands(self) -> None:
        packet = _valid_packet()
        for key in (
            "rehearsal_references",
            "reviewer_disposition_evidence",
            "rollback_note_rows",
            "dependency_order_checks",
            "hold_reject_reasons",
        ):
            packet[key] = []
        packet["validation_commands"] = []

        codes = _codes(packet)

        self.assertIn("missing_rehearsal_references", codes)
        self.assertIn("missing_reviewer_disposition_evidence", codes)
        self.assertIn("missing_rollback_note_rows", codes)
        self.assertIn("missing_dependency_order_checks", codes)
        self.assertIn("missing_hold_reject_reasons", codes)
        self.assertIn("missing_validation_commands", codes)

    def test_rejects_malformed_required_rows(self) -> None:
        packet = _valid_packet()
        packet["rehearsal_references"][0].pop("packet_ref")
        packet["reviewer_disposition_evidence"][0].pop("evidence_ref")
        packet["rollback_note_rows"][0].pop("note")
        packet["dependency_order_checks"][0].pop("after")
        packet["hold_reject_reasons"][0].pop("reason")

        codes = _codes(packet)

        self.assertIn("invalid_rehearsal_reference", codes)
        self.assertIn("invalid_reviewer_disposition_evidence", codes)
        self.assertIn("invalid_rollback_note_row", codes)
        self.assertIn("invalid_dependency_order_check", codes)
        self.assertIn("invalid_hold_reject_reason", codes)

    def test_rejects_private_session_browser_raw_and_downloaded_artifacts(self) -> None:
        packet = _valid_packet()
        packet["session_artifact"] = "redacted"
        packet["rollback_note_rows"][0]["note"] = "Do not store raw PDF or downloaded document content."

        codes = _codes(packet)

        self.assertIn("private_or_raw_artifact_field", codes)
        self.assertIn("private_or_raw_artifact_text", codes)

    def test_rejects_live_claims_guarantees_official_action_claims_and_promotion_claims(self) -> None:
        packet = _valid_packet()
        packet["rehearsal_references"][0]["summary"] = "The live crawl completed."
        packet["reviewer_disposition_evidence"][0]["summary"] = "The permit will be approved."
        packet["rollback_note_rows"][0]["note"] = "Official action completed."
        packet["hold_reject_reasons"][0]["reason"] = "Release promoted."

        codes = _codes(packet)

        self.assertIn("live_crawl_or_devhub_claim", codes)
        self.assertIn("legal_or_permitting_guarantee", codes)
        self.assertIn("official_action_completion_claim", codes)
        self.assertIn("release_promotion_claim", codes)

    def test_rejects_active_mutation_flags_and_unsafe_validation_commands(self) -> None:
        packet = _valid_packet()
        packet["active_guardrail_mutation"] = True
        packet["validation_commands"] = [["python3", "ppd/devhub/live_browser.py"]]

        codes = _codes(packet)

        self.assertIn("active_mutation_flag", codes)
        self.assertIn("unsafe_validation_command", codes)

    def test_validation_does_not_mutate_input(self) -> None:
        packet = _valid_packet()
        original = copy.deepcopy(packet)
        validate_release_approval_checklist_packet_v1(packet)
        self.assertEqual(packet, original)


if __name__ == "__main__":
    unittest.main()
