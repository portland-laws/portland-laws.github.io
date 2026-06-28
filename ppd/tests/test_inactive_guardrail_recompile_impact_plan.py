from __future__ import annotations

import pytest

from ppd.logic.inactive_guardrail_recompile_impact_plan import (
    REQUIRED_NON_EMPTY_SECTIONS,
    InactiveGuardrailRecompileImpactPlanError,
    assert_valid_inactive_guardrail_recompile_impact_plan_v1,
    validate_inactive_guardrail_recompile_impact_plan_v1,
)


def valid_plan() -> dict[str, object]:
    return {
        "version": "inactive_guardrail_recompile_impact_plan_v1",
        "status": "inactive",
        "process_model_delta_refs": ["delta:fixture-process-model:2026-06-01"],
        "inactive_guardrail_patch_placeholders": ["patch-placeholder:guardrail-bundle:building-permit"],
        "deterministic_predicate_impacts": ["predicate impact is reviewed before activation"],
        "deontic_rule_impacts": ["obligation and prohibition impacts are held for review"],
        "temporal_rule_impacts": ["deadline impact is represented without claiming current law"],
        "reversible_action_predicate_impacts": ["draft-only action predicate remains reversible"],
        "exact_confirmation_predicate_impacts": ["exact confirmation remains required"],
        "refused_action_predicate_impacts": ["submission refusal remains enforced"],
        "agent_facing_explanation_impacts": ["explanation text is updated after reviewer approval"],
        "reviewer_holds": ["human reviewer must clear the inactive patch"],
        "rollback_notes": ["remove inactive placeholder and restore prior bundle reference"],
        "validation_commands": [["python3", "-m", "pytest", "ppd/tests/test_inactive_guardrail_recompile_impact_plan.py"]],
    }


def rendered_errors(plan: dict[str, object]) -> list[str]:
    return [finding.render() for finding in validate_inactive_guardrail_recompile_impact_plan_v1(plan)]


def test_valid_inactive_plan_passes() -> None:
    assert rendered_errors(valid_plan()) == []
    assert_valid_inactive_guardrail_recompile_impact_plan_v1(valid_plan())


@pytest.mark.parametrize("section", REQUIRED_NON_EMPTY_SECTIONS)
def test_rejects_missing_required_impact_sections(section: str) -> None:
    plan = valid_plan()
    plan.pop(section)

    errors = rendered_errors(plan)

    assert any(section in error and "non-empty" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("private_artifact_ref", "s3://private/session.json", "private_artifact"),
        ("raw_crawl_output", "stored raw crawl body", "raw_crawl"),
        ("downloaded_artifact_path", "downloads/form.pdf", "downloaded_artifact"),
        ("note", "live crawl verified this change", "live crawl"),
        ("note", "scraped DevHub and confirmed the result", "scraped devhub"),
        ("note", "promote to production after this patch", "promote to production"),
        ("note", "official action complete after submission", "official action complete"),
        ("note", "this is a guaranteed permit outcome", "guaranteed permit"),
        ("note", "this is a legal guarantee", "legal guarantee"),
        ("active_mutation_enabled", True, "active mutation"),
        ("promotion_enabled", "true", "active mutation"),
    ],
)
def test_rejects_forbidden_artifacts_claims_and_mutation_flags(
    field: str,
    value: object,
    expected: str,
) -> None:
    plan = valid_plan()
    plan[field] = value

    errors = rendered_errors(plan)

    assert any(expected in error for error in errors)


def test_assert_valid_raises_stable_error() -> None:
    plan = valid_plan()
    plan["status"] = "active"
    plan["enabled"] = True

    with pytest.raises(InactiveGuardrailRecompileImpactPlanError) as exc_info:
        assert_valid_inactive_guardrail_recompile_impact_plan_v1(plan)

    message = str(exc_info.value)
    assert "status" in message
    assert "enabled" in message
