from __future__ import annotations

import json
from pathlib import Path

from ppd.extraction.requirement_rerun_review_disposition_packet import build_requirement_rerun_review_disposition_packet
from ppd.logic.guardrail_bundle_update_candidate_packet import (
    build_guardrail_bundle_update_candidate_packet,
    finding_codes,
    require_valid_guardrail_bundle_update_candidate_packet,
    validate_guardrail_bundle_update_candidate_packet,
)
from ppd.logic.guardrail_recompilation_rehearsal_packet import build_guardrail_recompilation_rehearsal_packet
from ppd.logic.process_model_update_candidate import build_process_model_update_candidate


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "guardrail_bundle_update_candidate"


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _fixture() -> dict:
    return _load_json(FIXTURE_DIR / "packet_inputs.json")


def _source_path(relative_path: str) -> Path:
    return (FIXTURE_DIR / relative_path).resolve()


def _input_packets() -> tuple[dict, dict, dict, dict]:
    fixture = _fixture()
    paths = fixture["source_packet_fixture_paths"]

    requirement_inputs = _load_json(_source_path(paths["requirement_rerun_review_disposition_inputs"]))
    requirement_packet = build_requirement_rerun_review_disposition_packet(
        requirement_inputs["requirement_extraction_rerun_rehearsal_packet"],
        requirement_inputs["validation_fixture"],
        generated_at=requirement_inputs["generated_at"],
    )

    process_packet = build_process_model_update_candidate(
        _load_json(_source_path(paths["process_model_update_requirement_review"])),
        _load_json(_source_path(paths["process_model_update_impact_rehearsal"])),
        generated_at=fixture["generated_at"],
    )

    rehearsal_packet = build_guardrail_recompilation_rehearsal_packet(
        _load_json(_source_path(paths["guardrail_recompilation_reviewed_requirements"])),
        [_load_json(_source_path(paths["guardrail_recompilation_process_model"]))],
        active_guardrail_bundle_id=fixture["active_guardrail_bundle_id"],
        active_guardrail_bundle_revision=fixture["active_guardrail_bundle_revision"],
    )
    return fixture, requirement_packet, process_packet, rehearsal_packet


def _packet() -> dict:
    fixture, requirement_packet, process_packet, rehearsal_packet = _input_packets()
    return build_guardrail_bundle_update_candidate_packet(
        requirement_packet,
        process_packet,
        rehearsal_packet,
        generated_at=fixture["generated_at"],
    )


def test_builds_deterministic_fixture_first_update_candidate_packet() -> None:
    fixture, requirement_packet, process_packet, rehearsal_packet = _input_packets()

    first = build_guardrail_bundle_update_candidate_packet(
        requirement_packet,
        process_packet,
        rehearsal_packet,
        generated_at=fixture["generated_at"],
    )
    second = build_guardrail_bundle_update_candidate_packet(
        requirement_packet,
        process_packet,
        rehearsal_packet,
        generated_at=fixture["generated_at"],
    )

    assert first == second
    assert first["packet_type"] == "fixture_first_guardrail_bundle_update_candidate_packet"
    assert first["packet_mode"] == "candidate_packet_no_compile_no_promotion"
    assert first["candidate_status"] == "draft_requires_human_review"
    assert first["active_guardrail_bundle_id"] == fixture["active_guardrail_bundle_id"]
    assert first["input_packet_refs"] == {
        "requirement_rerun_review_disposition_packet_id": requirement_packet["packet_id"],
        "process_model_update_candidate_packet_id": process_packet["packet_id"],
        "guardrail_recompilation_rehearsal_packet_id": rehearsal_packet["packet_id"],
    }
    assert first["no_active_guardrail_mutation_attestations"] | fixture["expected_attestations"] == first["no_active_guardrail_mutation_attestations"]


def test_packet_contains_required_review_sections_with_cited_predicates() -> None:
    fixture = _fixture()
    packet = _packet()

    for field, minimum in fixture["expected_minimums"].items():
        assert len(packet[field]) >= minimum

    assert {item["operation"] for item in packet["cited_predicate_additions"]} == {"add"}
    assert {item["operation"] for item in packet["cited_predicate_removals"]} == {"remove_candidate_predicate"}
    assert all(item["source_evidence_ids"] for item in packet["cited_predicate_additions"])
    assert all(item["source_evidence_ids"] for item in packet["cited_predicate_removals"])
    assert all(item["activation_allowed"] is False for item in packet["cited_predicate_additions"])
    assert all(item["activation_allowed"] is False for item in packet["cited_predicate_removals"])


def test_blocked_actions_have_exact_confirmation_and_manual_handoff_notes() -> None:
    packet = _packet()

    blocked_actions = {item["action"] for item in packet["blocked_action_expectations"]}
    checkpoint_actions = {item["action"] for item in packet["exact_confirmation_checkpoints"]}
    handoff_actions = {item["blocked_action"] for item in packet["manual_handoff_notes"]}

    assert blocked_actions
    assert blocked_actions.issubset(checkpoint_actions)
    assert blocked_actions.issubset(handoff_actions)
    assert all(item["expected_decision"] == "block_until_attended_exact_confirmation" for item in packet["blocked_action_expectations"])
    assert all(item["requires_user_attendance"] is True for item in packet["exact_confirmation_checkpoints"])


def test_valid_candidate_packet_passes_validation_without_compilation_or_promotion() -> None:
    packet = _packet()

    assert validate_guardrail_bundle_update_candidate_packet(packet) == []
    require_valid_guardrail_bundle_update_candidate_packet(packet)
    attestations = packet["no_active_guardrail_mutation_attestations"]
    assert attestations["compiled_guardrail_bundle"] is False
    assert attestations["promoted_guardrail_bundle"] is False
    assert attestations["mutated_active_guardrail_bundle"] is False
    assert attestations["no_active_guardrail_mutation"] is True


def test_validation_rejects_compile_promotion_and_uncited_predicate_claims() -> None:
    packet = _packet()
    packet["no_active_guardrail_mutation_attestations"]["compiled_guardrail_bundle"] = True
    packet["no_active_guardrail_mutation_attestations"]["promoted_guardrail_bundle"] = True
    packet["cited_predicate_additions"][0]["source_evidence_ids"] = []
    packet["cited_predicate_additions"][0]["citations"] = []

    codes = finding_codes(validate_guardrail_bundle_update_candidate_packet(packet))

    assert "attestation_not_false" in codes
    assert "uncited_predicate" in codes


def test_validation_rejects_missing_checkpoint_or_handoff_for_blocked_action() -> None:
    packet = _packet()
    packet["exact_confirmation_checkpoints"] = []
    packet["manual_handoff_notes"] = []

    codes = finding_codes(validate_guardrail_bundle_update_candidate_packet(packet))

    assert "missing_exact_confirmation_checkpoints" in codes
    assert "missing_manual_handoff_notes" in codes
    assert "missing_checkpoint_for_blocked_action" in codes
    assert "missing_handoff_for_blocked_action" in codes
