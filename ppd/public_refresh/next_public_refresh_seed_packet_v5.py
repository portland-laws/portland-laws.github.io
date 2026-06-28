"""Offline validator for next public refresh seed packet v5.

The v5 packet is a planning artifact only. It may rank candidate public
refresh seeds and route them for human review, but it must not claim that a
live crawl, raw body capture, document download, authenticated session, legal
outcome, permitting outcome, or active mutation has occurred.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

PACKET_VERSION = "next-public-refresh-seed-packet-v5"
MODE = "fixture-first-offline-public-refresh-planning"

VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/public_refresh/next_public_refresh_seed_packet_v5.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_next_public_refresh_seed_packet_v5.py"],
]

REQUIRED_TOP_LEVEL_FIELDS = (
    "packet_version",
    "mode",
    "monitoring_rehearsal_references",
    "source_registry_placeholders",
    "refresh_candidate_ranking",
    "stale_source_hold_mapping",
    "reviewer_routing",
    "rollback_notes",
    "validation_commands",
)

REQUIRED_CANDIDATE_FIELDS = (
    "seed_id",
    "rank",
    "source_registry_placeholder_id",
    "monitoring_rehearsal_reference",
    "changed_requirement_risk_label",
    "crawl_frequency_label",
    "skipped_source_reason",
    "stale_source_hold_key",
    "reviewer_route",
    "rollback_note",
)

RISK_LABELS = frozenset({"none", "low", "medium", "high", "review_required"})
CRAWL_FREQUENCY_LABELS = frozenset({"daily", "every_few_days", "weekly", "monthly", "skip_until_review"})
SKIPPED_SOURCE_REASONS = frozenset({"not_skipped", "outside_allowlist", "unsupported_scheme", "private_or_authenticated", "robots_or_policy_disallowed", "raw_download_not_permitted", "too_large", "unsupported_content_type", "missing_official_source_anchor"})

FORBIDDEN_MARKERS = (
    "live crawl completed",
    "live crawl ran",
    "live crawler ran",
    "crawled live",
    "raw body",
    "raw_body",
    "raw html",
    "raw crawl output",
    "downloaded document",
    "downloaded artifact",
    "download complete",
    "auth_state",
    "session_state",
    "authenticated session",
    "devhub session",
    "cookie",
    "credential",
    "password",
    "private artifact",
    "private case file",
    "trace.zip",
    "har file",
    "file://",
    "/home/",
    "legal guarantee",
    "permitting guarantee",
    "permit guaranteed",
    "guarantee permit",
    "approval guaranteed",
)

ACTIVE_MUTATION_KEYS = frozenset({
    "active_mutation",
    "active_mutation_enabled",
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
})


class NextPublicRefreshSeedPacketV5ValidationError(ValueError):
    """Raised when a v5 packet is incomplete or unsafe."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("next public refresh seed packet v5 rejected: " + "; ".join(errors))


