"""Validate the mocked DevHub permit-fee review fixture."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub_workflow_snapshots"
    / "permit_fee_review_payment_readiness.json"
)


class PermitFeeReviewPaymentReadinessFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)
        self.serialized = json.dumps(self.fixture, sort_keys=True).lower()

    def test_fixture_is_mocked_and_contains_no_live_artifacts(self) -> None:
        self.assertEqual(self.fixture["sourceKind"], "synthetic_mock_devhub_workflow_snapshot")
        self.assertTrue(self.fixture["commitSafe"])
        self.assertTrue(self.fixture["redactionPolicy"]["noLiveBrowserArtifacts"])
        self.assertTrue(self.fixture["redactionPolicy"]["noPaymentInstrumentData"])
        for marker in (
            "screenshot",
            "password",
            "credential",
            "secret",
            "storage_state",
            "raw_body",
            "raw_html",
            "trace.zip",
            "card_number",
            "bank_account",
        ):
            self.assertNotIn(marker, self.serialized)

    def test_visible_balances_are_redacted(self) -> None:
        balances = self.fixture["visibleBalances"]
        self.assertGreaterEqual(len(balances), 3)
        for balance in balances:
            self.assertTrue(balance["visibleOnPage"])
            self.assertTrue(balance["redacted"])
            self.assertIsNone(balance["amountValue"])
            self.assertEqual(balance["currency"], "USD")
            self.assertTrue(balance["displayValue"].startswith("[REDACTED_"))

    def test_read_only_status_and_payment_instructions_are_explicit(self) -> None:
        read_only = self.fixture["workflowState"]["readOnlyStatus"]
        self.assertEqual(read_only["classification"], "safe_read_only")
        self.assertTrue(read_only["reviewOnly"])
        self.assertFalse(read_only["draftMutationAllowed"])
        self.assertFalse(read_only["financialActionAllowed"])

        readiness = self.fixture["paymentReadiness"]
        self.assertTrue(readiness["readyForUserReview"])
        self.assertFalse(readiness["readyForAutomatedPayment"])
        instruction_text = " ".join(item["text"] for item in readiness["instructions"]).lower()
        self.assertIn("review", instruction_text)
        self.assertIn("stop before", instruction_text)
        self.assertIn("confirming payment", instruction_text)

    def test_financial_actions_are_stop_points(self) -> None:
        stop_points = self.fixture["financialActionStopPoints"]
        self.assertEqual(
            {item["stopPointId"] for item in stop_points},
            {"continue_to_payment", "enter_payment_details", "confirm_payment"},
        )
        for stop_point in stop_points:
            self.assertEqual(stop_point["classification"], "financial")
            self.assertTrue(stop_point["stopBeforeAction"])
            self.assertTrue(stop_point["requiresExactUserConfirmation"])
            self.assertFalse(stop_point["confirmationIncludedInFixture"])

    def test_selectors_are_semantic_not_css_or_xpath(self) -> None:
        selectors = self.fixture["semanticSelectors"]
        self.assertGreaterEqual(len(selectors), 3)
        for selector in selectors:
            self.assertIn("role", selector)
            self.assertIn("accessibleName", selector)
            self.assertIn("labelText", selector)
            self.assertIn("nearbyHeading", selector)
            self.assertIn("urlState", selector)
            self.assertNotIn("css", selector)
            self.assertNotIn("xpath", selector)

    def test_navigation_to_payment_is_blocked_in_fixture(self) -> None:
        financial_edges = [
            edge
            for edge in self.fixture["navigationEdges"]
            if edge["classification"] == "financial"
        ]
        self.assertEqual(len(financial_edges), 1)
        self.assertTrue(financial_edges[0]["blockedInFixture"])


if __name__ == "__main__":
    unittest.main()
