from pathlib import Path
import unittest

from ppd.logic.missing_information_prompt_corpus import (
    REQUIRED_PROMPT_CATEGORIES,
    REQUIRED_SOURCE_IDS,
    expected_prompt_matrix,
    load_prompt_corpus,
    validate_prompt_corpus,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "agent_missing_information_prompt_corpus"
    / "corpus.json"
)


class AgentMissingInformationPromptCorpusTest(unittest.TestCase):
    def setUp(self):
        self.corpus = load_prompt_corpus(FIXTURE_PATH)

    def test_fixture_validates_without_llm_or_private_files(self):
        result = validate_prompt_corpus(self.corpus)

        self.assertEqual([], result.errors)
        self.assertTrue(result.ok)
        self.assertGreaterEqual(result.case_count, 3)
        self.assertTrue(REQUIRED_SOURCE_IDS.issubset(result.source_ids))
        self.assertTrue(REQUIRED_PROMPT_CATEGORIES.issubset(result.prompt_categories))

    def test_prompt_matrix_covers_release_blocker_expectations(self):
        matrix = expected_prompt_matrix(self.corpus)

        self.assertIn(
            "missing_fact_question",
            matrix["synthetic-sfr-plan-review-missing-property-facts"],
        )
        self.assertIn(
            "stale_evidence_prompt",
            matrix["synthetic-trade-permit-stale-fee-guidance"],
        )
        self.assertIn(
            "manual_handoff_prompt",
            matrix["synthetic-correction-upload-attended-handoff"],
        )
        self.assertIn(
            "refused_consequential_action_prompt",
            matrix["synthetic-correction-upload-attended-handoff"],
        )
        self.assertIn(
            "local_preview_only_expectation",
            matrix["synthetic-sfr-plan-review-missing-property-facts"],
        )

    def test_each_expected_prompt_is_source_cited(self):
        for case in self.corpus["synthetic_user_cases"]:
            self.assertTrue(case["citations"], case["case_id"])
            for prompt in case["expected_prompts"]:
                self.assertTrue(prompt["citations"], prompt["category"])
                cited_sources = {citation["source_id"] for citation in prompt["citations"]}
                self.assertTrue(cited_sources.issubset(REQUIRED_SOURCE_IDS))


if __name__ == "__main__":
    unittest.main()
