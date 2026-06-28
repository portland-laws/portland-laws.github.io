from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest

from ppd.agent_readiness.process_model_refresh_impact_queue_v6 import (
    EXPECTED_VALIDATION_COMMANDS,
    build_process_model_refresh_impact_queue_v6_from_fixture,
    load_reextracted_requirement_candidate_set_v6,
    validate_process_model_refresh_impact_queue_v6,
    validate_reextracted_requirement_candidate_set_v6,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "process_model_refresh_impact_queue_v6"
    / "reextracted_requirement_candidate_set_v6.json"
)


def test_builds_fixture_first_process_model_refresh_impact_queue_v6() -> None:
    queue = build_process_model_refresh_impact_queue_v6_from_fixture(FIXTURE_PATH)

    assert queue["queue_type"] == "ppd.process_model_refresh_impact_queue.v6"
    assert queue["fixture_first"] is True
    assert queue["consumes_only_reextracted_requirement_candidate_set_v6_fixtures"] is True
    assert queue["source_candidate_set_ref"] == "candidate-set:public-refresh-reextracted-requirements-v6-fixture"
    assert queue["validation_commands"] == EXPECTED_VALIDATION_COMMANDS
    assert queue["affected_process_models"] == [
        "process-model:residential-building-permit",
        "process-model:trade-permit",
    ]
    assert queue["attestations"]["live_crawl"] is False
    assert queue["attestations"]["devhub_opened"] is False
    assert queue["attestations"]["legal_or_permitting_guarantee"] is False

    residential_group = queue["impact_groups"][0]
    assert residential_group["process_model_id"] == "process-model:residential-building-permit"
    assert residential_group["activation_allowed"] is False
    assert "user-fact-change:site-address-confirmation-placeholder" in residential_group["required_user_fact_changes"]
    assert "document-change:single-pdf-plan-set-placeholder" in residential_group["document_requirement_changes"]
    assert "deadline-change-placeholder:prescreen-response-window-review" in residential_group["deadline_change_placeholders"]
    assert "action-gate-change-placeholder:acknowledgement-review-required" in residential_group["action_gate_change_placeholders"]

    validate_process_model_refresh_impact_queue_v6(queue)


def test_candidate_set_rejects_live_or_devhub_claims() -> None:
    candidate_set = load_reextracted_requirement_candidate_set_v6(FIXTURE_PATH)
    candidate_set["live_crawl"] = True

    with pytest.raises(ValueError, match="live_crawl"):
        validate_reextracted_requirement_candidate_set_v6(candidate_set)

    candidate_set = load_reextracted_requirement_candidate_set_v6(FIXTURE_PATH)
    candidate_set["requirement_candidates"][0]["candidate_summary"] = "DevHub opened and application submitted"

    with pytest.raises(ValueError, match="prohibited claim phrase"):
        validate_reextracted_requirement_candidate_set_v6(candidate_set)


def test_queue_rejects_non_offline_validation_commands() -> None:
    queue = build_process_model_refresh_impact_queue_v6_from_fixture(FIXTURE_PATH)
    mutated = copy.deepcopy(queue)
    mutated["validation_commands"] = [["python3", "-m", "pytest"]]

    with pytest.raises(ValueError, match="exact offline validation_commands"):
        validate_process_model_refresh_impact_queue_v6(mutated)


def test_queue_rejects_active_mutation_attestation() -> None:
    queue = build_process_model_refresh_impact_queue_v6_from_fixture(FIXTURE_PATH)
    mutated = copy.deepcopy(queue)
    mutated["attestations"]["active_process_model_mutation"] = True

    with pytest.raises(ValueError, match="active_process_model_mutation"):
        validate_process_model_refresh_impact_queue_v6(mutated)


@pytest.mark.parametrize(
    ("mutator", "error_fragment"),
    [
        (lambda packet: packet.pop("source_candidate_set_ref"), "source_candidate_set_ref"),
        (lambda packet: packet["impact_groups"].pop(), "missing impact groups"),
        (lambda packet: packet["impact_groups"][0].update({"required_user_fact_changes": []}), "required_user_fact_changes"),
        (lambda packet: packet["impact_groups"][0].update({"document_requirement_changes": []}), "document_requirement_changes"),
        (lambda packet: packet["impact_groups"][0].update({"fee_change_placeholders": []}), "fee_change_placeholders"),
        (lambda packet: packet["impact_groups"][0].update({"deadline_change_placeholders": []}), "deadline_change_placeholders"),
        (lambda packet: packet["impact_groups"][0].update({"action_gate_change_placeholders": []}), "action_gate_change_placeholders"),
        (lambda packet: packet["impact_groups"][0].update({"unsupported_path_reminders": []}), "unsupported_path_reminders"),
        (lambda packet: packet.update({"reviewer_hold_rows": []}), "reviewer_hold_ref rows"),
        (
            lambda packet: packet.update({"inactive_guardrail_dependency_notes": []}),
            "dependency_note_ref rows",
        ),
    ],
)
def test_queue_rejects_missing_required_references_and_rows(mutator: Any, error_fragment: str) -> None:
    queue = build_process_model_refresh_impact_queue_v6_from_fixture(FIXTURE_PATH)
    mutated = copy.deepcopy(queue)
    mutator(mutated)

    with pytest.raises(ValueError, match=error_fragment):
        validate_process_model_refresh_impact_queue_v6(mutated)


@pytest.mark.parametrize(
    ("field", "value", "error_fragment"),
    [
        ("operator_note", "live crawl execution finished", "live crawl execution"),
        ("artifact_note", "raw crawl artifact stored", "raw crawl artifact"),
        ("download_note", "downloaded document was retained", "downloaded document"),
        ("private_note", "private session artifact was kept", "private session artifact"),
        ("auth_state", {"token": "redacted"}, "prohibited key"),
        ("official_note", "official action completed", "official action completed"),
        ("legal_note", "approval guaranteed", "approval guaranteed"),
        ("active_mutation", True, "active mutation flag"),
    ],
)
def test_queue_rejects_prohibited_claims_artifacts_and_active_mutation_flags(
    field: str,
    value: Any,
    error_fragment: str,
) -> None:
    queue = build_process_model_refresh_impact_queue_v6_from_fixture(FIXTURE_PATH)
    mutated = copy.deepcopy(queue)
    mutated[field] = value

    with pytest.raises(ValueError, match=error_fragment):
        validate_process_model_refresh_impact_queue_v6(mutated)


def test_queue_rejects_missing_reference_rows_for_group_refs() -> None:
    queue = build_process_model_refresh_impact_queue_v6_from_fixture(FIXTURE_PATH)
    mutated = copy.deepcopy(queue)
    mutated["reviewer_hold_rows"] = mutated["reviewer_hold_rows"][:1]

    with pytest.raises(ValueError, match="missing reviewer_hold_ref rows"):
        validate_process_model_refresh_impact_queue_v6(mutated)

    mutated = copy.deepcopy(queue)
    mutated["inactive_guardrail_dependency_notes"] = mutated["inactive_guardrail_dependency_notes"][:1]

    with pytest.raises(ValueError, match="missing dependency_note_ref rows"):
        validate_process_model_refresh_impact_queue_v6(mutated)
