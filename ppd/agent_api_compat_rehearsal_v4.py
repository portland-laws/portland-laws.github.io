"""Fixture-first validation for agent API compatibility rehearsal v4."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_TOP_LEVEL_LISTS = (
    "monitoring_rehearsal_references",
    "synthetic_agent_request_fixtures",
    "expected_api_response_rows",
    "source_citation_payloads",
    "validation_commands",
)

REQUIRED_RESPONSE_KINDS = (
    "missing_fact",
    "stale_evidence",
    "reversible_draft_only",
    "manual_handoff",
    "refusal_explanation",
)

PRIVATE_ARTIFACT_MARKERS = (
    "auth",
    "authorization",
    "cookie",
    "password",
    "private",
    "raw_crawl",
    "session",
    "token",
    "trace",
)

ACTIVE_MUTATION_FLAGS = (
    "active_mutation",
    "cancel",
    "certify",
    "commit",
    "create_account",
    "live_submit",
    "mutates_live_systems",
    "pay",
    "payment",
    "submit",
    "upload",
)

OFFICIAL_ACTION_FLAGS = (
    "agent_can_file_permit",
    "autonomous_official_action",
    "official_action",
    "permit_submission",
)

GUARANTEE_FLAGS = (
    "guarantees_approval",
    "legal_guarantee",
    "permitting_guarantee",
)


def load_rehearsal_fixture(path: str | Path) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("rehearsal fixture must be a JSON object")
    return data


def validate_agent_api_compatibility_rehearsal_v4(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_TOP_LEVEL_LISTS:
        value = payload.get(key)
        if not isinstance(value, list) or not value:
            errors.append(f"missing non-empty {key}")

    commands = payload.get("validation_commands")
    if isinstance(commands, list) and commands:
        for index, command in enumerate(commands):
            if not isinstance(command, list) or not command or not all(isinstance(part, str) and part for part in command):
                errors.append(f"validation_commands[{index}] must be a non-empty list of strings")

    response_kinds = _response_kinds(payload)
    for kind in REQUIRED_RESPONSE_KINDS:
        if kind not in response_kinds:
            errors.append(f"missing {kind} response handling")

    _reject_prohibited_content(payload, errors)
    return errors


def assert_valid_agent_api_compatibility_rehearsal_v4(payload: dict[str, Any]) -> None:
    errors = validate_agent_api_compatibility_rehearsal_v4(payload)
    if errors:
        raise ValueError("agent API compatibility rehearsal v4 validation failed: " + "; ".join(errors))


def _response_kinds(payload: dict[str, Any]) -> set[str]:
    found: set[str] = set()
    candidates = payload.get("response_scenarios", payload.get("responses", []))
    if isinstance(candidates, dict):
        for key, value in candidates.items():
            if value:
                found.add(str(key))
        return found
    if isinstance(candidates, list):
        for item in candidates:
            if isinstance(item, dict):
                kind = item.get("kind") or item.get("id") or item.get("name")
                if kind and item.get("expected_response"):
                    found.add(str(kind))
    return found


def _reject_prohibited_content(value: Any, errors: list[str], path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(marker in normalized for marker in PRIVATE_ARTIFACT_MARKERS):
                errors.append(f"private/session/auth artifact is not allowed at {path}.{key}")
            if normalized in ACTIVE_MUTATION_FLAGS and child is True:
                errors.append(f"active mutation flag is not allowed at {path}.{key}")
            if normalized in OFFICIAL_ACTION_FLAGS and child is True:
                errors.append(f"autonomous official-action claim is not allowed at {path}.{key}")
            if normalized in GUARANTEE_FLAGS and child is True:
                errors.append(f"legal or permitting guarantee is not allowed at {path}.{key}")
            _reject_prohibited_content(child, errors, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_prohibited_content(child, errors, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if "guaranteed approval" in lowered or "permit will be approved" in lowered:
            errors.append(f"legal or permitting guarantee is not allowed at {path}")
        if "i submitted" in lowered or "i filed the permit" in lowered:
            errors.append(f"autonomous official-action claim is not allowed at {path}")


if __name__ == "__main__":
    import sys

    for fixture_path in sys.argv[1:]:
        assert_valid_agent_api_compatibility_rehearsal_v4(load_rehearsal_fixture(fixture_path))
