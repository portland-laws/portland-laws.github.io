#!/usr/bin/env python3
"""Validate mocked, redacted DevHub workflow snapshot fixtures.

This validator is deterministic and fixture-only. It does not open DevHub,
authenticate, submit, upload, pay, read browser state, or inspect private files.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub-workflows" / "mock_workflow_snapshots.json"

SECRET_PATTERNS = (
    re.compile(r"password", re.IGNORECASE),
    re.compile(r"access[_-]?token", re.IGNORECASE),
    re.compile(r"refresh[_-]?token", re.IGNORECASE),
    re.compile(r"storage[_-]?state", re.IGNORECASE),
    re.compile(r"auth[_-]?state", re.IGNORECASE),
    re.compile(r"trace\.zip", re.IGNORECASE),
    re.compile(r"\.har\b", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\b\d{16}\b"),
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE),
)


def fail(message: str) -> None:
    raise AssertionError(message)


def load_fixture() -> dict[str, Any]:
    try:
        data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{FIXTURE_PATH.relative_to(ROOT)} is not valid JSON: {exc}")
    if not isinstance(data, dict):
        fail(f"{FIXTURE_PATH.relative_to(ROOT)} must contain a JSON object")
    return data


def parse_utc_timestamp(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        fail(f"{field} must be an ISO UTC timestamp ending in Z")
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        fail(f"{field} is not a valid ISO timestamp: {exc}")


def scan_for_private_values(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            scan_for_private_values(key, f"{path}.{key}#key")
            scan_for_private_values(child, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            scan_for_private_values(child, f"{path}[{index}]")
        return
    if isinstance(value, str):
        for pattern in SECRET_PATTERNS:
            if pattern.search(value):
                fail(f"fixture contains private/session-like value at {path}")


def validate_fixture_shape(data: dict[str, Any]) -> None:
    if data.get("fixtureKind") != "devhub_workflow_snapshots":
        fail("fixtureKind must be devhub_workflow_snapshots")
    if data.get("schemaVersion") != 1:
        fail("schemaVersion must be 1")
    parse_utc_timestamp(data.get("generatedAt"), "generatedAt")
    policy = data.get("redactionPolicy")
    if not isinstance(policy, str) or "[REDACTED]" not in policy:
        fail("redactionPolicy must describe [REDACTED] value handling")


def validate_with_contracts(data: dict[str, Any]) -> None:
    sys.path.insert(0, str(ROOT))
    from ppd.contracts.devhub_workflows import edge_from_dict, state_from_dict

    states = data.get("states")
    if not isinstance(states, list) or not states:
        fail("states must be a non-empty array")
    state_models = [state_from_dict(state) for state in states]
    state_ids = {state.id for state in state_models}
    if len(state_ids) != len(state_models):
        fail("state ids must be unique")

    saw_semantic_selector = False
    saw_validation_message = False
    saw_upload_control = False
    saw_redacted_field = False
    saw_confirmation_gated_upload = False
    saw_confirmation_gated_submit = False

    for state in state_models:
        errors = state.validate()
        if errors:
            fail(f"state {state.id} failed validation: {errors}")
        for field in state.fields:
            saw_redacted_field = saw_redacted_field or field.value_state == "[REDACTED]"
            saw_semantic_selector = saw_semantic_selector or bool(
                field.selector.label_text or field.selector.nearby_heading or field.selector.url_state or field.selector.test_id
            )
        saw_validation_message = saw_validation_message or bool(state.validation_messages)
        saw_upload_control = saw_upload_control or bool(state.upload_controls)
        for action in state.actions:
            if action.kind.value == "upload" and action.confirmation_required:
                saw_confirmation_gated_upload = True
            if action.kind.value == "submit" and action.confirmation_required:
                saw_confirmation_gated_submit = True
            if action.target_state_id and action.target_state_id not in state_ids:
                fail(f"action {action.id} targets unknown state {action.target_state_id}")
        for next_state in state.next_states:
            if next_state not in state_ids:
                fail(f"state {state.id} references unknown next state {next_state}")

    edges = data.get("navigationEdges")
    if not isinstance(edges, list) or not edges:
        fail("navigationEdges must be a non-empty array")
    action_ids_by_state = {state.id: {action.id for action in state.actions} for state in state_models}
    for item in edges:
        edge = edge_from_dict(item)
        errors = edge.validate(state_ids)
        if errors:
            fail(f"navigation edge failed validation: {errors}")
        if edge.action_id not in action_ids_by_state.get(edge.from_state_id, set()):
            fail(f"navigation edge references action {edge.action_id} that is not on state {edge.from_state_id}")

    if not saw_semantic_selector:
        fail("fixture must include semantic selector context")
    if not saw_validation_message:
        fail("fixture must include validation messages")
    if not saw_upload_control:
        fail("fixture must include upload controls")
    if not saw_redacted_field:
        fail("fixture must include redacted field values")
    if not saw_confirmation_gated_upload:
        fail("upload actions in fixtures must be confirmation gated")
    if not saw_confirmation_gated_submit:
        fail("submit actions in fixtures must be confirmation gated")


def main() -> int:
    data = load_fixture()
    scan_for_private_values(data)
    validate_fixture_shape(data)
    validate_with_contracts(data)
    print("DevHub workflow snapshot fixtures are redacted and valid.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"DevHub workflow snapshot validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
