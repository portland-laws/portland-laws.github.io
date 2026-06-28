from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.logic.guardrail_recompilation_rehearsal import (
    build_guardrail_recompilation_rehearsal,
    finding_codes,
    require_valid_guardrail_recompilation_rehearsal,
    validate_guardrail_recompilation_rehearsal,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "guardrail_recompilation_rehearsal" / "process_model_impact_candidate.json"


def _load_fixture() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _build_packet() -> dict:
    return build_guardrail_recompilation_rehearsal(
        _load_fixture(),
        active_guardrail_bundle_id="guardrail-bundle-single-pdf-active",
        active_guardrail_bundle_revision="active-2026-05-20",
    )


def test_builds_deterministic_disabled_rehearsal_without_mutating_input() -> None:
    fixture = _load_fixture()
    original = copy.deepcopy(fixture)

    first = build_guardrail_recompilation_rehearsal(
        fixture,
        active_guardrail_bundle_id="guardrail-bundle-single-pdf-active",
        active_guardrail_bundle_revision="active-2026-05-20",
    )
    second = build_guardrail_recompilation_rehearsal(
        fixture,
        active_guardrail_bundle_id="guardrail-bundle-single-pdf-active",
        active_guardrail_bundle_revision="active-2026-05-20",
    )

    assert first == second
    assert fixture == original
    assert first["packet_type"] == "guardrail_recompilation_rehearsal"
    assert first["rehearsal_mode"] == "fixture_first_disabled_review_only"
    assert first["candidate_status"] == "draft_rehearsal_only"
    assert first["activation_state"]["disabled"] is True
    assert first["activation_state"]["activation_enabled"] is False
    assert first["activation_state"]["promotion_target"] == "none"


def test_records_draft_predicate_changes_for_each_process_model_impact_area() -> None:
    packet = _build_packet()

    kinds = {change["predicate_kind"] for change in packet["draft_predicate_changes"]}
    assert {
        "process_stage_review_required",
        "required_user_fact_review_required",
        "required_document_review_required",
        "unsupported_path_review_required",
    }.issubset(kinds)

    covered_diff_ids = {
        diff_id
        for change in packet["draft_predicate_changes"]
        for diff_id in change["source_requirement_diff_ids"]
    }
    assert set(packet["source_requirement_diff_ids"]).issubset(covered_diff_ids)
    assert all(change["review_status"] == "draft_requires_human_review" for change in packet["draft_predicate_changes"])
    assert all(change["activation_allowed"] is False for change in packet["draft_predicate_changes"])


def test_records_exact_confirmation_and_refused_consequential_action_coverage() -> None:
    packet = _build_packet()

    exact_actions = {gate["action"] for gate in packet["exact_confirmation_gate_coverage"]}
    refused_actions = {refusal["action"] for refusal in packet["refused_consequential_action_coverage"]}

    assert {"certify acknowledgement", "submit permit request", "submit payment", "upload permit documents"}.issubset(exact_actions)
    assert exact_actions.issubset(refused_actions)
    assert all(gate["requires_exact_confirmation"] is True for gate in packet["exact_confirmation_gate_coverage"])
    assert all(gate["required_confirmation_text"] for gate in packet["exact_confirmation_gate_coverage"])
    assert all(refusal["refuse_until_attended_exact_confirmation"] is True for refusal in packet["refused_consequential_action_coverage"])


def test_records_explanation_template_deltas_and_rollback_references() -> None:
    packet = _build_packet()

    covered_refs = {delta["covers_ref"] for delta in packet["explanation_template_deltas"]}
    predicate_refs = {change["predicate_id"] for change in packet["draft_predicate_changes"]}
    gate_refs = {gate["gate_id"] for gate in packet["exact_confirmation_gate_coverage"]}
    refusal_refs = {refusal["refusal_id"] for refusal in packet["refused_consequential_action_coverage"]}

    assert predicate_refs.issubset(covered_refs)
    assert gate_refs.issubset(covered_refs)
    assert refusal_refs.issubset(covered_refs)
    assert all(delta["review_status"] == "draft_requires_human_review" for delta in packet["explanation_template_deltas"])

    assert packet["rollback_references"] == [
        {
            "rollback_ref_id": "rollback.guardrail-bundle-single-pdf-active.active-2026-05-20",
            "active_guardrail_bundle_id": "guardrail-bundle-single-pdf-active",
            "active_guardrail_bundle_revision": "active-2026-05-20",
            "restore_action": "retain_active_bundle_and_discard_rehearsal_candidate",
            "activation_blocked": True,
        }
    ]


def test_valid_rehearsal_passes_validation() -> None:
    packet = _build_packet()

    assert validate_guardrail_recompilation_rehearsal(packet) == []
    require_valid_guardrail_recompilation_rehearsal(packet)


def test_validation_rejects_activation_or_missing_rollback() -> None:
    packet = _build_packet()
    packet["activation_state"]["activation_enabled"] = True
    packet["activation_state"]["promotion_target"] = "active_guardrail_bundle"
    packet["rollback_references"] = []

    codes = finding_codes(validate_guardrail_recompilation_rehearsal(packet))

    assert "activation_enabled" in codes
    assert "promotion_target_enabled" in codes
    assert "missing_rollback_references" in codes


def test_validation_rejects_missing_refusal_coverage_for_exact_gate() -> None:
    packet = _build_packet()
    packet["refused_consequential_action_coverage"] = packet["refused_consequential_action_coverage"][:-1]

    codes = finding_codes(validate_guardrail_recompilation_rehearsal(packet))

    assert "missing_refused_action_coverage" in codes
