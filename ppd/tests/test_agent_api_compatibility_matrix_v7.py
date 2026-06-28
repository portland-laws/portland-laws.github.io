from __future__ import annotations

import pytest

from ppd.logic.agent_api_compatibility_matrix_v7 import (
    assert_agent_api_compatibility_matrix_v7,
    validate_agent_api_compatibility_matrix_v7,
)


def valid_matrix() -> dict[str, object]:
    return {
        "version": "v7",
        "smoke_replay_ref": "ppd/tests/fixtures/agent_api/v7/smoke_replay.json",
        "release_decision_ref": "ppd/tests/fixtures/agent_api/v7/release_decision.json",
        "supported_query_rows": [
            {
                "query": "explain required documents",
                "expected_boundary": "cite sources and ask for missing facts before drafting",
            }
        ],
        "blocked_action_classes": [
            "submit_permit_request",
            "certify_acknowledgement",
            "upload_to_official_record",
            "pay_fee",
            "schedule_inspection",
            "cancel_or_reactivate_record",
        ],
        "citation_explanation_behavior": {
            "requires_citations": True,
            "explains_uncited_limits": True,
        },
        "stale_evidence_hold_behavior": {
            "hold_on_stale_source": True,
            "requires_freshness_review": True,
        },
        "missing_information_prompts": [
            "Ask for permit type, site address, owner or contractor role, and stale documents before proposing next actions."
        ],
        "reversible_draft_boundaries": [
            "Draft fields only before certification, upload, payment, scheduling, cancellation, or submission."
        ],
        "local_pdf_preview_boundaries": [
            "Preview local field mappings without committing private paths or uploading documents."
        ],
        "exact_confirmation_checkpoints": [
            "Require action-specific confirmation before any consequential official action."
        ],
        "manual_handoff_surfaces": [
            "DevHub login, MFA, CAPTCHA, certification, payment, upload, submit, schedule, and cancel."
        ],
        "rollback_visibility": [
            "Show draft reset and staged-value review surfaces before handoff."
        ],
        "validation_commands": [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]],
        "claims": [
            "Matrix is validation evidence only and does not activate, promote, crawl live sources, mutate records, complete official actions, or guarantee legal or permitting outcomes."
        ],
        "active_mutation_enabled": False,
        "live_crawl_executed": False,
        "stores_auth_state": False,
        "official_action_completed": False,
    }


def finding_codes(matrix: dict[str, object]) -> set[str]:
    return {finding.code for finding in validate_agent_api_compatibility_matrix_v7(matrix)}


def test_matrix_v7_accepts_complete_safe_release_evidence() -> None:
    assert validate_agent_api_compatibility_matrix_v7(valid_matrix()) == []
    assert_agent_api_compatibility_matrix_v7(valid_matrix())


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("smoke_replay_ref", "missing_smoke_replay_ref"),
        ("release_decision_ref", "missing_release_decision_ref"),
        ("supported_query_rows", "missing_supported_query_rows"),
        ("blocked_action_classes", "missing_blocked_action_classes"),
        ("citation_explanation_behavior", "missing_citation_explanation_behavior"),
        ("stale_evidence_hold_behavior", "missing_stale_evidence_hold_behavior"),
        ("missing_information_prompts", "missing_missing_information_prompts"),
        ("reversible_draft_boundaries", "missing_reversible_draft_boundaries"),
        ("local_pdf_preview_boundaries", "missing_local_pdf_preview_boundaries"),
        ("exact_confirmation_checkpoints", "missing_exact_confirmation_checkpoints"),
        ("manual_handoff_surfaces", "missing_manual_handoff_surfaces"),
        ("rollback_visibility", "missing_rollback_visibility"),
        ("validation_commands", "missing_validation_commands"),
    ],
)
def test_matrix_v7_rejects_missing_required_evidence(field: str, code: str) -> None:
    matrix = valid_matrix()
    matrix.pop(field)

    assert code in finding_codes(matrix)


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("claims", ["Activation complete for the promoted production release."], "actual_activation_or_promotion_claim"),
        ("claims", ["Live crawl executed successfully against DevHub."], "live_crawl_execution_claim"),
        ("claims", ["Committed cookies and auth state for replay."], "private_session_or_auth_artifact_claim"),
        ("claims", ["Submitted permit and payment complete."], "official_action_completion_claim"),
        ("claims", ["Permit guaranteed and compliance guaranteed."], "legal_or_permitting_guarantee"),
        ("active_mutation_enabled", True, "active_mutation_flags"),
        ("live_crawl_executed", True, "live_crawl_execution_claim"),
        ("stores_auth_state", True, "private_session_or_auth_artifact_claim"),
        ("official_action_completed", True, "official_action_completion_claim"),
        ("guarantees_approval", True, "legal_or_permitting_guarantee"),
    ],
)
def test_matrix_v7_rejects_prohibited_claims_and_flags(field: str, value: object, code: str) -> None:
    matrix = valid_matrix()
    matrix[field] = value

    assert code in finding_codes(matrix)


def test_matrix_v7_assertion_reports_failures() -> None:
    matrix = valid_matrix()
    matrix.pop("supported_query_rows")
    matrix["can_submit"] = True

    with pytest.raises(ValueError) as error:
        assert_agent_api_compatibility_matrix_v7(matrix)

    message = str(error.value)
    assert "missing_supported_query_rows" in message
    assert "active_mutation_flags" in message
