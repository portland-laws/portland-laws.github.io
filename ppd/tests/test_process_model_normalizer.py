from pathlib import Path

import pytest

from ppd.logic.process_model_normalizer import (
    ProcessModelNormalizationError,
    compile_process_model_from_fixture,
    normalize_process_model,
)


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "process_model"
    / "minimal_trade_permit_requirements.json"
)


def test_compile_process_model_from_committed_fixture() -> None:
    compiled = compile_process_model_from_fixture(FIXTURE)

    model = compiled["process_model"]
    guardrails = compiled["guardrail_bundle"]

    assert model["process_id"] == "standard-trade-permit-minimal-fixture"
    assert model["permit_type"] == "standard trade permit"
    assert model["guardrail_bundle_id"] == guardrails["guardrail_bundle_id"]
    assert model["source_evidence_ids"] == guardrails["source_evidence_ids"]
    assert "account setup or manual login" in model["stages"]
    assert "submission" in model["stages"]

    fact_keys = {fact["fact_key"] for fact in model["required_user_facts"]}
    assert "has_devhub_account" in fact_keys
    assert "contractor_license_context" in fact_keys

    unsupported_paths = {path["path"] for path in model["unsupported_paths"]}
    assert "standard purchase when plan review is required" in unsupported_paths

    exact_actions = {predicate["action"] for predicate in guardrails["exact_confirmation_predicates"]}
    refused_actions = {predicate["action"] for predicate in guardrails["refused_action_predicates"]}
    reversible_actions = {predicate["action"] for predicate in guardrails["reversible_action_predicates"]}

    assert "submit or purchase" in exact_actions
    assert "enter payment details or submit payment" in refused_actions
    assert "draft" in reversible_actions


def test_normalizer_rejects_uncommitted_evidence_ids() -> None:
    payload = {
        "process_id": "bad-fixture",
        "permit_type": "standard trade permit",
        "scope": "invalid evidence test",
        "source_evidence": [
            {
                "evidence_id": "ppd-source:committed",
                "source_id": "fixture",
                "canonical_url": "https://www.portland.gov/ppd",
            }
        ],
        "requirements": [
            {
                "requirement_id": "req-bad-evidence",
                "source_evidence_ids": ["ppd-source:not-committed"],
                "requirement_type": "precondition",
                "subject": "agent",
                "action": "check",
                "object": "fixture evidence",
                "conditions": {},
                "process_stage": "eligibility screening",
            }
        ],
    }

    with pytest.raises(ProcessModelNormalizationError, match="uncommitted evidence id"):
        normalize_process_model(payload)


def test_normalizer_is_deterministic() -> None:
    first = compile_process_model_from_fixture(FIXTURE)
    second = compile_process_model_from_fixture(FIXTURE)

    assert first == second
