from __future__ import annotations

import json
from pathlib import Path
import unittest

from ppd.agent_response_regression_matrix import (
    MatrixValidationError,
    assert_valid_agent_response_regression_matrix,
    validate_agent_response_regression_matrix,
)


FIXTURE = Path(__file__).parent / "fixtures" / "agent_response_regression_matrix" / "invalid_cases.json"


class AgentResponseRegressionMatrixValidationTest(unittest.TestCase):
    def test_rejects_required_invalid_matrix_cases(self) -> None:
        matrix = json.loads(FIXTURE.read_text(encoding="utf-8"))

        issues = validate_agent_response_regression_matrix(matrix)
        codes = {issue.code for issue in issues}

        self.assertIn("uncited_expected_outcome", codes)
        self.assertIn("private_value", codes)
        self.assertIn("local_private_path", codes)
        self.assertIn("stale_source_marked_valid", codes)
        self.assertIn("blocked_action_downgraded_to_allowed", codes)
        self.assertIn("missing_manual_handoff_expectation", codes)

        with self.assertRaises(MatrixValidationError):
            assert_valid_agent_response_regression_matrix(matrix)

    def test_accepts_cited_read_only_regression_case(self) -> None:
        matrix = {
            "source_registry": {
                "ppd-devhub-faq-2026-05-08": {"freshness_status": "current"}
            },
            "cases": [
                {
                    "id": "read-only-status-review",
                    "workflow": "permit status review",
                    "expected_outcome": {
                        "policy": "allowed",
                        "source_evidence_ids": ["ppd-devhub-faq-2026-05-08"],
                    },
                    "validation_status": "valid",
                }
            ],
        }

        self.assertEqual(validate_agent_response_regression_matrix(matrix), [])
        assert_valid_agent_response_regression_matrix(matrix)


if __name__ == "__main__":
    unittest.main()
