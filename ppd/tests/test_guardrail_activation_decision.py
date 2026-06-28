from __future__ import annotations

import copy
from pathlib import Path
import importlib.util


MODULE_PATH = Path(__file__).parents[1] / "guardrails" / "activation_decision.py"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrails" / "activation_decision_packet.json"

spec = importlib.util.spec_from_file_location("activation_decision", MODULE_PATH)
assert spec is not None and spec.loader is not None
activation_decision = importlib.util.module_from_spec(spec)
spec.loader.exec_module(activation_decision)


def _packet() -> dict:
    return activation_decision.load_packet(FIXTURE_PATH)


def _errors(packet: dict) -> list[str]:
    return activation_decision.validate_packet(packet)


def test_activation_decision_fixture_is_valid_and_disabled() -> None:
    packet = _packet()
    activation_decision.assert_valid_packet(packet)

    assert packet["fixture_first"] is True
    assert packet["metadata_only"] is True
    assert packet["mutates_active_guardrail_bundles"] is False
    assert packet["live_enforcement_enabled"] is False
    assert packet["disabled_live_enforcement"]["enabled"] is False


def test_activation_decision_consumes_rehearsal_and_release_gate_packets() -> None:
    packet = _packet()
    consumed_roles = {record["packet_role"] for record in packet["consumes"]}

    assert consumed_roles == {"guardrail_activation_rehearsal", "release_gate_status"}
    assert all(record["freshness_status"] == "current" for record in packet["consumes"])
    assert all(record["stale"] is False for record in packet["consumes"])


def test_activation_decision_records_reviewer_defer_decisions_by_predicate_bundle() -> None:
    packet = _packet()
    selected = activation_decision.selected_decisions(packet)

    assert selected == {
        "predicate-bundle.ppd-devhub-consequential-actions.v1": "defer",
        "predicate-bundle.ppd-exact-confirmation-gates.v1": "defer",
    }
    assert all(record["applies_to_active_bundle"] is False for record in packet["reviewer_decisions"])
    assert all(record["mutates_active_bundle"] is False for record in packet["reviewer_decisions"])


def test_activation_decision_records_exact_confirmation_and_refusal_coverage() -> None:
    packet = _packet()
    expected = {"payment", "upload", "submission", "scheduling", "cancellation", "certification"}

    exact = packet["exact_confirmation_coverage"]
    refused = packet["refused_consequential_action_coverage"]

    assert exact["all_required_categories_covered"] is True
    assert refused["all_required_categories_refused"] is True
    assert expected.issubset(set(exact["covered_action_categories"]))
    assert expected.issubset(set(refused["refused_action_categories"]))
    assert exact["missing_categories"] == []
    assert refused["missing_categories"] == []


def test_activation_decision_records_rollback_notes_without_active_bundle_changes() -> None:
    packet = _packet()

    assert packet["rollback_notes"]
    assert packet.get("active_bundle_changes") is None
    assert packet.get("active_bundle_replacement") is None
    assert packet.get("active_guardrail_bundle") is None


def test_activation_decision_rejects_missing_rehearsal_link() -> None:
    packet = _packet()
    packet["consumes"] = [record for record in packet["consumes"] if record["packet_role"] != "guardrail_activation_rehearsal"]

    assert "consumes must include guardrail_activation_rehearsal" in _errors(packet)


def test_activation_decision_rejects_stale_rehearsal_link() -> None:
    packet = _packet()
    packet["consumes"][0]["freshness_status"] = "stale"
    packet["consumes"][0]["stale"] = True

    errors = _errors(packet)

    assert "consumes[0].freshness_status must be current" in errors
    assert "consumes[0] must not be stale" in errors


def test_activation_decision_rejects_uncited_activation_decision_evidence() -> None:
    packet = _packet()
    packet["reviewer_decisions"][0]["selected_decision"] = "activate"
    packet["reviewer_decisions"][0]["source_evidence_ids"] = ["ev-not-linked-from-consumed-packets"]

    assert "reviewer_decisions[0].source_evidence_ids references uncited evidence ev-not-linked-from-consumed-packets" in _errors(packet)


def test_activation_decision_rejects_missing_exact_confirmation_category() -> None:
    packet = _packet()
    packet["exact_confirmation_coverage"]["covered_action_categories"] = ["payment", "upload", "submission", "scheduling", "cancellation"]

    assert "exact confirmation coverage missing certification" in _errors(packet)


def test_activation_decision_rejects_missing_exact_confirmation_gate() -> None:
    packet = _packet()
    packet["exact_confirmation_coverage"]["source_gate_ids"] = [
        "payment_confirmation",
        "upload_confirmation",
        "submission_confirmation",
        "scheduling_confirmation",
        "cancellation_confirmation",
    ]

    assert "exact confirmation gate missing certification_confirmation" in _errors(packet)


def test_activation_decision_rejects_missing_refusal_coverage_action() -> None:
    packet = _packet()
    packet["refused_consequential_action_coverage"]["source_refusal_actions"] = [
        "enter_or_submit_payment",
        "upload_or_certify_documents",
        "submit_devhub_application",
        "schedule_inspection",
        "cancel_or_withdraw",
    ]

    assert "refusal coverage missing certify_acknowledgement" in _errors(packet)


def test_activation_decision_rejects_private_case_facts() -> None:
    packet = _packet()
    packet["private_case_facts"] = {"site_address": "123 private test address"}

    assert "packet.private_case_facts uses forbidden private or live artifact field" in _errors(packet)


def test_activation_decision_rejects_unresolved_blockers_marked_activated() -> None:
    packet = _packet()
    packet["decision_status"] = "activated"

    assert "release_gate_blockers_acknowledged[0] is unresolved and cannot be marked activated" in _errors(packet)


def test_activation_decision_rejects_active_bundle_mutation() -> None:
    packet = _packet()
    packet["mutates_active_guardrail_bundles"] = True
    packet["active_bundle_changes"] = [{"field": "deterministic_predicates"}]

    errors = _errors(packet)

    assert "mutates_active_guardrail_bundles must be false" in errors
    assert "activation decision packet must not include active_bundle_changes" in errors


def test_activation_decision_rejects_nested_active_bundle_mutation_flags() -> None:
    packet = _packet()
    packet["audit"]["active_guardrail_bundle_mutated"] = True

    assert "packet.audit.active_guardrail_bundle_mutated must be false" in _errors(packet)


def test_activation_decision_validation_does_not_mutate_input() -> None:
    packet = _packet()
    original = copy.deepcopy(packet)

    activation_decision.validate_packet(packet)

    assert packet == original
