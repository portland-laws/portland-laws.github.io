"""Fixture-only guardrail tests for Playwright planning confirmations.

These tests validate synthetic planning records only. They do not launch a
browser, authenticate, upload files, submit applications, certify statements,
pay fees, cancel requests, schedule inspections, complete MFA/CAPTCHA, create
accounts, or recover passwords.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub"
    / "playwright_planning_confirmation_guardrails.json"
)

CONFIRMATION_FIELD = "exactExplicitUserConfirmationPresent"
REFUSED_FIELD = "refused"
AUTOMATION_ALLOWED_FIELD = "automationAllowed"

GATED_ACTION_KINDS = {
    "upload",
    "submit",
    "certify",
    "pay",
    "cancel",
    "schedule_inspection",
    "mfa",
    "captcha",
    "account_creation",
    "password_recovery",
}


class PlaywrightPlanningConfirmationGuardrailTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)
        self.actions: list[dict[str, Any]] = list(self.fixture.get("actions", []))

    def test_fixture_is_offline_redacted_planning_only(self) -> None:
        context = self.fixture.get("planningContext", {})
        self.assertEqual(self.fixture.get("schemaVersion"), 1)
        self.assertFalse(context.get("browserLaunched"))
        self.assertFalse(context.get("liveDevHubSession"))
        self.assertFalse(context.get("authenticatedAutomation"))
        self.assertTrue(context.get("valuesRedacted"))

    def test_all_guarded_action_kinds_are_represented(self) -> None:
        observed_kinds = {str(action.get("kind")) for action in self.actions}
        self.assertEqual(set(), GATED_ACTION_KINDS - observed_kinds)

    def test_guarded_actions_without_exact_confirmation_are_refused(self) -> None:
        unconfirmed_actions = [
            action
            for action in self.actions
            if action.get("kind") in GATED_ACTION_KINDS
            and action.get(CONFIRMATION_FIELD) is False
        ]
        self.assertEqual(len(GATED_ACTION_KINDS), len(unconfirmed_actions))

        for action in unconfirmed_actions:
            with self.subTest(action=action.get("id")):
                self.assertIs(action.get(CONFIRMATION_FIELD), False)
                self.assertIs(action.get(REFUSED_FIELD), True)
                self.assertIs(action.get(AUTOMATION_ALLOWED_FIELD), False)
                self.assertIsInstance(action.get("refusalReason"), str)
                self.assertNotEqual("", action.get("refusalReason", "").strip())

    def test_refusal_is_not_claimed_when_exact_confirmation_is_present(self) -> None:
        confirmed_actions = [
            action
            for action in self.actions
            if action.get("kind") in GATED_ACTION_KINDS
            and action.get(CONFIRMATION_FIELD) is True
        ]
        self.assertGreaterEqual(len(confirmed_actions), 1)

        for action in confirmed_actions:
            with self.subTest(action=action.get("id")):
                self.assertIs(action.get(REFUSED_FIELD), False)
                self.assertIs(action.get(AUTOMATION_ALLOWED_FIELD), False)
                self.assertIs(action.get("requiresManualCheckpoint"), True)


if __name__ == "__main__":
    unittest.main()
