from pathlib import Path

from ppd.guardrails.inactive_promotion_rehearsal_v6 import (
    forbidden_rule_ids,
    required_rule_ids,
    validate_inactive_promotion_rehearsal_v6,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "inactive_promotion_rehearsal_v6"


def test_valid_inactive_promotion_rehearsal_v6_passes() -> None:
    text = (FIXTURE_DIR / "valid_rehearsal.md").read_text(encoding="utf-8")

    result = validate_inactive_promotion_rehearsal_v6(text)

    assert result.is_valid
    assert result.missing_required == ()
    assert result.forbidden_claims == ()


def test_invalid_inactive_promotion_rehearsal_v6_reports_missing_and_forbidden_content() -> None:
    text = (FIXTURE_DIR / "invalid_rehearsal.md").read_text(encoding="utf-8")

    result = validate_inactive_promotion_rehearsal_v6(text)

    assert not result.is_valid
    assert "release_readiness_references" in result.missing_required
    assert "active_mutation_flags" in result.forbidden_claims


def test_inactive_promotion_rehearsal_v6_rule_ids_cover_task_requirements() -> None:
    assert set(required_rule_ids()) == {
        "release_readiness_references",
        "inactive_promotion_candidate_rows",
        "reviewer_controlled_signoff_placeholders",
        "source_freshness_clearance_prerequisites",
        "unresolved_hold_propagation",
        "rollback_checkpoint_rows",
        "post_promotion_smoke_replay_expectations",
        "agent_api_compatibility_reminders",
        "monitoring_handoff_rows",
        "validation_commands",
    }
    assert set(forbidden_rule_ids()) == {
        "active_activation_claims",
        "private_session_or_auth_artifacts",
        "official_action_completion_claims",
        "legal_or_permitting_guarantees",
        "active_mutation_flags",
    }
