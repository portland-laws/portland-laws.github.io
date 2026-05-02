from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "playwright_accessible_selector_contract.json"
ALLOWED_ROLES = {"textbox", "combobox", "checkbox", "radio", "spinbutton"}
ALLOWED_REQUIRED_BASES = {"aria-required", "visible_label", "html_required", "not_required"}


class PlaywrightAccessibleSelectorContractTest(unittest.TestCase):
    def test_mocked_devhub_form_page_uses_stable_accessible_selectors(self) -> None:
        fixture = _load_fixture()

        self.assertEqual(fixture["fixtureSchema"], "ppd.devhub.playwright_accessible_selector_contract.v1")
        self.assertEqual(fixture["captureMode"], "synthetic_fixture_only")
        self.assertTrue(fixture["noLiveBrowserSession"])
        self.assertFalse(fixture["usesAuthenticationState"])
        self.assertFalse(fixture["usesBrowserTrace"])
        self.assertFalse(fixture["usesScreenshots"])

        page = fixture["page"]
        self.assertEqual(page["stateKind"], "mocked_devhub_draft_page")
        self.assertTrue(page["urlState"]["stableUrl"].startswith("https://devhub.portlandoregon.gov/"))
        self.assertEqual(page["urlState"]["queryState"], "[REDACTED]")
        self.assertTrue(page["heading"].strip())

        fields = page["fields"]
        self.assertGreaterEqual(len(fields), 1)
        for field in fields:
            with self.subTest(field=field["fieldId"]):
                self.assertIn(field["role"], ALLOWED_ROLES)
                self.assertTrue(field["accessibleName"].strip())
                self.assertTrue(field["labelText"].strip())
                self.assertTrue(field["nearbyHeading"].strip())
                self.assertIsInstance(field["required"], bool)
                self.assertIn(field["requiredFlagBasis"], ALLOWED_REQUIRED_BASES)
                self.assertRegex(field["redactedValue"], r"^\[[A-Z_]+\]$")

                selector = field["selectorBasis"]
                self.assertEqual(selector["strategy"], "accessible_role_name")
                self.assertEqual(selector["role"], field["role"])
                self.assertEqual(selector["name"], field["accessibleName"])
                self.assertIs(selector["exact"], True)
                self.assertIn("getByRole", selector["stableLocator"])

                serialized = json.dumps(field)
                self.assertNotIn('"css"', serialized)
                self.assertNotIn('"xpath"', serialized)
                self.assertNotIn("storage_state", serialized.lower())
                self.assertNotIn("cookie", serialized.lower())

    def test_required_fields_explain_required_flag_basis(self) -> None:
        fixture = _load_fixture()
        required_fields = [field for field in fixture["page"]["fields"] if field["required"]]

        self.assertGreater(len(required_fields), 0)
        for field in required_fields:
            self.assertIn(field["requiredFlagBasis"], {"aria-required", "visible_label", "html_required"})


def _load_fixture() -> dict[str, Any]:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError("Playwright accessible selector fixture must be a JSON object")
    return data


if __name__ == "__main__":
    unittest.main()
