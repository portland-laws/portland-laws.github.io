"""Fixture-first public refresh preflight packet v5.

This packet consumes only next public refresh seed packet v5 fixtures. It assembles
and validates offline preflight review material and never crawls live sites,
downloads documents, stores source bodies, opens DevHub, or makes legal or
permitting guarantees.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from ppd.public_refresh.next_public_refresh_seed_packet_v5 import (
    PACKET_VERSION as SEED_PACKET_VERSION,
    assert_valid_packet,
    load_packet as load_seed_packet,
)

PACKET_VERSION = "public-refresh-preflight-packet-v5"
MODE = "fixture-first-offline-public-refresh-preflight"

VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/public_refresh/public_refresh_preflight_packet_v5.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_refresh_preflight_packet_v5.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

PUBLIC_HOST_ALLOWLIST = [
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
]

NO_HOLD_KEY = "hold-none"

REQUIRED_TOP_LEVEL_FIELDS = (
    "packet_version",
    "mode",
    "input_packet_version",
    "offline_only",
    "source_fixture_policy",
    "allowlist_checks",
    "robots_policy_preflight_placeholders",
    "processor_handoff_readiness",
    "raw_body_persistence_refusal",
    "rate_limit_notes",
    "skipped_source_inventory",
    "reviewer_holds",
    "rollback_notes",
    "validation_commands",
)

FORBIDDEN_TEXT_MARKERS = (
    "live crawl completed",
    "live crawl ran",
    "live crawler ran",
    "crawled live",
    "live request completed",
    "raw body artifact",
    "raw body persisted",
    "raw html persisted",
    "raw response body",
    "raw crawl output",
    "downloaded document",
    "downloaded artifact",
    "download complete",
    "auth_state",
    "session_state",
    "authenticated session",
    "devhub session",
    "private artifact",
    "private case file",
    "cookie jar",
    "credential stored",
    "password stored",
    "trace.zip",
    "har file",
    "file://",
    "/home/",
    "legal guarantee",
    "permitting guarantee",
    "permit guaranteed",
    "guarantee permit",
    "approval guaranteed",
    "mutation enabled",
    "active mutation",
)

ACTIVE_MUTATION_KEYS = frozenset(
    {
        "active_mutation",
        "active_mutation_enabled",
        "active_mutation_flags",
        "mutates_sources",
        "mutates_registry",
        "mutates_guardrails",
        "mutates_release_state",
        "live_crawl_enabled",
        "download_enabled",
        "auth_enabled",
        "devhub_enabled",
        "release_activation_enabled",
        "official_action_enabled",
    }
)


class PublicRefreshPreflightPacketV5Error(ValueError):
    """Raised when the v5 preflight packet cannot be assembled safely."""


class PublicRefreshPreflightPacketV5ValidationError(ValueError):
    """Raised when an assembled v5 preflight packet is incomplete or unsafe."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("public refresh preflight packet v5 rejected: " + "; ".join(errors))


def assemble_preflight_packet(seed_packet: Mapping[str, Any]) -> dict[str, Any]:
    """Assemble an offline public refresh preflight packet from a seed packet v5 fixture."""

    if not isinstance(seed_packet, dict):
        raise PublicRefreshPreflightPacketV5Error("seed packet must be a JSON object")
    assert_valid_packet(seed_packet)

    placeholders = _placeholders_by_id(seed_packet)
    candidates = sorted(seed_packet["refresh_candidate_ranking"], key=lambda row: row["rank"])

    allowlist_checks = [_allowlist_check(candidate, placeholders[candidate["source_registry_placeholder_id"]]) for candidate in candidates]
    robots_policy_placeholders = [_robots_policy_placeholder(candidate) for candidate in candidates]
    processor_handoff = [_processor_handoff(candidate) for candidate in candidates]
    skipped_sources = [_skipped_source(candidate) for candidate in candidates if candidate["skipped_source_reason"] != "not_skipped"]
    reviewer_holds = _reviewer_holds(seed_packet, candidates)

    packet = {
        "packet_version": PACKET_VERSION,
        "mode": MODE,
        "input_packet_version": SEED_PACKET_VERSION,
        "offline_only": True,
        "source_fixture_policy": {
            "accepted_input": "next public refresh seed packet v5 fixture only",
            "live_crawl_permitted": False,
            "document_download_permitted": False,
            "raw_body_storage_permitted": False,
            "devhub_access_permitted": False,
            "legal_or_permitting_guarantees_permitted": False,
        },
        "allowlist_checks": allowlist_checks,
        "robots_policy_preflight_placeholders": robots_policy_placeholders,
        "processor_handoff_readiness": processor_handoff,
        "raw_body_persistence_refusal": {
            "decision": "refuse_raw_body_persistence",
            "metadata_only_manifest": True,
            "allowed_persisted_material": [
                "source registry placeholder identifiers",
                "canonical source placeholder references",
                "skip reasons",
                "reviewer routing labels",
                "rollback notes",
                "validation command arrays",
            ],
        },
        "rate_limit_notes": [_rate_limit_note(candidate) for candidate in candidates],
        "skipped_source_inventory": skipped_sources,
        "reviewer_holds": reviewer_holds,
        "rollback_notes": {
            "packet_level": seed_packet["rollback_notes"],
            "candidate_level": [
                {"seed_id": candidate["seed_id"], "rollback_note": candidate["rollback_note"]}
                for candidate in candidates
            ],
        },
        "validation_commands": VALIDATION_COMMANDS,
    }
    assert_valid_preflight_packet(packet)
    return packet