def _is_empty(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _require_non_empty(container: dict[str, Any], field: str, path: str, errors: list[str]) -> None:
    if field not in container or _is_empty(container.get(field)):
        errors.append(f"missing {path}.{field}")


def _scan_forbidden(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            lowered_key = str(key).lower()
            if lowered_key in ACTIVE_MUTATION_KEYS and child is True:
                errors.append(f"active mutation flag must be false or absent: {child_path}")
            _scan_forbidden(child, child_path, errors)
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            _scan_forbidden(child, f"{path}[{index}]", errors)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for marker in FORBIDDEN_MARKERS:
            if marker in lowered:
                errors.append(f"forbidden live, raw, downloaded, private, auth, guarantee, or mutation claim at {path}")
                break


def validate_packet(packet: dict[str, Any]) -> list[str]:
    """Return deterministic validation errors for a v5 seed packet."""

    if not isinstance(packet, dict):
        return ["packet must be an object"]

    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        _require_non_empty(packet, field, "packet", errors)

    if packet.get("packet_version") != PACKET_VERSION:
        errors.append(f"packet.packet_version must be {PACKET_VERSION}")
    if packet.get("mode") != MODE:
        errors.append(f"packet.mode must be {MODE}")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        errors.append("missing validation_commands or commands are not exact offline validation commands")

    monitoring_refs = packet.get("monitoring_rehearsal_references")
    if isinstance(monitoring_refs, list) and monitoring_refs:
        for index, ref in enumerate(monitoring_refs):
            if not isinstance(ref, str) or not ref.startswith("monitoring-rehearsal://"):
                errors.append(f"packet.monitoring_rehearsal_references[{index}] must be a monitoring-rehearsal:// reference")
    elif "missing packet.monitoring_rehearsal_references" not in errors:
        errors.append("missing monitoring rehearsal references")

    placeholders = packet.get("source_registry_placeholders")
    placeholder_ids: set[str] = set()
    if isinstance(placeholders, list) and placeholders:
        for index, row in enumerate(placeholders):
            if not isinstance(row, dict):
                errors.append(f"packet.source_registry_placeholders[{index}] must be an object")
                continue
            _require_non_empty(row, "placeholder_id", f"packet.source_registry_placeholders[{index}]", errors)
            _require_non_empty(row, "source_registry_ref", f"packet.source_registry_placeholders[{index}]", errors)
            placeholder_id = row.get("placeholder_id")
            if isinstance(placeholder_id, str):
                placeholder_ids.add(placeholder_id)
            ref = row.get("source_registry_ref")
            if not isinstance(ref, str) or not ref.startswith("source-registry-placeholder://"):
                errors.append(f"packet.source_registry_placeholders[{index}].source_registry_ref must be a source-registry-placeholder:// reference")
    elif "missing packet.source_registry_placeholders" not in errors:
        errors.append("missing source registry placeholders")

    stale_mapping = packet.get("stale_source_hold_mapping")
    stale_keys: set[str] = set()
    if isinstance(stale_mapping, dict) and stale_mapping:
        for key, value in stale_mapping.items():
            stale_keys.add(str(key))
            if not isinstance(value, str) or not value:
                errors.append(f"packet.stale_source_hold_mapping.{key} must describe the hold disposition")
    elif "missing packet.stale_source_hold_mapping" not in errors:
        errors.append("missing stale-source hold mapping")

    routing = packet.get("reviewer_routing")
    if isinstance(routing, dict):
        _require_non_empty(routing, "queue", "packet.reviewer_routing", errors)
        _require_non_empty(routing, "reviewer_role", "packet.reviewer_routing", errors)
        _require_non_empty(routing, "routing_note", "packet.reviewer_routing", errors)
    elif "missing packet.reviewer_routing" not in errors:
        errors.append("missing reviewer routing")

    candidates = packet.get("refresh_candidate_ranking")
    if not isinstance(candidates, list) or not candidates:
        if "missing packet.refresh_candidate_ranking" not in errors:
            errors.append("missing refresh candidate ranking")
    else:
        ranks: list[Any] = []
        for index, candidate in enumerate(candidates):
            path = f"packet.refresh_candidate_ranking[{index}]"
            if not isinstance(candidate, dict):
                errors.append(f"{path} must be an object")
                continue
            for field in REQUIRED_CANDIDATE_FIELDS:
                _require_non_empty(candidate, field, path, errors)
            ranks.append(candidate.get("rank"))

            placeholder_id = candidate.get("source_registry_placeholder_id")
            if isinstance(placeholder_id, str) and placeholder_ids and placeholder_id not in placeholder_ids:
                errors.append(f"{path}.source_registry_placeholder_id must map to source_registry_placeholders")
            monitoring_ref = candidate.get("monitoring_rehearsal_reference")
            if isinstance(monitoring_refs, list) and monitoring_refs and monitoring_ref not in monitoring_refs:
                errors.append(f"{path}.monitoring_rehearsal_reference must map to monitoring_rehearsal_references")
            hold_key = candidate.get("stale_source_hold_key")
            if isinstance(hold_key, str) and stale_keys and hold_key not in stale_keys:
                errors.append(f"{path}.stale_source_hold_key must map to stale_source_hold_mapping")

            if candidate.get("changed_requirement_risk_label") not in RISK_LABELS:
                errors.append(f"{path}.changed_requirement_risk_label must be one of {sorted(RISK_LABELS)}")
            if candidate.get("crawl_frequency_label") not in CRAWL_FREQUENCY_LABELS:
                errors.append(f"{path}.crawl_frequency_label must be one of {sorted(CRAWL_FREQUENCY_LABELS)}")
            if candidate.get("skipped_source_reason") not in SKIPPED_SOURCE_REASONS:
                errors.append(f"{path}.skipped_source_reason must be one of {sorted(SKIPPED_SOURCE_REASONS)}")
        if ranks != list(range(1, len(candidates) + 1)):
            errors.append("refresh candidate ranking must use contiguous rank values starting at 1")

    _scan_forbidden(packet, "packet", errors)
    return errors


def assert_valid_packet(packet: dict[str, Any]) -> None:
    errors = validate_packet(packet)
    if errors:
        raise NextPublicRefreshSeedPacketV5ValidationError(errors)


def load_packet(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise ValueError("packet fixture must be a JSON object")
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an offline next public refresh seed packet v5 fixture.")
    parser.add_argument("packet", type=Path)
    args = parser.parse_args()
    packet = load_packet(args.packet)
    assert_valid_packet(packet)
    print(json.dumps({"valid": True, "packet_version": PACKET_VERSION}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
