from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ppd.agent_readiness.inactive_activation_rehearsal_checklist_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    InactiveActivationRehearsalChecklistV1Error,
    assert_valid_inactive_activation_rehearsal_checklist_v1,
    build_checklist_from_fixture,
    load_inactive_activation_rehearsal_checklist_v1,
    validate_inactive_activation_rehearsal_checklist_v1,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "inactive_activation_rehearsal_checklist_v1"
SOURCE_FIXTURE = FIXTURE_DIR / "source_rows.json"
PACKET_FIXTURE = FIXTURE_DIR / "packet.json"


class InactiveActivationRehearsalChecklistV1Tests(unittest.TestCase):
    def test_builder_consumes_only_synthetic_approved_decision_and_smoke_rows(self) -> None:
        packet = build_checklist_from_fixture(SOURCE_FIXTURE)

        self.assertEqual(validate_inactive_activation_rehearsal_checklist_v1(packet), [])
        self.assertEqual(packet["source_kind"], "synthetic_approved_inactive_release_decision_rows_and_inactive_smoke_replay_rows")
        self.assertEqual(packet["validation_commands"], EXACT_OFFLINE_VALIDATION_COMMANDS)
        self.assertEqual(packet["exact_offline_validation_commands"], EXACT_OFFLINE_VALIDATION_COMMANDS)
        self.assertEqual(len(packet["activation_prerequisites"]), 3)
        self.assertEqual(len(packet["post_activation_smoke_requirements"]), 3)

    def test_committed_packet_lists_required_activation_rehearsal_sections(self) -> None:
        packet = load_inactive_activation_rehearsal_checklist_v1(PACKET_FIXTURE)

        self.assertEqual(validate_inactive_activation_rehearsal_checklist_v1(packet), [])
        self.assertTrue(packet["activation_prerequisites"])
        self.assertTrue(packet["source_evidence_placeholder_checks"])
        self.assertTrue(packet["reviewer_signoff_placeholders"])
        self.assertTrue(packet["rollback_checkpoints"])
        self.assertTrue(packet["post_activation_smoke_requirements"])
        self.assertTrue(packet["hold_conditions"])
        self.assertTrue(packet["release_notes_placeholders"])
        for requirement in packet["post_activation_smoke_requirements"]:
            self.assertEqual(requirement["offline_validation_commands"], EXACT_OFFLINE_VALIDATION_COMMANDS)

    def test_boundaries_deny_activation_prompt_changes_live_devhub_private_artifacts_and_official_actions(self) -> None:
        packet = load_inactive_activation_rehearsal_checklist_v1(PACKET_FIXTURE)

        self.assertTrue(packet["boundaries"]["fixture_first"])
        self.assertTrue(packet["boundaries"]["synthetic_rows_only"])
        self.assertTrue(packet["boundaries"]["approved_inactive_decision_rows_only"])
        self.assertFalse(packet["boundaries"]["activation_enabled"])
        self.assertFalse(packet["boundaries"]["guardrail_activation_enabled"])
        self.assertFalse(packet["boundaries"]["active_prompt_changes_enabled"])
        self.assertFalse(packet["boundaries"]["live_crawling_enabled"])
        self.assertFalse(packet["boundaries"]["devhub_opened"])
        self.assertFalse(packet["boundaries"]["private_artifact_storage_enabled"])
        self.assertFalse(packet["boundaries"]["official_action_enabled"])

    def test_rejects_missing_required_sections_and_consumed_rows(self) -> None:
        packet = load_inactive_activation_rehearsal_checklist_v1(PACKET_FIXTURE)
        unsafe = copy.deepcopy(packet)
        unsafe["activation_prerequisites"] = []
        unsafe["source_evidence_placeholder_checks"] = []
        unsafe["consumed_approved_inactive_release_decision_row_ids"] = []
        unsafe["consumed_inactive_smoke_replay_row_ids"] = []

        errors = validate_inactive_activation_rehearsal_checklist_v1(unsafe)
        joined = "; ".join(errors)

        self.assertIn("activation_prerequisites must be a non-empty list", joined)
        self.assertIn("source_evidence_placeholder_checks must be a non-empty list", joined)
        self.assertIn("consumed_approved_inactive_release_decision_row_ids must be non-empty", joined)
        self.assertIn("consumed_inactive_smoke_replay_row_ids must be non-empty", joined)

    def test_rejects_missing_placeholders_signoffs_rollbacks_smoke_holds_notes_and_commands(self) -> None:
        packet = load_inactive_activation_rehearsal_checklist_v1(PACKET_FIXTURE)
        unsafe = copy.deepcopy(packet)
        unsafe["source_evidence_placeholder_checks"][0]["placeholder_ids"] = []
        unsafe["reviewer_signoff_placeholders"][0]["status"] = "signed"
        unsafe["reviewer_signoff_placeholders"][0]["signature_record"] = "reviewer-signature"
        unsafe["rollback_checkpoints"][0]["status"] = "complete"
        unsafe["post_activation_smoke_requirements"][0]["expected_smoke_checks"] = []
        unsafe["post_activation_smoke_requirements"][0]["offline_validation_commands"] = [["python3", "-m", "pytest"]]
        unsafe["hold_conditions"][0]["blocked_action_expectations"] = []
        unsafe["release_notes_placeholders"][0]["notes_text"] = "notes filled"
        unsafe["validation_commands"] = [["python3", "-m", "pytest"]]

        errors = validate_inactive_activation_rehearsal_checklist_v1(unsafe)
        joined = "; ".join(errors)

        self.assertIn("placeholder_ids must be a non-empty list of text", joined)
        self.assertIn("status must be not_signed", joined)
        self.assertIn("signature_record must be null", joined)
        self.assertIn("status must be pending_rehearsal_review", joined)
        self.assertIn("expected_smoke_checks must be a non-empty list of text", joined)
        self.assertIn("offline_validation_commands must contain only the daemon self-test command", joined)
        self.assertIn("blocked_action_expectations must be a non-empty list of text", joined)
        self.assertIn("notes_text must be null", joined)
        self.assertIn("validation_commands must contain only the daemon self-test command", joined)

    def test_rejects_live_private_official_activation_prompt_and_guardrail_claims(self) -> None:
        packet = load_inactive_activation_rehearsal_checklist_v1(PACKET_FIXTURE)
        unsafe = copy.deepcopy(packet)
        unsafe["boundaries"]["devhub_opened"] = True
        unsafe["active_prompt_mutation"] = True
        unsafe["active_guardrail_mutation"] = True
        unsafe["notes"] = [
            "opened DevHub",
            "live crawl completed",
            "downloaded document retained",
            "official action completed",
            "release activated",
            "approval is guaranteed",
        ]
        unsafe["browser_state_path"] = "state.json"
        unsafe["raw_pdf_artifact"] = "raw.pdf"

        errors = validate_inactive_activation_rehearsal_checklist_v1(unsafe)
        joined = "; ".join(errors)

        self.assertIn("boundaries must exactly keep the checklist fixture-only", joined)
        self.assertIn("forbidden live/private/official/release/legal guarantee claim", joined)
        self.assertIn("forbidden private/session/browser/raw artifact field", joined)
        self.assertIn("forbidden active/live/private/official true flag", joined)
        self.assertIn("forbidden active mutation flag", joined)
        with self.assertRaises(InactiveActivationRehearsalChecklistV1Error):
            assert_valid_inactive_activation_rehearsal_checklist_v1(unsafe)

    def test_committed_packet_matches_builder_output(self) -> None:
        built = build_checklist_from_fixture(SOURCE_FIXTURE)
        committed = json.loads(PACKET_FIXTURE.read_text(encoding="utf-8"))

        self.assertEqual(committed, built)


if __name__ == "__main__":
    unittest.main()
