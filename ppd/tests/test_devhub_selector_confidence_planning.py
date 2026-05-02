"""Validate mocked DevHub selector-confidence planning fixtures.

The fixture is intentionally Playwright-shaped but never imports or launches
Playwright. It checks planning evidence before any live browser session could be
started.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "selector_confidence_planning.json"
DISALLOWED_ACTIONS = {
    "upload",
    "submit",
    "certify",
    "payment",
    "cancel",
    "schedule_inspection",
    "mfa",
    "captcha",
    "account_creation",
    "password_recovery",
}
ACCESSIBLE_SELECTOR_BASIS = {"role_and_accessible_name", "label_text"}


class DevhubSelectorConfidencePlanningTest(unittest.TestCase):
    def load_fixture(self) -> dict:
        with FIXTURE_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_selector_candidates_are_ranked_by_accessible_evidence_confidence(self) -> None:
        fixture = self.load_fixture()

        self.assertEqual(fixture["planningMode"], "mocked_playwright_fixture_only")
        self.assertFalse(fixture["browserLaunchRequested"])
        self.assertFalse(fixture["liveBrowserSessionLaunched"])

        minimum_confidence = fixture["selectorPolicy"]["minimumConfidence"]
        self.assertGreaterEqual(minimum_confidence, 0.75)

        for plan in fixture["selectorPlans"]:
            candidates = plan["rankedCandidates"]
            self.assertGreaterEqual(len(candidates), 2)
            self.assertEqual([candidate["rank"] for candidate in candidates], list(range(1, len(candidates) + 1)))

            confidences = [candidate["confidence"] for candidate in candidates]
            self.assertEqual(confidences, sorted(confidences, reverse=True))

            selected = candidates[plan["selectedCandidateRank"] - 1]
            self.assertEqual(selected["decision"], "allow_preview")
            self.assertGreaterEqual(selected["confidence"], minimum_confidence)
            self.assertIn(selected["selectorBasis"], ACCESSIBLE_SELECTOR_BASIS)
            self.assertTrue(selected["role"].strip())
            self.assertTrue(selected["accessibleName"].strip() or selected["labelText"].strip())
            self.assertTrue(selected["nearbyHeading"].strip())
            self.assertTrue(selected["evidence"])
            self.assertEqual(plan["intendedAction"], "reversible_draft_edit")
            self.assertEqual(plan["redactedPlannedValue"], "")

    def test_low_confidence_selectors_are_refused_before_browser_session(self) -> None:
        fixture = self.load_fixture()
        minimum_confidence = fixture["selectorPolicy"]["minimumConfidence"]
        disallowed_basis = set(fixture["selectorPolicy"]["disallowedSelectorBasis"])

        self.assertTrue(fixture["selectorPolicy"]["refuseBeforeBrowserSession"])
        self.assertFalse(fixture["liveBrowserSessionLaunched"])

        for plan in fixture["selectorPlans"]:
            candidates_by_rank = {candidate["rank"]: candidate for candidate in plan["rankedCandidates"]}
            self.assertTrue(plan["refusals"])
            for refusal in plan["refusals"]:
                candidate = candidates_by_rank[refusal["candidateRank"]]
                self.assertEqual(refusal["decision"], "refuse_low_confidence")
                self.assertEqual(candidate["decision"], "refuse_low_confidence")
                self.assertLess(candidate["confidence"], minimum_confidence)
                self.assertIn(candidate["selectorBasis"], disallowed_basis)
                self.assertTrue(refusal["refusedBeforeBrowserSession"])
                self.assertTrue(refusal["reason"].strip())

    def test_fixture_excludes_live_or_consequential_playwright_actions(self) -> None:
        fixture = self.load_fixture()

        self.assertFalse(fixture["browserLaunchRequested"])
        self.assertFalse(fixture["liveBrowserSessionLaunched"])
        self.assertTrue(DISALLOWED_ACTIONS.issubset(set(fixture["prohibitedActions"])))

        for plan in fixture["selectorPlans"]:
            self.assertEqual(plan["intendedAction"], "reversible_draft_edit")
            self.assertNotIn(plan["intendedAction"], DISALLOWED_ACTIONS)
            for candidate in plan["rankedCandidates"]:
                selector_text = candidate["selector"].lower()
                self.assertNotIn("xpath=", selector_text)
                self.assertNotIn("submit", selector_text)
                self.assertNotIn("payment", selector_text)


if __name__ == "__main__":
    unittest.main()
