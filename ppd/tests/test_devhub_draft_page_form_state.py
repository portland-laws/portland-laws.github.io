"""Validate the redacted DevHub draft-page form-state fixture.

This test intentionally inspects a committed JSON fixture only. It must not
import Playwright, launch a browser, use private auth state, or exercise live
DevHub workflows.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "draft_page_form_state.json"

ALLOWED_FIELD_ROLES = {"textbox", "combobox", "checkbox", "radio", "group"}
ALLOWED_SELECTOR_STRATEGIES = {"accessible_role_name", "label_text", "accessible_name"}
FORBIDDEN_ACTION_WORDS = {
    "captcha",
    "cancel",
    "certify",
    "inspection",
    "mfa",
    "payment",
    "pay",
    "schedule",
    "submit",
    "upload",
}
FORBIDDEN_CLASSIFICATIONS = {
    "financial",
    "potentially_consequential",
    "official_upload",
    "submission",
    "certification",
    "inspection_scheduling",
}
FORBIDDEN_SOURCE_FLAGS = {
    "capturedFromLiveSession",
    "browserLaunched",
    "containsPrivateAuthState",
    "containsScreenshot",
    "containsTrace",
}


class DevHubDraftPageFormStateFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)

    def test_fixture_is_redacted_and_does_not_describe_browser_runtime(self) -> None:
        source = self.fixture.get("source", {})
        self.assertEqual(source.get("kind"), "synthetic_redacted_fixture")
        for flag in FORBIDDEN_SOURCE_FLAGS:
            self.assertIs(source.get(flag), False, flag)
        self.assertEqual(self.fixture.get("forbiddenRuntimeArtifacts"), [])

    def test_page_state_is_a_draft_page_shape(self) -> None:
        page_state = self.fixture.get("pageState", {})
        self.assertEqual(page_state.get("workflowStatus"), "draft")
        self.assertIn("draft", page_state.get("urlPattern", ""))
        self.assertTrue(page_state.get("heading"))
        self.assertTrue(page_state.get("title"))

    def test_fields_have_accessible_selectors_labels_roles_and_required_flags(self) -> None:
        fields = self.fixture.get("fields")
        self.assertIsInstance(fields, list)
        self.assertGreaterEqual(len(fields), 3)
        self.assertTrue(any(field.get("required") is True for field in fields))
        self.assertTrue(any(field.get("required") is False for field in fields))

        seen_field_ids: set[str] = set()
        for field in fields:
            with self.subTest(field=field.get("fieldId")):
                field_id = field.get("fieldId")
                self.assertIsInstance(field_id, str)
                self.assertNotIn(field_id, seen_field_ids)
                seen_field_ids.add(field_id)

                label = field.get("label")
                role = field.get("role")
                required = field.get("required")
                selector = field.get("selector", {})

                self.assertIsInstance(label, str)
                self.assertTrue(label.strip())
                self.assertIn(role, ALLOWED_FIELD_ROLES)
                self.assertIsInstance(required, bool)
                self.assertIn(selector.get("strategy"), ALLOWED_SELECTOR_STRATEGIES)
                self.assertEqual(selector.get("role"), role)
                self.assertEqual(selector.get("labelText"), label)
                self.assertTrue(selector.get("name"))

    def test_field_values_are_redacted_placeholders_only(self) -> None:
        for field in self.fixture.get("fields", []):
            with self.subTest(field=field.get("fieldId")):
                value = field.get("value", {})
                placeholder = value.get("placeholder")
                self.assertIs(value.get("redacted"), True)
                self.assertIsInstance(placeholder, str)
                self.assertTrue(placeholder.startswith("[REDACTED:"), placeholder)
                self.assertTrue(placeholder.endswith("]"), placeholder)
                self.assertNotIn("example.com", placeholder.lower())
                self.assertNotIn("@", placeholder)

    def test_available_actions_exclude_consequential_or_prohibited_workflows(self) -> None:
        actions = self.fixture.get("availableActions", [])
        self.assertIsInstance(actions, list)
        for action in actions:
            with self.subTest(action=action.get("actionId")):
                action_text = " ".join(
                    str(action.get(key, "")).lower()
                    for key in ("actionId", "label", "classification")
                )
                self.assertNotIn(action.get("classification"), FORBIDDEN_CLASSIFICATIONS)
                for word in FORBIDDEN_ACTION_WORDS:
                    self.assertNotIn(word, action_text)


if __name__ == "__main__":
    unittest.main()
