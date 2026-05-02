"""Validate DevHub draft-action previews remain reversible and non-consequential."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "draft_action_preview.json"
REVERSIBLE_ACTION_CLASS = "reversible_draft_fill"
ALLOWED_PLAYWRIGHT_ACTIONS = {"fill", "selectOption", "check", "uncheck"}
FORBIDDEN_ACTION_CLASSES = {
    "upload",
    "submit",
    "certify",
    "payment",
    "cancellation",
    "mfa",
    "captcha",
    "inspection_scheduling",
    "consequential",
    "financial",
}


class DevHubDraftActionPreviewFixtureTest(unittest.TestCase):
    def setUp(self) -> None:
        with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
            self.fixture: dict[str, Any] = json.load(fixture_file)

    def test_reversible_draft_fills_are_preview_only(self) -> None:
        previews = self.fixture.get("draftActionPreviews")
        self.assertIsInstance(previews, list)
        self.assertGreater(len(previews), 0)

        preview_mode = self.fixture.get("previewMode", {})
        self.assertTrue(preview_mode.get("enabled"))
        self.assertTrue(preview_mode.get("dryRun"))
        self.assertFalse(preview_mode.get("executesBrowserActions"))
        self.assertTrue(preview_mode.get("requiresUserReviewBeforeExecution"))

        for preview in previews:
            with self.subTest(preview_id=preview.get("previewId")):
                self.assertEqual(preview.get("actionClass"), REVERSIBLE_ACTION_CLASS)
                self.assertIn(preview.get("playwrightAction"), ALLOWED_PLAYWRIGHT_ACTIONS)
                self.assertTrue(preview.get("previewOnly"))
                self.assertEqual(preview.get("executionStatus"), "not_executed")
                self.assert_accessible_selector(preview.get("selectorBasis"))
                self.assert_redacted_field_values(preview.get("field"))
                self.assert_source_evidence(preview.get("sourceEvidenceIds"))

    def test_preview_actions_do_not_include_forbidden_actions(self) -> None:
        previews = self.fixture["draftActionPreviews"]
        forbidden_terms = {term.lower() for term in self.fixture.get("forbiddenActionTerms", [])}
        self.assertTrue(forbidden_terms)

        for preview in previews:
            with self.subTest(preview_id=preview.get("previewId")):
                searchable_values = [
                    preview.get("previewId", ""),
                    preview.get("actionClass", ""),
                    preview.get("playwrightAction", ""),
                    preview.get("field", {}).get("fieldId", ""),
                    preview.get("field", {}).get("label", ""),
                ]
                searchable = " ".join(str(value).lower() for value in searchable_values)
                for forbidden_term in forbidden_terms:
                    self.assertNotIn(forbidden_term, searchable)

                action_class = str(preview.get("actionClass", "")).lower()
                self.assertNotIn(action_class, FORBIDDEN_ACTION_CLASSES)
                self.assert_no_forbidden_stop_action(preview.get("stopBefore", []))

    def assert_accessible_selector(self, selector: Any) -> None:
        self.assertIsInstance(selector, dict)
        self.assertIn(selector.get("role"), {"textbox", "combobox", "checkbox", "radio"})
        self.assertTrue(str(selector.get("accessibleName", "")).strip())
        self.assertTrue(str(selector.get("label", "")).strip())
        self.assertIsInstance(selector.get("required"), bool)

    def assert_redacted_field_values(self, field: Any) -> None:
        self.assertIsInstance(field, dict)
        self.assertTrue(str(field.get("fieldId", "")).strip())
        self.assertTrue(str(field.get("label", "")).strip())
        self.assertIsInstance(field.get("required"), bool)
        before_value = str(field.get("beforeValue", ""))
        preview_value = str(field.get("previewValue", ""))
        self.assertTrue(before_value.startswith("[redacted"))
        self.assertTrue(preview_value.startswith("[redacted"))

    def assert_source_evidence(self, source_evidence_ids: Any) -> None:
        self.assertIsInstance(source_evidence_ids, list)
        self.assertGreater(len(source_evidence_ids), 0)
        for source_evidence_id in source_evidence_ids:
            self.assertTrue(str(source_evidence_id).strip())

    def assert_no_forbidden_stop_action(self, stop_before: Any) -> None:
        self.assertIsInstance(stop_before, list)
        forbidden_stop_actions = {
            "official_submission",
            "certification",
            "payment",
            "upload",
            "inspection_scheduling",
        }
        self.assertTrue(forbidden_stop_actions.issubset(set(stop_before)))


if __name__ == "__main__":
    unittest.main()
