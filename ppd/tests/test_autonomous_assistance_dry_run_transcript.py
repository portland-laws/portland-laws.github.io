from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "autonomous_assistance" / "dry_run_transcript.json"
FORBIDDEN_MARKERS = (
    "ppd/data/private",
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
    "cookie",
    "password",
    "token",
)


class AutonomousAssistanceDryRunTranscriptTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_transcript_steps_are_ordered_from_facts_to_questions_to_actions(self) -> None:
        self.assertEqual("autonomous_assistance_dry_run_transcript", self.fixture["fixtureKind"])
        steps = self.fixture["orderedSteps"]
        self.assertEqual(list(range(1, len(steps) + 1)), [step["stepOrder"] for step in steps])
        self.assertEqual("known_user_fact", steps[0]["stepType"])
        self.assertEqual("missing_fact_question", steps[1]["stepType"])
        self.assertEqual("reversible_draft_action", steps[2]["stepType"])
        self.assertTrue(all(step["stepType"] == "refused_official_action" for step in steps[3:]))

    def test_known_facts_are_redacted_and_missing_facts_ask_user(self) -> None:
        known = next(step for step in self.fixture["orderedSteps"] if step["stepType"] == "known_user_fact")
        self.assertTrue(known["redactedValue"].startswith("[REDACTED_"))
        self.assertEqual("user_document_store", known["source"])

        missing = next(step for step in self.fixture["orderedSteps"] if step["stepType"] == "missing_fact_question")
        self.assertTrue(missing["question"].endswith("?"))
        self.assertEqual("ask_user", missing["defaultOutcome"])

    def test_draft_actions_are_reversible_and_official_actions_are_refused(self) -> None:
        draft = next(step for step in self.fixture["orderedSteps"] if step["stepType"] == "reversible_draft_action")
        self.assertTrue(draft["allowedAutonomous"])
        self.assertFalse(draft["requiresExactConfirmation"])

        refused = [step for step in self.fixture["orderedSteps"] if step["stepType"] == "refused_official_action"]
        self.assertEqual({"upload_official_document", "submit_application", "pay_fee"}, {step["actionId"] for step in refused})
        for step in refused:
            self.assertTrue(step["requiresExactConfirmation"])
            self.assertFalse(step["exactConfirmationPresent"])
            self.assertEqual("refuse", step["defaultOutcome"])

    def test_boundary_source_evidence_and_guardrails_remain_fixture_only(self) -> None:
        boundary = self.fixture["boundary"]
        self.assertTrue(boundary["fixtureOnly"])
        self.assertFalse(boundary["liveDevhubAccess"])
        self.assertFalse(boundary["playwrightLaunched"])
        self.assertFalse(boundary["officialActionAllowed"])
        self.assertFalse(boundary["privateArtifactStored"])

        for source in self.fixture["sourceEvidence"]:
            self.assertTrue(source["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertTrue(source["citation"]["locator"])
            self.assertTrue(source["citation"]["paraphrase"])

        outcome = self.fixture["guardrailOutcome"]
        self.assertTrue(outcome["knownFactsMaySeedDraftPreview"])
        self.assertTrue(outcome["missingFactsBlockCompletion"])
        self.assertTrue(outcome["officialActionsRefused"])
        self.assertTrue(outcome["humanReviewRequiredBeforeOfficialAction"])

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)


if __name__ == "__main__":
    unittest.main()
