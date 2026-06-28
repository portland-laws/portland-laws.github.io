from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.agent_prompt_update_candidate_packet import (
    PromptRegressionPacketError,
    assert_valid_prompt_regression_dry_run_packet,
    build_candidate_packet,
    build_prompt_regression_dry_run_packet,
    validate_candidate_packet,
    validate_prompt_regression_dry_run_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "agent_prompt_regression_dry_run_packets.json"


class AgentPromptRegressionDryRunPacketTest(unittest.TestCase):
    def _fixtures(self) -> dict[str, object]:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_built_candidate_and_dry_run_packets_validate(self) -> None:
        self.assertEqual([], validate_candidate_packet(build_candidate_packet()))
        assert_valid_prompt_regression_dry_run_packet(build_prompt_regression_dry_run_packet())

    def test_fixture_valid_packet_has_no_findings(self) -> None:
        packet = self._fixtures()["valid_packet"]
        self.assertEqual([], validate_prompt_regression_dry_run_packet(packet))

    def test_fixture_invalid_packet_rejects_required_safety_failures(self) -> None:
        packet = self._fixtures()["invalid_packet"]
        findings = validate_prompt_regression_dry_run_packet(packet)
        codes = {finding["code"] for finding in findings}

        self.assertIn("private_case_facts", codes)
        self.assertIn("local_private_path", codes)
        self.assertIn("uncited_expectation", codes)
        self.assertIn("missing_before_outcome", codes)
        self.assertIn("missing_after_outcome", codes)
        self.assertIn("missing_reviewer_owner", codes)
        self.assertIn("missing_rerun_expectations", codes)
        self.assertIn("live_execution_claim", codes)
        self.assertIn("outcome_guarantee", codes)
        self.assertIn("enabled_consequential_control", codes)
        self.assertIn("active_mutation_flag", codes)

    def test_assert_valid_raises_with_rejection_paths(self) -> None:
        packet = self._fixtures()["invalid_packet"]
        with self.assertRaises(PromptRegressionPacketError) as raised:
            assert_valid_prompt_regression_dry_run_packet(packet)
        message = str(raised.exception)
        self.assertIn("private_case_facts", message)
        self.assertIn("live_execution_claim", message)


if __name__ == "__main__":
    unittest.main()
