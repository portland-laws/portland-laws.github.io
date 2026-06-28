from __future__ import annotations

import copy
from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).parents[1] / "guardrails" / "activation_rehearsal.py"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrails" / "activation_rehearsal_packet.json"

spec = importlib.util.spec_from_file_location("activation_rehearsal", MODULE_PATH)
assert spec is not None and spec.loader is not None
activation_rehearsal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation_rehearsal)


def _packet() -> dict:
    return activation_rehearsal.load_packet(FIXTURE_PATH)


def _errors(packet: dict) -> list[str]:
    return activation_rehearsal.validate_packet(packet)


def test_activation_rehearsal_fixture_is_valid_and_disabled() -> None:
    packet = _packet()
    activation_rehearsal.assert_valid_packet(packet)
    assert packet["activation_status"] == "disabled_by_default"
    assert packet["mutates_active_bundles"] is False
    assert packet["consumes"]["consumption_mode"] == "fixture_only"


def test_activation_rehearsal_records_expected_predicate_diff() -> None:
    packet = _packet()
    draft = activation_rehearsal.predicate_names(packet, "draft")
    active = activation_rehearsal.predicate_names(packet, "active")
    assert sorted(draft - active) == packet["predicate_diff"]["recorded_changes"]["added"]
    assert sorted(active - draft) == packet["predicate_diff"]["recorded_changes"]["removed"]


def test_activation_rehearsal_refuses_consequential_actions() -> None:
    packet = _packet()
    refused = packet["refused_consequential_actions"]
    refused_names = {entry["action"] for entry in refused if entry["refused"] is True}
    refused_categories = {entry["action_category"] for entry in refused if entry["refused"] is True}
    assert "submit_devhub_application" in refused_names
    assert "activate_guardrail_bundle" in refused_names
    assert "upload_or_certify_documents" in refused_names
    assert {"payment", "upload", "submission", "scheduling", "cancellation", "certification"}.issubset(refused_categories)


def test_activation_rehearsal_has_confirmation_citations_and_rollback_notes() -> None:
    packet = _packet()
    assert all(gate["required"] is True and gate["exact_phrase"] for gate in packet["exact_confirmation_gates"])
    assert packet["citation_coverage"]["missing_citations"] == []
    assert packet["citation_coverage"]["required_citations"] == packet["citation_coverage"]["covered_citations"]
    assert packet["rollback_notes"]


def test_activation_rehearsal_rejects_uncited_predicate_diff() -> None:
    packet = _packet()
    packet["predicate_diff"]["diff_citations"]["refuses_consequential_devhub_actions"] = []
    assert "predicate diff is uncited: refuses_consequential_devhub_actions" in _errors(packet)


def test_activation_rehearsal_rejects_stale_or_missing_readiness_contract_links() -> None:
    stale = _packet()
    stale["consumes"]["readiness_contract_links"][0]["freshness_status"] = "stale"
    stale["consumes"]["readiness_contract_links"][0]["stale"] = True
    missing = _packet()
    missing["consumes"]["readiness_contract_links"] = []
    stale_errors = _errors(stale)
    assert "readiness contract link readiness-contract.agent-facing-v1 must be current" in stale_errors
    assert "readiness contract link readiness-contract.agent-facing-v1 is stale" in stale_errors
    assert "readiness_contract_links are required" in _errors(missing)


def test_activation_rehearsal_rejects_missing_refusal_rule_for_each_high_risk_action() -> None:
    packet = _packet()
    packet["refused_consequential_actions"] = [action for action in packet["refused_consequential_actions"] if action.get("action_category") != "payment"]
    assert "high-risk action payment is missing a refusal rule" in _errors(packet)


def test_activation_rehearsal_rejects_missing_exact_confirmation_gate_for_each_high_risk_action() -> None:
    packet = _packet()
    packet["exact_confirmation_gates"] = [gate for gate in packet["exact_confirmation_gates"] if gate.get("action_category") != "scheduling"]
    assert "high-risk action scheduling is missing an exact-confirmation gate" in _errors(packet)


def test_activation_rehearsal_rejects_private_case_facts() -> None:
    packet = _packet()
    packet["case_facts"] = [{"fact_id": "case.address", "privacy_classification": "private_case_fact", "value": "123 Private Street"}]
    errors = _errors(packet)
    assert "private case fact is not allowed: case_facts[0]" in errors
    assert "private case fact value is not allowed: case_facts[0].value" in errors


def test_activation_rehearsal_rejects_unresolved_review_items_marked_activated() -> None:
    packet = _packet()
    packet["review_items"] = [{"item_id": "review.open-payment-gate", "status": "open", "marked_activated": True}]
    assert "unresolved review item is marked activated: review.open-payment-gate" in _errors(packet)


def test_activation_rehearsal_rejects_active_bundle_mutation() -> None:
    packet = _packet()
    packet["mutates_active_bundles"] = True
    packet["active_bundle_changes"] = [{"field": "deterministic_predicates"}]
    errors = _errors(packet)
    assert "mutates_active_bundles must be false" in errors
    assert "activation rehearsal must not include active_bundle_changes" in errors


def test_activation_rehearsal_validation_does_not_mutate_input() -> None:
    packet = _packet()
    original = copy.deepcopy(packet)
    activation_rehearsal.validate_packet(packet)
    assert packet == original
