"""Guardrail tests for mocked DevHub fee review and payment readiness."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.devhub.fee_review_guardrails import (
    ENTER_PAYMENT_DETAILS_ACTION,
    EXECUTE_PAYMENT_ACTION,
    READ_ONLY_SUMMARY_ACTION,
    evaluate_fee_review_action,
    summarize_payment_readiness,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub_fee_review" / "payment_readiness_snapshot.json"


class DevHubFeeReviewGuardrailTests(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fee_review_summarizes_payment_readiness_from_mocked_fixture(self) -> None:
        summary = summarize_payment_readiness(self.snapshot)

        self.assertEqual(summary["action"], READ_ONLY_SUMMARY_ACTION)
        self.assertEqual(summary["action_classification"], "safe_read_only")
        self.assertTrue(summary["ready_for_user_payment_review"])
        self.assertEqual(summary["payable_item_count"], 1)
        self.assertEqual(summary["total_due"], "295.50")
        self.assertEqual(summary["payable_items"][0]["id"], "fee-intake-review")
        self.assertIn(ENTER_PAYMENT_DETAILS_ACTION, summary["blocked_agent_actions"])
        self.assertIn(EXECUTE_PAYMENT_ACTION, summary["blocked_agent_actions"])

        serialized = json.dumps(summary).lower()
        self.assertNotIn("card_number", serialized)
        self.assertNotIn("routing_number", serialized)
        self.assertNotIn("security_code", serialized)

    def test_payment_detail_entry_is_refused_without_exact_session_confirmation(self) -> None:
        no_confirmation = evaluate_fee_review_action(self.snapshot, ENTER_PAYMENT_DETAILS_ACTION)
        self.assertFalse(no_confirmation["permitted"])
        self.assertFalse(no_confirmation["confirmation_satisfied"])
        self.assertIn("exact_session_specific_user_confirmation_required", no_confirmation["refusal_reasons"])
        self.assertIn("payment_detail_entry_must_remain_manual", no_confirmation["refusal_reasons"])

        generic_confirmation = evaluate_fee_review_action(
            self.snapshot,
            ENTER_PAYMENT_DETAILS_ACTION,
            confirmation_text="Please pay the fee.",
            session_id=self.snapshot["sessionId"],
        )
        self.assertFalse(generic_confirmation["permitted"])
        self.assertFalse(generic_confirmation["confirmation_satisfied"])

        exact_text_wrong_session = evaluate_fee_review_action(
            self.snapshot,
            ENTER_PAYMENT_DETAILS_ACTION,
            confirmation_text=self.snapshot["confirmation"]["exactText"],
            session_id="different-session",
        )
        self.assertFalse(exact_text_wrong_session["permitted"])
        self.assertFalse(exact_text_wrong_session["confirmation_satisfied"])

    def test_payment_execution_is_refused_without_exact_session_confirmation(self) -> None:
        generic_confirmation = evaluate_fee_review_action(
            self.snapshot,
            EXECUTE_PAYMENT_ACTION,
            confirmation_text="I confirm payment.",
            session_id=self.snapshot["sessionId"],
        )
        self.assertFalse(generic_confirmation["permitted"])
        self.assertFalse(generic_confirmation["confirmation_satisfied"])
        self.assertIn("exact_session_specific_user_confirmation_required", generic_confirmation["refusal_reasons"])
        self.assertIn("payment_execution_must_remain_manual", generic_confirmation["refusal_reasons"])

    def test_exact_session_confirmation_satisfies_checkpoint_but_does_not_automate_payment(self) -> None:
        exact_payment_detail_decision = evaluate_fee_review_action(
            self.snapshot,
            ENTER_PAYMENT_DETAILS_ACTION,
            confirmation_text=self.snapshot["confirmation"]["exactText"],
            session_id=self.snapshot["sessionId"],
        )
        self.assertTrue(exact_payment_detail_decision["confirmation_satisfied"])
        self.assertFalse(exact_payment_detail_decision["permitted"])
        self.assertEqual(exact_payment_detail_decision["action_classification"], "financial")
        self.assertIn("payment_detail_entry_must_remain_manual", exact_payment_detail_decision["refusal_reasons"])

        exact_execute_decision = evaluate_fee_review_action(
            self.snapshot,
            EXECUTE_PAYMENT_ACTION,
            confirmation_text=self.snapshot["confirmation"]["exactText"],
            session_id=self.snapshot["sessionId"],
        )
        self.assertTrue(exact_execute_decision["confirmation_satisfied"])
        self.assertFalse(exact_execute_decision["permitted"])
        self.assertIn("payment_execution_must_remain_manual", exact_execute_decision["refusal_reasons"])

    def test_read_only_summary_action_is_allowed_without_payment_confirmation(self) -> None:
        decision = evaluate_fee_review_action(self.snapshot, READ_ONLY_SUMMARY_ACTION)

        self.assertTrue(decision["permitted"])
        self.assertTrue(decision["confirmation_satisfied"])
        self.assertEqual(decision["summary"]["total_due"], "295.50")
        self.assertEqual(decision["refusal_reasons"], [])


if __name__ == "__main__":
    unittest.main()
