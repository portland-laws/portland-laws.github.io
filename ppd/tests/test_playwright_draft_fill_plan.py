from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "playwright_draft_fill_plan.json"
FORBIDDEN_ACTIONS = {
    "upload",
    "submit",
    "payment",
    "certify",
    "cancel",
    "schedule_inspection",
    "mfa",
    "captcha",
    "account_creation",
    "password_recovery",
}
FORBIDDEN_MARKERS = (
    "ppd/data/private",
    "ppd/data/raw",
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
    "xpath=",
)
ALLOWED_SELECTOR_BASIS = {
    "role_and_accessible_name",
    "label_text",
    "nearby_heading_and_label",
}


class PlaywrightDraftFillPlanTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_plan_is_fixture_only_and_draft_preview_only(self) -> None:
        self.assertEqual("mocked_playwright_draft_fill_plan", self.fixture["fixtureKind"])
        self.assertEqual("fixture_only_no_browser", self.fixture["planningMode"])
        self.assertFalse(self.fixture["browserLaunchRequested"])
        self.assertFalse(self.fixture["liveBrowserStarted"])
        self.assertTrue(self.fixture["draftPreviewOnly"])
        self.assertTrue(FORBIDDEN_ACTIONS.issubset(set(self.fixture["refusedActions"])))

    def test_selector_candidates_are_ranked_and_confidence_gated(self) -> None:
        minimum = self.fixture["selectorPolicy"]["minimumConfidence"]
        self.assertGreaterEqual(minimum, 0.8)
        self.assertTrue(self.fixture["selectorPolicy"]["refuseLowConfidenceBeforeBrowser"])

        for field in self.fixture["fields"]:
            selectors = field["rankedSelectors"]
            self.assertEqual([selector["rank"] for selector in selectors], list(range(1, len(selectors) + 1)))
            confidences = [selector["confidence"] for selector in selectors]
            self.assertEqual(confidences, sorted(confidences, reverse=True))
            allowed = [selector for selector in selectors if selector["decision"] == "allow_draft_preview"]
            refused = [selector for selector in selectors if selector["decision"] == "refuse_low_confidence"]
            self.assertTrue(allowed)
            self.assertTrue(refused)
            for selector in allowed:
                self.assertGreaterEqual(selector["confidence"], minimum)
                self.assertIn(selector["selectorBasis"], ALLOWED_SELECTOR_BASIS)
                self.assertTrue(selector["role"])
                self.assertTrue(selector["accessibleName"] or selector["labelText"])
                self.assertTrue(selector["nearbyHeading"])
                self.assertTrue(selector["evidence"])
            for selector in refused:
                self.assertLess(selector["confidence"], minimum)
                self.assertIn(selector["selectorBasis"], self.fixture["selectorPolicy"]["disallowedSelectorBasis"])
                self.assertTrue(selector["refusalReason"])

    def test_missing_user_facts_are_questions_not_private_values(self) -> None:
        for field in self.fixture["fields"]:
            self.assertTrue(field["requiredUserFactId"].startswith("user."))
            self.assertTrue(field["missingFactQuestion"].endswith("?") or field["missingFactQuestion"].endswith("."))
            self.assertEqual("", field["redactedPreviewValue"])
            self.assertEqual("set_text_preview_only", field["plannedMutation"])
            self.assertTrue(field["mutationReversible"])

    def test_fixture_excludes_private_runtime_artifacts(self) -> None:
        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)
        findings = validate_no_private_runtime_artifacts(self.fixture)
        self.assertEqual([], findings)


def validate_no_private_runtime_artifacts(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).lower()
            if lowered in {"cookie", "cookies", "token", "password", "rawbody", "screenshotpath", "tracepath"}:
                findings.append(f"{path}.{key}")
            findings.extend(validate_no_private_runtime_artifacts(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(validate_no_private_runtime_artifacts(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in FORBIDDEN_MARKERS):
            findings.append(path)
    return findings


if __name__ == "__main__":
    unittest.main()
