"""Validate missing-information to mocked DevHub form-field mappings."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub"
    / "missing_information_form_field_mapping.json"
)

FORBIDDEN_DRAFT_ACTION_TYPES = {
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


class DevHubMissingInformationFormFieldMappingTest(unittest.TestCase):
    def test_fixture_links_one_required_fact_to_one_field_evidence_and_preview(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(fixture["schemaVersion"], 1)
        mapping = fixture["mapping"]
        required_fact = mapping["requiredUserFact"]
        field = mapping["mockedDevHubField"]
        evidence = mapping["sourceEvidence"]
        action = mapping["draftPreviewAction"]

        self.assertTrue(required_fact["required"])
        self.assertEqual(
            required_fact["sourceEvidenceId"],
            evidence["evidenceId"],
        )
        self.assertEqual(action["fieldId"], field["fieldId"])
        self.assertEqual(action["classification"], "reversible_draft_edit")
        self.assertEqual(action["actionType"], "fill_field_preview")
        self.assertTrue(action["isPreviewOnly"])
        self.assertTrue(action["reversible"])
        self.assertFalse(action["executesBrowserAction"])
        self.assertFalse(action["requiresExactUserConfirmation"])

        self.assertEqual(field["role"], "textbox")
        self.assertEqual(field["selectorBasis"]["strategy"], "accessible_role_and_name")
        self.assertEqual(field["selectorBasis"]["role"], field["role"])
        self.assertEqual(field["selectorBasis"]["name"], field["accessibleName"])
        self.assertTrue(field["required"])

    def test_fixture_uses_only_redacted_values_and_blocks_irreversible_actions(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        action = fixture["mapping"]["draftPreviewAction"]
        field = fixture["mapping"]["mockedDevHubField"]

        value_fields = (
            action["beforeValue"],
            action["afterValue"],
            field["currentValue"],
        )
        for value in value_fields:
            self.assertTrue(value.startswith(""), value)

        blocked = set(action["blockedActionTypes"])
        self.assertEqual(blocked, FORBIDDEN_DRAFT_ACTION_TYPES)
        self.assertNotIn(action["actionType"], FORBIDDEN_DRAFT_ACTION_TYPES)


if __name__ == "__main__":
    unittest.main()
