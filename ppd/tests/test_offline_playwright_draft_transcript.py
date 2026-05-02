from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub"
    / "offline_playwright_draft_transcript.json"
)

FORBIDDEN_ACTIONS = {
    "upload_official_document",
    "submit_application",
    "pay_fee",
    "certify_statement",
    "cancel_request",
    "schedule_inspection",
    "mfa",
    "captcha",
}
FORBIDDEN_MARKERS = (
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
    "screenshot",
    "cookie",
    "password",
    "token",
    "ppd/data/private",
)


class OfflinePlaywrightDraftTranscriptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_transcript_is_offline_and_redacted(self) -> None:
        boundary = self.fixture["executionBoundary"]
        self.assertEqual("offline_playwright_draft_transcript", self.fixture["fixtureKind"])
        self.assertTrue(boundary["offlineFixture"])
        self.assertFalse(boundary["browserLaunched"])
        self.assertFalse(boundary["networkAccess"])
        self.assertFalse(boundary["authenticatedDevhubAccess"])
        self.assertFalse(boundary["rawBrowserStateStored"])
        self.assertFalse(boundary["visualArtifactsStored"])
        self.assertFalse(boundary["tracesStored"])

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)
        self.assertEqual([], find_unredacted_values(self.fixture))

    def test_accessible_selector_steps_are_reversible_preview_only(self) -> None:
        field_ids = {field["fieldId"] for field in self.fixture["pageSnapshot"]["fields"]}
        for step in self.fixture["plannedTranscript"]:
            self.assertEqual("preview_fill", step["action"])
            self.assertEqual("reversible_draft_edit", step["actionClass"])
            self.assertIn(step["linkedFieldId"], field_ids)
            self.assertFalse(step["executesInFixture"])
            self.assertEqual("[REDACTED_EMPTY]", step["beforeValue"])
            self.assertTrue(step["afterValue"].startswith("[REDACTED_USER_SUPPLIED_"))
            selector = step["selector"]
            self.assertIn(selector["basis"], {"role_and_accessible_name", "label_text"})
            self.assertTrue(selector["role"])
            self.assertTrue(selector["accessibleName"])
            self.assertGreaterEqual(selector["confidence"], 0.9)

    def test_exact_confirmation_gates_refuse_high_risk_actions_by_default(self) -> None:
        gates = self.fixture["exactConfirmationGates"]
        blocked = {gate["blockedAction"] for gate in gates}
        self.assertTrue(FORBIDDEN_ACTIONS.issubset(blocked))

        for gate in gates:
            self.assertTrue(gate["requiresExactConfirmation"])
            self.assertFalse(gate["exactConfirmationPresent"])
            self.assertEqual("refuse", gate["defaultDecision"])
            self.assertIn(gate["actionClass"], {"consequential", "financial", "authentication_challenge"})

    def test_audit_summary_allows_only_reversible_draft_edits(self) -> None:
        summary = self.fixture["auditSummary"]
        self.assertEqual(["reversible_draft_edit"], summary["allowedActionClasses"])
        self.assertIn("consequential", summary["refusedActionClasses"])
        self.assertIn("financial", summary["refusedActionClasses"])
        self.assertIn("authentication_challenge", summary["refusedActionClasses"])
        self.assertTrue(summary["storesOnlyRedactedValues"])
        self.assertFalse(summary["canReplayAgainstLiveDevhub"])


def find_unredacted_values(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in {"rawvalue", "privatevalue", "knownvalue"}:
                findings.append(f"{path}.{key}")
            findings.extend(find_unredacted_values(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_unredacted_values(child, f"{path}[{index}]"))
    elif isinstance(value, str) and "real user" in value.lower():
        findings.append(path)
    return findings


if __name__ == "__main__":
    unittest.main()