def validate_preflight_packet(packet: Mapping[str, Any]) -> list[str]:
    """Return fail-closed validation errors for an assembled preflight packet v5."""

    if not isinstance(packet, dict):
        return ["packet must be an object"]

    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in packet or _missing(packet.get(field)):
            errors.append(f"missing packet.{field}")

    if packet.get("packet_version") != PACKET_VERSION:
        errors.append(f"packet.packet_version must be {PACKET_VERSION}")
    if packet.get("mode") != MODE:
        errors.append(f"packet.mode must be {MODE}")
    if packet.get("input_packet_version") != SEED_PACKET_VERSION:
        errors.append(f"packet.input_packet_version must be {SEED_PACKET_VERSION}")
    if packet.get("offline_only") is not True:
        errors.append("packet.offline_only must be true")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        errors.append("missing validation_commands or commands are not exact offline validation commands")

    _validate_source_fixture_policy(packet.get("source_fixture_policy"), errors)
    allowlist_seed_ids = _validate_allowlist_checks(packet.get("allowlist_checks"), errors)
    _validate_robots_policy(packet.get("robots_policy_preflight_placeholders"), allowlist_seed_ids, errors)
    _validate_processor_handoff(packet.get("processor_handoff_readiness"), allowlist_seed_ids, errors)
    _validate_raw_body_refusal(packet.get("raw_body_persistence_refusal"), errors)
    _validate_rate_limit_notes(packet.get("rate_limit_notes"), allowlist_seed_ids, errors)
    _validate_skipped_inventory(packet.get("skipped_source_inventory"), allowlist_seed_ids, errors)
    _validate_reviewer_holds(packet.get("reviewer_holds"), allowlist_seed_ids, errors)
    _validate_rollback_notes(packet.get("rollback_notes"), allowlist_seed_ids, errors)
    _scan_forbidden(packet, "packet", errors)
    return errors


def assert_valid_preflight_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_preflight_packet(packet)
    if errors:
        raise PublicRefreshPreflightPacketV5ValidationError(errors)


