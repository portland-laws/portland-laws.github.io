"""Fixture-first public refresh reviewer bundle packet v1.

Consumes only synthetic public-refresh ProcessModel delta plan rows,
guardrail recompile plan rows, and agent gap-analysis replay rows. The packet is
reviewer-ready but offline-only: it records dispositions, signoff placeholders,
dependency sequencing, release-blocker notes, rollback checkpoints, and exact
validation commands without live crawling, live extraction, downloads, DevHub
access, release activation, active artifact mutation, or official actions.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

PACKET_TYPE = "ppd.public_refresh_reviewer_bundle_packet.v1"
PACKET_VERSION = "v1"
EXECUTION_MODE = "fixture_first_offline_reviewer_bundle_only"

EXACT_OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/public_refresh_reviewer_bundle_packet_v1.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_public_refresh_reviewer_bundle_packet_v1.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_refresh_reviewer_bundle_packet_v1.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

FALSE_BOUNDARY_FLAGS: tuple[str, ...] = (
    "live_crawl",
    "live_extraction",
    "documents_downloaded",
    "devhub_opened",
    "release_activation",
    "active_artifacts_mutated",
    "official_actions_performed",
    "raw_outputs_stored",
)

REQUIRED_BLOCKED_ACTION_CLASSES = frozenset(
    {
        "upload",
        "submit",
        "certify",
        "pay",
        "schedule",
        "cancel",
        "official_record_change",
    }
)

PRIVATE_OR_RUNTIME_KEY_MARKERS = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "downloaded_document",
    "har",
    "local_private_path",
    "password",
    "raw_body",
    "raw_crawl_output",
    "raw_download",
    "raw_output",
    "screenshot",
    "session_state",
    "storage_state",
    "trace",
    "warc_path",
)

FORBIDDEN_TEXT_MARKERS = (
    "active artifact mutated",
    "application submitted",
    "certification completed",
    "devhub opened",
    "document downloaded",
    "fee paid",
    "inspection scheduled",
    "live crawl completed",
    "live extraction completed",
    "official action completed",
    "raw crawl output",
    "release activated",
    "uploaded correction",
)


def load_public_refresh_reviewer_bundle_fixture_v1(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("public refresh reviewer bundle fixture must be a JSON object")
    return loaded


def build_public_refresh_reviewer_bundle_packet_v1_from_file(path: str | Path) -> dict[str, Any]:
    return build_public_refresh_reviewer_bundle_packet_v1(load_public_refresh_reviewer_bundle_fixture_v1(path))


def build_public_refresh_reviewer_bundle_packet_v1(fixture: Mapping[str, Any]) -> dict[str, Any]:
    _reject_private_runtime_or_forbidden_claims(fixture)
    _validate_fixture_boundaries(fixture)
    process_rows = _validated_rows(
        fixture.get("synthetic_process_model_delta_plan_rows"),
        "synthetic_process_model_delta_plan_rows",
        "synthetic_process_model_delta_plan_row",
    )
    guardrail_rows = _validated_rows(
        fixture.get("synthetic_guardrail_recompile_plan_rows"),
        "synthetic_guardrail_recompile_plan_rows",
        "synthetic_guardrail_recompile_plan_row",
    )
    agent_rows = _validated_rows(
        fixture.get("synthetic_agent_gap_analysis_replay_rows"),
        "synthetic_agent_gap_analysis_replay_rows",
        "synthetic_agent_gap_analysis_replay_row",
    )

    bundle_rows = []
    for index, process_row in enumerate(process_rows, start=1):
        process_model_id = _required_text(process_row, "process_model_id")
        guardrail_row = _match_row(guardrail_rows, "process_model_id", process_model_id, "guardrail recompile plan")
        agent_row = _match_row(agent_rows, "process_model_id", process_model_id, "agent gap-analysis replay")
        bundle_rows.append(_bundle_disposition(index, process_row, guardrail_row, agent_row))

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "public-refresh-reviewer-bundle-packet-v1",
        "execution_mode": EXECUTION_MODE,
        "input_contract": "synthetic_process_model_delta_guardrail_recompile_and_agent_gap_analysis_replay_rows_only",
        "fixture_first": True,
        "boundary_flags": {flag: False for flag in FALSE_BOUNDARY_FLAGS},
        "source_row_refs": {
            "process_model_delta_plan_row_ids": [_required_text(row, "row_id") for row in process_rows],
            "guardrail_recompile_plan_row_ids": [_required_text(row, "row_id") for row in guardrail_rows],
            "agent_gap_analysis_replay_row_ids": [_required_text(row, "row_id") for row in agent_rows],
        },
        "reviewer_ready_dispositions": bundle_rows,
        "owner_signoff_placeholders": [_owner_signoff(row) for row in bundle_rows],
        "dependency_sequencing": [_dependency_sequence(row) for row in bundle_rows],
        "release_blocker_notes": [_release_blocker_note(row) for row in bundle_rows],
        "rollback_checkpoints": [_rollback_checkpoint(row) for row in bundle_rows],
        "prohibited_actions": [
            "live_crawling",
            "live_extraction",
            "document_download",
            "devhub_access",
            "release_activation",
            "active_artifact_mutation",
            "official_action",
        ],
        "exact_offline_validation_commands": [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS],
    }
    assert_valid_public_refresh_reviewer_bundle_packet_v1(packet)
    return packet


def assert_valid_public_refresh_reviewer_bundle_packet_v1(packet: Mapping[str, Any]) -> None:
    problems = validate_public_refresh_reviewer_bundle_packet_v1(packet)
    if problems:
        raise ValueError("invalid public refresh reviewer bundle packet v1: " + "; ".join(problems))


def validate_public_refresh_reviewer_bundle_packet_v1(packet: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    if not isinstance(packet, Mapping):
        return ["packet must be an object"]
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v1")
    if packet.get("execution_mode") != EXECUTION_MODE:
        problems.append(f"execution_mode must be {EXECUTION_MODE}")
    if packet.get("fixture_first") is not True:
        problems.append("fixture_first must be true")
    if packet.get("boundary_flags") != {flag: False for flag in FALSE_BOUNDARY_FLAGS}:
        problems.append("boundary_flags must preserve offline no-mutation boundaries")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("exact_offline_validation_commands must exactly match the reviewer bundle command list")

    dispositions = _mapping_sequence(packet.get("reviewer_ready_dispositions"))
    if not dispositions:
        problems.append("reviewer_ready_dispositions must be a non-empty list")
    for index, row in enumerate(dispositions):
        prefix = f"reviewer_ready_dispositions[{index}]"
        for section in ("requirement_disposition", "process_disposition", "guardrail_disposition", "agent_impact_disposition"):
            if not isinstance(row.get(section), Mapping):
                problems.append(f"{prefix}.{section} must be an object")
        blocked_classes = set(_text_sequence(row.get("blocked_action_classes")))
        missing = REQUIRED_BLOCKED_ACTION_CLASSES - blocked_classes
        if missing:
            problems.append(f"{prefix}.blocked_action_classes missing required blockers: {sorted(missing)}")

    disposition_ids = {_required_text(row, "bundle_disposition_id") for row in dispositions if isinstance(row, Mapping) and row.get("bundle_disposition_id")}
    _validate_refs(packet.get("owner_signoff_placeholders"), disposition_ids, "owner_signoff_placeholders", problems)
    _validate_refs(packet.get("dependency_sequencing"), disposition_ids, "dependency_sequencing", problems)
    _validate_refs(packet.get("release_blocker_notes"), disposition_ids, "release_blocker_notes", problems)
    _validate_refs(packet.get("rollback_checkpoints"), disposition_ids, "rollback_checkpoints", problems)
    _reject_private_runtime_or_forbidden_claims(packet, problems)
    return problems


def _validate_fixture_boundaries(fixture: Mapping[str, Any]) -> None:
    if fixture.get("fixture_first") is not True:
        raise ValueError("fixture_first must be true")
    for flag in FALSE_BOUNDARY_FLAGS:
        if fixture.get(flag) is not False:
            raise ValueError(f"{flag} must be false")


def _validated_rows(value: Any, field_name: str, row_type: str) -> list[Mapping[str, Any]]:
    rows = _mapping_sequence(value)
    if not rows:
        raise ValueError(f"{field_name} must be a non-empty list")
    seen: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"{field_name}[{index}]"
        if row.get("row_type") != row_type:
            raise ValueError(f"{prefix}.row_type must be {row_type}")
        if row.get("synthetic") is not True:
            raise ValueError(f"{prefix} must be synthetic")
        if row.get("state") != "inactive":
            raise ValueError(f"{prefix}.state must be inactive")
        row_id = _required_text(row, "row_id")
        if row_id in seen:
            raise ValueError(f"{prefix}.row_id must be unique")
        seen.add(row_id)
    return rows


def _bundle_disposition(
    index: int,
    process_row: Mapping[str, Any],
    guardrail_row: Mapping[str, Any],
    agent_row: Mapping[str, Any],
) -> dict[str, Any]:
    process_model_id = _required_text(process_row, "process_model_id")
    blocked_action_classes = sorted(set(_text_sequence(agent_row.get("blocked_action_classes"))))
    return {
        "bundle_disposition_id": f"public-refresh-reviewer-bundle-v1-{index:03d}",
        "process_model_id": process_model_id,
        "source_rows": {
            "process_model_delta_plan_row_id": _required_text(process_row, "row_id"),
            "guardrail_recompile_plan_row_id": _required_text(guardrail_row, "row_id"),
            "agent_gap_analysis_replay_row_id": _required_text(agent_row, "row_id"),
        },
        "requirement_disposition": {
            "status": _required_text(process_row, "requirement_disposition"),
            "requirement_refs": _text_sequence(process_row.get("requirement_refs")),
            "reviewer_action": "review synthetic requirement disposition before any public refresh promotion",
        },
        "process_disposition": {
            "status": _required_text(process_row, "process_disposition"),
            "process_stage": _required_text(process_row, "process_stage"),
            "reviewer_action": "review inactive ProcessModel delta sequencing only",
        },
        "guardrail_disposition": {
            "status": _required_text(guardrail_row, "guardrail_disposition"),
            "guardrail_bundle_id": _required_text(guardrail_row, "guardrail_bundle_id"),
            "reviewer_action": "review inactive GuardrailBundle recompile impacts only",
        },
        "agent_impact_disposition": {
            "status": _required_text(agent_row, "agent_impact_disposition"),
            "replay_id": _required_text(agent_row, "replay_id"),
            "reviewer_action": "review UserGapAnalysis replay expectations without active agent mutation",
        },
        "blocked_action_classes": blocked_action_classes,
        "release_blocker_status": _required_text(agent_row, "release_blocker_status"),
        "owner": _required_text(process_row, "owner"),
    }


def _owner_signoff(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "bundle_disposition_ref": _required_text(row, "bundle_disposition_id"),
        "owner": _required_text(row, "owner"),
        "signoff_status": "placeholder_pending_owner_review",
        "signed_off": False,
    }


def _dependency_sequence(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "bundle_disposition_ref": _required_text(row, "bundle_disposition_id"),
        "ordered_steps": [
            "review requirement disposition",
            "review inactive process delta disposition",
            "review inactive guardrail recompile disposition",
            "review agent gap-analysis replay impact",
            "resolve release blockers",
            "confirm rollback checkpoint",
            "collect owner signoff placeholder",
        ],
    }


def _release_blocker_note(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "bundle_disposition_ref": _required_text(row, "bundle_disposition_id"),
        "release_blocker_status": _required_text(row, "release_blocker_status"),
        "blocked_action_classes": _text_sequence(row.get("blocked_action_classes")),
        "note": "Release remains blocked until reviewer disposition and owner signoff are complete; this packet does not activate a release or mutate active artifacts.",
    }


def _rollback_checkpoint(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "bundle_disposition_ref": _required_text(row, "bundle_disposition_id"),
        "checkpoint_id": f"rollback-{_required_text(row, 'bundle_disposition_id')}",
        "rollback_action": "discard this offline reviewer bundle and its synthetic fixture rows",
        "active_artifact_effect": "none",
    }


def _match_row(rows: Sequence[Mapping[str, Any]], key: str, value: str, label: str) -> Mapping[str, Any]:
    matches = [row for row in rows if row.get(key) == value]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one {label} row for {key}={value}")
    return matches[0]


def _validate_refs(value: Any, disposition_ids: set[str], section: str, problems: list[str]) -> None:
    rows = _mapping_sequence(value)
    if not rows:
        problems.append(f"{section} must be a non-empty list")
        return
    refs = {_required_text(row, "bundle_disposition_ref") for row in rows if isinstance(row, Mapping) and row.get("bundle_disposition_ref")}
    if refs != disposition_ids:
        problems.append(f"{section} must reference every reviewer disposition exactly once")


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text_sequence(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value


def _reject_private_runtime_or_forbidden_claims(value: Any, problems: list[str] | None = None, path: str = "$") -> None:
    local_problems: list[str] = [] if problems is None else problems
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key).lower()
            if any(marker in key_text for marker in PRIVATE_OR_RUNTIME_KEY_MARKERS):
                local_problems.append(f"private or runtime key is not allowed at {path}.{key}")
            _reject_private_runtime_or_forbidden_claims(nested, local_problems, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_private_runtime_or_forbidden_claims(nested, local_problems, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        for marker in FORBIDDEN_TEXT_MARKERS:
            if marker in lowered:
                local_problems.append(f"forbidden live, private, mutating, or official-action claim at {path}: {marker}")
    if problems is None and local_problems:
        raise ValueError("; ".join(local_problems))
