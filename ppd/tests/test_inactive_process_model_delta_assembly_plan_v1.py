from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.agent_readiness.inactive_process_model_delta_assembly_plan_v1 import (
    ACTIVE_MUTATION_FLAGS,
    REQUIRED_TOP_LEVEL_SEQUENCES,
    VALIDATION_COMMANDS,
    load_inactive_process_model_delta_assembly_plan_v1,
    validate_inactive_process_model_delta_assembly_plan_v1,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "inactive_process_model_delta_assembly_plan_v1" / "valid_plan.json"


def _valid_packet() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_inactive_process_model_delta_assembly_plan_v1_valid_fixture_loads() -> None:
    packet = load_inactive_process_model_delta_assembly_plan_v1(FIXTURE_PATH)
    result = validate_inactive_process_model_delta_assembly_plan_v1(packet)
    assert result.valid, result.problems


def test_inactive_process_model_delta_assembly_plan_v1_requires_required_sections() -> None:
    for key in REQUIRED_TOP_LEVEL_SEQUENCES:
        packet = _valid_packet()
        packet.pop(key)
        result = validate_inactive_process_model_delta_assembly_plan_v1(packet)
        assert not result.valid
        assert any(key in problem for problem in result.problems), result.problems


def test_inactive_process_model_delta_assembly_plan_v1_rejects_non_synthetic_queue_rows() -> None:
    packet = _valid_packet()
    rows = copy.deepcopy(packet["synthetic_requirement_reextraction_candidate_queue_rows"])
    rows[0]["queue_source"] = "public_source_reextraction_queue"
    packet["synthetic_requirement_reextraction_candidate_queue_rows"] = rows
    result = validate_inactive_process_model_delta_assembly_plan_v1(packet)
    assert not result.valid
    assert any("queue_source must be synthetic_requirement_reextraction_candidate_queue" in problem for problem in result.problems)


def test_inactive_process_model_delta_assembly_plan_v1_rejects_active_mutation_flags() -> None:
    for flag in ACTIVE_MUTATION_FLAGS:
        packet = _valid_packet()
        packet[flag] = True
        result = validate_inactive_process_model_delta_assembly_plan_v1(packet)
        assert not result.valid
        assert f"{flag} must be false" in result.problems


def test_inactive_process_model_delta_assembly_plan_v1_rejects_unknown_refs() -> None:
    unknown_ref_examples = {
        "candidate_row_refs": "missing-candidate-row",
        "affected_stage_refs": "missing-stage-impact",
        "required_user_fact_impact_refs": "missing-fact-impact",
        "required_document_impact_refs": "missing-document-impact",
        "unsupported_path_note_refs": "missing-unsupported-note",
        "reviewer_hold_refs": "missing-reviewer-hold",
        "rollback_note_refs": "missing-rollback-note",
    }
    for field, missing_ref in unknown_ref_examples.items():
        packet = _valid_packet()
        placeholder = copy.deepcopy(packet["inactive_process_model_patch_placeholders"][0])  # type: ignore[index]
        placeholder[field] = [missing_ref]
        packet["inactive_process_model_patch_placeholders"] = [placeholder]
        result = validate_inactive_process_model_delta_assembly_plan_v1(packet)
        assert not result.valid
        assert any(f"unknown ref {missing_ref}" in problem for problem in result.problems), result.problems


def test_inactive_process_model_delta_assembly_plan_v1_rejects_forbidden_payloads() -> None:
    examples = (
        "opened DevHub during assembly",
        "live crawl result was used",
        "private artifact path",
        "browser state saved",
        "active process model promoted",
        "official action completed",
        "permit will be approved",
    )
    for value in examples:
        packet = _valid_packet()
        packet["unsafe_note"] = value
        result = validate_inactive_process_model_delta_assembly_plan_v1(packet)
        assert not result.valid, value


def test_inactive_process_model_delta_assembly_plan_v1_requires_exact_validation_commands() -> None:
    packet = _valid_packet()
    packet["validation_commands"] = [["python3", "-m", "unittest"]]
    result = validate_inactive_process_model_delta_assembly_plan_v1(packet)
    assert not result.valid
    assert "validation_commands must contain only the PP&D daemon self-test command" in result.problems

    packet = _valid_packet()
    placeholder = copy.deepcopy(packet["inactive_process_model_patch_placeholders"][0])  # type: ignore[index]
    placeholder["validation_commands"] = []
    packet["inactive_process_model_patch_placeholders"] = [placeholder]
    result = validate_inactive_process_model_delta_assembly_plan_v1(packet)
    assert not result.valid
    assert any("validation_commands must contain only" in problem for problem in result.problems)
    assert VALIDATION_COMMANDS != []
