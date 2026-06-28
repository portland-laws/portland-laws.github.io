from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ppd.inactive_activation_checklist_v5 import (
    OFFLINE_VALIDATION_COMMANDS,
    assert_valid_inactive_activation_checklist_v5,
    build_from_fixture_path,
    issue_codes,
    load_post_decision_smoke_replay_v5,
    validate_inactive_activation_checklist_v5,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "post_decision_smoke_replay_v5.json"


def _valid_checklist() -> dict[str, Any]:
    return build_from_fixture_path(FIXTURE_PATH)


def _codes(packet: dict[str, Any]) -> set[str]:
    return issue_codes(validate_inactive_activation_checklist_v5(packet))


def test_builds_inactive_activation_checklist_from_fixture_only() -> None:
    checklist = _valid_checklist()

    assert checklist["checklist_version"] == "inactive-activation-checklist-v5"
    assert checklist["status"] == "inactive-review-only"
    assert checklist["fixture_source"] == "ppd-post-decision-smoke-replay-v5-fixture"
    assert checklist["smoke_replay_references"]
    assert "does_not_activate_guardrails" in checklist["non_actions"]
    assert "does_not_open_devhub" in checklist["non_actions"]
    assert checklist["offline_validation_commands"] == OFFLINE_VALIDATION_COMMANDS
    assert validate_inactive_activation_checklist_v5(checklist) == []
    assert_valid_inactive_activation_checklist_v5(checklist)


def test_checklist_contains_required_review_sections() -> None:
    checklist = _valid_checklist()

    assert checklist["smoke_replay_references"]
    assert checklist["activation_prerequisites"]
    assert checklist["required_signoff_placeholders"]
    assert checklist["source_freshness_hold_clearance_criteria"]
    assert checklist["rollback_checkpoint_rows"]
    assert checklist["post_activation_smoke_checks"]
    assert checklist["agent_notification_notes"]
    assert checklist["monitoring_rehearsal_handoff_rows"]


def test_rejects_non_fixture_path() -> None:
    with pytest.raises(ValueError, match="ppd/tests/fixtures"):
        load_post_decision_smoke_replay_v5(Path("/tmp/post_decision_smoke_replay_v5.json"))


@pytest.mark.parametrize(
    ("field", "code"),
    [
        ("smoke_replay_references", "missing_smoke_replay_references"),
        ("activation_prerequisites", "missing_reviewer_controlled_activation_prerequisites"),
        ("required_signoff_placeholders", "missing_signoff_placeholders"),
        ("source_freshness_hold_clearance_criteria", "missing_source_freshness_hold_clearance_criteria"),
        ("rollback_checkpoint_rows", "missing_rollback_checkpoint_rows"),
        ("post_activation_smoke_checks", "missing_post_activation_smoke_checks"),
        ("agent_notification_notes", "missing_agent_notification_notes"),
        ("monitoring_rehearsal_handoff_rows", "missing_monitoring_rehearsal_handoff_rows"),
        ("offline_validation_commands", "missing_validation_commands"),
    ],
)
def test_rejects_missing_required_sections(field: str, code: str) -> None:
    checklist = _valid_checklist()
    checklist[field] = []

    assert code in _codes(checklist)


def test_rejects_missing_reviewer_controlled_activation_prerequisites() -> None:
    checklist = _valid_checklist()
    checklist["activation_prerequisites"][0]["owner"] = "automation"
    checklist["activation_prerequisites"][0]["reviewer_controlled"] = False

    assert "missing_reviewer_controlled_activation_prerequisites" in _codes(checklist)


def test_rejects_missing_signoff_placeholder_details() -> None:
    checklist = _valid_checklist()
    checklist["required_signoff_placeholders"][0].pop("placeholder")

    assert "missing_signoff_placeholders" in _codes(checklist)


def test_rejects_missing_source_freshness_hold_clearance_criteria() -> None:
    checklist = _valid_checklist()
    checklist["source_freshness_hold_clearance_criteria"][0]["clearance"] = ""

    assert "missing_source_freshness_hold_clearance_criteria" in _codes(checklist)


def test_rejects_missing_rollback_checkpoint_row_details() -> None:
    checklist = _valid_checklist()
    checklist["rollback_checkpoint_rows"][0]["expected_state"] = ""

    assert "missing_rollback_checkpoint_rows" in _codes(checklist)


def test_rejects_missing_post_activation_smoke_check_details() -> None:
    checklist = _valid_checklist()
    checklist["post_activation_smoke_checks"][0]["expected"] = ""

    assert "missing_post_activation_smoke_checks" in _codes(checklist)


def test_rejects_missing_agent_notification_note_details() -> None:
    checklist = _valid_checklist()
    checklist["agent_notification_notes"][0]["note"] = ""

    assert "missing_agent_notification_notes" in _codes(checklist)


def test_rejects_missing_monitoring_rehearsal_handoff_row_details() -> None:
    checklist = _valid_checklist()
    checklist["monitoring_rehearsal_handoff_rows"][0]["next_reviewer_action"] = ""

    assert "missing_monitoring_rehearsal_handoff_rows" in _codes(checklist)


def test_rejects_invalid_validation_commands() -> None:
    checklist = _valid_checklist()
    checklist["offline_validation_commands"] = [["python3", "live_crawl.py"]]

    assert "invalid_validation_commands" in _codes(checklist)


@pytest.mark.parametrize(
    ("mutator", "code"),
    [
        (lambda packet: packet.update({"notes": "activation is active"}), "active_activation_claim"),
        (lambda packet: packet.update({"session_file": "state.json"}), "private_session_auth_artifact"),
        (lambda packet: packet.update({"notes": "submitted permit application to the official record"}), "official_action_completion_claim"),
        (lambda packet: packet.update({"notes": "permit will be approved"}), "legal_or_permitting_guarantee"),
        (lambda packet: packet.update({"active_mutation": True}), "active_mutation_flag"),
        (lambda packet: packet["rollback_checkpoint_rows"][0].update({"active_state_changed": True}), "active_mutation_flag"),
        (lambda packet: packet["post_activation_smoke_checks"][0].update({"activation_allowed": True}), "active_activation_claim"),
    ],
)
def test_rejects_safety_violations(mutator: Any, code: str) -> None:
    checklist = _valid_checklist()
    mutator(checklist)

    assert code in _codes(checklist)


def test_validation_does_not_mutate_input() -> None:
    checklist = _valid_checklist()
    before = deepcopy(checklist)

    validate_inactive_activation_checklist_v5(checklist)

    assert checklist == before
