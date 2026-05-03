from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "process_state" / "process_state_transition_scenario.json"


class ProcessStateTransitionScenarioTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_states_include_public_mocked_preview_and_blocked_transition_types(self) -> None:
        self.assertEqual("process_state_transition_scenario", self.fixture["fixtureKind"])
        state_types = {state["stateType"] for state in self.fixture["states"]}
        self.assertTrue(
            {
                "public_guidance",
                "mocked_devhub_read_only",
                "reversible_preview",
                "blocked_consequential_transition",
            }.issubset(state_types)
        )

    def test_transitions_gate_questions_preview_and_submission(self) -> None:
        states = {state["stateId"] for state in self.fixture["states"]}
        for transition in self.fixture["transitions"]:
            self.assertIn(transition["fromState"], states)
            self.assertIn(transition["toState"], states)
        submit = next(item for item in self.fixture["transitions"] if item["transitionId"] == "transition-submit-application")
        self.assertEqual("consequential", submit["actionClass"])
        self.assertFalse(submit["allowedAutonomous"])
        self.assertTrue(submit["blockedByDefault"])
        self.assertTrue(submit["requiresExactConfirmation"])
        self.assertFalse(submit["exactConfirmationPresent"])
        question = next(item for item in self.fixture["transitions"] if item["actionClass"] == "ask_user_question")
        self.assertTrue(question["sourceLinkedQuestion"].endswith("?"))
        self.assertTrue(question["allowedAutonomous"])

    def test_stale_evidence_blocks_preview_and_runtime_is_offline(self) -> None:
        invalidation = self.fixture["staleEvidenceInvalidation"]
        self.assertTrue(invalidation["enabled"])
        self.assertEqual("block_preview_and_ask_human_review", invalidation["whenEvidenceStale"])
        self.assertIn("draft-preview-ready-after-user-answer", invalidation["affectedStates"])
        boundary = self.fixture["runtimeBoundary"]
        self.assertFalse(boundary["playwrightLaunched"])
        self.assertFalse(boundary["liveAccountTouched"])
        self.assertFalse(boundary["authArtifactsStored"])
        self.assertFalse(boundary["rawBrowserStateStored"])


if __name__ == "__main__":
    unittest.main()
