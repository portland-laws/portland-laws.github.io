from __future__ import annotations

import copy
import json
from pathlib import Path

from ppd.devhub.read_only_observation_intake_schema_v3 import validate_observation_intake_v3


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_read_only_observation_intake_schema_v3"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _without(payload: dict, dotted_path: str) -> dict:
    clone = copy.deepcopy(payload)
    current = clone
    parts = dotted_path.split(".")
    for part in parts[:-1]:
        current = current[part]
    current.pop(parts[-1], None)
    return clone


def _codes(payload: dict) -> set[str]:
    return {error.code for error in validate_observation_intake_v3(payload).errors}


def test_valid_fixture_passes_schema_v3_validation() -> None:
    result = validate_observation_intake_v3(_fixture("valid_observation_intake_v3.json"))

    assert result.ok, result.errors


def test_schema_v3_rejects_required_missing_top_level_placeholders() -> None:
    valid = _fixture("valid_observation_intake_v3.json")
    cases = {
        "authorization_checklist_reference": "missing_authorization_checklist_reference",
        "redacted_observation_rows": "missing_redacted_observation_row_placeholders",
        "validation_message_placeholders": "missing_validation_message_placeholders",
        "non_action_upload_control_evidence_labels": "missing_non_action_upload_control_evidence_labels",
        "state_transition_placeholders": "missing_state_transition_placeholders",
        "selector_confidence_notes": "missing_selector_confidence_notes",
        "source_evidence_placeholders": "missing_source_evidence_placeholders",
        "reviewer_holds": "missing_reviewer_holds",
        "validation_commands": "missing_validation_commands",
    }

    for path, expected_code in cases.items():
        assert expected_code in _codes(_without(valid, path))


def test_schema_v3_rejects_missing_surface_identity_fields() -> None:
    valid = _fixture("valid_observation_intake_v3.json")

    assert "missing_title" in _codes(_without(valid, "surface.title"))
    assert "missing_page_heading" in _codes(_without(valid, "surface.page_heading"))
    assert "missing_url_pattern" in _codes(_without(valid, "surface.url_pattern"))


def test_schema_v3_rejects_missing_accessible_landmark_or_read_only_action_labels() -> None:
    valid = _fixture("valid_observation_intake_v3.json")
    invalid = copy.deepcopy(valid)
    invalid["accessible_landmarks"] = []
    invalid["read_only_actions"] = [{"action_id": "review-status"}]

    codes = _codes(invalid)

    assert "missing_accessible_landmark_or_read_only_action_labels" in codes
    assert "missing_read_only_action_label" in codes


def test_schema_v3_rejects_missing_row_and_upload_evidence_placeholders() -> None:
    valid = _fixture("valid_observation_intake_v3.json")
    invalid = copy.deepcopy(valid)
    invalid["redacted_observation_rows"] = [{"row_id": "row-without-placeholder"}]
    invalid["upload_controls"] = [{"control_id": "upload-without-evidence-label"}]

    codes = _codes(invalid)

    assert "missing_redacted_observation_row_placeholder" in codes
    assert "missing_upload_control_evidence_label" in codes


def test_schema_v3_rejects_validation_commands_that_are_not_argument_lists() -> None:
    valid = _fixture("valid_observation_intake_v3.json")
    invalid = copy.deepcopy(valid)
    invalid["validation_commands"] = ["python3 ppd/daemon/ppd_daemon.py --self-test"]

    assert "invalid_validation_command" in _codes(invalid)


def test_schema_v3_rejects_private_artifacts_and_prohibited_claims() -> None:
    base = _fixture("valid_observation_intake_v3.json")
    forbidden_cases = {
        "cookie value was captured": "private_or_session_artifact_claim",
        "operator saved a screenshot for review": "screenshot_trace_or_har_claim",
        "observer clicked in DevHub during a real DevHub session": "live_devhub_interaction_claim",
        "the worker uploaded a selected file": "form_fill_or_upload_claim",
        "permit submitted to PP&D": "official_action_completion_claim",
        "permit will be approved": "legal_or_permitting_guarantee",
    }

    for claim, expected_code in forbidden_cases.items():
        invalid = copy.deepcopy(base)
        invalid["notes"] = claim
        assert expected_code in _codes(invalid)


def test_schema_v3_rejects_active_mutation_flags() -> None:
    valid = _fixture("valid_observation_intake_v3.json")
    invalid = copy.deepcopy(valid)
    invalid["active_mutation"] = True
    invalid["runtime"] = {"mutation_mode": "active"}

    assert "active_mutation_flag" in _codes(invalid)
