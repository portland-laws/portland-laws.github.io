from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.logic.guardrail_bundle_promotion_review_packet import (
    build_guardrail_bundle_promotion_review_packet,
    validate_guardrail_bundle_promotion_review_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "guardrail_bundle_promotion_review_packet"


def _load_fixture() -> dict:
    with (FIXTURE_DIR / "review_inputs.json").open(encoding="utf-8") as handle:
        return json.load(handle)


def _codes(packet: dict) -> set[str]:
    return set(validate_guardrail_bundle_promotion_review_packet(packet))


def test_review_packet_is_deterministic_and_preserves_inputs() -> None:
    fixture = _load_fixture()
    original = copy.deepcopy(fixture)

    first = build_guardrail_bundle_promotion_review_packet(fixture)
    second = build_guardrail_bundle_promotion_review_packet(fixture)

    assert first == second
    assert fixture == original
    assert first["packet_status"] == "draft_review_required_no_active_bundle_mutation"
    assert first["packet_mode"] == "fixture_first_promotion_review_only"
    assert first["does_not_replace_active_bundle"] is True
    assert first["active_bundle_mutated"] is False
    assert first["promotion_decision"] == "blocked_pending_human_review"
    assert "active_guardrail_bundle" not in first


def test_review_packet_records_diffs_citations_blocks_gates_prompts_and_rollback() -> None:
    packet = build_guardrail_bundle_promotion_review_packet(_load_fixture())

    diff_groups = {diff["target_group"] for diff in packet["draft_bundle_diffs"]}
    assert diff_groups == {
        "deterministic_predicates",
        "exact_confirmation_predicates",
        "explanation_templates",
        "refused_action_predicates",
    }
    assert all(diff["mutates_active_bundle"] is False for diff in packet["draft_bundle_diffs"])
    assert all(diff["source_evidence_ids"] for diff in packet["draft_bundle_diffs"])

    citation_ids = {citation["evidence_id"] for citation in packet["source_evidence_citations"]}
    assert "evidence-submit-plans-single-pdf-rule" in citation_ids
    assert "evidence-submit-application-confirmation" in citation_ids

    blocked_actions = {action["action_id"] for action in packet["blocked_consequential_actions"]}
    assert {"submit permit application", "upload supporting documents"}.issubset(blocked_actions)
    assert all(action["requires_attendance"] is True for action in packet["blocked_consequential_actions"])
    assert all(action["requires_exact_confirmation"] is True for action in packet["blocked_consequential_actions"])

    gate_actions = {gate["action_id"] for gate in packet["exact_confirmation_gates"]}
    assert {"submit permit application", "upload supporting documents"}.issubset(gate_actions)
    assert any(gate["required_confirmation_text"] == "I confirm I am ready to submit this PP&D permit application." for gate in packet["exact_confirmation_gates"])

    assert any(prompt["prompt_type"] == "agent_regression_rerun_plan" for prompt in packet["reviewer_prompts"])
    assert all(prompt["blocks_promotion"] is True for prompt in packet["reviewer_prompts"])
    assert {note["note_id"] for note in packet["rollback_notes"]} == {
        "rollback.discard-draft-diffs",
        "rollback.keep-active-bundle",
        "rollback.rerun-agent-regression-fixtures",
    }


def test_review_packet_validation_rejects_active_bundle_replacement_content() -> None:
    packet = build_guardrail_bundle_promotion_review_packet(_load_fixture())
    packet["active_guardrail_bundle"] = {"guardrail_bundle_id": "replacement"}

    errors = _codes(packet)

    assert "packet must not include active bundle replacement content" in errors


def test_review_packet_validation_rejects_uncited_diff() -> None:
    packet = build_guardrail_bundle_promotion_review_packet(_load_fixture())
    packet["draft_bundle_diffs"][0]["source_evidence_ids"] = []

    errors = _codes(packet)

    assert any(error.startswith("draft bundle diff is uncited") for error in errors)


def test_review_packet_validation_rejects_blocked_action_without_exact_confirmation_gate() -> None:
    packet = build_guardrail_bundle_promotion_review_packet(_load_fixture())
    packet["exact_confirmation_gates"] = [
        gate for gate in packet["exact_confirmation_gates"] if gate["action_id"] != "upload supporting documents"
    ]

    errors = _codes(packet)

    assert "consequential action lacks exact confirmation gate: upload supporting documents" in errors
