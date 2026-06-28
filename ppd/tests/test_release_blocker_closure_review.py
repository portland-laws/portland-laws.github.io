import unittest

from ppd.release_blockers.closure_review import (
    finding_codes,
    require_release_blocker_closure_review_packet,
    validate_release_blocker_closure_review_packet,
)


def valid_packet():
    return {
        "packet_type": "ppd_release_blocker_closure_review",
        "consumed_packet_refs": ["packet:readiness-reconciliation-1"],
        "reviewer_owners": ["release-reviewer"],
        "follow_up_validation_commands": ["python3 -m unittest discover -s ppd/tests -p test_*.py"],
        "blocker_decisions": [
            {
                "blocker_id": "blocker-1",
                "decision": "keep_open",
                "citations": ["readiness-reconciliation-1:blocker-1"],
                "consumed_packet_refs": ["packet:readiness-reconciliation-1"],
                "reviewer_owner": "release-reviewer",
                "rationale": "Fixture review confirms the closure decision remains evidence-backed.",
            }
        ],
    }


class ReleaseBlockerClosureReviewPacketTests(unittest.TestCase):
    def test_accepts_valid_fixture_first_packet(self):
        result = validate_release_blocker_closure_review_packet(valid_packet())
        self.assertTrue(result.ok)
        self.assertEqual((), result.findings)
        require_release_blocker_closure_review_packet(valid_packet())

    def test_rejects_missing_decision_citations_refs_owners_and_commands(self):
        packet = {"blocker_decisions": [{"blocker_id": "blocker-1", "decision": "closed"}]}
        codes = finding_codes(validate_release_blocker_closure_review_packet(packet))
        self.assertIn("uncited_blocker_decision", codes)
        self.assertIn("missing_consumed_packet_refs", codes)
        self.assertIn("missing_reviewer_owner", codes)
        self.assertIn("missing_follow_up_validation_commands", codes)

    def test_rejects_raw_private_live_guarantee_and_mutation_content(self):
        packet = valid_packet()
        packet["raw_body"] = "raw html"
        packet["session_cookie"] = "cookie=secret"
        packet["notes"] = "Ran live crawler and launched DevHub; permit approval is guaranteed."
        packet["active_guardrail_bundle_mutation"] = True
        codes = finding_codes(validate_release_blocker_closure_review_packet(packet))
        self.assertIn("raw_body_download_archive_reference", codes)
        self.assertIn("private_session_artifact", codes)
        self.assertIn("live_execution_claim", codes)
        self.assertIn("outcome_guarantee", codes)
        self.assertIn("active_mutation_flag", codes)


if __name__ == "__main__":
    unittest.main()
