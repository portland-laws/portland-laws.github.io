from __future__ import annotations

import json
from pathlib import Path

from ppd.guardrails.inactive_promotion_rehearsal_v7 import (
    assert_valid_inactive_guardrail_promotion_rehearsal_v7,
    validate_inactive_guardrail_promotion_rehearsal_v7,
)

_FIXTURES = Path(__file__).parent / "fixtures" / "inactive_promotion_rehearsal_v7"


def _load_fixture(name: str) -> dict[str, object]:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_inactive_promotion_rehearsal_v7_fixture_passes() -> None:
    payload = _load_fixture("valid_rehearsal.json")

    assert validate_inactive_guardrail_promotion_rehearsal_v7(payload) == []
    assert_valid_inactive_guardrail_promotion_rehearsal_v7(payload)


def test_missing_required_rehearsal_sections_are_rejected() -> None:
    payload = {
        "rehearsal_version": 7,
        "rehearsal_mode": "inactive",
    }

    issues = validate_inactive_guardrail_promotion_rehearsal_v7(payload)
    codes = {issue.code for issue in issues}

    assert "missing_release_decision_references" in codes
    assert "missing_reviewer_controlled_promotion_checklist_rows" in codes
    assert "missing_unresolved_hold_carry_forward_conditions" in codes
    assert "missing_pre_promotion_source_freshness_reminders" in codes
    assert "missing_agent_notification_placeholders" in codes
    assert "missing_rollback_checkpoint_references" in codes
    assert "missing_monitoring_watch_rows" in codes
    assert "missing_validation_commands" in codes


def test_rehearsal_rejects_live_claims_private_artifacts_and_active_flags() -> None:
    payload = _load_fixture("valid_rehearsal.json")
    payload.update(
        {
            "active": True,
            "mutation_enabled": True,
            "claims": [
                "Promoted to production after reviewer pass.",
                "Live crawl completed for all PP&D sources.",
                "Submitted permit and paid fees.",
                "Approval guaranteed for the applicant.",
            ],
            "auth_state": "committed-browser-state.json",
            "trace": "trace.zip",
        }
    )

    issues = validate_inactive_guardrail_promotion_rehearsal_v7(payload)
    codes = {issue.code for issue in issues}

    assert "active_mutation_flag" in codes
    assert "actual_activation_or_promotion_claim" in codes
    assert "live_crawl_execution_claim" in codes
    assert "official_action_completion_claim" in codes
    assert "legal_or_permitting_guarantee" in codes
    assert "private_session_or_auth_artifact" in codes


def test_required_rows_must_include_reviewer_visible_fields() -> None:
    payload = _load_fixture("valid_rehearsal.json")
    payload["release_decision_references"] = [{"decision_id": "release-decision-184"}]

    issues = validate_inactive_guardrail_promotion_rehearsal_v7(payload)
    codes = {issue.code for issue in issues}

    assert "missing_release_decision_references_evidence_ref" in codes
    assert "missing_release_decision_references_reviewer_role" in codes
