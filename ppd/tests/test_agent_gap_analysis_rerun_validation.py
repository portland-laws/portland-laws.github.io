from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ppd.validation.agent_gap_analysis_rerun import issue_codes


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_gap_analysis_rerun_validation"


def _load_fixture(name: str) -> dict:
    with (FIXTURE_DIR / name).open(encoding="utf-8") as handle:
        return json.load(handle)


class AgentGapAnalysisRerunValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.packet = _load_fixture("valid_rerun_packet.json")

    def test_valid_fixture_has_no_validation_issues(self) -> None:
        self.assertEqual(issue_codes(self.packet), set())

    def test_rejects_uncited_agent_prompts(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["user_facing_questions"][0].pop("source_evidence_ids")

        self.assertIn("uncited_prompt", issue_codes(packet))

    def test_rejects_private_document_paths_and_values(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["document_metadata"] = [
            {
                "document_id": "private-site-plan",
                "local_path": "/home/alex/private/site-plan.pdf",
                "email": "owner@example.invalid"
            }
        ]

        codes = issue_codes(packet)
        self.assertIn("private_document_path", codes)
        self.assertIn("private_document_value", codes)

    def test_rejects_unsupported_next_actions(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["allowed_local_previews"].append(
            {
                "action_id": "open_devhub_authenticated_portal",
                "allowed": True,
                "requires_devhub": True,
                "requires_private_file_read": False
            }
        )

        self.assertIn("unsupported_next_action", issue_codes(packet))

    def test_rejects_changed_blocked_action_downgrades(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["comparison_to_prior_gap_analysis"]["changed_blocked_actions"]["removed"] = [
            "submit permit application"
        ]

        self.assertIn("blocked_action_downgrade", issue_codes(packet))

    def test_rejects_consequential_automation(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet["next_safe_actions"].append("submit permit application")

        self.assertIn("consequential_automation", issue_codes(packet))

    def test_rejects_missing_comparison_to_prior_gap_analysis(self) -> None:
        packet = copy.deepcopy(self.packet)
        packet.pop("comparison_to_prior_gap_analysis")

        self.assertIn("missing_prior_comparison", issue_codes(packet))


if __name__ == "__main__":
    unittest.main()
