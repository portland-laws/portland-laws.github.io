from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.process_model_impact_candidate_v5 import (
    ProcessModelImpactCandidateV5Error,
    assert_valid_process_model_impact_candidate_v5,
    validate_process_model_impact_candidate_v5,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "process_model_impact_candidate_v5"


def load_valid_candidate() -> dict[str, object]:
    with (FIXTURE_DIR / "valid_candidate.json").open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    assert isinstance(loaded, dict)
    return loaded


def error_codes(candidate: dict[str, object]) -> set[str]:
    report = validate_process_model_impact_candidate_v5(candidate)
    return {error.code for error in report.errors}


def test_valid_candidate_passes() -> None:
    candidate = load_valid_candidate()

    report = validate_process_model_impact_candidate_v5(candidate)

    assert report.ok is True
    assert report.errors == ()
    assert_valid_process_model_impact_candidate_v5(candidate)


@pytest.mark.parametrize(
    ("field_name", "expected_code"),
    [
        ("requirement_queue_refs", "missing_requirement_queue_refs"),
        ("inactive_process_model_delta_rows", "missing_inactive_process_model_delta_rows"),
        ("eligibility_deltas", "missing_eligibility_deltas"),
        ("fact_deltas", "missing_fact_deltas"),
        ("document_deltas", "missing_document_deltas"),
        ("file_rule_deltas", "missing_file_rule_deltas"),
        ("fee_caveats", "missing_fee_caveats"),
        ("deadline_caveats", "missing_deadline_caveats"),
        ("unsupported_path_handling", "missing_unsupported_path_handling"),
        ("devhub_reference_caveats", "missing_devhub_reference_caveats"),
        ("reviewer_holds", "missing_reviewer_holds"),
        ("rollback_notes", "missing_rollback_notes"),
        ("validation_commands", "missing_validation_commands"),
    ],
)
def test_required_candidate_sections_are_fail_closed(field_name: str, expected_code: str) -> None:
    candidate = load_valid_candidate()
    candidate.pop(field_name)

    assert expected_code in error_codes(candidate)


def test_rejects_active_process_model_delta_rows() -> None:
    candidate = load_valid_candidate()
    candidate["inactive_process_model_delta_rows"] = [
        {"process_id": "residential-alteration", "active": True, "operation": "mutate active model"}
    ]

    codes = error_codes(candidate)

    assert "delta_row_not_inactive" in codes
    assert "delta_row_mutates_active_model" in codes


@pytest.mark.parametrize(
    ("field_name", "field_value", "expected_code"),
    [
        ("active_model_mutation", True, "active_mutation_flag"),
        ("storage_state", "ppd/tests/fixtures/devhub.storageState.json", "private_session_or_auth_artifact"),
        ("result", "application submitted in DevHub", "official_action_completion_claim"),
        ("note", "permit will be approved", "legal_or_permitting_guarantee"),
        ("artifact", "local-run.har", "private_session_or_auth_artifact"),
    ],
)
def test_rejects_unsafe_claims_and_private_artifacts(
    field_name: str,
    field_value: object,
    expected_code: str,
) -> None:
    candidate = load_valid_candidate()
    candidate[field_name] = field_value

    assert expected_code in error_codes(candidate)


def test_assert_helper_raises_with_error_codes() -> None:
    candidate = load_valid_candidate()
    candidate.pop("rollback_notes")

    with pytest.raises(ProcessModelImpactCandidateV5Error) as excinfo:
        assert_valid_process_model_impact_candidate_v5(candidate)

    assert "missing_rollback_notes" in str(excinfo.value)


def test_nested_private_artifacts_are_rejected() -> None:
    candidate = load_valid_candidate()
    nested = copy.deepcopy(candidate)
    nested["devhub_reference_caveats"] = [
        {"surface_id": "devhub-upload", "trace_path": "private-authenticated-run.zip"}
    ]

    assert "private_session_or_auth_artifact" in error_codes(nested)


def test_validation_commands_must_be_argv_lists() -> None:
    candidate = load_valid_candidate()
    candidate["validation_commands"] = ["python3 ppd/daemon/ppd_daemon.py --self-test"]

    assert "invalid_validation_command" in error_codes(candidate)
