"""Tests for demolition application draft-review DevHub action gates."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.devhub.demolition_draft_review_guardrails import (
    GUARDED_ACTIONS,
    PREVIEW_ACTION,
    required_confirmation_phrase,
    review_action,
    validate_demolition_draft_review_fixture,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "demolition_draft_review_guardrails.json"


class DevHubDemolitionDraftReviewGuardrailTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        self.session_id = self.fixture["sessionId"]

    def test_fixture_is_valid_and_complete(self) -> None:
        self.assertEqual([], validate_demolition_draft_review_fixture(self.fixture))

    def test_draft_review_preview_is_allowed_without_confirmation(self) -> None:
        preview_action = next(
            action for action in self.fixture["actions"] if action["actionId"] == PREVIEW_ACTION
        )

        result = review_action(preview_action, self.session_id)

        self.assertTrue(result["allowed"])
        self.assertEqual("preview_allowed", result["decision"])
        self.assertFalse(result["requiresConfirmation"])

    def test_guarded_actions_are_refused_without_exact_session_confirmation(self) -> None:
        guarded_actions = [
            action for action in self.fixture["actions"] if action["actionId"] in GUARDED_ACTIONS
        ]
        self.assertEqual(GUARDED_ACTIONS, {action["actionId"] for action in guarded_actions})

        for action in guarded_actions:
            with self.subTest(action_id=action["actionId"]):
                result = review_action(action, self.session_id)
                self.assertFalse(result["allowed"])
                self.assertEqual("exact_session_confirmation_missing", result["decision"])
                self.assertEqual(
                    required_confirmation_phrase(self.session_id, action["actionId"]),
                    result["requiredConfirmation"],
                )

    def test_exact_confirmation_is_session_and_action_specific(self) -> None:
        action = {"actionId": "official_upload"}

        missing = review_action(action, self.session_id)
        wrong_session = review_action(
            {
                "actionId": "official_upload",
                "userConfirmation": required_confirmation_phrase("fixture-session-other", "official_upload"),
            },
            self.session_id,
        )
        wrong_action = review_action(
            {
                "actionId": "official_upload",
                "userConfirmation": required_confirmation_phrase(self.session_id, "submit_application"),
            },
            self.session_id,
        )
        exact = review_action(
            {
                "actionId": "official_upload",
                "userConfirmation": required_confirmation_phrase(self.session_id, "official_upload"),
            },
            self.session_id,
        )

        self.assertFalse(missing["allowed"])
        self.assertFalse(wrong_session["allowed"])
        self.assertFalse(wrong_action["allowed"])
        self.assertTrue(exact["allowed"])
        self.assertEqual("exact_session_confirmation_present", exact["decision"])


if __name__ == "__main__":
    unittest.main()
