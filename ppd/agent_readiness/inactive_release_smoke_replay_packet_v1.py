"""Fixture-first inactive release smoke replay packet v1.

This packet consumes only committed synthetic inactive release decision rows and
post-recompile agent readiness replay rows. It is an offline smoke replay index:
it lists the scenario ids and expected agent-facing outcomes without promoting a
release, opening DevHub, crawling sources, storing private artifacts, or taking
any official action.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PACKET_TYPE = "ppd.inactive_release_smoke_replay_packet.v1"
PACKET_VERSION = "v1"
MODE = "fixture_first_inactive_release_smoke_replay_only"
SOURCE_KIND = "synthetic_inactive_release_decision_rows_and_post_recompile_agent_readiness_replay_rows"
DECISION_ROW_TYPE = "synthetic_inactive_release_decision_packet_row"
READINESS_ROW_TYPE = "synthetic_post_recompile_agent_readiness_replay_row"
EXACT_OFFLINE_VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

REQUIRED_BOUNDARIES = {
    "fixture_first": True,
    "synthetic_rows_only": True,
    "inactive_release_only": True,
    "post_recompile_replay_rows_only": True,
    "release_promotion_enabled": False,
    "live_crawling_enabled": False,
    "devhub_opened": False,
    "browser_automation_enabled": False,
    "private_artifact_storage_enabled": False,
    "official_action_enabled": False,
}

REQUIRED_SCENARIO_KINDS = {
    "missing_information",
    "blocked_action",
    "reversible_draft",
    "exact_confirmation",
    "citation_placeholder",
}

REQUIRED_SCENARIO_REFERENCE_FIELDS = (
    "source_inactive_release_decision_row_id",
    "source_post_recompile_readiness_row_id",
)

REQUIRED_SCENARIO_FIELDS = (
    "expected_missing_information_prompts",
    "expected_blocked_action_outcomes",
    "expected_reversible_draft_outcomes",
    "expected_exact_confirmation_warnings",
    "citation_placeholder_checks",
    "rollback_notes",
    "reviewer_holds",
)

FORBIDDEN_TEXT_MARKERS = (
    "active release enabled",
    "authenticated devhub",
    "browser state",
    "candidate promoted",
    "certification completed",
    "cookie",
    "credential",
    "devhub opened",
    "devhub session",
    "downloaded artifact",
    "downloaded document",
    "fee paid",
    "har file",
    "legal guarantee",
    "legally sufficient",
    "live crawl",
    "live devhub",
    "opened devhub",
    "official action completed",
    "official action performed",
    "payment completed",
    "permit approval guaranteed",
    "permit outcome guaranteed",
    "permit will be approved",
    "permit will be issued",
    "private artifact",
    "private file",
    "raw crawl",
    "raw download",
    "raw html",
    "raw pdf",
    "release activated",
    "release promoted",
    "release promotion completed",
    "screenshot",
    "session state",
    "storage state",
    "submitted permit",
    "trace file",
    "uploaded plans",
)

FORBIDDEN_TEXT_RE = re.compile(
    r"\b(approval is guaranteed|guaranteed approval|guaranteed issuance|guaranteed permit|"
    r"legal advice|legal conclusion|officially complete|official completion|promotion succeeded|"
    r"release promotion succeeded|release state updated|successfully promoted|will pass plan review)\b",
    re.IGNORECASE,
)

FORBIDDEN_KEY_MARKERS = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "downloaded_artifact",
    "downloaded_document",
    "har",
    "private_artifact",
    "raw_artifact",
    "raw_body",
    "raw_crawl",
    "raw_download",
    "raw_html",
    "raw_pdf",
    "screenshot",
    "session_state",
    "storage_state",
    "trace",
)

FORBIDDEN_TRUE_FLAGS = (
    "active_agent_state_mutation",
    "active_artifact_mutation",
    "active_fixture_mutation",
    "active_guardrail_mutation",
    "active_process_mutation",
    "active_prompt_mutation",
    "active_release_enabled",
    "active_release_state_mutation",
    "active_surface_registry_mutation",
    "agent_state_write_enabled",
    "browser_automation_enabled",
    "devhub_opened",
    "fixture_promotion_enabled",
    "guardrail_mutation_enabled",
    "live_crawling_enabled",
    "official_action_enabled",
    "private_artifact_storage_enabled",
    "prompt_mutation_enabled",
    "release_promotion_enabled",
    "release_state_update_enabled",
    "surface_registry_mutation_enabled",
    "surface_registry_write_enabled",
)

ACTIVE_MUTATION_KEY_RE = re.compile(
    r"(^|_)(active_)?(agent_state|artifact|fixture|guardrail|process|prompt|release_state|surface_registry)_"
    r"(mutation|mutating|update|write|promotion)(_|$)",
    re.IGNORECASE,
)


class InactiveReleaseSmokeReplayPacketV1Error(ValueError):
    """Raised when the inactive smoke replay packet is not fixture-safe."""

    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("invalid inactive release smoke replay packet v1: " + "; ".join(self.errors))


def load_source_rows(path: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping):
        raise ValueError("source fixture must be an object")
    decision_rows = _dict_rows(loaded.get("inactive_release_decision_packet_rows"), "inactive_release_decision_packet_rows")
    readiness_rows = _dict_rows(loaded.get("post_recompile_agent_readiness_replay_rows"), "post_recompile_agent_readiness_replay_rows")
    return decision_rows, readiness_rows


def build_packet_from_fixture(path: str | Path) -> dict[str, Any]:
    decision_rows, readiness_rows = load_source_rows(path)
    return build_packet(decision_rows, readiness_rows)


def load_inactive_release_smoke_replay_packet_v1(path: str | Path) -> dict[str, Any]:
    packet = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(packet, dict):
        raise InactiveReleaseSmokeReplayPacketV1Error(["packet must be an object"])
    assert_valid_inactive_release_smoke_replay_packet_v1(packet)
    return packet


def build_packet(
    decision_rows: Sequence[Mapping[str, Any]],
    readiness_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    decisions = _validated_decision_rows(decision_rows)
    readiness_by_key = _validated_readiness_rows(readiness_rows)
    scenarios = [_scenario_from_decision(row, readiness_by_key[str(row["scenario_key"])]) for row in decisions]
    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "inactive-release-smoke-replay-packet-v1",
        "mode": MODE,
        "source_kind": SOURCE_KIND,
        "boundaries": dict(REQUIRED_BOUNDARIES),
        "consumed_inactive_release_decision_row_ids": [str(row["decision_row_id"]) for row in decisions],
        "consumed_post_recompile_readiness_row_ids": [str(readiness_by_key[str(row["scenario_key"])]["readiness_row_id"]) for row in decisions],
        "smoke_scenario_ids": [scenario["smoke_scenario_id"] for scenario in scenarios],
        "smoke_scenarios": scenarios,
        "exact_offline_validation_commands": EXACT_OFFLINE_VALIDATION_COMMANDS,
        "validation_commands": EXACT_OFFLINE_VALIDATION_COMMANDS,
    }
    assert_valid_inactive_release_smoke_replay_packet_v1(packet)
    return packet


def validate_inactive_release_smoke_replay_packet_v1(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        errors.append("packet_version must be v1")
    if packet.get("mode") != MODE:
        errors.append(f"mode must be {MODE}")
    if packet.get("source_kind") != SOURCE_KIND:
        errors.append(f"source_kind must be {SOURCE_KIND}")
    if packet.get("boundaries") != REQUIRED_BOUNDARIES:
        errors.append("boundaries must exactly keep the replay fixture-only, inactive, offline, non-mutating, and non-official")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append("exact_offline_validation_commands must contain only the daemon self-test command")
    if packet.get("validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append("validation_commands must contain only the daemon self-test command")

    scenario_ids = _string_list(packet.get("smoke_scenario_ids"))
    if not scenario_ids:
        errors.append("smoke_scenario_ids must be a non-empty list of text")
    scenarios = packet.get("smoke_scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        errors.append("smoke_scenarios must be a non-empty list")
        scenarios = []
    else:
        actual_ids = [scenario.get("smoke_scenario_id") for scenario in scenarios if isinstance(scenario, Mapping)]
        if scenario_ids != actual_ids:
            errors.append("smoke_scenario_ids must list smoke_scenarios in order")
    _validate_scenarios(scenarios, errors)
    _validate_consumed_rows(packet, scenarios, errors)
    _scan_for_forbidden_payload(packet, "$", errors)
    return sorted(set(errors))


def assert_valid_inactive_release_smoke_replay_packet_v1(packet: Mapping[str, Any]) -> None:
    errors = validate_inactive_release_smoke_replay_packet_v1(packet)
    if errors:
        raise InactiveReleaseSmokeReplayPacketV1Error(errors)


def _validated_decision_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    if not rows:
        raise ValueError("at least one synthetic inactive release decision row is required")
    validated: list[Mapping[str, Any]] = []
    for index, row in enumerate(rows):
        prefix = f"decision row {index}"
        if row.get("row_type") != DECISION_ROW_TYPE:
            raise ValueError(f"{prefix} must have row_type {DECISION_ROW_TYPE}")
        if row.get("synthetic") is not True:
            raise ValueError(f"{prefix} must be synthetic")
        if row.get("release_state") != "inactive":
            raise ValueError(f"{prefix} must remain inactive")
        if row.get("promotion_enabled") is not False:
            raise ValueError(f"{prefix} must keep promotion_enabled false")
        for field in ("decision_row_id", "scenario_key", "scenario_kind", "decision_outcome", "reviewer_hold"):
            if not _text(row.get(field)):
                raise ValueError(f"{prefix}.{field} must be non-empty")
        if not _string_list(row.get("citation_placeholder_ids")):
            raise ValueError(f"{prefix}.citation_placeholder_ids must be non-empty")
        validated.append(row)
    return sorted(validated, key=lambda row: str(row["decision_row_id"]))


def _validated_readiness_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    if not rows:
        raise ValueError("at least one synthetic post-recompile readiness replay row is required")
    by_key: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(rows):
        prefix = f"readiness row {index}"
        if row.get("row_type") != READINESS_ROW_TYPE:
            raise ValueError(f"{prefix} must have row_type {READINESS_ROW_TYPE}")
        if row.get("synthetic") is not True:
            raise ValueError(f"{prefix} must be synthetic")
        if row.get("offline_only") is not True:
            raise ValueError(f"{prefix} must be offline_only")
        for field in ("readiness_row_id", "scenario_key") + REQUIRED_SCENARIO_FIELDS:
            value = row.get(field)
            if field in REQUIRED_SCENARIO_FIELDS:
                if not _string_list(value):
                    raise ValueError(f"{prefix}.{field} must be a non-empty list of text")
            elif not _text(value):
                raise ValueError(f"{prefix}.{field} must be non-empty")
        key = str(row["scenario_key"])
        if key in by_key:
            raise ValueError(f"duplicate readiness scenario_key {key}")
        by_key[key] = row
    return by_key


def _scenario_from_decision(decision: Mapping[str, Any], readiness: Mapping[str, Any]) -> dict[str, Any]:
    scenario_key = str(decision["scenario_key"])
    return {
        "smoke_scenario_id": f"smoke-{scenario_key}",
        "scenario_key": scenario_key,
        "scenario_kind": str(decision["scenario_kind"]),
        "source_inactive_release_decision_row_id": str(decision["decision_row_id"]),
        "source_post_recompile_readiness_row_id": str(readiness["readiness_row_id"]),
        "expected_decision_outcome": str(decision["decision_outcome"]),
        "expected_missing_information_prompts": _string_list(readiness.get("expected_missing_information_prompts")),
        "expected_blocked_action_outcomes": _string_list(readiness.get("expected_blocked_action_outcomes")),
        "expected_reversible_draft_outcomes": _string_list(readiness.get("expected_reversible_draft_outcomes")),
        "expected_exact_confirmation_warnings": _string_list(readiness.get("expected_exact_confirmation_warnings")),
        "citation_placeholder_checks": _string_list(readiness.get("citation_placeholder_checks")),
        "rollback_notes": _string_list(readiness.get("rollback_notes")),
        "reviewer_holds": [str(decision["reviewer_hold"])] + _string_list(readiness.get("reviewer_holds")),
        "citation_placeholder_ids": sorted(set(_string_list(decision.get("citation_placeholder_ids")) + _string_list(readiness.get("citation_placeholder_ids")))),
        "offline_validation_commands": EXACT_OFFLINE_VALIDATION_COMMANDS,
    }


def _validate_scenarios(scenarios: Sequence[Any], errors: list[str]) -> None:
    seen_kinds: set[str] = set()
    seen_ids: set[str] = set()
    for index, scenario in enumerate(scenarios):
        prefix = f"smoke_scenarios[{index}]"
        if not isinstance(scenario, Mapping):
            errors.append(f"{prefix} must be an object")
            continue
        scenario_id = scenario.get("smoke_scenario_id")
        if not _text(scenario_id):
            errors.append(f"{prefix}.smoke_scenario_id must be non-empty")
        elif str(scenario_id) in seen_ids:
            errors.append(f"{prefix}.smoke_scenario_id must be unique")
        else:
            seen_ids.add(str(scenario_id))
        kind = scenario.get("scenario_kind")
        if kind not in REQUIRED_SCENARIO_KINDS:
            errors.append(f"{prefix}.scenario_kind must be one of the required smoke scenario kinds")
        else:
            seen_kinds.add(str(kind))
        for field in REQUIRED_SCENARIO_REFERENCE_FIELDS:
            if not _text(scenario.get(field)):
                errors.append(f"{prefix}.{field} must be non-empty")
        for field in REQUIRED_SCENARIO_FIELDS:
            if not _string_list(scenario.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty list of text")
        if not _string_list(scenario.get("citation_placeholder_ids")):
            errors.append(f"{prefix}.citation_placeholder_ids must be non-empty")
        if scenario.get("offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
            errors.append(f"{prefix}.offline_validation_commands must contain only the daemon self-test command")
    missing = REQUIRED_SCENARIO_KINDS - seen_kinds
    if missing:
        errors.append("missing required smoke scenario kinds: " + ", ".join(sorted(missing)))


def _validate_consumed_rows(packet: Mapping[str, Any], scenarios: Sequence[Any], errors: list[str]) -> None:
    decision_ids = _string_list(packet.get("consumed_inactive_release_decision_row_ids"))
    readiness_ids = _string_list(packet.get("consumed_post_recompile_readiness_row_ids"))
    if not decision_ids:
        errors.append("consumed_inactive_release_decision_row_ids must be non-empty")
    if not readiness_ids:
        errors.append("consumed_post_recompile_readiness_row_ids must be non-empty")
    scenario_decisions = [scenario.get("source_inactive_release_decision_row_id") for scenario in scenarios if isinstance(scenario, Mapping)]
    scenario_readiness = [scenario.get("source_post_recompile_readiness_row_id") for scenario in scenarios if isinstance(scenario, Mapping)]
    if decision_ids != scenario_decisions:
        errors.append("consumed_inactive_release_decision_row_ids must match scenario source decision rows in order")
    if readiness_ids != scenario_readiness:
        errors.append("consumed_post_recompile_readiness_row_ids must match scenario source readiness rows in order")


def _scan_for_forbidden_payload(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            child_path = f"{path}.{key}"
            if normalized_key in FORBIDDEN_TRUE_FLAGS and child is True:
                errors.append(f"forbidden active/live/private/official true flag at {child_path}")
            if ACTIVE_MUTATION_KEY_RE.search(normalized_key) and child is True:
                errors.append(f"forbidden active mutation flag at {child_path}")
            if any(marker in normalized_key for marker in FORBIDDEN_KEY_MARKERS) and child not in (None, False, "", [], {}):
                errors.append(f"forbidden private/session/browser/raw artifact field at {child_path}")
            _scan_for_forbidden_payload(child, child_path, errors)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_payload(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        lowered = value.lower()
        for marker in FORBIDDEN_TEXT_MARKERS:
            if marker in lowered:
                errors.append(f"forbidden live/private/official/release/legal guarantee claim at {path}: {marker}")
        if FORBIDDEN_TEXT_RE.search(value):
            errors.append(f"forbidden live/private/official/release/legal guarantee claim at {path}")


def _dict_rows(value: Any, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"{field}[{index}] must be an object")
        rows.append(row)
    return rows


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
