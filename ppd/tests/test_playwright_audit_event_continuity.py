from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "audit_event_continuity.json"
PROHIBITED_ACTIONS = {
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


class PlaywrightAuditEventContinuityTest(unittest.TestCase):
    def test_audit_event_records_reversible_draft_edit_context(self) -> None:
        fixture = _load_fixture()
        event = fixture["auditEvent"]

        self.assertEqual(fixture["captureMode"], "synthetic_fixture_only")
        self.assertTrue(fixture["noLiveBrowserSession"])
        self.assertFalse(fixture["usesAuthenticationState"])
        self.assertFalse(fixture["usesBrowserTrace"])
        self.assertFalse(fixture["usesScreenshots"])
        self.assertEqual(event["actionClassification"], "reversible_draft_edit")
        self.assertEqual(event["actionType"], "fill_field_preview")
        self.assertFalse(event["executesBrowserAction"])
        self.assertTrue(event["previewOnly"])

    def test_selector_basis_and_source_requirement_are_present(self) -> None:
        fixture = _load_fixture()
        selector = fixture["auditEvent"]["selectorBasis"]
        requirement = fixture["sourceRequirement"]

        self.assertEqual(selector["strategy"], "accessible_role_name")
        self.assertEqual(selector["role"], "textbox")
        self.assertTrue(selector["accessibleName"])
        self.assertTrue(selector["labelText"])
        self.assertTrue(selector["nearbyHeading"])
        self.assertIn("getByRole", selector["stableLocator"])
        self.assertEqual(requirement["requirementId"], "required-fact-project-description")
        self.assertGreaterEqual(len(requirement["sourceEvidenceIds"]), 1)
        self.assertEqual(
            set(requirement["sourceEvidenceIds"]),
            set(fixture["auditEvent"]["sourceEvidenceIds"]),
        )

    def test_user_confirmation_state_fails_closed_for_preview(self) -> None:
        confirmation = _load_fixture()["auditEvent"]["userConfirmation"]

        self.assertFalse(confirmation["exactExplicitConfirmationPresent"])
        self.assertFalse(confirmation["requiredForDraftPreview"])

    def test_before_after_field_state_is_redacted_and_distinct(self) -> None:
        field_state = _load_fixture()["auditEvent"]["fieldState"]

        self.assertEqual(field_state["before"]["redactionState"], "redacted")
        self.assertEqual(field_state["after"]["redactionState"], "redacted")
        self.assertRegex(field_state["before"]["value"], r"^\[[A-Z_]+\]$")
        self.assertRegex(field_state["after"]["value"], r"^\[[A-Z_]+\]$")
        self.assertNotEqual(field_state["before"]["value"], field_state["after"]["value"])

    def test_irreversible_or_access_control_actions_are_only_blocked_metadata(self) -> None:
        event = _load_fixture()["auditEvent"]

        self.assertEqual(PROHIBITED_ACTIONS, set(event["blockedActionTypes"]))
        serialized = json.dumps(event).lower()
        self.assertNotIn("storage_state", serialized)
        self.assertNotIn("cookie", serialized)
        self.assertNotIn("trace.zip", serialized)
        self.assertNotIn("screenshot", serialized)


def _load_fixture() -> dict[str, Any]:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError("audit event fixture must be a JSON object")
    return data


if __name__ == "__main__":
    unittest.main()
