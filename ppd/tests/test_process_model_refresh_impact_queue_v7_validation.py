from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.process_model_refresh_impact_queue_v7_validation import (
    reject_process_model_refresh_impact_queue_v7,
    validate_process_model_refresh_impact_queue_v7,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "process_model_refresh_impact_queue_v7"


def _load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_valid_queue_fixture_is_accepted() -> None:
    payload = _load_fixture("valid_queue.json")

    issues = validate_process_model_refresh_impact_queue_v7(payload)

    assert issues == []
    reject_process_model_refresh_impact_queue_v7(payload)


def test_missing_required_refresh_impact_fields_are_rejected() -> None:
    payload = _load_fixture("valid_queue.json")
    for field in (
        "requirement_node_candidate_set_refs",
        "affected_process_model_rows",
        "eligibility_impact_placeholders",
        "document_impact_placeholders",
        "fee_impact_placeholders",
        "deadline_impact_placeholders",
        "stage_impact_placeholders",
        "unsupported_path_carry_forward_notes",
        "guardrail_bundle_recompile_suggestions",
        "stale_evidence_holds",
        "reviewer_signoff_placeholders",
        "validation_commands",
    ):
        mutated = dict(payload)
        mutated[field] = []

        issues = validate_process_model_refresh_impact_queue_v7(mutated)

        assert any(issue.path == field for issue in issues)


def test_missing_candidate_set_ref_details_are_rejected() -> None:
    payload = _load_fixture("valid_queue.json")
    payload["requirement_node_candidate_set_refs"] = [{"candidate_set_id": ""}]

    issues = validate_process_model_refresh_impact_queue_v7(payload)

    assert {issue.code for issue in issues} >= {"missing_requirement_candidate_ids"}


def test_missing_affected_process_model_row_details_are_rejected() -> None:
    payload = _load_fixture("valid_queue.json")
    payload["affected_process_model_rows"] = [{"process_id": "pm-building-alteration"}]

    issues = validate_process_model_refresh_impact_queue_v7(payload)

    assert {issue.path for issue in issues} >= {
        "affected_process_model_rows[0].permit_type",
        "affected_process_model_rows[0].guardrail_bundle_id",
    }


def test_unsafe_claims_and_artifacts_are_rejected() -> None:
    payload = _load_fixture("invalid_unsafe_claims.json")

    issues = validate_process_model_refresh_impact_queue_v7(payload)
    codes = {issue.code for issue in issues}

    assert "active_mutation_claim" in codes
    assert "live_crawl_execution_claim" in codes
    assert "raw_or_downloaded_artifact" in codes
    assert "private_or_auth_artifact" in codes
    assert "official_action_completion_claim" in codes
    assert "legal_or_permitting_guarantee" in codes


def test_reject_helper_raises_for_invalid_payload() -> None:
    payload = _load_fixture("invalid_unsafe_claims.json")

    try:
        reject_process_model_refresh_impact_queue_v7(payload)
    except ValueError as exc:
        assert "process model refresh impact queue v7 is invalid" in str(exc)
    else:
        raise AssertionError("invalid queue payload was accepted")
