from __future__ import annotations

import json
from pathlib import Path

from ppd.agent_handoff_expectations import validate_handoff_expectation_matrix


_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "agent_handoff_expectations"


def _load_fixture(name: str) -> dict:
    with (_FIXTURE_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_valid_handoff_expectation_matrix_has_no_issues() -> None:
    matrix = _load_fixture("valid_matrix.json")

    assert validate_handoff_expectation_matrix(matrix) == []


def test_invalid_handoff_expectation_matrix_rejects_required_safety_failures() -> None:
    matrix = _load_fixture("invalid_matrix.json")

    issue_codes = {issue.code for issue in validate_handoff_expectation_matrix(matrix)}

    assert "uncited_expected_response" in issue_codes
    assert "outcome_guarantee" in issue_codes
    assert "private_value_or_path" in issue_codes
    assert "stale_source_marked_current" in issue_codes
    assert "blocked_action_downgrade" in issue_codes
    assert "missing_manual_handoff_expectation" in issue_codes
    assert "live_llm_execution_flag" in issue_codes
    assert "devhub_automation_claim" in issue_codes
    assert "enabled_consequential_control" in issue_codes
