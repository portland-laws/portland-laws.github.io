from __future__ import annotations

import json
from pathlib import Path

from ppd.guardrails.recompile_candidate_v5 import validate_guardrail_bundle_recompile_candidate_v5

FIXTURES = Path(__file__).parent / "fixtures" / "guardrail_bundle_recompile_candidate_v5"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_valid_candidate_v5_passes() -> None:
    assert validate_guardrail_bundle_recompile_candidate_v5(_load("valid.json")) == []


def test_missing_required_sections_are_rejected() -> None:
    errors = validate_guardrail_bundle_recompile_candidate_v5(_load("missing_required.json"))
    assert "missing_process_model_impact_references" in errors
    assert "missing_inactive_guardrail_bundle_delta_rows" in errors
    assert "missing_deterministic_predicate_deltas" in errors
    assert "missing_deontic_predicate_deltas" in errors
    assert "missing_temporal_rule_deltas" in errors
    assert "missing_reversible_action_handling" in errors
    assert "missing_exact_confirmation_gates" in errors
    assert "missing_refused_consequential_action_gates" in errors
    assert "missing_refused_financial_action_gates" in errors
    assert "missing_stale_evidence_blocks" in errors
    assert "missing_explanation_templates" in errors
    assert "missing_reviewer_holds" in errors
    assert "missing_rollback_notes" in errors
    assert "missing_validation_commands" in errors


def test_prohibited_claims_and_artifacts_are_rejected() -> None:
    errors = validate_guardrail_bundle_recompile_candidate_v5(_load("prohibited_claims.json"))
    assert "active_guardrail_mutation_claims" in errors
    assert "private_session_or_auth_artifacts" in errors
    assert "official_action_completion_claims" in errors
    assert "legal_or_permitting_guarantees" in errors
    assert "active_mutation_flags" in errors
