"""Fixture-first PP&D post-decision smoke replay v3.

This module intentionally consumes only committed read-only fixtures. It does not
open DevHub, authenticate, fill forms, upload files, submit official actions, or
write crawl/session artifacts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FORBIDDEN_PACKET_KEYS = {
    "auth_state",
    "session",
    "cookies",
    "local_storage",
    "screenshots",
    "traces",
    "har",
    "private_values",
    "raw_crawl_output",
}

FORBIDDEN_ACTION_TYPES = {
    "captcha",
    "mfa",
    "account_creation",
    "payment",
    "submission",
    "certification",
    "cancellation",
    "upload",
    "form_fill",
    "schedule",
    "official_action",
}

EXPECTED_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/replay/post_decision_smoke_replay_v3.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_post_decision_smoke_replay_v3.py"],
]


@dataclass(frozen=True)
class ReplayFinding:
    check: str
    ok: bool
    detail: str


def load_json_fixture(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"fixture must contain a JSON object: {path}")
    return value


def classify_action(action: dict[str, Any]) -> str:
    action_type = str(action.get("type", "")).strip()
    if action_type in FORBIDDEN_ACTION_TYPES:
        return "forbidden_mutating_or_official_action"
    if action.get("manual_handoff_required") is True:
        return "manual_handoff_gate"
    if action.get("reviewer_hold") is True:
        return "reviewer_hold_gate"
    if action.get("requires_exact_confirmation") is True:
        return "exact_confirmation_gate"
    if action_type == "read_only_route_lookup":
        return "read_only_route_lookup"
    return "offline_non_mutating_check"


def _surface_routes(surface_map: dict[str, Any]) -> dict[str, dict[str, Any]]:
    routes = surface_map.get("routes", [])
    if not isinstance(routes, list):
        raise ValueError("surface map routes must be a list")
    result: dict[str, dict[str, Any]] = {}
    for route in routes:
        if not isinstance(route, dict):
            raise ValueError("surface map route entries must be objects")
        route_id = route.get("id")
        if not isinstance(route_id, str) or not route_id:
            raise ValueError("surface map route entries must have string ids")
        result[route_id] = route
    return result


def replay_post_decision_smoke_v3(
    decision_packet: dict[str, Any], surface_map: dict[str, Any]
) -> dict[str, Any]:
    findings: list[ReplayFinding] = []

    packet_version = decision_packet.get("packet_version")
    findings.append(
        ReplayFinding(
            "decision_packet_v3",
            packet_version == "devhub_read_only_release_decision_packet_v3",
            f"packet_version={packet_version!r}",
        )
    )

    packet_mode = decision_packet.get("mode")
    findings.append(
        ReplayFinding(
            "fixture_first_mode",
            packet_mode == "fixture_only_read_only",
            f"mode={packet_mode!r}",
        )
    )

    present_forbidden_keys = sorted(FORBIDDEN_PACKET_KEYS.intersection(decision_packet))
    findings.append(
        ReplayFinding(
            "no_private_or_session_artifacts",
            not present_forbidden_keys,
            "present=" + ",".join(present_forbidden_keys),
        )
    )

    routes = _surface_routes(surface_map)
    requested_route_ids = decision_packet.get("route_lookup_ids", [])
    if not isinstance(requested_route_ids, list):
        raise ValueError("route_lookup_ids must be a list")
    missing_routes = [route_id for route_id in requested_route_ids if route_id not in routes]
    non_read_only_routes = [
        route_id
        for route_id in requested_route_ids
        if route_id in routes and routes[route_id].get("read_only") is not True
    ]
    findings.append(
        ReplayFinding(
            "read_only_route_lookup",
            not missing_routes and not non_read_only_routes,
            f"missing={missing_routes!r}; non_read_only={non_read_only_routes!r}",
        )
    )

    actions = decision_packet.get("actions", [])
    if not isinstance(actions, list):
        raise ValueError("actions must be a list")
    classifications = [classify_action(action) for action in actions if isinstance(action, dict)]
    findings.append(
        ReplayFinding(
            "action_classification",
            len(classifications) == len(actions)
            and "forbidden_mutating_or_official_action" not in classifications,
            "classifications=" + ",".join(classifications),
        )
    )
    findings.append(
        ReplayFinding(
            "exact_confirmation_gates",
            "exact_confirmation_gate" in classifications,
            "required_classification=exact_confirmation_gate",
        )
    )
    findings.append(
        ReplayFinding(
            "manual_handoff_gates",
            "manual_handoff_gate" in classifications,
            "required_classification=manual_handoff_gate",
        )
    )
    findings.append(
        ReplayFinding(
            "reviewer_holds",
            "reviewer_hold_gate" in classifications,
            "required_classification=reviewer_hold_gate",
        )
    )

    rollback = decision_packet.get("rollback_readiness", {})
    rollback_ready = isinstance(rollback, dict) and rollback.get("ready") is True
    findings.append(
        ReplayFinding(
            "rollback_readiness",
            rollback_ready and rollback.get("requires_live_reversal") is False,
            f"rollback={rollback!r}",
        )
    )

    validation_commands = decision_packet.get("offline_validation_commands")
    findings.append(
        ReplayFinding(
            "exact_offline_validation_commands",
            validation_commands == EXPECTED_OFFLINE_VALIDATION_COMMANDS,
            f"commands={validation_commands!r}",
        )
    )

    return {
        "schema": "ppd_post_decision_smoke_replay_v3_report",
        "ok": all(finding.ok for finding in findings),
        "findings": [finding.__dict__ for finding in findings],
    }


def replay_from_fixture_paths(packet_path: Path, surface_map_path: Path) -> dict[str, Any]:
    return replay_post_decision_smoke_v3(
        load_json_fixture(packet_path), load_json_fixture(surface_map_path)
    )
