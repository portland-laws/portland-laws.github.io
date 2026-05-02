"""Validate mocked DevHub recorder transition fixtures.

The fixtures in this module are deliberately synthetic and redacted. They are
intended to exercise recorder transition handling without creating or depending
on private DevHub sessions, traces, screenshots, raw crawl output, or downloads.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "recorder_transitions.json"
REDACTED_VALUE = "[REDACTED]"
REQUIRED_TRANSITION_KINDS = {
    "save_for_later",
    "back",
    "continue",
    "upload_validation",
    "draft_resume",
}
DISALLOWED_KEYS = {
    "authorization",
    "auth",
    "auth_state",
    "authState",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "password",
    "raw_body",
    "rawBody",
    "response_body",
    "responseBody",
    "screenshot",
    "screenshots",
    "secret",
    "session",
    "session_cookie",
    "sessionCookie",
    "storage_state",
    "storageState",
    "token",
    "trace",
    "traces",
    "username",
}
DISALLOWED_VALUE_PATTERNS = (
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}"),
    re.compile(r"\\b\\d{3}[-.]\\d{3}[-.]\\d{4}\\b"),
    re.compile(r"\\bBearer\\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    re.compile(r"ppd[/\\\\]data[/\\\\]private", re.IGNORECASE),
    re.compile(r"[/\\\\]traces?[/\\\\]|trace\\.zip", re.IGNORECASE),
    re.compile(r"[/\\\\]screenshots?[/\\\\]|screenshot\\.(png|jpe?g|webp)", re.IGNORECASE),
    re.compile(r"[/\\\\]downloads?[/\\\\]", re.IGNORECASE),
)


def test_recorder_transition_fixture_covers_required_states() -> None:
    fixture = _load_fixture()

    states = {state["id"]: state for state in fixture["states"]}
    assert {"project_info", "document_upload", "document_upload_validation", "draft_saved"}.issubset(states)

    transition_kinds = {transition["transition_kind"] for transition in fixture["transitions"]}
    assert REQUIRED_TRANSITION_KINDS.issubset(transition_kinds)

    save_transitions = [
        transition for transition in fixture["transitions"] if transition["transition_kind"] == "save_for_later"
    ]
    assert save_transitions
    assert all(transition["to_state_id"] == "draft_saved" for transition in save_transitions)

    resume_transitions = [
        transition for transition in fixture["transitions"] if transition["transition_kind"] == "draft_resume"
    ]
    assert resume_transitions == [
        {
            "from_state_id": "draft_saved",
            "action_id": "resume_saved_draft",
            "to_state_id": "project_info",
            "transition_kind": "draft_resume",
            "guard": "Resume returns to a redacted editable draft state.",
        }
    ]


def test_recorder_transition_fixture_edges_reference_known_actions() -> None:
    fixture = _load_fixture()
    states = {state["id"]: state for state in fixture["states"]}

    for transition in fixture["transitions"]:
        assert transition["from_state_id"] in states
        assert transition["to_state_id"] in states
        assert transition["guard"].strip()

        source_actions = {action["id"]: action for action in states[transition["from_state_id"]].get("actions", [])}
        assert transition["action_id"] in source_actions
        assert source_actions[transition["action_id"]]["target_state_id"] == transition["to_state_id"]

    upload_action = _action_by_id(states["document_upload"], "validate_plan_upload")
    assert upload_action["kind"] == "upload"
    assert upload_action["confirmation_required"] is True


def test_upload_validation_messages_are_redacted_and_field_linked() -> None:
    fixture = _load_fixture()
    states = {state["id"]: state for state in fixture["states"]}
    validation_state = states["document_upload_validation"]

    upload_controls = {control["id"]: control for control in validation_state["upload_controls"]}
    assert "plan_pdf_upload" in upload_controls
    assert upload_controls["plan_pdf_upload"]["accepted_file_types"] == ["application/pdf"]

    messages = validation_state["validation_messages"]
    assert {message["id"] for message in messages} == {
        "plans_pdf_required",
        "plans_pdf_type",
        "plans_pdf_size",
    }
    assert {message["field_id"] for message in messages} == {"plan_pdf_upload"}
    assert {message["severity"] for message in messages} == {"error", "warning"}

    blocked_continue = _action_by_id(validation_state, "continue_blocked_after_validation")
    assert blocked_continue["enabled"] is False


def test_all_private_values_are_redacted() -> None:
    fixture = _load_fixture()

    for state in fixture["states"]:
        assert state["url_pattern"].startswith("https://devhub.portlandoregon.gov/")
        assert "[REDACTED]" in state["url_pattern"] or state["id"] == "review_draft"
        for field in state.get("fields", []):
            assert field["value_state"] == REDACTED_VALUE
            selector = field["selector"]
            assert selector["role"].strip()
            assert selector["accessible_name"].strip()
            assert selector.get("label_text") or selector.get("nearby_heading") or selector.get("url_state")

    _assert_no_private_artifacts(fixture)


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        fixture = json.load(fixture_file)
    assert fixture["captured_mode"] == "mocked_redacted_fixture_only"
    return fixture


def _action_by_id(state: dict[str, Any], action_id: str) -> dict[str, Any]:
    for action in state.get("actions", []):
        if action["id"] == action_id:
            return action
    raise AssertionError(f"missing action {action_id}")


def _assert_no_private_artifacts(value: Any, path: str = "$", key: str | None = None) -> None:
    if key in DISALLOWED_KEYS:
        raise AssertionError(f"disallowed private key at {path}: {key}")

    if isinstance(value, dict):
        for child_key, child_value in value.items():
            _assert_no_private_artifacts(child_value, f"{path}.{child_key}", str(child_key))
        return

    if isinstance(value, list):
        for index, child_value in enumerate(value):
            _assert_no_private_artifacts(child_value, f"{path}[{index}]", key)
        return

    if isinstance(value, str):
        for pattern in DISALLOWED_VALUE_PATTERNS:
            if pattern.search(value):
                raise AssertionError(f"private value pattern at {path}: {value!r}")
