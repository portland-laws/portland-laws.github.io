from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.agent_readiness.inactive_guardrail_recompile_impact_plan_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    FALSE_GUARDRAIL_FLAGS,
    REQUIRED_PLAN_SECTIONS,
    InactiveGuardrailRecompileImpactPlanV1Error,
    build_inactive_guardrail_recompile_impact_plan_v1,
    build_inactive_guardrail_recompile_impact_plan_v1_from_file,
    validate_inactive_guardrail_recompile_impact_plan_v1,
    validate_synthetic_inactive_process_model_delta_assembly_rows_v1,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "inactive_guardrail_recompile_impact_plan_v1" / "synthetic_delta_rows.json"


def _source_packet() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _built_plan() -> dict[str, object]:
    return build_inactive_guardrail_recompile_impact_plan_v1_from_file(FIXTURE_PATH)


def test_builds_fixture_first_inactive_guardrail_recompile_impact_plan_v1() -> None:
    plan = _built_plan()

    assert plan["plan_type"] == "ppd.inactive_guardrail_recompile_impact_plan.v1"
    assert plan["fixture_first"] is True
    assert plan["impact_mode"] == "inactive_guardrail_bundle_patch_placeholders_only"
    assert plan["input_policy"] == "synthetic_inactive_process_model_delta_assembly_rows_only"
    assert plan["validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS
    assert plan["offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS
    for flag in FALSE_GUARDRAIL_FLAGS:
        assert plan[flag] is False
    result = validate_inactive_guardrail_recompile_impact_plan_v1(plan)
    assert result.valid, result.problems


def test_maps_every_required_impact_section_from_synthetic_rows() -> None:
    plan = _built_plan()
    source_rows = plan["source_delta_rows"]
    assert isinstance(source_rows, list)
    source_row_ids = {row["row_id"] for row in source_rows}

    for section in REQUIRED_PLAN_SECTIONS:
        rows = plan[section]
        assert isinstance(rows, list)
        assert len(rows) == len(source_rows)
        if section != "source_delta_rows":
            refs = {row["source_delta_row_ref"] for row in rows}
            assert refs == source_row_ids

    patch_rows = plan["inactive_guardrail_bundle_patch_placeholders"]
    assert all(row["activation_allowed"] is False for row in patch_rows)
    assert all(row["recompile_allowed"] is False for row in patch_rows)


def test_source_fixture_rejects_non_synthetic_inputs_and_active_flags() -> None:
    packet = _source_packet()
    assert validate_synthetic_inactive_process_model_delta_assembly_rows_v1(packet) == []

    broken = copy.deepcopy(packet)
    broken["synthetic_inactive_process_model_delta_assembly_rows"][0]["synthetic_evidence_refs"] = ["public-source:real-row"]
    errors = validate_synthetic_inactive_process_model_delta_assembly_rows_v1(broken)
    assert any("synthetic_evidence_refs" in error for error in errors)

    for flag in FALSE_GUARDRAIL_FLAGS:
        broken = copy.deepcopy(packet)
        broken[flag] = True
        errors = validate_synthetic_inactive_process_model_delta_assembly_rows_v1(broken)
        assert f"{flag} must be false" in errors


def test_plan_rejects_missing_sections_unknown_refs_and_command_changes() -> None:
    plan = _built_plan()
    for section in REQUIRED_PLAN_SECTIONS:
        broken = copy.deepcopy(plan)
        broken[section] = []
        result = validate_inactive_guardrail_recompile_impact_plan_v1(broken)
        assert not result.valid
        assert any(section in problem for problem in result.problems)

    broken = copy.deepcopy(plan)
    broken["deterministic_predicate_impacts"][0]["source_delta_row_ref"] = "missing-row"
    result = validate_inactive_guardrail_recompile_impact_plan_v1(broken)
    assert not result.valid
    assert any("source_delta_row_ref must reference source_delta_rows" in problem for problem in result.problems)

    broken = copy.deepcopy(plan)
    broken["validation_commands"] = [["python3", "-m", "unittest"]]
    result = validate_inactive_guardrail_recompile_impact_plan_v1(broken)
    assert not result.valid
    assert "validation_commands must exactly match the offline validation command bundle" in result.problems


def test_rejects_forbidden_live_private_or_official_action_payloads() -> None:
    forbidden_values = (
        "opened DevHub",
        "live crawl",
        "private artifact",
        "browser state",
        "active guardrail changed",
        "submitted permit",
    )
    for value in forbidden_values:
        packet = _source_packet()
        packet["unsafe_note"] = value
        errors = validate_synthetic_inactive_process_model_delta_assembly_rows_v1(packet)
        assert errors, value

    plan = _built_plan()
    plan["unsafe_note"] = "raw crawl"
    result = validate_inactive_guardrail_recompile_impact_plan_v1(plan)
    assert not result.valid


def test_builder_raises_on_invalid_source_fixture() -> None:
    packet = _source_packet()
    packet["input_kind"] = "live_process_model_delta_rows"

    with pytest.raises(InactiveGuardrailRecompileImpactPlanV1Error):
        build_inactive_guardrail_recompile_impact_plan_v1(packet)
