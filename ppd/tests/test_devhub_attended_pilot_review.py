import copy
import unittest
from pathlib import Path

from ppd.devhub.attended_pilot_review import load_review_packet, review_attended_pilot_packet


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "attended_pilot_review_packet.complete.json"


class AttendedPilotReviewTests(unittest.TestCase):
    def test_complete_fixture_passes(self):
        packet = load_review_packet(FIXTURE_PATH)

        result = review_attended_pilot_packet(packet)

        self.assertTrue(result.ok, [finding.to_dict() for finding in result.findings])
        self.assertEqual(
            result.journal_event_ids,
            [
                "JRN-DEVHUB-PREFLIGHT",
                "JRN-MANUAL-HANDOFF",
                "JRN-ABORT-GATE",
                "JRN-HARDENING-REVIEW",
            ],
        )

    def test_rejects_live_session_authorization(self):
        packet = load_review_packet(FIXTURE_PATH)
        packet["live_session_authorized"] = True

        result = review_attended_pilot_packet(packet)

        self.assertFalse(result.ok)
        self.assertIn("live_session_block", {finding.code for finding in result.findings})

    def test_rejects_missing_redaction_attestation(self):
        packet = load_review_packet(FIXTURE_PATH)
        packet["redaction_attestations"][0]["prohibited_values_absent"] = False

        result = review_attended_pilot_packet(packet)

        self.assertFalse(result.ok)
        self.assertIn("redaction_private_values", {finding.code for finding in result.findings})

    def test_rejects_abort_condition_without_known_journal_event(self):
        packet = load_review_packet(FIXTURE_PATH)
        packet["abort_conditions"][0]["journal_event_id"] = "JRN-MISSING"

        result = review_attended_pilot_packet(packet)

        self.assertFalse(result.ok)
        self.assertIn("abort_condition_journal_link", {finding.code for finding in result.findings})

    def test_rejects_duplicate_journal_event_ids(self):
        packet = load_review_packet(FIXTURE_PATH)
        duplicate = copy.deepcopy(packet["journal_events"][0])
        packet["journal_events"].append(duplicate)

        result = review_attended_pilot_packet(packet)

        self.assertFalse(result.ok)
        self.assertIn("journal_event_duplicate", {finding.code for finding in result.findings})

    def test_rejects_incomplete_operator_checklist(self):
        packet = load_review_packet(FIXTURE_PATH)
        packet["operator"]["completed_checklist"] = ["operator_identity_recorded"]

        result = review_attended_pilot_packet(packet)

        self.assertFalse(result.ok)
        self.assertIn("operator_checklist_missing", {finding.code for finding in result.findings})


if __name__ == "__main__":
    unittest.main()
