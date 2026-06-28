from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.logic.guardrail_recompilation_rehearsal_packet import (
    build_guardrail_recompilation_rehearsal_packet,
    finding_codes,
    require_valid_guardrail_recompilation_rehearsal_packet,
    validate_guardrail_recompilation_rehearsal_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"
REVIEWED_REQUIREMENTS_PATH = FIXTURE_DIR / "guardrail_recompilation_rehearsal" / "reviewed_synthetic_requirement_candidates.json"
PROCESS_MODEL_PATH = FIXTURE_DIR / "process_models" / "synthetic_public_process.json"


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _build_packet() -> dict:
    return build_guardrail_recompilation_rehearsal_packet(
        _load_json(REVIEWED_REQUIREMENTS_PATH),
        [_load_json(PROCESS_MODEL_PATH)],
        active_guardrail_bundle_id="guardrail-bundle-single-pdf-active",
        active_guardrail_bundle_revision="active-2026-05-29",
    )


def test_builds_deterministic_rehearsal_packet_without_mutating_inputs() -> None:
    requirements = _load_json(REVIEWED_REQUIREMENTS_PATH)
    process_model = _load_json(PROCESS_MODEL_PATH)
    original_requirements = copy.deepcopy(requirements)
    original_process_model = copy.deepcopy(process_model)

    first = build_guardrail_recompilation_rehearsal_packet(
        requirements,
        [process_model],
        active_guardrail_bundle_id="guardrail-bundle-single-pdf-active",
        active_guardrail_bundle_revision="active-2026-05-29",
    )
    second = build_guardrail_recompilation_rehearsal_packet(
        requirements,
        [process_model],
        active_guardrail_bundle_id="guardrail-bundle-single-pdf-active",
        active_guardrail_bundle_revision="active-2026-05-29",
    )

    assert first == second
    assert requirements == original_requirements
    assert process_model == original_process_model
    assert first["packet_type"] == "fixture_first_guardrail_recompilation_rehearsal_packet"
    assert first["packet_mode"] == "fixture_first_rehearsal_only"
    assert first["activation_state"]["compile_attempted"] is False
    assert first["activation_state"]["active_bundle_promoted"] is False
    assert first["activation_state"]["active_bundle_mutated"] is False
    assert first["activation_state"]["promotion_target"] == "none"


def test_records_cited_predicate_diffs_and_affected_process_ids() -> None:
    packet = _build_packet()

    assert packet["affected_process_ids"] == ["synthetic-public-single-pdf-process"]
    assert packet["source_process_model_fixture_ids"] == ["synthetic-public-single-pdf-process"]
    assert {item["predicate_kind"] for item in packet["predicate_diff_candidates"]} == {
        "action_gate_predicate_diff",
        "document_requirement_predicate_diff",
    }
    assert all(item["source_evidence_ids"] for item in packet["predicate_diff_candidates"])
    assert all(item["activation_allowed"] is False for item in packet["predicate_diff_candidates"])
    assert all(item["affected_process_ids"] == ["synthetic-public-single-pdf-process"] for item in packet["predicate_diff_candidates"])


def test_records_blocked_actions_exact_confirmation_and_manual_handoff_notes() -> None:
    packet = _build_packet()

    blocked_actions = {item["action"] for item in packet["blocked_action_expectations"]}
    checkpoint_actions = {item["action"] for item in packet["exact_confirmation_checkpoints"]}
    handoff_actions = {item["blocked_action"] for item in packet["manual_handoff_notes"]}

    assert {"submit permit request", "upload permit documents"}.issubset(blocked_actions)
    assert blocked_actions.issubset(checkpoint_actions)
    assert blocked_actions.issubset(handoff_actions)
    assert all(item["expected_decision"] == "block_until_attended_exact_confirmation" for item in packet["blocked_action_expectations"])
    assert all(item["requires_user_attendance"] is True for item in packet["exact_confirmation_checkpoints"])
    assert all(item["exact_confirmation_text"] for item in packet["exact_confirmation_checkpoints"])
    assert all("Do not compile or promote" in item["operator_instruction"] for item in packet["manual_handoff_notes"])


def test_valid_rehearsal_packet_passes_validation() -> None:
    packet = _build_packet()

    assert validate_guardrail_recompilation_rehearsal_packet(packet) == []
    require_valid_guardrail_recompilation_rehearsal_packet(packet)


def test_validation_rejects_promotion_and_uncited_predicate_diff() -> None:
    packet = _build_packet()
    packet["activation_state"]["compile_attempted"] = True
    packet["activation_state"]["promotion_target"] = "active_guardrail_bundle"
    packet["predicate_diff_candidates"][0]["source_evidence_ids"] = []

    codes = finding_codes(validate_guardrail_recompilation_rehearsal_packet(packet))

    assert "unsafe_activation_state" in codes
    assert "promotion_target_enabled" in codes
    assert "uncited_predicate_diff" in codes


def test_validation_rejects_missing_checkpoint_for_blocked_action() -> None:
    packet = _build_packet()
    packet["exact_confirmation_checkpoints"] = packet["exact_confirmation_checkpoints"][:-1]

    codes = finding_codes(validate_guardrail_recompilation_rehearsal_packet(packet))

    assert "missing_exact_confirmation_checkpoint" in codes