def _placeholders_by_id(seed_packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    placeholders: dict[str, Mapping[str, Any]] = {}
    for placeholder in seed_packet["source_registry_placeholders"]:
        placeholders[placeholder["placeholder_id"]] = placeholder
    return placeholders


def _allowlist_check(candidate: Mapping[str, Any], placeholder: Mapping[str, Any]) -> dict[str, Any]:
    skipped_reason = candidate["skipped_source_reason"]
    return {
        "seed_id": candidate["seed_id"],
        "source_registry_placeholder_id": candidate["source_registry_placeholder_id"],
        "source_registry_ref": placeholder["source_registry_ref"],
        "owning_surface": placeholder["owning_surface"],
        "allowed_public_hosts": PUBLIC_HOST_ALLOWLIST,
        "fixture_decision": "allowlist_placeholder_ready" if skipped_reason == "not_skipped" else "skip_before_allowlist_handoff",
        "skip_reason": skipped_reason,
        "preflight_note": "Host and path must be rechecked by a later offline-reviewed network preflight before any live request.",
    }


def _robots_policy_placeholder(candidate: Mapping[str, Any]) -> dict[str, str]:
    return {
        "seed_id": candidate["seed_id"],
        "robots_policy_state": "placeholder_pending_future_check",
        "policy_state": "fixture_review_only",
        "preflight_note": "No robots.txt fetch or policy lookup occurs in this packet.",
    }


def _processor_handoff(candidate: Mapping[str, Any]) -> dict[str, Any]:
    blocked = candidate["skipped_source_reason"] != "not_skipped" or candidate["stale_source_hold_key"] != NO_HOLD_KEY
    return {
        "seed_id": candidate["seed_id"],
        "source_registry_placeholder_id": candidate["source_registry_placeholder_id"],
        "metadata_only": True,
        "raw_body_storage": False,
        "processor_handoff_state": "blocked_by_skip_or_reviewer_hold" if blocked else "metadata_manifest_candidate_ready",
        "handoff_note": "Processor execution is not invoked by this packet.",
    }


def _rate_limit_note(candidate: Mapping[str, Any]) -> dict[str, str]:
    return {
        "seed_id": candidate["seed_id"],
        "crawl_frequency_label": candidate["crawl_frequency_label"],
        "rate_limit_note": "No request budget is consumed; any later live refresh must use a separately approved rate limit preflight.",
    }


def _skipped_source(candidate: Mapping[str, Any]) -> dict[str, str]:
    return {
        "seed_id": candidate["seed_id"],
        "skipped_source_reason": candidate["skipped_source_reason"],
        "reviewer_route": candidate["reviewer_route"],
    }


def _reviewer_holds(seed_packet: Mapping[str, Any], candidates: list[Mapping[str, Any]]) -> dict[str, Any]:
    candidate_holds = []
    for candidate in candidates:
        hold_key = candidate["stale_source_hold_key"]
        if hold_key == NO_HOLD_KEY:
            continue
        candidate_holds.append(
            {
                "seed_id": candidate["seed_id"],
                "stale_source_hold_key": hold_key,
                "hold_disposition": seed_packet["stale_source_hold_mapping"][hold_key],
                "reviewer_route": candidate["reviewer_route"],
            }
        )
    return {
        "mapping": seed_packet["stale_source_hold_mapping"],
        "candidate_holds": candidate_holds,
        "routing": seed_packet["reviewer_routing"],
    }


def _missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _require_string(row: Mapping[str, Any], field: str, path: str, errors: list[str]) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value:
        errors.append(f"missing {path}.{field}")
        return ""
    return value


def _validate_source_fixture_policy(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("packet.source_fixture_policy must be an object")
        return
    if value.get("accepted_input") != "next public refresh seed packet v5 fixture only":
        errors.append("packet.source_fixture_policy.accepted_input must name the seed packet fixture-only input")
    for field in (
        "live_crawl_permitted",
        "document_download_permitted",
        "raw_body_storage_permitted",
        "devhub_access_permitted",
        "legal_or_permitting_guarantees_permitted",
    ):
        if value.get(field) is not False:
            errors.append(f"packet.source_fixture_policy.{field} must be false")


def _validate_allowlist_checks(value: Any, errors: list[str]) -> set[str]:
    seed_ids: set[str] = set()
    if not isinstance(value, list) or not value:
        errors.append("missing allowlist checks")
        return seed_ids
    for index, row in enumerate(value):
        path = f"packet.allowlist_checks[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        seed_id = _require_string(row, "seed_id", path, errors)
        if seed_id:
            seed_ids.add(seed_id)
        _require_string(row, "source_registry_placeholder_id", path, errors)
        source_registry_ref = _require_string(row, "source_registry_ref", path, errors)
        _require_string(row, "owning_surface", path, errors)
        _require_string(row, "fixture_decision", path, errors)
        _require_string(row, "skip_reason", path, errors)
        _require_string(row, "preflight_note", path, errors)
        if source_registry_ref and not source_registry_ref.startswith("source-registry-placeholder://"):
            errors.append(f"{path}.source_registry_ref must be a source-registry-placeholder:// reference")
        if row.get("allowed_public_hosts") != PUBLIC_HOST_ALLOWLIST:
            errors.append(f"{path}.allowed_public_hosts must match the PP&D public allowlist")
    return seed_ids


def _validate_robots_policy(value: Any, seed_ids: set[str], errors: list[str]) -> None:
    rows = _validate_seed_scoped_rows(value, seed_ids, "robots_policy_preflight_placeholders", "missing robots or policy preflight placeholders", errors)
    for index, row in rows:
        path = f"packet.robots_policy_preflight_placeholders[{index}]"
        _require_string(row, "robots_policy_state", path, errors)
        _require_string(row, "policy_state", path, errors)
        _require_string(row, "preflight_note", path, errors)


def _validate_processor_handoff(value: Any, seed_ids: set[str], errors: list[str]) -> None:
    rows = _validate_seed_scoped_rows(value, seed_ids, "processor_handoff_readiness", "missing processor handoff readiness", errors)
    for index, row in rows:
        path = f"packet.processor_handoff_readiness[{index}]"
        _require_string(row, "source_registry_placeholder_id", path, errors)
        _require_string(row, "processor_handoff_state", path, errors)
        _require_string(row, "handoff_note", path, errors)
        if row.get("metadata_only") is not True:
            errors.append(f"{path}.metadata_only must be true")
        if row.get("raw_body_storage") is not False:
            errors.append(f"{path}.raw_body_storage must be false")


def _validate_raw_body_refusal(value: Any, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("missing raw-body persistence refusal")
        return
    if value.get("decision") != "refuse_raw_body_persistence":
        errors.append("packet.raw_body_persistence_refusal.decision must refuse raw body persistence")
    if value.get("metadata_only_manifest") is not True:
        errors.append("packet.raw_body_persistence_refusal.metadata_only_manifest must be true")
    materials = value.get("allowed_persisted_material")
    if not isinstance(materials, list) or not materials or not all(isinstance(item, str) and item for item in materials):
        errors.append("packet.raw_body_persistence_refusal.allowed_persisted_material must be a non-empty string list")


def _validate_rate_limit_notes(value: Any, seed_ids: set[str], errors: list[str]) -> None:
    rows = _validate_seed_scoped_rows(value, seed_ids, "rate_limit_notes", "missing rate-limit notes", errors)
    for index, row in rows:
        path = f"packet.rate_limit_notes[{index}]"
        _require_string(row, "crawl_frequency_label", path, errors)
        _require_string(row, "rate_limit_note", path, errors)


def _validate_skipped_inventory(value: Any, seed_ids: set[str], errors: list[str]) -> None:
    rows = _validate_seed_scoped_rows(value, seed_ids, "skipped_source_inventory", "missing skipped-source inventory", errors, require_all_seed_ids=False)
    if not rows:
        return
    for index, row in rows:
        path = f"packet.skipped_source_inventory[{index}]"
        _require_string(row, "skipped_source_reason", path, errors)
        _require_string(row, "reviewer_route", path, errors)


def _validate_reviewer_holds(value: Any, seed_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("missing reviewer holds")
        return
    if not isinstance(value.get("mapping"), dict) or not value.get("mapping"):
        errors.append("packet.reviewer_holds.mapping must be non-empty")
    if not isinstance(value.get("routing"), dict) or not value.get("routing"):
        errors.append("packet.reviewer_holds.routing must be non-empty")
    rows = _validate_seed_scoped_rows(value.get("candidate_holds"), seed_ids, "reviewer_holds.candidate_holds", "missing reviewer holds", errors, require_all_seed_ids=False)
    for index, row in rows:
        path = f"packet.reviewer_holds.candidate_holds[{index}]"
        _require_string(row, "stale_source_hold_key", path, errors)
        _require_string(row, "hold_disposition", path, errors)
        _require_string(row, "reviewer_route", path, errors)


def _validate_rollback_notes(value: Any, seed_ids: set[str], errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append("missing rollback notes")
        return
    if not isinstance(value.get("packet_level"), str) or not value.get("packet_level"):
        errors.append("missing packet.rollback_notes.packet_level")
    rows = _validate_seed_scoped_rows(value.get("candidate_level"), seed_ids, "rollback_notes.candidate_level", "missing rollback notes", errors)
    for index, row in rows:
        path = f"packet.rollback_notes.candidate_level[{index}]"
        _require_string(row, "rollback_note", path, errors)


def _validate_seed_scoped_rows(
    value: Any,
    expected_seed_ids: set[str],
    field: str,
    missing_message: str,
    errors: list[str],
    require_all_seed_ids: bool = True,
) -> list[tuple[int, Mapping[str, Any]]]:
    if not isinstance(value, list) or not value:
        errors.append(missing_message)
        return []
    rows: list[tuple[int, Mapping[str, Any]]] = []
    found_seed_ids: set[str] = set()
    for index, row in enumerate(value):
        path = f"packet.{field}[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{path} must be an object")
            continue
        seed_id = _require_string(row, "seed_id", path, errors)
        if seed_id:
            found_seed_ids.add(seed_id)
            if expected_seed_ids and seed_id not in expected_seed_ids:
                errors.append(f"{path}.seed_id must reference an allowlist check seed_id")
        rows.append((index, row))
    if require_all_seed_ids and expected_seed_ids and found_seed_ids != expected_seed_ids:
        errors.append(f"packet.{field} must cover every allowlist check seed_id")
    return rows


def _scan_forbidden(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            lowered_key = str(key).lower()
            if lowered_key in ACTIVE_MUTATION_KEYS:
                if child is True or (isinstance(child, list) and child) or (isinstance(child, dict) and child):
                    errors.append(f"active mutation flag must be false, empty, or absent: {child_path}")
            _scan_forbidden(child, child_path, errors)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden(child, f"{path}[{index}]", errors)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for marker in FORBIDDEN_TEXT_MARKERS:
            if marker in lowered:
                errors.append(f"forbidden live, raw, downloaded, private, auth, guarantee, or mutation claim at {path}")
                break


def main() -> int:
    parser = argparse.ArgumentParser(description="Assemble fixture-first public refresh preflight packet v5.")
    parser.add_argument("seed_packet", type=Path)
    args = parser.parse_args()
    packet = assemble_preflight_packet(load_seed_packet(args.seed_packet))
    print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
