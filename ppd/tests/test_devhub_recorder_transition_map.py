from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "recorder_state_transition_map.json"
FORBIDDEN_PREVIEW_ACTIONS = {
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


class DevHubRecorderTransitionMapTest(unittest.TestCase):
    def test_transition_map_links_selector_preview_and_audit_fixtures(self) -> None:
        fixture = _load_fixture()
        linked = fixture["linkedFixtureIds"]

        self.assertEqual(fixture["captureMode"], "synthetic_fixture_only")
        self.assertTrue(fixture["noLiveBrowserSession"])
        self.assertFalse(fixture["usesAuthenticationState"])
        self.assertFalse(fixture["usesBrowserTrace"])
        self.assertFalse(fixture["usesScreenshots"])
        self.assertTrue(linked["accessibleSelectorContract"])
        self.assertTrue(linked["draftActionPreview"])
        self.assertTrue(linked["auditEvent"])

    def test_transitions_are_fixture_only_and_redacted(self) -> None:
        fixture = _load_fixture()
        transitions = fixture["transitions"]

        self.assertGreaterEqual(len(transitions), 2)
        for transition in transitions:
            with self.subTest(transition=transition["transitionId"]):
                self.assertFalse(transition["executesBrowserAction"])
                self.assertTrue(transition["sourceEvidenceIds"])
                serialized = json.dumps(transition).lower()
                self.assertNotIn("storage_state", serialized)
                self.assertNotIn("cookie", serialized)
                self.assertNotIn("trace.zip", serialized)
                self.assertNotIn("screenshot", serialized)
                for key in ("beforeValue", "afterValue"):
                    if key in transition:
                        self.assertRegex(transition[key], r"^\[[A-Z_]+\]$")
                selector = transition.get("selectorBasis")
                if selector:
                    self.assertEqual(selector["strategy"], "accessible_role_name")
                    self.assertRegex(selector["redactedValue"], r"^\[[A-Z_]+\]$")

    def test_refused_actions_are_declared_but_not_used_as_previews(self) -> None:
        fixture = _load_fixture()
        refused_actions = set(fixture["refusedActionTypes"])
        transition_event_kinds = {transition["eventKind"] for transition in fixture["transitions"]}

        self.assertTrue(FORBIDDEN_PREVIEW_ACTIONS.issubset(refused_actions))
        self.assertFalse(FORBIDDEN_PREVIEW_ACTIONS.intersection(transition_event_kinds))


def _load_fixture() -> dict[str, Any]:
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise AssertionError("recorder transition map fixture must be a JSON object")
    return data


if __name__ == "__main__":
    unittest.main()
