from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ppd.logic.inactive_guardrail_promotion_candidate_v5 import (
    assert_valid_inactive_guardrail_promotion_candidate_v5,
    validate_inactive_guardrail_promotion_candidate_v5,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "inactive_guardrail_promotion_candidate_v5"


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def issue_codes(candidate: dict[str, Any]) -> set[str]:
    return {issue.code for issue in validate_inactive_guardrail_promotion_candidate_v5(candidate)}


def test_valid_inactive_candidate_fixture_is_accepted() -> None:
    candidate = load_fixture("valid_inactive_candidate.json")

    assert validate_inactive_guardrail_promotion_candidate_v5(candidate) == []
    assert_valid_inactive_guardrail_promotion_candidate_v5(candidate)


@pytest.mark.parametrize(
    ("field", "expected_code"),
    [
        ("readiness_replay_refs", "missing_readiness_replay_references"),
        ("inactive_promotion_rows", "missing_inactive_promotion_rows"),
        ("activation_prerequisites", "missing_activation_prerequisites"),
        ("unresolved_hold_inventory", "missing_unresolved_hold_inventory"),
        ("reviewer_signoff_placeholders", "missing_reviewer_signoff_placeholders"),
        ("source_freshness_clearance_criteria", "missing_source_freshness_clearance_criteria"),
        ("rollback_checkpoint_rows", "missing_rollback_checkpoint_rows"),
        ("post_promotion_smoke_checks", "missing_post_promotion_smoke_checks"),
        ("agent_notification_notes", "missing_agent_notification_notes"),
        ("validation_commands", "missing_validation_commands"),
    ],
)
def test_rejects_missing_required_inventory_sections(field: str, expected_code: str) -> None:
    candidate = load_fixture("valid_inactive_candidate.json")
    candidate.pop(field)

    assert expected_code in issue_codes(candidate)


def test_rejects_active_activation_claims() -> None:
    candidate = load_fixture("valid_inactive_candidate.json")
    candidate["activation_state"] = "active"
    candidate["inactive_promotion_rows"][0]["state"] = "active"

    assert "active_activation_claim" in issue_codes(candidate)


def test_rejects_private_session_and_auth_artifacts() -> None:
    candidate = load_fixture("valid_inactive_candidate.json")
    candidate["private_artifacts"] = ["/tmp/devhub-storage-state.json"]
    candidate["operator_context"] = {"cookies": [{"name": "session"}]}

    assert "private_session_auth_artifact" in issue_codes(candidate)


def test_rejects_official_action_completion_claims() -> None:
    candidate = load_fixture("valid_inactive_candidate.json")
    candidate["official_submission_complete"] = True
    candidate["reviewer_signoff_placeholders"][0]["approved"] = True

    assert "official_action_completion_claim" in issue_codes(candidate)


def test_rejects_legal_or_permitting_guarantees() -> None:
    candidate = load_fixture("valid_inactive_candidate.json")
    candidate["legal_guarantee"] = "Permit approval is guaranteed."

    assert "legal_or_permitting_guarantee" in issue_codes(candidate)


def test_rejects_active_mutation_flags() -> None:
    candidate = load_fixture("valid_inactive_candidate.json")
    candidate["runtime_controls"] = {"writes_enabled": True}

    assert "active_mutation_flag" in issue_codes(candidate)


def test_assertion_raises_stable_rejection_summary() -> None:
    candidate = load_fixture("valid_inactive_candidate.json")
    candidate["validation_commands"] = []

    with pytest.raises(ValueError, match="missing_validation_commands"):
        assert_valid_inactive_guardrail_promotion_candidate_v5(candidate)
