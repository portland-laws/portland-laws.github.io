from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.logic.agent_regression_matrix_validation import (
    MatrixValidationError,
    collect_agent_regression_matrix_issues,
    load_and_validate_agent_regression_matrix,
    validate_agent_regression_matrix,
)


_FIXTURES = Path(__file__).parent / "fixtures" / "agent_regression_matrices"


def _load_fixture(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_generated_agent_regression_matrix_passes() -> None:
    matrix = _load_fixture("valid_generated_matrix.json")

    validate_agent_regression_matrix(matrix)
    loaded = load_and_validate_agent_regression_matrix(str(_FIXTURES / "valid_generated_matrix.json"))

    assert loaded["matrix_id"] == "valid-generated-agent-regression-matrix"


def test_invalid_generated_agent_regression_matrix_reports_required_rejections() -> None:
    matrix = _load_fixture("invalid_generated_matrix.json")

    issues = collect_agent_regression_matrix_issues(matrix)
    codes = {issue.code for issue in issues}

    assert "uncited_expected_outcome" in codes
    assert "local_private_path" in codes
    assert "stale_source_marked_current" in codes
    assert "blocked_action_downgrade" in codes
    assert "missing_manual_handoff_expectation" in codes
    assert "live_llm_execution_flag" in codes
    assert "devhub_automation_claim" in codes
    assert "enabled_consequential_control" in codes


def test_invalid_generated_agent_regression_matrix_raises_with_issue_details() -> None:
    matrix = _load_fixture("invalid_generated_matrix.json")

    with pytest.raises(MatrixValidationError) as excinfo:
        validate_agent_regression_matrix(matrix)

    assert excinfo.value.issues
    assert "live_llm_execution_flag" in str(excinfo.value)


def test_private_secret_values_are_rejected_without_requiring_schema_specific_fields() -> None:
    matrix = {
        "generated_at": "2026-05-28T00:00:00Z",
        "cases": [
            {
                "case_id": "secret-value",
                "action": "draft field mapping",
                "expected_outcome": {
                    "decision": "blocked",
                    "source_evidence_ids": ["source-private-value-policy"],
                },
                "observed_value": "password=not-for-fixtures",
            }
        ],
    }

    codes = {issue.code for issue in collect_agent_regression_matrix_issues(matrix)}

    assert "private_value" in codes


def test_manual_handoff_blocks_can_be_cited_and_valid() -> None:
    matrix = {
        "generated_at": "2026-05-28T00:00:00Z",
        "cases": [
            {
                "case_id": "mfa-handoff",
                "action": "complete MFA during DevHub sign in",
                "expected_outcome": {
                    "decision": "blocked manual_handoff requires_attendance",
                    "source_evidence_ids": ["source-devhub-sign-in"],
                },
            }
        ],
    }

    validate_agent_regression_matrix(matrix)
