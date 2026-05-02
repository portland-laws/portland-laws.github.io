"""Fixture-backed guardrail tests for FCC wireless DevHub draft review.

These tests use only a synthetic mocked workflow fixture. They do not open
DevHub, authenticate, upload files, certify statements, submit requests, enter
payment details, cancel requests, or schedule inspections.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any, Mapping


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub"
    / "fcc_wireless_application_draft_review_guardrails.json"
)

OFFICIAL_OPERATIONS = {
    "official_upload",
    "certification",
    "submission",
    "payment",
    "cancellation",
    "inspection_scheduling",
}

OFFICIAL_CLASSIFICATIONS = {"consequential", "financial"}

PRIVATE_MARKERS = (
    "password",
    "authorization",
    "bearer ",
    "cookie",
    "client_secret",
    "refresh_token",
    "storage_state",
    "auth_state",
    "trace.zip",
    "/traces/",
    "\\traces\\",
    "/screenshots/",
    "\\screenshots\\",
    "ppd/data/private",
    "ppd\\data\\private",
    "raw_crawl",
    "raw-crawl",
)


def _load_fixture() -> Mapping[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _decision(
    action: Mapping[str, Any],
    current_session_id: str,
    confirmation: Mapping[str, str] | None,
) -> Mapping[str, Any]:
    if action["classification"] == "draft_preview":
        return {
            "allowed": bool(action.get("allowedWithoutConfirmation")),
            "reason": "preview_only",
            "mayMutateDevHub": bool(action["expectedPreview"]["mayMutateDevHub"]),
            "mayCreateOfficialRecord": bool(action["expectedPreview"]["mayCreateOfficialRecord"]),
            "mayChargeFees": bool(action["expectedPreview"]["mayChargeFees"]),
            "mayScheduleInspection": bool(action["expectedPreview"]["mayScheduleInspection"]),
        }

    if not action.get("requiresExactSessionConfirmation"):
        return {"allowed": True, "reason": "confirmation_not_required"}

    if confirmation is None:
        return {"allowed": False, "reason": "missing_exact_session_confirmation"}

    if confirmation.get("sessionId") != current_session_id:
        return {"allowed": False, "reason": "session_mismatch"}

    if confirmation.get("text") != action.get("exactConfirmationText"):
        return {"allowed": False, "reason": "confirmation_text_mismatch"}

    return {"allowed": True, "reason": "exact_session_confirmation_present"}


class DevHubFccWirelessDraftReviewGuardrailTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = _load_fixture()
        self.current_session_id = str(self.fixture["currentSessionId"])
        self.actions = list(self.fixture["actions"])

    def test_fixture_is_synthetic_redacted_and_committed_under_ppd_tests(self) -> None:
        self.assertTrue(str(FIXTURE_PATH).endswith("ppd/tests/fixtures/devhub/fcc_wireless_application_draft_review_guardrails.json"))
        self.assertEqual("fixture_contains_only_redacted_values", self.fixture["workflowState"]["redactionStatus"])
        privacy_assertions = self.fixture["privacyAssertions"]
        self.assertTrue(privacy_assertions)
        self.assertFalse(any(privacy_assertions.values()))

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in PRIVATE_MARKERS:
            self.assertNotIn(marker, serialized)

    def test_fcc_wireless_draft_review_can_produce_preview_without_confirmation(self) -> None:
        preview_actions = [action for action in self.actions if action["operation"] == "preview"]
        self.assertEqual(1, len(preview_actions))

        decision = _decision(preview_actions[0], self.current_session_id, confirmation=None)

        self.assertTrue(decision["allowed"])
        self.assertEqual("preview_only", decision["reason"])
        self.assertFalse(decision["mayMutateDevHub"])
        self.assertFalse(decision["mayCreateOfficialRecord"])
        self.assertFalse(decision["mayChargeFees"])
        self.assertFalse(decision["mayScheduleInspection"])

    def test_official_fcc_wireless_actions_require_exact_session_confirmation(self) -> None:
        official_actions = [action for action in self.actions if action["operation"] in OFFICIAL_OPERATIONS]
        self.assertEqual(OFFICIAL_OPERATIONS, {action["operation"] for action in official_actions})

        for action in official_actions:
            with self.subTest(action=action["id"]):
                self.assertIn(action["classification"], OFFICIAL_CLASSIFICATIONS)
                self.assertTrue(action["requiresExactSessionConfirmation"])
                self.assertTrue(action["blockedWithoutExactSessionConfirmation"])
                self.assertIn(self.current_session_id, action["exactConfirmationText"])
                self.assertIn("ppd_guarded_action_executor_plan", action["evidenceIds"])

                missing_decision = _decision(action, self.current_session_id, confirmation=None)
                self.assertFalse(missing_decision["allowed"])
                self.assertEqual("missing_exact_session_confirmation", missing_decision["reason"])

    def test_generic_stale_or_wrong_action_confirmations_do_not_unlock_official_actions(self) -> None:
        official_actions = [action for action in self.actions if action["operation"] in OFFICIAL_OPERATIONS]
        negative_cases = list(self.fixture["negativeConfirmationCases"])
        self.assertEqual(4, len(negative_cases))

        for action in official_actions:
            for case in negative_cases:
                with self.subTest(action=action["id"], case=case["id"]):
                    decision = _decision(action, self.current_session_id, case["confirmation"])
                    self.assertEqual(case["expectedAllowed"], decision["allowed"])
                    self.assertEqual(case["expectedReason"], decision["reason"])

    def test_exact_current_session_confirmation_is_action_specific(self) -> None:
        official_actions = [action for action in self.actions if action["operation"] in OFFICIAL_OPERATIONS]

        for action in official_actions:
            with self.subTest(action=action["id"]):
                confirmation = {
                    "sessionId": self.current_session_id,
                    "text": action["exactConfirmationText"],
                }
                decision = _decision(action, self.current_session_id, confirmation)
                self.assertTrue(decision["allowed"])
                self.assertEqual("exact_session_confirmation_present", decision["reason"])


if __name__ == "__main__":
    unittest.main()
