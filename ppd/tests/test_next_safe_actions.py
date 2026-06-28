from __future__ import annotations

import unittest
from pathlib import Path

from ppd.logic.next_safe_actions import build_next_safe_actions, load_fixture_bundle


class NextSafeActionsTest(unittest.TestCase):
    def test_next_safe_actions_fixture_first(self):
        fixture = (
            Path(__file__).parent
            / "fixtures"
            / "next_safe_actions"
            / "sample_gap_analysis.json"
        )
        process_model, gap_analysis, guardrails = load_fixture_bundle(fixture)

        result = build_next_safe_actions(process_model, gap_analysis, guardrails)

        self.assertEqual(result["case_id"], "case-fixture-001")
        self.assertEqual(result["process_id"], "ppd-demo-permit-intake")
        self.assertEqual(result["guardrail_bundle_id"], "ppd-fixture-guardrails")

        self.assertEqual(
            [question["kind"] for question in result["missing_questions"]],
            ["missing_fact", "missing_document"],
        )
        self.assertEqual(
            result["missing_questions"][0]["citations"][0]["evidence_id"],
            "process-001",
        )

        self.assertEqual(len(result["evidence_warnings"]), 1)
        self.assertEqual(result["evidence_warnings"][0]["kind"], "stale_evidence")

        self.assertEqual(
            [action["action_id"] for action in result["reversible_draft_actions"]],
            ["draft_questions"],
        )
        self.assertTrue(result["reversible_draft_actions"][0]["draft_only"])

        blocked_by_id = {
            action["action_id"]: action
            for action in result["blocked_consequential_actions"]
        }
        self.assertEqual(
            blocked_by_id["submit_application"]["reason_code"],
            "requires_exact_confirmation",
        )
        self.assertEqual(blocked_by_id["pay_fee"]["reason_code"], "refused_by_guardrail")
        self.assertEqual(
            blocked_by_id["schedule_inspection"]["reason_code"],
            "gap_analysis_block",
        )
        self.assertTrue(
            blocked_by_id["schedule_inspection"]["requires_attended_handoff"]
        )


if __name__ == "__main__":
    unittest.main()
