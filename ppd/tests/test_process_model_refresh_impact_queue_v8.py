from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.logic.process_model_refresh_impact_queue_v8 import (
    ProcessModelRefreshImpactQueueV8Error,
    assert_valid_process_model_refresh_impact_queue_v8,
    validate_process_model_refresh_impact_queue_v8,
)


_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "process_model_refresh_impact_queue_v8" / "valid_queue.json"


def _valid_record() -> dict:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def _codes(record: dict) -> set[str]:
    return {issue.code for issue in validate_process_model_refresh_impact_queue_v8(record)}


def test_valid_queue_fixture_passes() -> None:
    assert validate_process_model_refresh_impact_queue_v8(_valid_record()) == []


def test_rejects_missing_required_refresh_impact_sections() -> None:
    record = _valid_record()
    for field_name in (
        "requirement_node_candidate_set_refs",
        "process_model_refs",
        "affected_process_ids",
        "permit_type_impact_rows",
        "eligibility_impact_placeholders",
        "required_fact_impact_placeholders",
        "required_document_impact_placeholders",
        "file_rule_impact_placeholders",
        "fee_impact_placeholders",
        "deadline_impact_placeholders",
        "action_gate_impact_placeholders",
        "unsupported_path_carry_forward_rows",
        "guardrail_recompile_candidate_refs",
        "reviewer_hold_notes",
        "validation_commands",
    ):
        record[field_name] = []

    issues = validate_process_model_refresh_impact_queue_v8(record)

    assert len([issue for issue in issues if issue.code == "missing_required_field"]) == 15


def test_rejects_active_guardrail_activation_claims() -> None:
    record = _valid_record()
    record["notes"] = "Guardrails activated for live use."

    assert "active_guardrail_activation_claim" in _codes(record)


def test_rejects_live_crawl_execution_claims() -> None:
    record = _valid_record()
    record["crawl_status"] = "Live crawl executed against official pages."

    assert "live_crawl_execution_claim" in _codes(record)


def test_rejects_private_session_auth_artifacts() -> None:
    record = _valid_record()
    record["evidence"] = {"session_state": "committed-browser-state.json"}

    assert "private_session_auth_artifact" in _codes(record)


def test_rejects_official_action_completion_claims() -> None:
    record = _valid_record()
    record["completion"] = "Permit submitted through DevHub."

    assert "official_action_completion_claim" in _codes(record)


def test_rejects_legal_or_permitting_guarantees() -> None:
    record = _valid_record()
    record["assurance"] = "The permit is guaranteed approval."

    assert "legal_or_permitting_guarantee" in _codes(record)


def test_rejects_active_mutation_flags() -> None:
    record = _valid_record()
    record["runtime"] = {"writes_enabled": True, "mutation_mode": "active"}

    codes = _codes(record)

    assert "active_mutation_flag" in codes


def test_assert_valid_raises_structured_error() -> None:
    record = _valid_record()
    record["validation_commands"] = []

    with pytest.raises(ProcessModelRefreshImpactQueueV8Error) as exc_info:
        assert_valid_process_model_refresh_impact_queue_v8(record)

    assert exc_info.value.issues[0].code == "missing_required_field"
