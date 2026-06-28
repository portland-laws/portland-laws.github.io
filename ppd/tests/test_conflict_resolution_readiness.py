from __future__ import annotations

from pathlib import Path
import unittest

from ppd.logic.conflict_resolution_readiness import (
    evaluate_conflict_resolution_readiness,
    load_conflict_fixture,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "conflict_resolution_readiness"
    / "contradictory_requirements.json"
)


class ConflictResolutionReadinessTest(unittest.TestCase):
    def test_contradictory_requirements_block_formalization(self) -> None:
        fixture = load_conflict_fixture(FIXTURE_PATH)

        result = evaluate_conflict_resolution_readiness(fixture)

        self.assertEqual(
            result["readiness_status"], "blocked_by_contradictory_requirements"
        )
        self.assertFalse(result["formalization_allowed"])
        self.assertIsNone(result["selected_requirement_id"])
        self.assertEqual(len(result["conflicts"]), 1)

        conflict = result["conflicts"][0]
        self.assertEqual(
            conflict["requirement_ids"],
            ["req-plan-drawings-single-pdf", "req-plan-drawings-not-single-pdf"],
        )
        self.assertEqual(
            conflict["citation_ids"],
            ["evidence-separate-plan-files-guidance", "evidence-single-pdf-guidance"],
        )

        statuses = result["requirement_statuses"]
        self.assertEqual(
            statuses["req-plan-drawings-single-pdf"],
            "blocked_pending_human_review",
        )
        self.assertEqual(
            statuses["req-plan-drawings-not-single-pdf"],
            "blocked_pending_human_review",
        )

    def test_conflict_prompts_are_cited_and_do_not_choose_winner(self) -> None:
        fixture = load_conflict_fixture(FIXTURE_PATH)

        result = evaluate_conflict_resolution_readiness(fixture)

        prompts = result["prompts"]
        self.assertEqual(
            {prompt["prompt_type"] for prompt in prompts},
            {"missing_information", "human_review"},
        )
        for prompt in prompts:
            self.assertEqual(
                prompt["requirement_ids"],
                ["req-plan-drawings-single-pdf", "req-plan-drawings-not-single-pdf"],
            )
            self.assertEqual(
                prompt["citation_ids"],
                [
                    "evidence-separate-plan-files-guidance",
                    "evidence-single-pdf-guidance",
                ],
            )
            self.assertNotIn("winner", prompt["message"].lower())
            self.assertNotIn("prefer", prompt["message"].lower())


if __name__ == "__main__":
    unittest.main()
