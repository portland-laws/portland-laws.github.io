"""Validate mocked Playwright action-classification fixtures for PP&D DevHub planning."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "action_classification_playwright.json"
EXPECTED_CLASSES = {
    "read_only",
    "reversible_draft_edit",
    "consequential",
    "financial",
}
FORBIDDEN_AUTOMATION_TERMS = (
    "captcha",
    "mfa",
    "account_creation",
    "password_recovery",
    "upload_file",
    "submit_now",
    "certify_now",
    "pay_now",
    "cancel_now",
    "schedule_inspection_now",
)


class PlaywrightActionClassificationFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_is_mocked_and_offline_only(self) -> None:
        self.assertEqual(self.fixture["schemaVersion"], 1)
        self.assertEqual(self.fixture["fixtureType"], "playwright_action_classification")
        self.assertIs(self.fixture["liveDevhubSession"], False)
        self.assertIs(self.fixture["playwrightRuntimeRequired"], False)

    def test_exact_confirmation_defaults_are_false_for_every_class(self) -> None:
        defaults = self.fixture["classificationDefaults"]
        self.assertEqual(set(defaults), EXPECTED_CLASSES)
        for classification, values in defaults.items():
            self.assertIs(
                values["exactConfirmationProvided"],
                False,
                f"{classification} must default exact confirmation to false",
            )

    def test_mocked_interactions_cover_all_action_classes(self) -> None:
        interactions = self.fixture["mockedFormInteractions"]
        self.assertEqual({item["classification"] for item in interactions}, EXPECTED_CLASSES)

    def test_interactions_use_accessible_selector_basis_and_redacted_values(self) -> None:
        for interaction in self.fixture["mockedFormInteractions"]:
            with self.subTest(interaction=interaction["id"]):
                selector = interaction["selectorBasis"]
                self.assertTrue(selector["role"])
                self.assertTrue(selector["accessibleName"])
                self.assertTrue(selector["labelText"])
                self.assertTrue(selector["nearbyHeading"])
                self.assertIn(selector["stableSelectorBasis"], {"role_and_accessible_name", "label_and_role"})
                self.assertIs(interaction["exactConfirmationProvidedDefault"], False)
                self.assertTrue(interaction["sourceEvidenceIds"])
                self.assert_redacted(interaction["redaction"])

    def test_consequential_and_financial_actions_stop_without_exact_confirmation(self) -> None:
        for interaction in self.fixture["mockedFormInteractions"]:
            classification = interaction["classification"]
            if classification in {"consequential", "financial"}:
                self.assertIs(interaction["exactConfirmationRequired"], True)
                self.assertIs(interaction["allowedWithoutExactConfirmation"], False)
                self.assertTrue(interaction["mockedPlaywrightAction"].startswith("stop_before"))
            else:
                self.assertIs(interaction["exactConfirmationRequired"], False)
                self.assertIs(interaction["allowedWithoutExactConfirmation"], True)

    def test_fixture_does_not_plan_forbidden_live_automation(self) -> None:
        fixture_text = json.dumps(self.fixture, sort_keys=True).lower()
        for term in FORBIDDEN_AUTOMATION_TERMS:
            self.assertNotIn(term, fixture_text)

    def assert_redacted(self, redaction: dict[str, Any]) -> None:
        for key, value in redaction.items():
            if key == "containsPrivateUserValue":
                self.assertIsInstance(value, bool)
                continue
            self.assertIsInstance(value, str)
            self.assertTrue(value.startswith("["), f"{key} must be redacted placeholder text")
            self.assertTrue(value.endswith("]"), f"{key} must be redacted placeholder text")


if __name__ == "__main__":
    unittest.main()
