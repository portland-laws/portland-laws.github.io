from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "fees" / "fee_notice_payment_gate.json"
FORBIDDEN_MARKERS = (
    "card_number",
    "routing_number",
    "account_number",
    "cvv",
    "password",
    "token",
    "cookie",
    "auth-state",
    "storage-state",
)


class FeeNoticePaymentGateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fee_guidance_and_notices_are_public_notice_only(self) -> None:
        evidence_ids = {item["sourceEvidenceId"] for item in self.fixture["publicFeeGuidance"]}
        self.assertEqual("fee_notice_payment_gate", self.fixture["fixtureKind"])
        for source in self.fixture["publicFeeGuidance"]:
            self.assertTrue(source["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertTrue(source["citation"]["locator"])
            self.assertTrue(source["citation"]["paraphrase"])
        for notice in self.fixture["estimatedFeeNotices"]:
            self.assertFalse(notice["amountStored"])
            self.assertTrue(notice["noticeOnly"])
            self.assertTrue(set(notice["sourceEvidenceIds"]).issubset(evidence_ids))
            self.assertTrue(notice["redactedDisplay"].startswith("[REDACTED_"))

    def test_payment_is_financial_and_refused_without_exact_confirmation(self) -> None:
        action = self.fixture["financialActionClassification"]
        self.assertEqual("pay_fee", action["actionId"])
        self.assertEqual("financial", action["actionClass"])
        self.assertFalse(action["automationAllowed"])
        self.assertFalse(action["paymentDataStored"])
        self.assertTrue(action["requiresExactPaymentSpecificConfirmation"])
        self.assertFalse(action["exactPaymentSpecificConfirmationPresent"])
        requirement = self.fixture["exactConfirmationRequirements"][0]
        self.assertEqual("pay_fee", requirement["requiredPhraseMatchesAction"])
        self.assertEqual("refuse", requirement["defaultDecision"])

    def test_audit_events_and_planner_do_not_store_or_plan_payment_data(self) -> None:
        for event in self.fixture["auditEvents"]:
            self.assertFalse(event["storesPaymentData"])
        outcome = self.fixture["plannerOutcome"]
        self.assertTrue(outcome["mayShowFeeNotice"])
        self.assertFalse(outcome["mayPlanPaymentAutomation"])

    def test_private_or_payment_artifacts_are_absent(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)


if __name__ == "__main__":
    unittest.main()
