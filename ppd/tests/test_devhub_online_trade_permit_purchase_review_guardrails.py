from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.devhub.online_trade_permit_purchase_review_guardrails import (
    CONFIRMED_STATUS,
    GUARDED_ACTIONS,
    PREVIEW_ACTION,
    PREVIEW_STATUS,
    REFUSED_STATUS,
    build_purchase_review_preview,
    evaluate_purchase_review_action,
    validate_purchase_review_fixture,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub"
    / "online_trade_permit_purchase_review_guardrails.json"
)


class DevhubOnlineTradePermitPurchaseReviewGuardrailTests(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture = json.load(fixture_file)
        self.workflow = self.fixture["workflow"]

    def test_fixture_is_valid_and_contains_no_private_devhub_artifacts(self) -> None:
        self.assertEqual([], validate_purchase_review_fixture(self.fixture))

    def test_purchase_review_can_produce_redacted_preview_without_official_action(self) -> None:
        preview = build_purchase_review_preview(self.workflow)

        self.assertEqual(PREVIEW_STATUS, preview["status"])
        self.assertEqual(PREVIEW_ACTION, preview["actionId"])
        self.assertFalse(preview["officialActionPerformed"])
        self.assertFalse(preview["paymentAttempted"])
        self.assertFalse(preview["certificationAttempted"])
        self.assertFalse(preview["cancellationAttempted"])
        self.assertFalse(preview["inspectionSchedulingAttempted"])
        self.assertGreaterEqual(len(preview["reviewSteps"]), 3)
        for step in preview["reviewSteps"]:
            self.assertTrue(step["redactedValue"].startswith("[REDACTED"))

    def test_guarded_actions_are_refused_without_confirmation(self) -> None:
        for action_id in GUARDED_ACTIONS:
            with self.subTest(action_id=action_id):
                decision = evaluate_purchase_review_action(self.workflow, action_id)
                self.assertEqual(REFUSED_STATUS, decision["status"])
                self.assertFalse(decision["allowed"])
                self.assertFalse(decision["officialActionPerformed"])
                self.assertFalse(decision["paymentAttempted"])
                self.assertIn("exact current-session confirmation", decision["reason"])

    def test_generic_wrong_session_and_wrong_action_confirmations_are_refused(self) -> None:
        refused_attempt_ids = {
            "generic-confirmation",
            "wrong-session",
            "wrong-action",
        }
        for attempt in self.fixture["attempts"]:
            if attempt["attemptId"] not in refused_attempt_ids:
                continue
            with self.subTest(attempt_id=attempt["attemptId"]):
                decision = evaluate_purchase_review_action(
                    self.workflow,
                    attempt["actionId"],
                    attempt.get("confirmation"),
                )
                self.assertEqual(REFUSED_STATUS, decision["status"])
                self.assertFalse(decision["allowed"])
                self.assertEqual(attempt["expectedStatus"], decision["status"])

    def test_exact_session_specific_purchase_confirmation_reaches_checkpoint_only(self) -> None:
        attempt = next(
            item
            for item in self.fixture["attempts"]
            if item["attemptId"] == "exact-purchase-confirmation"
        )
        decision = evaluate_purchase_review_action(
            self.workflow,
            attempt["actionId"],
            attempt["confirmation"],
        )

        self.assertEqual(CONFIRMED_STATUS, decision["status"])
        self.assertTrue(decision["allowed"])
        self.assertTrue(decision["confirmationRecorded"])
        self.assertFalse(decision["officialActionPerformed"])
        self.assertFalse(decision["paymentAttempted"])
        self.assertIn("fixture performs no live DevHub action", decision["nextStep"])

    def test_fixture_attempt_expectations_match_evaluator(self) -> None:
        for attempt in self.fixture["attempts"]:
            with self.subTest(attempt_id=attempt["attemptId"]):
                decision = evaluate_purchase_review_action(
                    self.workflow,
                    attempt["actionId"],
                    attempt.get("confirmation"),
                )
                self.assertEqual(attempt["expectedStatus"], decision["status"])


if __name__ == "__main__":
    unittest.main()
