from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub"
    / "workflow_resume_redacted_draft_discovery.json"
)

FORBIDDEN_ACTION_KINDS = {
    "browser_launch",
    "auth_state",
    "cookie",
    "trace",
    "screenshot",
    "upload",
    "submission",
    "payment",
    "mfa",
    "captcha",
    "cancellation",
    "certification",
    "inspection_scheduling",
}


class DevhubWorkflowResumeRedactedDiscoveryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_fixture_is_mocked_read_only_redacted_state(self) -> None:
        self.assertEqual(self.fixture["mode"], "mocked_redacted_state_only")
        self.assertFalse(self.fixture["browserLaunch"])
        self.assertFalse(self.fixture["authenticatedSession"])
        self.assertTrue(self.fixture["workflowResume"]["readOnly"])
        self.assertEqual(self.fixture["workflowResume"]["discoverySource"], "redactedState")
        self.assertTrue(self.fixture["missingFieldDetection"]["derivedFromRedactedValuesOnly"])

        for artifact_name, present in self.fixture["privateSessionArtifacts"].items():
            self.assertFalse(present, artifact_name)

    def test_discovers_saved_draft_without_private_values(self) -> None:
        drafts = self.fixture["workflowResume"]["drafts"]
        self.assertEqual(len(drafts), 1)
        draft = drafts[0]
        self.assertEqual(draft["status"], "saved_draft")
        self.assertTrue(draft["draftId"].startswith("[REDACTED_"))
        self.assertIn("stableStateKey", draft)

        for field in draft["requiredFields"]:
            self.assertTrue(field["required"])
            self.assertTrue(field["redactedValue"].startswith("[REDACTED_"), field["fieldId"])
            self.assertTrue(field["sourceEvidenceIds"], field["fieldId"])

    def test_missing_fields_are_derived_from_redacted_empty_required_fields(self) -> None:
        draft = self.fixture["workflowResume"]["drafts"][0]
        required_fields = {field["fieldId"]: field for field in draft["requiredFields"]}
        missing_fields = self.fixture["missingFieldDetection"]["missingFields"]
        missing_ids = {field["fieldId"] for field in missing_fields}

        expected_missing = {
            field_id
            for field_id, field in required_fields.items()
            if field["required"] and not field["present"] and field["redactedValue"] == "[REDACTED_EMPTY]"
        }
        self.assertEqual(missing_ids, expected_missing)

        for missing in missing_fields:
            source = required_fields[missing["fieldId"]]
            self.assertEqual(missing["reason"], "required_field_redacted_empty")
            self.assertEqual(missing["sourceEvidenceIds"], source["sourceEvidenceIds"])

    def test_action_inventory_contains_only_read_only_actions(self) -> None:
        actions = self.fixture["actionInventory"]["availableActions"]
        self.assertTrue(actions)
        for action in actions:
            self.assertEqual(action["kind"], "read_only")
            self.assertFalse(action["requiresExactUserConfirmation"])
            self.assertNotIn(action["kind"], FORBIDDEN_ACTION_KINDS)
            normalized_id = action["actionId"].lower().replace("-", "_")
            for forbidden in FORBIDDEN_ACTION_KINDS:
                self.assertNotIn(forbidden, normalized_id)

    def test_no_nested_private_artifact_payloads_are_present(self) -> None:
        forbidden_keys = {
            "authState",
            "auth_state",
            "cookies",
            "tracePath",
            "screenshotPath",
            "downloadPath",
            "rawCrawlOutput",
            "storageState",
        }
        allowed_boolean_artifact_keys = set(self.fixture["privateSessionArtifacts"].keys())

        for path, key, value in _walk_json(self.fixture):
            if key in allowed_boolean_artifact_keys:
                self.assertIs(value, False, path)
                continue
            self.assertNotIn(key, forbidden_keys, path)


def _walk_json(value: Any, path: str = "$", key: str = "") -> list[tuple[str, str, Any]]:
    items: list[tuple[str, str, Any]] = [(path, key, value)]
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            items.extend(_walk_json(child_value, f"{path}.{child_key}", str(child_key)))
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            items.extend(_walk_json(child_value, f"{path}[{index}]", key))
    return items


if __name__ == "__main__":
    unittest.main()
