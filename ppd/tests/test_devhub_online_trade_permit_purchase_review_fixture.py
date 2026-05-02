import json
import re
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub"
    / "online_trade_permit_purchase_review_snapshot.json"
)

FORBIDDEN_KEYS = {
    "auth",
    "authState",
    "auth_state",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "download",
    "downloads",
    "html",
    "localStorage",
    "password",
    "raw",
    "rawBody",
    "raw_body",
    "responseBody",
    "response_body",
    "screenShot",
    "screenshot",
    "screenshots",
    "secret",
    "storageState",
    "storage_state",
    "token",
    "trace",
    "traces",
}

UNREDACTED_VALUE_PATTERNS = (
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\\.[A-Z]{2,}", re.IGNORECASE),
    re.compile(r"\\b\\d{3}[-. ]\\d{3}[-. ]\\d{4}\\b"),
    re.compile(r"\\b\\d{5}(?:-\\d{4})?\\b"),
    re.compile(r"\\b(?:4\\d{12}(?:\\d{3})?|5[1-5]\\d{14}|3[47]\\d{13})\\b"),
    re.compile(r"\\b[A-Z]{2,4}-?\\d{5,}\\b"),
)

REDACTABLE_VALUE_KEYS = {
    "redactedAmount",
    "redactedDraftReference",
    "redactedTotal",
    "redactedValue",
}


class DevHubOnlineTradePermitPurchaseReviewFixtureTest(unittest.TestCase):
    def load_fixture(self):
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            return json.load(fixture_file)

    def walk(self, value, path="$"):
        yield path, value
        if isinstance(value, dict):
            for key, child in value.items():
                yield from self.walk(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from self.walk(child, f"{path}[{index}]")

    def test_fixture_shape_and_mock_boundaries(self):
        fixture = self.load_fixture()
        self.assertEqual(1, fixture["schemaVersion"])
        self.assertEqual("online_trade_permit_purchase_review", fixture["workflow"])
        self.assertEqual("mocked_devhub_fixture_only", fixture["capturedFrom"])
        self.assertFalse(fixture["sourceLimits"]["liveDevHubUsed"])
        self.assertFalse(fixture["sourceLimits"]["browserTraceIncluded"])
        self.assertFalse(fixture["sourceLimits"]["screenshotIncluded"])
        self.assertFalse(fixture["sourceLimits"]["rawResponseIncluded"])
        self.assertFalse(fixture["sourceLimits"]["downloadIncluded"])
        self.assertFalse(fixture["sourceLimits"]["paymentDataIncluded"])
        self.assertGreaterEqual(len(fixture["screenStates"]), 2)

    def test_semantic_selectors_required_fields_and_validation_messages(self):
        fixture = self.load_fixture()
        states = fixture["screenStates"]
        selector_ids = {
            selector["selectorId"]
            for state in states
            for selector in state["semanticSelectors"]
        }
        self.assertIn("contractor-license-field", selector_ids)
        self.assertIn("fee-review-region", selector_ids)
        self.assertIn("confirm-purchase-button", selector_ids)

        for state in states:
            self.assertTrue(state["semanticSelectors"])
            for selector in state["semanticSelectors"]:
                self.assertIn(selector["role"], {"button", "checkbox", "combobox", "region", "textbox"})
                self.assertTrue(selector["accessibleName"])
                self.assertTrue(selector["labelText"])
                self.assertTrue(selector["nearbyHeading"])
                self.assertIsNone(selector["fallbackCss"])

        missing_state = next(state for state in states if state["stateId"] == "review_required_fields_missing")
        missing_required = {
            field["fieldId"]
            for field in missing_state["requiredFields"]
            if field["required"] and field["status"] == "missing"
        }
        self.assertEqual(
            {"contractor-license-number", "work-description", "applicant-attestation-review"},
            missing_required,
        )
        self.assertEqual(3, len(missing_state["validationMessages"]))

    def test_fee_review_save_for_later_and_confirmation_gates(self):
        fixture = self.load_fixture()
        states_by_id = {state["stateId"]: state for state in fixture["screenStates"]}
        blocked_state = states_by_id["review_required_fields_missing"]
        ready_state = states_by_id["review_ready_for_exact_confirmation"]

        self.assertEqual("blocked_until_required_fields_complete", blocked_state["feeReviewState"]["status"])
        self.assertEqual("ready_for_user_confirmation", ready_state["feeReviewState"]["status"])
        for state in (blocked_state, ready_state):
            self.assertTrue(state["feeReviewState"]["amountsRedacted"])
            self.assertTrue(state["feeReviewState"]["rows"])
            self.assertTrue(state["saveForLaterState"]["available"])
            self.assertEqual("save-for-later-button", state["saveForLaterState"]["buttonSelectorId"])

        gates = [gate for state in fixture["screenStates"] for gate in state["confirmationGates"]]
        purchase_gates = [gate for gate in gates if gate["action"] == "purchase_online_trade_permit"]
        self.assertEqual(2, len(purchase_gates))
        for gate in purchase_gates:
            self.assertEqual("financial", gate["classification"])
            self.assertEqual(
                "I confirm I want to purchase this online trade permit after reviewing the redacted fee total.",
                gate["requiredExactConfirmation"],
            )
            self.assertTrue(gate["blockingReasons"])

        payment_gate = next(gate for gate in gates if gate["action"] == "enter_payment_details")
        self.assertEqual("refused_for_automation", payment_gate["currentState"])
        self.assertIn("payment_details_must_not_be_automated", payment_gate["blockingReasons"])

    def test_navigation_edges_are_non_irreversible_except_stop_gate(self):
        fixture = self.load_fixture()
        allowed = {"safe_read_only", "reversible_draft_edit", "financial"}
        edges = [edge for state in fixture["screenStates"] for edge in state["navigationEdges"]]
        self.assertTrue(edges)
        for edge in edges:
            self.assertIn(edge["classification"], allowed)
            self.assertTrue(edge["fromStateId"])
            self.assertTrue(edge["toStateId"])
            self.assertTrue(edge["accessibleName"])
        financial_edges = [edge for edge in edges if edge["classification"] == "financial"]
        self.assertEqual(["purchase_not_performed_by_fixture"], [edge["toStateId"] for edge in financial_edges])

    def test_fixture_contains_no_private_artifact_keys_or_unredacted_values(self):
        fixture = self.load_fixture()
        for path, value in self.walk(fixture):
            if isinstance(value, dict):
                for key in value:
                    self.assertNotIn(key, FORBIDDEN_KEYS, f"forbidden key at {path}.{key}")
            if isinstance(value, str):
                for pattern in UNREDACTED_VALUE_PATTERNS:
                    self.assertIsNone(pattern.search(value), f"unredacted value at {path}: {value}")

        for path, value in self.walk(fixture):
            if path.rsplit(".", 1)[-1] in REDACTABLE_VALUE_KEYS:
                self.assertIsInstance(value, str)
                self.assertTrue(value.startswith("REDACTED_"), f"expected redacted placeholder at {path}")


if __name__ == "__main__":
    unittest.main()
