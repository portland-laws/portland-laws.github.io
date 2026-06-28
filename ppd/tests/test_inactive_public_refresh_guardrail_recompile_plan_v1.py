from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.inactive_public_refresh_guardrail_recompile_plan_v1 import (
    reject_reasons,
    validate_inactive_public_refresh_guardrail_recompile_plan_v1,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "guardrails"
    / "inactive_public_refresh_guardrail_recompile_plan_v1.json"
)


def _fixtures() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_valid_inactive_public_refresh_recompile_plan_is_accepted() -> None:
    plan = _fixtures()["valid_plan"]

    result = validate_inactive_public_refresh_guardrail_recompile_plan_v1(plan)

    assert result.accepted is True
    assert result.issues == ()


def test_rejects_missing_required_recompile_references_and_impacts() -> None:
    plan = _fixtures()["invalid_plan"]

    codes = set(reject_reasons(plan))

    assert "missing_process_model_delta_refs" in codes
    assert "missing_requirement_reextraction_queue_refs" in codes
    assert "missing_deterministic_predicate_placeholder_changes" in codes
    assert "missing_reversible_action_predicate_impacts" in codes
    assert "missing_exact_confirmation_predicate_impacts" in codes
    assert "missing_refused_action_predicate_impacts" in codes
    assert "missing_explanation_template_refresh_notes" in codes
    assert "missing_validation_status_holds" in codes
    assert "missing_rollback_notes" in codes
    assert "missing_validation_commands" in codes


def test_rejects_active_candidate_and_forbidden_claims() -> None:
    plan = _fixtures()["invalid_plan"]

    codes = set(reject_reasons(plan))

    assert "missing_inactive_guardrailbundle_recompile_candidate" in codes
    assert "live_crawl_claim" in codes
    assert "devhub_claim" in codes
    assert "official_action_completion_claim" in codes
    assert "private_artifact_claim" in codes
    assert "raw_artifact_claim" in codes
    assert "downloaded_artifact_claim" in codes
    assert "legal_or_permitting_guarantee" in codes


def test_rejects_active_mutation_flags() -> None:
    plan = _fixtures()["invalid_plan"]

    codes = reject_reasons(plan)

    assert codes.count("active_mutation_flag") == 2
