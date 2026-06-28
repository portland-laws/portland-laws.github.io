from __future__ import annotations

import json
from pathlib import Path

from ppd.logic.manual_handoff import (
    DEVHUB_AUTOMATION_ACTION_TYPE,
    MANUAL_HANDOFF_ACTION_TYPE,
    assert_no_devhub_automation_for_unsupported_paths,
    manual_handoff_reasons,
    next_safe_actions,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "process_models" / "unsupported_manual_handoff_paths.json"


def load_fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_fixture_declares_manual_or_email_unsupported_paths() -> None:
    process_model = load_fixture()

    reasons = manual_handoff_reasons(process_model)

    assert {reason.path_id for reason in reasons} == {
        "not_listed_in_devhub_apply_guide",
        "email_intake_required",
    }
    assert all(reason.source_evidence_ids for reason in reasons)
    assert {reason.required_channel for reason in reasons} == {
        "manual PP&D contact or official non-DevHub intake channel",
        "email_or_staff_handoff",
    }


def test_unsupported_paths_produce_manual_handoff_next_safe_actions() -> None:
    process_model = load_fixture()

    actions = next_safe_actions(process_model)

    assert actions
    assert {action["action_type"] for action in actions} == {MANUAL_HANDOFF_ACTION_TYPE}
    assert all(action["requires_user_attendance"] is True for action in actions)
    assert all(action["requires_exact_confirmation"] is False for action in actions)
    assert all(DEVHUB_AUTOMATION_ACTION_TYPE in action["blocked_action_types"] for action in actions)


def test_unsupported_paths_do_not_emit_devhub_automation() -> None:
    process_model = load_fixture()

    assert_no_devhub_automation_for_unsupported_paths(process_model)

    actions = next_safe_actions(process_model)
    assert not any(action["action_type"] == DEVHUB_AUTOMATION_ACTION_TYPE for action in actions)
