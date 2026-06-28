from __future__ import annotations

import json
from pathlib import Path
import unittest

from ppd.logic.stale_predicate_remediation import (
    validate_stale_predicate_remediation_candidate,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "stale_predicate_remediation_candidates.json"


class StalePredicateRemediationValidationTests(unittest.TestCase):
    def test_valid_candidate_passes(self) -> None:
        fixtures = _load_fixtures()

        result = validate_stale_predicate_remediation_candidate(fixtures["valid_candidate"])

        self.assertTrue(result.ok)
        self.assertEqual([], result.errors)

    def test_invalid_candidate_rejects_all_required_guardrail_failures(self) -> None:
        fixtures = _load_fixtures()

        result = validate_stale_predicate_remediation_candidate(fixtures["invalid_candidate"])

        self.assertFalse(result.ok)
        self.assertIn("uncited_predicate_change:change-submit-permit", result.errors)
        self.assertIn("missing_stale_input_comparisons", result.errors)
        self.assertIn("missing_consequential_action_refusal:submit_permit_request", result.errors)
        self.assertIn("private_case_facts_present", result.errors)
        self.assertIn("private_citation_used:case-note-1", result.errors)
        self.assertIn("active_bundle_mutation", result.errors)
        self.assertIn("replacement_reuses_active_bundle_id", result.errors)
        self.assertIn("production_ready_before_human_review", result.errors)

    def test_unknown_citation_is_rejected(self) -> None:
        candidate = dict(_load_fixtures()["valid_candidate"])
        candidate["proposed_predicate_changes"] = [
            {
                "id": "change-with-missing-citation",
                "predicate_id": "predicate-upload-corrections-refusal",
                "action": "upload_correction",
                "citation_ids": ["missing-source"],
            }
        ]

        result = validate_stale_predicate_remediation_candidate(candidate)

        self.assertFalse(result.ok)
        self.assertIn(
            "unknown_predicate_change_citation:change-with-missing-citation:missing-source",
            result.errors,
        )

    def test_production_ready_is_allowed_after_resolved_review(self) -> None:
        candidate = dict(_load_fixtures()["valid_candidate"])
        candidate["validation_status"] = "production_ready"
        candidate["human_review_status"] = "approved"

        result = validate_stale_predicate_remediation_candidate(candidate)

        self.assertTrue(result.ok)


def _load_fixtures() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
