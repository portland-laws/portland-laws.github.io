from __future__ import annotations

from copy import deepcopy
import json
import unittest
from pathlib import Path

from ppd.agent_consumer_regression import build_agent_consumer_regression_rerun_plan
from ppd.agent_readiness.dry_run_promotion_sequence_packet import build_dry_run_promotion_sequence_packet
from ppd.agent_readiness.post_promotion_smoke_test_plan import (
    build_post_promotion_smoke_test_plan,
    validate_post_promotion_smoke_test_plan,
)

FIXTURES = Path(__file__).parent / "fixtures"
EXPECTATIONS = FIXTURES / "agent_readiness" / "post_promotion_smoke_test_plan_expectations.json"


def _load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _source_packets() -> tuple[dict, dict]:
    dry_run = build_dry_run_promotion_sequence_packet(
        _load_json(FIXTURES / "agent_readiness" / "dry_run_promotion_sequence_source_decision_packet.json")
    )
    regression = build_agent_consumer_regression_rerun_plan(
        _load_json(FIXTURES / "agent_consumer_regression" / "guardrail_bundle_update_candidates.json"),
        _load_json(FIXTURES / "agent_consumer_regression" / "safe_action_regression_matrix.json"),
    )
    return dry_run, regression


class PostPromotionSmokeTestPlanTest(unittest.TestCase):
    def test_builds_fixture_first_post_promotion_smoke_plan(self) -> None:
        dry_run, regression = _source_packets()
        packet = build_post_promotion_smoke_test_plan(dry_run, regression)
        expected = _load_json(EXPECTATIONS)

        result = validate_post_promotion_smoke_test_plan(packet)
        self.assertTrue(result.valid, result.problems)
        self.assertEqual(packet["packet_type"], "ppd.post_promotion_smoke_test_plan.v1")
        self.assertTrue(packet["fixture_only"])
        self.assertEqual(packet["execution_policy"], expected["execution_policy"])
        self.assertGreaterEqual(len(packet["synthetic_read_only_smoke_cases"]), expected["minimum_smoke_case_count"])
        self.assertEqual(
            {check["check_id"] for check in packet["refusal_checks"]},
            set(expected["required_refusal_check_ids"]),
        )
        self.assertEqual(
            {check["check_id"] for check in packet["reversible_draft_boundary_checks"]},
            set(expected["required_reversible_draft_boundary_check_ids"]),
        )

    def test_cases_have_citations_owners_and_no_execution_attestations(self) -> None:
        packet = build_post_promotion_smoke_test_plan(*_source_packets())
        owners = {owner["owner_id"] for owner in packet["reviewer_owners"]}
        coverage = {item["smoke_case_id"] for item in packet["expected_citation_coverage"]}

        for case in packet["synthetic_read_only_smoke_cases"]:
            self.assertIn(case["reviewer_owner"], owners)
            self.assertIn(case["smoke_case_id"], coverage)
            self.assertTrue(case["source_evidence_ids"])
            self.assertTrue(case["no_consumer_execution_attestation"])
            self.assertTrue(case["expected_read_only_answer"]["must_remain_read_only"])

    def test_validator_rejects_uncited_expected_response(self) -> None:
        packet = build_post_promotion_smoke_test_plan(*_source_packets())
        packet["synthetic_read_only_smoke_cases"][0]["source_evidence_ids"] = []
        packet["synthetic_read_only_smoke_cases"][0]["expected_read_only_answer"]["must_cite_source_evidence_ids"] = []

        result = validate_post_promotion_smoke_test_plan(packet)
        self.assertFalse(result.valid)
        self.assertTrue(any("citation" in problem or "source_evidence_ids" in problem for problem in result.problems))

    def test_validator_rejects_live_execution_private_paths_and_enabled_controls(self) -> None:
        packet = build_post_promotion_smoke_test_plan(*_source_packets())
        packet["execution_policy"]["devhub_invoked"] = True
        packet["notes"] = "The live DevHub browser executed."
        packet["local_path"] = "/tmp/private-case.json"
        packet["enabled_payment_control"] = True

        result = validate_post_promotion_smoke_test_plan(packet)
        self.assertFalse(result.valid)
        joined = "; ".join(result.problems)
        self.assertIn("devhub_invoked", joined)
        self.assertIn("local private", joined)
        self.assertIn("consequential", joined)

    def test_validator_rejects_missing_refusal_checks_and_reviewer_owners(self) -> None:
        packet = build_post_promotion_smoke_test_plan(*_source_packets())
        packet["refusal_checks"] = []
        packet["reviewer_owners"] = []
        packet["synthetic_read_only_smoke_cases"][0]["reviewer_owner"] = ""

        result = validate_post_promotion_smoke_test_plan(packet)
        self.assertFalse(result.valid)
        self.assertIn("refusal_checks must be a non-empty list", result.problems)
        self.assertIn("reviewer_owners must be a non-empty list", result.problems)

    def test_mutating_copy_does_not_affect_valid_plan(self) -> None:
        packet = build_post_promotion_smoke_test_plan(*_source_packets())
        altered = deepcopy(packet)
        altered["synthetic_read_only_smoke_cases"][0]["expected_read_only_answer"]["must_cite_source_evidence_ids"] = []

        self.assertFalse(validate_post_promotion_smoke_test_plan(altered).valid)
        self.assertTrue(validate_post_promotion_smoke_test_plan(packet).valid)


if __name__ == "__main__":
    unittest.main()
