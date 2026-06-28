from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.devhub.surface_map_delta_candidate_v3 import (
    OFFLINE_VALIDATION_COMMANDS,
    build_surface_map_delta_candidate_v3,
    validate_surface_map_delta_candidate_v3,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_surface_map_delta_candidate_v3"


def _load_source() -> dict[str, object]:
    return json.loads((FIXTURE_DIR / "source_packet.json").read_text(encoding="utf-8"))


def _candidate() -> dict[str, object]:
    return build_surface_map_delta_candidate_v3(_load_source())


def test_builds_inactive_delta_rows_from_synthetic_fixture_inputs() -> None:
    candidate = _candidate()

    assert candidate["packet_version"] == "devhub_surface_map_delta_candidate_v3"
    assert candidate["mode"] == "fixture_first_inactive_devhub_surface_map_delta_candidate_v3"
    assert candidate["source_inputs"]["synthetic_fixture_only"] is True
    assert len(candidate["source_inputs"]["prior_surface_map_fixture_placeholders"]) == 3
    assert len(candidate["read_only_surface_delta_rows"]) == 3
    assert validate_surface_map_delta_candidate_v3(candidate) == []


@pytest.mark.parametrize(
    "section",
    [
        "read_only_surface_delta_rows",
        "accessible_landmark_delta_rows",
        "action_classification_delta_rows",
        "validation_message_delta_rows",
        "upload_control_evidence_delta_rows",
        "state_transition_delta_rows",
        "redaction_policy_delta_rows",
        "selector_confidence_delta_rows",
        "attendance_requirement_delta_rows",
        "exact_confirmation_requirement_delta_rows",
        "reviewer_hold_delta_rows",
        "rollback_note_delta_rows",
    ],
)
def test_every_delta_section_is_inactive_fixture_only(section: str) -> None:
    candidate = _candidate()

    rows = candidate[section]
    assert rows
    assert {row["fixture_only"] for row in rows} == {True}
    assert {row["inactive"] for row in rows} == {True}
    assert {row["active_surface_map_mutation"] for row in rows} == {False}


def test_action_classifications_and_exact_confirmation_gates_are_explicit() -> None:
    candidate = _candidate()
    actions = {row["surface_delta_row_id"]: row for row in candidate["action_classification_delta_rows"]}
    exact = {row["surface_delta_row_id"]: row for row in candidate["exact_confirmation_requirement_delta_rows"]}

    blocked_ids = {row_id for row_id, row in actions.items() if row["classification"] == "blocked_official_action"}
    read_only_ids = {row_id for row_id, row in actions.items() if row["classification"] == "read_only_observation"}

    assert blocked_ids == {"delta-v3-002-action-submit-application", "delta-v3-003-upload-plans-control"}
    assert "delta-v3-001-field-status-heading" in read_only_ids
    assert all(actions[row_id]["official_action_allowed"] is False for row_id in actions)
    assert exact["delta-v3-002-action-submit-application"]["requires_exact_confirmation"] is True
    assert exact["delta-v3-003-upload-plans-control"]["requires_exact_confirmation"] is True


def test_upload_control_evidence_is_label_only_and_non_interactive() -> None:
    candidate = _candidate()
    upload_rows = candidate["upload_control_evidence_delta_rows"]

    assert any(row["upload_control_present"] is True for row in upload_rows)
    assert {row["file_interaction_allowed"] for row in upload_rows} == {False}
    assert {row["evidence_policy"] for row in upload_rows} == {"label_only_no_file_interaction"}


def test_validation_requires_exact_offline_commands() -> None:
    candidate = _candidate()

    assert candidate["validation_commands"] == OFFLINE_VALIDATION_COMMANDS
    mutated = copy.deepcopy(candidate)
    mutated["validation_commands"] = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

    assert "validation_commands_not_exact" in validate_surface_map_delta_candidate_v3(mutated)


@pytest.mark.parametrize(
    ("mutation", "expected_code"),
    [
        (lambda packet: packet["source_inputs"].pop("redaction_acceptance_packet_id"), "missing_redaction_acceptance_reference"),
        (lambda packet: packet["source_inputs"].pop("prior_surface_map_fixture_placeholders"), "missing_prior_surface_map_fixture_placeholders"),
        (lambda packet: packet.__setitem__("read_only_surface_delta_rows", []), "missing_inactive_devhub_surface_map_delta_rows"),
        (lambda packet: packet["accessible_landmark_delta_rows"][0].__setitem__("landmarks", []), "accessible_landmark_delta_rows_missing_accessible_landmarks"),
        (lambda packet: packet["action_classification_delta_rows"][0].pop("classification"), "action_classification_delta_rows_missing_classification"),
        (lambda packet: packet["validation_message_delta_rows"][0].pop("message"), "validation_message_delta_rows_missing_message"),
        (lambda packet: packet["upload_control_evidence_delta_rows"][0].__setitem__("evidence_policy", "file_picker_probe"), "upload_control_evidence_delta_rows_missing_upload_control_evidence"),
        (lambda packet: packet["state_transition_delta_rows"][0].pop("to_state"), "state_transition_delta_rows_missing_to_state"),
        (lambda packet: packet["redaction_policy_delta_rows"][0].pop("policy"), "redaction_policy_delta_rows_missing_policy"),
        (lambda packet: packet["selector_confidence_delta_rows"][0].pop("confidence"), "selector_confidence_delta_rows_missing_confidence"),
        (lambda packet: packet["attendance_requirement_delta_rows"][0].pop("requires_attendance"), "attendance_requirement_delta_rows_missing_requires_attendance"),
        (lambda packet: packet["exact_confirmation_requirement_delta_rows"][0].pop("requires_exact_confirmation"), "exact_confirmation_requirement_delta_rows_missing_requires_exact_confirmation"),
        (lambda packet: packet["reviewer_hold_delta_rows"][0].__setitem__("hold_required", False), "reviewer_hold_delta_rows_missing_reviewer_hold"),
        (lambda packet: packet["rollback_note_delta_rows"][0].pop("rollback_note"), "rollback_note_delta_rows_missing_rollback_note"),
    ],
)
def test_validation_rejects_missing_required_delta_evidence(mutation, expected_code: str) -> None:
    candidate = _candidate()
    mutation(candidate)

    assert expected_code in validate_surface_map_delta_candidate_v3(candidate)


def test_validation_rejects_active_mutation_private_artifact_and_live_claims() -> None:
    candidate = _candidate()
    candidate["read_only_surface_delta_rows"][0]["active_surface_map_mutation"] = True
    candidate["review_notes"] = "Opened DevHub, uploaded file, and stored screenshot for review. Permit guaranteed."
    candidate["auth_state"] = "not-allowed"

    codes = set(validate_surface_map_delta_candidate_v3(candidate))

    assert "read_only_surface_delta_rows_active_surface_map_mutation_not_false" in codes
    assert "active_mutation_flag" in codes
    assert "private_auth_or_browser_artifact_key" in codes
    assert "prohibited_live_private_or_official_action_claim" in codes


def test_validation_rejects_active_surface_map_promotion_claims() -> None:
    candidate = _candidate()
    candidate["state_transition_delta_rows"][0]["promotes_active_surface"] = True
    candidate["rollback_note_delta_rows"][0]["active_surface_map_unchanged"] = False

    codes = set(validate_surface_map_delta_candidate_v3(candidate))

    assert "state_transition_delta_rows_promotes_active_surface_not_false" in codes
    assert "rollback_note_delta_rows_active_surface_map_unchanged_not_true" in codes
