"""Fixture-only validation for DevHub draft-action previews.

This test intentionally does not launch Playwright, authenticate, upload files,
submit applications, certify statements, pay fees, cancel requests, handle MFA or
CAPTCHA, or schedule inspections. It validates only a committed redacted JSON
fixture shape.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "draft_action_preview.json"

FORBIDDEN_ACTION_TYPES = {
    "upload",
    "submit",
    "certify",
    "certification",
    "payment",
    "pay",
    "cancel",
    "cancellation",
    "mfa",
    "captcha",
    "schedule_inspection",
    "inspection_scheduling",
}

REVERSIBLE_CLASSIFICATIONS = {"reversible_draft_edit", "draft_preview"}
DRAFT_PLAYWRIGHT_ACTIONS = {"fill", "check", "uncheck", "selectOption"}


class DevHubDraftActionPreviewFixtureTest(unittest.TestCase):
    def load_fixture(self) -> dict[str, Any]:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            data = json.load(fixture_file)
        self.assertIsInstance(data, dict)
        return data

    def test_fixture_exposes_draft_action_previews(self) -> None:
        data = self.load_fixture()

        self.assertEqual(data.get("fixtureType"), "devhubDraftActionPreview")
        self.assertTrue(data.get("source", {}).get("noLiveBrowserSession"))
        self.assertFalse(data.get("source", {}).get("containsPrivateSessionState"))
        self.assertFalse(data.get("source", {}).get("containsScreenshots"))
        self.assertFalse(data.get("source", {}).get("containsTraces"))
        self.assertFalse(data.get("source", {}).get("containsUploads"))

        previews = data.get("draftActionPreviews")
        self.assertIsInstance(previews, list, "fixture must expose draftActionPreviews")
        self.assertGreater(len(previews), 0, "fixture must include at least one draft action preview")

    def test_draft_previews_are_reversible_fill_previews_only(self) -> None:
        data = self.load_fixture()
        previews = data["draftActionPreviews"]
        evidence_ids = {item["id"] for item in data.get("evidence", [])}

        for preview in previews:
            with self.subTest(preview=preview.get("id")):
                self.assertIn(preview.get("classification"), REVERSIBLE_CLASSIFICATIONS)
                self.assertIn(preview.get("playwrightAction"), DRAFT_PLAYWRIGHT_ACTIONS)
                self.assertEqual(preview.get("actionType"), "fill")
                self.assertTrue(preview.get("previewOnly"))
                self.assertFalse(preview.get("requiresExplicitConfirmation"))
                self.assertFalse(preview.get("isIrreversible"))

                before_value = preview.get("beforeValue")
                after_value = preview.get("afterValue")
                self.assertIsInstance(before_value, str)
                self.assertIsInstance(after_value, str)
                self.assertTrue(before_value.startswith("[REDACTED"))
                self.assertTrue(after_value.startswith("[REDACTED"))

                target = preview.get("target")
                self.assertIsInstance(target, dict)
                self.assertEqual(target.get("role"), "textbox")
                self.assertEqual(target.get("selectorBasis"), "label")
                self.assertIsInstance(target.get("accessibleName"), str)
                self.assertTrue(target.get("accessibleName", "").strip())

                linked_evidence = preview.get("sourceEvidenceIds")
                self.assertIsInstance(linked_evidence, list)
                self.assertGreater(len(linked_evidence), 0)
                self.assertTrue(set(linked_evidence).issubset(evidence_ids))

    def test_draft_previews_do_not_include_forbidden_actions(self) -> None:
        data = self.load_fixture()
        previews = data["draftActionPreviews"]

        for preview in previews:
            searchable_values = {
                str(preview.get("classification", "")).lower(),
                str(preview.get("actionType", "")).lower(),
                str(preview.get("playwrightAction", "")).lower(),
                str(preview.get("id", "")).lower(),
            }
            with self.subTest(preview=preview.get("id")):
                self.assertTrue(searchable_values.isdisjoint(FORBIDDEN_ACTION_TYPES))

    def test_stop_gates_list_forbidden_actions_without_authorizing_them(self) -> None:
        data = self.load_fixture()
        stop_gates = data.get("stopGates")
        self.assertIsInstance(stop_gates, list)
        self.assertGreater(len(stop_gates), 0)

        blocked_actions: set[str] = set()
        for gate in stop_gates:
            self.assertTrue(gate.get("requiresExplicitConfirmation"))
            self.assertFalse(gate.get("defaultConfirmed"))
            blocked_actions.update(str(action).lower() for action in gate.get("blockedActionTypes", []))

        self.assertTrue(FORBIDDEN_ACTION_TYPES.intersection(blocked_actions))
        self.assertIn("submit", blocked_actions)
        self.assertIn("upload", blocked_actions)
        self.assertIn("payment", blocked_actions)
        self.assertIn("mfa", blocked_actions)
        self.assertIn("captcha", blocked_actions)
        self.assertIn("schedule_inspection", blocked_actions)


if __name__ == "__main__":
    unittest.main()
