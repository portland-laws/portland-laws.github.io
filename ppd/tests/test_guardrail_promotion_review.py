from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from ppd.agent_readiness.promotion_review import (
    require_guardrail_bundle_promotion_review_packet_valid,
    validate_guardrail_bundle_promotion_review_packet,
)

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrail_promotion_review" / "packet.json"


def _fixture() -> dict:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


class GuardrailPromotionReviewValidationTest(unittest.TestCase):
    def test_accepts_complete_fixture(self) -> None:
        result = validate_guardrail_bundle_promotion_review_packet(_fixture())
        self.assertTrue(result.valid, result.problems)
        require_guardrail_bundle_promotion_review_packet_valid(_fixture())

    def test_rejects_uncited_predicate_diff(self) -> None:
        packet = _fixture()
        packet["predicate_diffs"][0].pop("source_evidence_ids")
        result = validate_guardrail_bundle_promotion_review_packet(packet)
        self.assertFalse(result.valid)
        self.assertIn("predicate diff diff-payment-gate must cite source evidence", result.problems)

    def test_rejects_missing_regression_coverage_link(self) -> None:
        packet = _fixture()
        packet["regression_coverage_links"][0]["covered_diff_ids"] = ["diff-payment-gate"]
        result = validate_guardrail_bundle_promotion_review_packet(packet)
        self.assertFalse(result.valid)
        self.assertIn("predicate diff diff-upload-refusal lacks regression coverage", result.problems)

    def test_rejects_missing_high_risk_refusal_or_exact_confirmation_gate(self) -> None:
        packet = _fixture()
        packet["guardrail_gates"] = [
            gate for gate in packet["guardrail_gates"] if not (gate["action_type"] == "payment" and gate["gate_type"] == "refusal")
        ]
        result = validate_guardrail_bundle_promotion_review_packet(packet)
        self.assertFalse(result.valid)
        self.assertIn("high-risk action payment is missing a refusal gate", result.problems)

    def test_rejects_private_case_facts(self) -> None:
        packet = _fixture()
        packet["case_facts"] = [
            {
                "fact_id": "applicant-email",
                "privacy_classification": "private",
                "value_policy": "metadata_only",
                "value": "applicant@example.invalid",
            }
        ]
        result = validate_guardrail_bundle_promotion_review_packet(packet)
        self.assertFalse(result.valid)
        self.assertIn("case fact applicant-email uses private privacy classification", result.problems)
        self.assertIn("case fact applicant-email contains private value field value", result.problems)

    def test_rejects_active_bundle_mutation(self) -> None:
        packet = _fixture()
        packet["active_bundle_mutation"] = True
        packet["predicate_diffs"][0]["target_bundle_id"] = packet["active_bundle_id"]
        result = validate_guardrail_bundle_promotion_review_packet(packet)
        self.assertFalse(result.valid)
        self.assertIn("promotion review packet must not mutate the active bundle", result.problems)
        self.assertIn("predicate diff diff-payment-gate targets the active bundle", result.problems)

    def test_rejects_production_ready_with_unresolved_review_items(self) -> None:
        packet = deepcopy(_fixture())
        packet["review_items"][0]["status"] = "open"
        result = validate_guardrail_bundle_promotion_review_packet(packet)
        self.assertFalse(result.valid)
        self.assertIn("production-ready promotion packet has unresolved review item legal-review", result.problems)


if __name__ == "__main__":
    unittest.main()
