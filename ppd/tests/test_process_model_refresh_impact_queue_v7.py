from __future__ import annotations

import copy
from pathlib import Path

import pytest

from ppd.agent_readiness.process_model_refresh_impact_queue_v7 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    build_process_model_refresh_impact_queue_v7_from_fixture,
    validate_reextracted_requirement_node_candidate_set_v7,
)

FIXTURE = Path(__file__).parent / "fixtures" / "process_model_refresh_impact_queue_v7" / "candidate_set.json"


def test_builds_fixture_first_process_model_refresh_impact_queue_v7() -> None:
    queue = build_process_model_refresh_impact_queue_v7_from_fixture(FIXTURE)

    assert queue["queue_type"] == "ppd.process_model_refresh_impact_queue.v7"
    assert queue["fixture_first"] is True
    assert queue["consumes_only"] == {"reextracted_requirement_node_candidate_set_v7_fixtures": True}
    assert queue["affected_process_models"] == ["pm-building-alteration", "pm-standard-trade"]
    assert queue["row_count"] == 2
    assert queue["exact_offline_validation_commands"] == EXACT_OFFLINE_VALIDATION_COMMANDS

    alteration = next(row for row in queue["affected_process_model_rows"] if row["process_model_id"] == "pm-building-alteration")
    assert alteration["candidate_refs"] == ["rnc-v7-doc-upload", "rnc-v7-fee-intake"]
    assert alteration["document_impact_placeholders"] == ["doc-impact::single-pdf-separated-supporting-docs"]
    assert alteration["fee_impact_placeholders"] == ["fee-impact::intake-fee-review-placeholder"]
    assert alteration["guardrail_activation_allowed"] is False
    assert alteration["process_model_mutation_allowed"] is False

    assert queue["unsupported_path_carry_forward_notes"]
    assert queue["guardrail_bundle_recompile_suggestions"]
    assert queue["stale_evidence_hold_rows"]
    assert queue["reviewer_signoff_placeholders"]
    assert all(row["activation_allowed"] is False for row in queue["guardrail_bundle_recompile_suggestions"])


def test_candidate_set_validator_rejects_non_v7_fixture() -> None:
    payload = copy.deepcopy(build_process_model_refresh_impact_queue_v7_from_fixture(FIXTURE))
    payload["candidate_set_type"] = "ppd.reextracted_requirement_node_candidate_set.v6"

    with pytest.raises(ValueError, match="candidate_set_type"):
        validate_reextracted_requirement_node_candidate_set_v7(payload)


def test_candidate_set_validator_rejects_live_or_devhub_path() -> None:
    candidate_set = {
        "candidate_set_type": "ppd.reextracted_requirement_node_candidate_set.v7",
        "candidate_set_version": "v7",
        "candidate_set_id": "bad-live-path",
        "mode": "fixture_first_reextracted_requirement_node_candidates_v7_only",
        "fixture_first": True,
        "consumes_only_reextracted_requirement_node_candidate_set_v7_fixtures": True,
        "exact_offline_validation_commands": EXACT_OFFLINE_VALIDATION_COMMANDS,
        "live_crawl_executed": False,
        "live_extraction_executed": False,
        "document_downloaded": False,
        "raw_body_stored": False,
        "devhub_opened": True,
        "private_document_read": False,
        "upload_attempted": False,
        "submission_attempted": False,
        "certification_attempted": False,
        "payment_attempted": False,
        "inspection_scheduling_attempted": False,
        "official_action_completed": False,
        "legal_or_permitting_guarantee": False,
        "active_process_model_mutation": False,
        "active_guardrail_mutation": False,
        "active_requirement_mutation": False,
        "guardrail_activation_attempted": False,
        "requirement_node_candidates": [],
    }

    with pytest.raises(ValueError, match="devhub_opened"):
        validate_reextracted_requirement_node_candidate_set_v7(candidate_set)
