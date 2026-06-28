from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.agent_rehearsal_regression_matrix import (
    REQUIRED_SCENARIOS,
    RehearsalMatrixError,
    assert_valid_agent_rehearsal_regression_matrix,
    validate_agent_rehearsal_regression_matrix,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "agent_rehearsal_regression_matrix"
    / "regenerated_requirement_guardrail_rehearsal.json"
)


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_rehearsal_matrix_covers_required_fixture_first_scenarios() -> None:
    matrix = _load_fixture()

    issues = validate_agent_rehearsal_regression_matrix(matrix)

    assert issues == []
    assert {case["scenario"] for case in matrix["cases"]} == REQUIRED_SCENARIOS
    assert_valid_agent_rehearsal_regression_matrix(matrix)


def test_rehearsal_matrix_keeps_all_cases_off_llm_devhub_and_private_files() -> None:
    matrix = _load_fixture()

    assert matrix["execution_boundaries"]["calls_llm"] is False
    assert matrix["execution_boundaries"]["launches_devhub"] is False
    assert matrix["execution_boundaries"]["reads_private_files"] is False
    assert matrix["execution_boundaries"]["uses_authenticated_session"] is False

    for case in matrix["cases"]:
        boundaries = case["execution_boundaries"]
        assert boundaries["calls_llm"] is False
        assert boundaries["launches_devhub"] is False
        assert boundaries["reads_private_files"] is False
        assert boundaries["uses_authenticated_session"] is False


def test_rehearsal_matrix_rejects_missing_required_scenario() -> None:
    matrix = _load_fixture()
    matrix["cases"] = [case for case in matrix["cases"] if case["scenario"] != "changed_file_rules"]

    issues = validate_agent_rehearsal_regression_matrix(matrix)

    assert any(issue.code == "missing_required_scenario" for issue in issues)
    with pytest.raises(RehearsalMatrixError):
        assert_valid_agent_rehearsal_regression_matrix(matrix)


def test_rehearsal_matrix_rejects_live_devhub_llm_and_private_path_inputs() -> None:
    matrix = _load_fixture()
    matrix["launch_devhub"] = True
    assert any(issue.code == "live_execution_requested" for issue in validate_agent_rehearsal_regression_matrix(matrix))

    matrix = _load_fixture()
    matrix["cases"][0]["calls_llm"] = True
    assert any(issue.code == "live_execution_requested" for issue in validate_agent_rehearsal_regression_matrix(matrix))

    matrix = _load_fixture()
    matrix["cases"][0]["private_path"] = "/home/example/private/devhub/session.json"
    assert any(issue.code == "private_field_present" for issue in validate_agent_rehearsal_regression_matrix(matrix))


def test_rehearsal_matrix_rejects_consequential_action_downgrade() -> None:
    matrix = _load_fixture()
    refused_case = next(case for case in matrix["cases"] if case["scenario"] == "refused_consequential_action")
    refused_case["expected_agent_response"]["response_kind"] = "local-preview"

    issues = validate_agent_rehearsal_regression_matrix(matrix)

    assert any(issue.code == "wrong_refusal_response" for issue in issues)


def test_rehearsal_matrix_rejects_reversible_preview_without_reversibility() -> None:
    matrix = _load_fixture()
    preview_case = next(case for case in matrix["cases"] if case["scenario"] == "reversible_local_preview")
    preview_case["local_preview"]["reversible"] = False

    issues = validate_agent_rehearsal_regression_matrix(matrix)

    assert any(issue.code == "missing_reversible_preview" for issue in issues)


def test_rehearsal_matrix_rejects_missing_manual_handoff_confirmation_gates() -> None:
    matrix = copy.deepcopy(_load_fixture())
    handoff_case = next(case for case in matrix["cases"] if case["scenario"] == "manual_handoff")
    handoff_case["manual_handoff"]["requires_attendance"] = False
    handoff_case["manual_handoff"]["requires_exact_confirmation"] = False

    issues = validate_agent_rehearsal_regression_matrix(matrix)

    assert any(issue.code == "missing_manual_handoff_gate" for issue in issues)
