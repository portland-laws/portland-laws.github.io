from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.agent_readiness.inactive_public_refresh_process_model_delta_plan_v1 import (
    ACTIVE_MUTATION_FLAGS,
    REQUIRED_TOP_LEVEL_SEQUENCES,
    VALIDATION_COMMANDS,
    load_inactive_public_refresh_process_model_delta_plan_v1,
    validate_inactive_public_refresh_process_model_delta_plan_v1,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "inactive_public_refresh_process_model_delta_plan_v1"
    / "valid_plan.json"
)


def _valid_packet() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_inactive_public_refresh_process_model_delta_plan_v1_valid_fixture_loads() -> None:
    packet = load_inactive_public_refresh_process_model_delta_plan_v1(FIXTURE_PATH)
    result = validate_inactive_public_refresh_process_model_delta_plan_v1(packet)
    assert result.valid, result.problems


def test_inactive_public_refresh_process_model_delta_plan_v1_rejects_missing_required_sections() -> None:
    for key in REQUIRED_TOP_LEVEL_SEQUENCES:
        packet = _valid_packet()
        packet.pop(key)
        result = validate_inactive_public_refresh_process_model_delta_plan_v1(packet)
        assert not result.valid
        assert any(key in problem for problem in result.problems), result.problems


def test_inactive_public_refresh_process_model_delta_plan_v1_rejects_missing_placeholder() -> None:
    packet = _valid_packet()
    packet["inactive_process_model_delta_placeholders"] = []
    result = validate_inactive_public_refresh_process_model_delta_plan_v1(packet)
    assert not result.valid
    assert any("inactive_process_model_delta_placeholders" in problem for problem in result.problems)


def test_inactive_public_refresh_process_model_delta_plan_v1_rejects_missing_placeholder_refs() -> None:
    ref_fields = (
        "requirement_reextraction_queue_refs",
        "stage_level_eligibility_change_refs",
        "document_requirement_change_refs",
        "unsupported_path_note_refs",
        "stale_or_conflicting_evidence_hold_refs",
        "affected_guardrail_bundle_refs",
        "reviewer_routing_refs",
        "rollback_note_refs",
    )
    for field in ref_fields:
        packet = _valid_packet()
        placeholder = copy.deepcopy(packet["inactive_process_model_delta_placeholders"][0])  # type: ignore[index]
        placeholder[field] = []
        packet["inactive_process_model_delta_placeholders"] = [placeholder]
        result = validate_inactive_public_refresh_process_model_delta_plan_v1(packet)
        assert not result.valid
        assert any(field in problem for problem in result.problems), result.problems


def test_inactive_public_refresh_process_model_delta_plan_v1_rejects_unknown_refs() -> None:
    examples = {
        "requirement_reextraction_queue_refs": "missing-queue-ref",
        "stage_level_eligibility_change_refs": "missing-stage-change",
        "document_requirement_change_refs": "missing-document-change",
        "unsupported_path_note_refs": "missing-unsupported-path-note",
        "stale_or_conflicting_evidence_hold_refs": "missing-evidence-hold",
        "affected_guardrail_bundle_refs": "missing-guardrail-bundle",
        "reviewer_routing_refs": "missing-reviewer-route",
        "rollback_note_refs": "missing-rollback-note",
    }
    for field, missing_ref in examples.items():
        packet = _valid_packet()
        placeholder = copy.deepcopy(packet["inactive_process_model_delta_placeholders"][0])  # type: ignore[index]
        placeholder[field] = [missing_ref]
        packet["inactive_process_model_delta_placeholders"] = [placeholder]
        result = validate_inactive_public_refresh_process_model_delta_plan_v1(packet)
        assert not result.valid
        assert any(f"unknown ref {missing_ref}" in problem for problem in result.problems), result.problems


def test_inactive_public_refresh_process_model_delta_plan_v1_rejects_active_mutation_flags() -> None:
    for flag in ACTIVE_MUTATION_FLAGS:
        packet = _valid_packet()
        packet[flag] = True
        result = validate_inactive_public_refresh_process_model_delta_plan_v1(packet)
        assert not result.valid
        assert any(flag in problem for problem in result.problems), result.problems


def test_inactive_public_refresh_process_model_delta_plan_v1_rejects_private_raw_downloaded_artifact_keys() -> None:
    for key in ("private_artifact", "raw_output", "downloaded_document", "raw_crawl_output", "session_state"):
        packet = _valid_packet()
        packet[key] = "unsafe"
        result = validate_inactive_public_refresh_process_model_delta_plan_v1(packet)
        assert not result.valid
        assert any("private, raw, downloaded, or runtime artifacts" in problem for problem in result.problems)


def test_inactive_public_refresh_process_model_delta_plan_v1_rejects_forbidden_claims() -> None:
    examples = (
        "live extraction completed",
        "live crawl completed",
        "DevHub opened",
        "DevHub portal verified",
        "active process model mutation",
        "active guardrail mutation",
        "official action completed",
        "submission completed",
        "legal advice",
        "permit approval guaranteed",
        "downloaded artifact",
        "raw crawl output",
    )
    for value in examples:
        packet = _valid_packet()
        packet["unsafe_note"] = value
        result = validate_inactive_public_refresh_process_model_delta_plan_v1(packet)
        assert not result.valid, value


def test_inactive_public_refresh_process_model_delta_plan_v1_requires_validation_commands() -> None:
    packet = _valid_packet()
    packet["validation_commands"] = []
    result = validate_inactive_public_refresh_process_model_delta_plan_v1(packet)
    assert not result.valid
    assert any("validation_commands" in problem for problem in result.problems)

    packet = _valid_packet()
    placeholder = copy.deepcopy(packet["inactive_process_model_delta_placeholders"][0])  # type: ignore[index]
    placeholder["validation_commands"] = [["python3", "-m", "pytest"]]
    packet["inactive_process_model_delta_placeholders"] = [placeholder]
    result = validate_inactive_public_refresh_process_model_delta_plan_v1(packet)
    assert not result.valid
    assert any("validation_commands must contain only" in problem for problem in result.problems)
    assert VALIDATION_COMMANDS != []
