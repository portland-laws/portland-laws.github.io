import unittest
from pathlib import Path

from ppd.logic.guardrail_recompile_reviewer_packet_v6 import (
    INACTIVE_STATUS,
    REVIEWER_PACKET_VERSION,
    ReviewerPacketError,
    build_reviewer_packet,
    build_reviewer_packet_from_fixture,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "guardrail_recompile_staging_v6"


class GuardrailRecompileReviewerPacketV6Tests(unittest.TestCase):
    def test_builds_reviewer_packet_from_staging_fixture_only(self):
        packet = build_reviewer_packet_from_fixture(
            FIXTURE_DIR / "permit_application_staging_packet_v6.json"
        )

        self.assertEqual(packet["packet_version"], REVIEWER_PACKET_VERSION)
        self.assertEqual(packet["guardrail_activation_status"], INACTIVE_STATUS)
        self.assertEqual(packet["source_packet_id"], "staging-v6-permit-application-fixture")
        self.assertEqual(len(packet["reviewer_comparison_rows"]), 2)
        self.assertIn("activate_guardrails", packet["prohibited_actions"])
        self.assertIn("open_devhub", packet["prohibited_actions"])
        self.assertIn("make_legal_or_permitting_guarantees", packet["prohibited_actions"])

    def test_preserves_inactive_status_notes_and_placeholders(self):
        packet = build_reviewer_packet_from_fixture(
            FIXTURE_DIR / "permit_application_staging_packet_v6.json"
        )

        statuses = {
            note["guardrail_id"]: note["activation_status"]
            for note in packet["inactive_guardrail_status_notes"]
        }
        self.assertEqual(statuses["gr-devhub-submit-final-action"], INACTIVE_STATUS)
        self.assertEqual(statuses["gr-upload-staging-only"], INACTIVE_STATUS)
        self.assertTrue(
            all(
                item["rollback_checkpoint_id"] == "TBD_BY_REVIEWER"
                for item in packet["rollback_checkpoint_placeholders"]
            )
        )
        self.assertTrue(
            all(
                item["signoff_owner"] == "TBD_BY_REVIEWER"
                for item in packet["signoff_owner_placeholders"]
            )
        )

    def test_reports_source_evidence_continuity_and_stale_hold_propagation(self):
        packet = build_reviewer_packet_from_fixture(
            FIXTURE_DIR / "permit_application_staging_packet_v6.json"
        )

        upload_check = next(
            item
            for item in packet["source_evidence_continuity_checks"]
            if item["guardrail_id"] == "gr-upload-staging-only"
        )
        self.assertEqual(upload_check["continuity_status"], "continuous")
        self.assertEqual(upload_check["stale_source_evidence_ids"], ["src-file-naming-standards"])
        self.assertTrue(upload_check["requires_human_review"])
        self.assertEqual(
            packet["stale_evidence_hold_propagation"][0]["reviewer_action"],
            "keep_hold_until_fresh_source_fixture_is_committed",
        )

    def test_emits_deterministic_prompts_and_preservation_summaries(self):
        packet = build_reviewer_packet_from_fixture(
            FIXTURE_DIR / "permit_application_staging_packet_v6.json"
        )

        prompts = packet["deterministic_predicate_review_prompts"]
        self.assertEqual(
            prompts[0]["expected_review_answers"],
            ["preserved", "narrowed", "stale-held", "refused"],
        )
        self.assertEqual(
            packet["exact_confirmation_preservation_summary"]["preserved_ids"],
            ["confirm-final-submit"],
        )
        self.assertEqual(
            packet["refused_action_preservation_summary"]["preserved_count"],
            2,
        )

    def test_accepts_payment_fixture_without_live_or_auth_actions(self):
        packet = build_reviewer_packet_from_fixture(
            FIXTURE_DIR / "payment_staging_packet_v6.json"
        )

        self.assertEqual(packet["source_packet_id"], "staging-v6-payment-fixture")
        self.assertEqual(packet["reviewer_comparison_rows"][0]["guardrail_id"], "gr-payment-final-action")
        self.assertEqual(packet["stale_evidence_hold_propagation"], [])
        self.assertEqual(
            packet["offline_validation_commands"],
            [["python3", "-m", "unittest", "ppd.tests.test_guardrail_recompile_reviewer_packet_v6"]],
        )

    def test_rejects_active_guardrail_fixture(self):
        with self.assertRaises(ReviewerPacketError):
            build_reviewer_packet(
                {
                    "packet_version": "guardrail_recompile_staging_packet_v6",
                    "packet_id": "bad-active-fixture",
                    "guardrails": [
                        {
                            "guardrail_id": "gr-active",
                            "process_id": "process",
                            "activation_status": "active",
                            "previous_rule_hash": "sha256:old",
                            "staged_rule_hash": "sha256:new",
                            "source_evidence_ids": [],
                            "comparison_note": "bad",
                        }
                    ],
                    "source_evidence": [],
                    "deterministic_predicates": [],
                    "exact_confirmations": [],
                    "refused_actions": [],
                    "stale_evidence": [],
                    "offline_validation_commands": [],
                }
            )

    def test_rejects_live_or_consequential_validation_commands(self):
        with self.assertRaises(ReviewerPacketError):
            build_reviewer_packet(
                {
                    "packet_version": "guardrail_recompile_staging_packet_v6",
                    "packet_id": "bad-command-fixture",
                    "guardrails": [],
                    "source_evidence": [],
                    "deterministic_predicates": [],
                    "exact_confirmations": [],
                    "refused_actions": [],
                    "stale_evidence": [],
                    "offline_validation_commands": [
                        {"argv": ["curl", "https://www.portland.gov/ppd"]}
                    ],
                }
            )


if __name__ == "__main__":
    unittest.main()
