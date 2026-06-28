from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.logic.process_model_impact_candidate import (
    build_process_model_impact_candidate,
    finding_codes,
    require_valid_process_model_impact_candidate,
    validate_process_model_impact_candidate,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "process_model_impact_candidate" / "regenerated_requirement_candidate.json"


def _load_fixture() -> dict:
    with FIXTURE_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def test_builds_deterministic_review_only_process_model_impact_candidate() -> None:
    fixture = _load_fixture()
    original = copy.deepcopy(fixture)

    first = build_process_model_impact_candidate(fixture)
    second = build_process_model_impact_candidate(fixture)

    assert first == second
    assert fixture == original
    assert first["packet_type"] == "process_model_impact_candidate"
    assert first["candidate_status"] == "draft_requires_human_review"
    assert first["candidate_mode"] == "fixture_first_review_only"
    assert first["does_not_replace_active_process_models"] is True
    assert first["active_process_model_mutated"] is False
    assert first["promotion"] == {"target": "candidate", "promote_to_active": False}
    assert "active_process_model" not in first
    assert "replacement_process_model" not in first


def test_maps_changed_requirements_to_process_model_impact_surfaces() -> None:
    packet = build_process_model_impact_candidate(_load_fixture())

    stage_ids = {item["stage_id"] for item in packet["affected_process_stages"]}
    assert {
        "property_lookup",
        "application_data_entry",
        "document_preparation",
        "upload_staging",
        "corrections_checksheets",
        "plan_review",
        "fee_payment",
        "acknowledgment_certification_review",
        "submission",
    }.issubset(stage_ids)

    fact_ids = {item["user_fact_id"] for item in packet["affected_user_facts"]}
    assert {"site_address", "property_owner_name", "checksheets_received_date", "fee_notice_received"}.issubset(fact_ids)

    document_ids = {item["required_document_id"] for item in packet["affected_required_documents"]}
    assert {"drawing_plan_single_pdf", "supporting_documents_separate_pdfs"}.issubset(document_ids)

    unsupported_path_ids = {item["unsupported_path_id"] for item in packet["affected_unsupported_paths"]}
    assert {"unattended_certification", "unattended_submission"}.issubset(unsupported_path_ids)

    prompt_diff_ids = {item["source_requirement_diff_id"] for item in packet["reviewer_prompts"]}
    assert prompt_diff_ids == set(packet["input_requirement_diff_ids"])
    assert all(prompt["blocks_process_model_promotion"] is True for prompt in packet["reviewer_prompts"])
    assert all(prompt["status"] == "unresolved" for prompt in packet["reviewer_prompts"])


def test_valid_process_model_impact_candidate_passes_validation() -> None:
    packet = build_process_model_impact_candidate(_load_fixture())

    assert validate_process_model_impact_candidate(packet) == []
    require_valid_process_model_impact_candidate(packet)


def test_validation_rejects_active_process_model_promotion_or_replacement() -> None:
    packet = build_process_model_impact_candidate(_load_fixture())
    packet["promotion"] = {"target": "active_process_model", "promote_to_active": True}
    packet["replacement_process_model"] = {"process_model_id": "process-single-pdf-submission"}

    codes = finding_codes(validate_process_model_impact_candidate(packet))

    assert "active_process_model_promotion" in codes
    assert "active_process_model_replacement" in codes


def test_validation_rejects_unmapped_requirement_diff() -> None:
    packet = build_process_model_impact_candidate(_load_fixture())
    packet["affected_process_stages"] = []
    packet["reviewer_prompts"] = packet["reviewer_prompts"][:-1]

    codes = finding_codes(validate_process_model_impact_candidate(packet))

    assert "missing_impact_group" in codes
    assert "unmapped_requirement_diff" in codes
    assert "missing_reviewer_prompt_for_diff" in codes


def test_validation_rejects_resolved_reviewer_prompt() -> None:
    packet = build_process_model_impact_candidate(_load_fixture())
    packet["reviewer_prompts"][0]["status"] = "resolved"
    packet["reviewer_prompts"][0]["blocks_process_model_promotion"] = False

    codes = finding_codes(validate_process_model_impact_candidate(packet))

    assert "resolved_reviewer_prompt" in codes
    assert "review_prompt_does_not_block_promotion" in codes
