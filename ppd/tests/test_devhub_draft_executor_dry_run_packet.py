from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.devhub.draft_executor_dry_run_packet import (
    assert_dry_run_packet,
    assert_dry_run_packet_file,
    validate_dry_run_packet,
    validate_dry_run_packet_file,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "draft_executor_dry_run_packet.json"


def _fixture_packet() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_fixture_first_reversible_draft_executor_dry_run_packet_is_accepted() -> None:
    assert validate_dry_run_packet_file(FIXTURE_PATH) == []
    assert_dry_run_packet_file(FIXTURE_PATH)


def test_fixture_ties_required_dry_run_evidence_without_browser_artifacts() -> None:
    packet = _fixture_packet()

    assert packet["live_devhub_session"] is False
    assert packet["browser_launched"] is False
    assert packet["browser_artifacts_saved"] is False

    classification = packet["allowed_action_classification"]
    assert isinstance(classification, dict)
    assert classification["action_class"] == "reversible_draft_fill_preview"
    assert classification["changes_official_state"] is False

    attendance = packet["attendance_requirement"]
    assert isinstance(attendance, dict)
    assert attendance["requires_user_attendance"] is True
    assert attendance["unattended_execution_allowed"] is False

    required_facts = packet["required_user_facts"]
    assert isinstance(required_facts, list)
    assert required_facts[0]["value_policy"] == "value_ref_only"

    steps = packet["steps"]
    assert isinstance(steps, list)
    step = steps[0]
    assert isinstance(step, dict)
    assert step["selector_confidence"] >= 0.85
    assert str(step["field_label_redacted"]).startswith("[REDACTED_FIELD_LABEL:")
    assert step["value_ref"] == required_facts[0]["fact_id"]

    preview_diff = step["preview_diff"]
    assert isinstance(preview_diff, dict)
    assert preview_diff["before"] == "[REDACTED_EMPTY]"
    assert str(preview_diff["after"]).startswith("[REDACTED_USER_FACT:")

    rollback = packet["rollback_evidence"]
    assert isinstance(rollback, dict)
    assert rollback["side_effects"] == "none"
    assert rollback["official_state_changed"] is False


@pytest.mark.parametrize(
    ("name", "patch", "expected_code"),
    [
        ("private field value", {"steps": [{"action": "fill_field", "selector": "[data-testid='project-address']", "selector_confidence": "high", "field_label_redacted": "[REDACTED_FIELD_LABEL:PROJECT_ADDRESS]", "value": "123 Private Street"}]}, "private_value"),
        ("missing fact provenance", {"required_user_facts": ["site_address"]}, "missing_fact_provenance"),
        ("unknown fact reference", {"steps": [{"action": "fill_field", "selector": "[data-testid='project-address']", "selector_confidence": "high", "field_label_redacted": "[REDACTED_FIELD_LABEL:PROJECT_ADDRESS]", "value_ref": "unproven_fact", "preview_diff": {"diff_kind": "redacted_field_fill", "before": "[REDACTED_EMPTY]", "after": "[REDACTED_USER_FACT:PROJECT_ADDRESS]", "value_ref": "unproven_fact"}}]}, "missing_fact_provenance"),
        ("low confidence selector", {"steps": [{"action": "fill_field", "selector": "input", "selector_confidence": 0.42, "field_label_redacted": "[REDACTED_FIELD_LABEL:PROJECT_DESCRIPTION]", "value_ref": "project_description"}]}, "low_confidence_selector"),
        ("unredacted field label", {"steps": [{"action": "fill_field", "selector": "[data-testid='project-description']", "selector_confidence": 0.96, "field_label_redacted": "Project description", "value_ref": "project_description", "preview_diff": {"diff_kind": "redacted_field_fill", "before": "[REDACTED_EMPTY]", "after": "[REDACTED_USER_FACT:PROJECT_DESCRIPTION]", "value_ref": "project_description"}}]}, "unredacted_field_label"),
        ("unredacted preview diff", {"steps": [{"action": "fill_field", "selector": "[data-testid='project-description']", "selector_confidence": 0.96, "field_label_redacted": "[REDACTED_FIELD_LABEL:PROJECT_DESCRIPTION]", "value_ref": "project_description", "preview_diff": {"diff_kind": "redacted_field_fill", "before": "", "after": "actual private value", "value_ref": "project_description"}}]}, "unredacted_preview_diff"),
        ("missing attendance", {"attendance_requirement": {"requires_user_attendance": False, "unattended_execution_allowed": True, "attendance_reason": ""}}, "missing_attendance"),
        ("unsafe classification", {"allowed_action_classification": {"action_class": "submission", "decision": "allow_reversible_draft", "may_execute_in_dry_run": True, "changes_official_state": True, "requires_exact_confirmation": True}}, "unsafe_action_classification"),
        ("missing rollback", {"rollback_evidence": {}}, "missing_rollback_evidence"),
        ("browser state", {"browser_state": {"origins": []}}, "browser_artifact"),
        ("screenshot", {"screenshot_path": "/tmp/devhub.png"}, "browser_artifact"),
        ("trace", {"trace_path": "/tmp/devhub-trace.zip"}, "browser_artifact"),
        ("har", {"har_data": {"log": {}}}, "browser_artifact"),
        ("cookies", {"cookies": [{"name": "session", "value": "redacted"}]}, "browser_artifact"),
        ("credentials", {"credentials": {"username": "redacted"}}, "private_value"),
        ("save control", {"steps": [{"action": "save_draft", "selector": "button[aria-label='Save']", "selector_confidence": "high", "field_label_redacted": "[REDACTED_FIELD_LABEL:SAVE]"}]}, "consequential_control"),
        ("continue control", {"steps": [{"action": "continue", "selector": "button[aria-label='Continue']", "selector_confidence": "high", "field_label_redacted": "[REDACTED_FIELD_LABEL:CONTINUE]"}]}, "consequential_control"),
        ("submit control", {"steps": [{"action": "submit_application", "selector": "button[aria-label='Submit']", "selector_confidence": "high", "field_label_redacted": "[REDACTED_FIELD_LABEL:SUBMIT]"}]}, "consequential_control"),
        ("certify control", {"steps": [{"action": "certify", "selector": "[data-testid='certify']", "selector_confidence": "high", "field_label_redacted": "[REDACTED_FIELD_LABEL:CERTIFY]"}]}, "consequential_control"),
        ("upload control", {"steps": [{"action": "upload", "selector": "[data-testid='upload']", "selector_confidence": "high", "field_label_redacted": "[REDACTED_FIELD_LABEL:UPLOAD]"}]}, "consequential_control"),
        ("payment control", {"steps": [{"action": "enter_payment_details", "selector": "[data-testid='payment']", "selector_confidence": "high", "field_label_redacted": "[REDACTED_FIELD_LABEL:PAYMENT]"}]}, "consequential_control"),
        ("schedule control", {"steps": [{"action": "schedule_inspection", "selector": "[data-testid='schedule']", "selector_confidence": "high", "field_label_redacted": "[REDACTED_FIELD_LABEL:SCHEDULE]"}]}, "consequential_control"),
        ("official state changed flag", {"official_devhub_state_changed": True}, "official_state_changed"),
        ("official state changed outcome", {"outcome": "submitted"}, "official_state_changed"),
    ],
)
def test_reversible_draft_executor_dry_run_packet_rejects_unsafe_content(name: str, patch: dict[str, object], expected_code: str) -> None:
    packet = _fixture_packet()
    packet.update(copy.deepcopy(patch))

    codes = {issue.code for issue in validate_dry_run_packet(packet)}

    assert expected_code in codes, name


def test_assert_dry_run_packet_reports_issue_codes() -> None:
    packet = _fixture_packet()
    packet["cookies"] = [{"name": "session", "value": "redacted"}]

    with pytest.raises(ValueError, match="browser_artifact"):
        assert_dry_run_packet(packet)
