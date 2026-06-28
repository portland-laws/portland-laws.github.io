"""Build fixture-first public source registry promotion decision packets.

This module is intentionally metadata-only: it reads completed rehearsal and
release-gate status packets plus reviewer decisions, then emits a deterministic
packet. It never mutates source registry records and never starts a crawl.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


VALID_DECISIONS = {"promote", "defer"}


class PromotionPacketError(ValueError):
    """Raised when promotion packet inputs are incomplete or inconsistent."""


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise PromotionPacketError(f"{path} must contain a JSON object")
    return value


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate_ids(rehearsal: dict[str, Any]) -> set[str]:
    candidates = rehearsal.get("candidate_sources")
    if not isinstance(candidates, list):
        raise PromotionPacketError("rehearsal packet must include candidate_sources")

    source_ids: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, dict) or not isinstance(candidate.get("source_id"), str):
            raise PromotionPacketError("each rehearsal candidate must include source_id")
        source_ids.add(candidate["source_id"])
    return source_ids


def _validate_rehearsal(rehearsal: dict[str, Any]) -> None:
    if rehearsal.get("packet_type") != "public_source_registry_promotion_rehearsal":
        raise PromotionPacketError("unexpected rehearsal packet_type")
    if rehearsal.get("status") != "completed":
        raise PromotionPacketError("promotion rehearsal must be completed")
    if rehearsal.get("crawl_ran") is not False:
        raise PromotionPacketError("promotion rehearsal must be fixture-only with crawl_ran=false")


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("packet_type") != "public_source_registry_release_gate_status":
        raise PromotionPacketError("unexpected release gate packet_type")
    if gate.get("status") != "passed":
        raise PromotionPacketError("release gate status must be passed")
    if gate.get("live_registry_mutated") is not False:
        raise PromotionPacketError("release gate packet must confirm live_registry_mutated=false")


def _normalize_decision(raw: dict[str, Any], allowed_sources: set[str]) -> dict[str, Any]:
    source_id = raw.get("source_id")
    decision = raw.get("decision")
    if not isinstance(source_id, str) or source_id not in allowed_sources:
        raise PromotionPacketError(f"unknown or missing source_id: {source_id!r}")
    if decision not in VALID_DECISIONS:
        raise PromotionPacketError(f"invalid decision for {source_id}: {decision!r}")

    blocker_refs = raw.get("blocker_refs", [])
    rollback_owner_notes = raw.get("rollback_owner_notes")
    invalidation_targets = raw.get("downstream_invalidation_targets", [])
    artifact_ids = raw.get("metadata_only_artifact_ids", [])

    if not isinstance(blocker_refs, list) or not all(isinstance(item, str) for item in blocker_refs):
        raise PromotionPacketError(f"blocker_refs for {source_id} must be a list of strings")
    if decision == "defer" and not blocker_refs:
        raise PromotionPacketError(f"defer decision for {source_id} requires explicit blocker_refs")
    if not isinstance(rollback_owner_notes, str) or not rollback_owner_notes.strip():
        raise PromotionPacketError(f"rollback_owner_notes for {source_id} must be non-empty")
    if not isinstance(invalidation_targets, list) or not all(isinstance(item, str) for item in invalidation_targets):
        raise PromotionPacketError(f"downstream_invalidation_targets for {source_id} must be a list of strings")
    if not isinstance(artifact_ids, list) or not all(isinstance(item, str) for item in artifact_ids):
        raise PromotionPacketError(f"metadata_only_artifact_ids for {source_id} must be a list of strings")

    return {
        "source_id": source_id,
        "decision": decision,
        "blocker_refs": sorted(blocker_refs),
        "rollback_owner_notes": rollback_owner_notes.strip(),
        "downstream_invalidation_targets": sorted(invalidation_targets),
        "metadata_only_artifact_ids": sorted(artifact_ids),
    }


def build_promotion_decision_packet(
    rehearsal_path: Path,
    release_gate_path: Path,
    reviewer_decisions_path: Path,
    *,
    generated_at: str = "2026-05-28T00:00:00Z",
) -> dict[str, Any]:
    """Return a deterministic metadata-only promotion decision packet."""

    rehearsal_path = Path(rehearsal_path)
    release_gate_path = Path(release_gate_path)
    reviewer_decisions_path = Path(reviewer_decisions_path)

    rehearsal = _read_json(rehearsal_path)
    release_gate = _read_json(release_gate_path)
    reviewer_decisions = _read_json(reviewer_decisions_path)

    _validate_rehearsal(rehearsal)
    _validate_gate(release_gate)

    allowed_sources = _candidate_ids(rehearsal)
    decisions = reviewer_decisions.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        raise PromotionPacketError("reviewer decision packet must include non-empty decisions")

    normalized = [_normalize_decision(item, allowed_sources) for item in decisions]
    seen = [item["source_id"] for item in normalized]
    if len(seen) != len(set(seen)):
        raise PromotionPacketError("reviewer decision packet contains duplicate source_id entries")

    return {
        "packet_type": "public_source_registry_promotion_decision",
        "schema_version": 1,
        "generated_at": generated_at,
        "fixture_first": True,
        "crawl_ran": False,
        "live_registry_mutated": False,
        "reviewer": reviewer_decisions.get("reviewer", "unassigned"),
        "registry_version": reviewer_decisions.get("registry_version", rehearsal.get("registry_version")),
        "inputs": {
            "promotion_rehearsal": {
                "path": rehearsal_path.as_posix(),
                "sha256": _file_sha256(rehearsal_path),
                "packet_id": rehearsal.get("packet_id"),
            },
            "release_gate_status": {
                "path": release_gate_path.as_posix(),
                "sha256": _file_sha256(release_gate_path),
                "packet_id": release_gate.get("packet_id"),
            },
        },
        "decisions": sorted(normalized, key=lambda item: item["source_id"]),
        "summary": {
            "promote": sum(1 for item in normalized if item["decision"] == "promote"),
            "defer": sum(1 for item in normalized if item["decision"] == "defer"),
        },
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build a PP&D source registry promotion decision packet")
    parser.add_argument("rehearsal", type=Path)
    parser.add_argument("release_gate", type=Path)
    parser.add_argument("reviewer_decisions", type=Path)
    args = parser.parse_args()

    packet = build_promotion_decision_packet(args.rehearsal, args.release_gate, args.reviewer_decisions)
    print(json.dumps(packet, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
