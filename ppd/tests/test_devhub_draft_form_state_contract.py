"""Fixture-only DevHub draft form-state contract validation.

This test validates committed synthetic DevHub draft form-state metadata for
future Playwright recorder work. It must not launch Playwright, read auth state,
or depend on a live DevHub browser session.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "draft_form_state_contract.json"
ALLOWED_ROLES = {"textbox", "combobox", "radio", "checkbox", "spinbutton"}
PROHIBITED_ACTION_TERMS = {
    "captcha",
    "certify",
    "mfa",
    "pay",
    "payment",
    "schedule_inspection",
    "submit",
    "upload",
}


class DevHubDraftFormStateContractTest(unittest.TestCase):
    def test_fixture_uses_accessible_selectors_and_redacted_values(self) -> None:
        fixture = _load_fixture()

        self.assertEqual(fixture["fixtureSchema"], "ppd.devhub.draft_form_state_contract.v1")
        self.assertEqual(fixture["captureMode"], "synthetic_fixture_only")
        self.assertTrue(fixture["noLiveBrowserSession"])
        self.assertFalse(fixture["usesAuthenticationState"])
        self.assertFalse(fixture["usesBrowserTrace"])
        self.assertFalse(fixture["usesScreenshots"])

        pages = fixture.get("pages")
        self.assertIsInstance(pages, list)
        self.assertGreater(len(pages), 0)

        for page in pages:
            self.assertEqual(page.get("stateKind"), "devhub_draft_page")
            self.assertEqual(page.get("valuePolicy"), "redacted_values_only")
            self.assertTrue(str(page.get("url", "")).startswith("https://devhub.portlandoregon.gov/"))
            self.assertNotIn("storage_state", json.dumps(page).lower())
            self.assertNotIn("cookie", json.dumps(page).lower())

            fields = page.get("fields")
            self.assertIsInstance(fields, list)
            self.assertGreater(len(fields), 0)

            for field in fields:
                self.assertIsInstance(field.get("required"), bool)
                self.assertIn(field.get("role"), ALLOWED_ROLES)
                self.assertIsInstance(field.get("label"), str)
                self.assertTrue(field["label"].strip())
                self.assertRegex(field.get("redactedValue", ""), r"^$")
                self.assertEqual(field.get("selectorStrategy"), "accessible")

                selector = field.get("selector")
                self.assertIsInstance(selector, dict)
                self.assertNotIn("css", selector)
                self.assertNotIn("xpath", selector)

                accessible = selector.get("accessible")
                self.assertIsInstance(accessible, dict)
                self.assertEqual(accessible.get("role"), field.get("role"))
                self.assertEqual(accessible.get("name"), field.get("label"))
                self.assertIsInstance(accessible.get("exact"), bool)

                if field["required"]:
                    required_signal = field.get("requiredSignal")
                    self.assertIsInstance(required_signal, dict)
                    self.assertEqual(required_signal.get("kind"), "required_flag")
                    self.assertIn(required_signal.get("basis"), {"aria-required", "visible_label", "html_required"})

            available_actions = page.get("availableActions", [])
            self.assertIsInstance(available_actions, list)
            lowered_actions = {str(action).lower() for action in available_actions}
            self.assertFalse(lowered_actions.intersection(PROHIBITED_ACTION_TERMS))


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        fixture = json.load(fixture_file)
    if not isinstance(fixture, dict):
        raise AssertionError("DevHub draft form-state fixture must be a JSON object")
    return fixture


if __name__ == "__main__":
    unittest.main()
