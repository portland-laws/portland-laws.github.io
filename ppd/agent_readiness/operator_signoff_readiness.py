"""Fixture-first operator signoff implementation readiness packet builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKET_SCHEMA_VERSION = "operator-signoff-implementation-readiness-packet.v1"

DEFAULT_PREREQUISITE_PACKET_VERSIONS = {
    "crawl_scope_packet": "ppd-crawl-scope-packet.v1",
    "fixture_validation_packet": "ppd-fixture-validation-packet.v1",
    "operator_signoff_ledger": "operator-signoff-ledger.v1",
}

APPROVED_STATUSES = {"approved", "signed_off", "accepted"}
BLOCKER_STATUSES = {"blocked", "blocker", "rejected", "needs_changes", "unresolved"}


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _entries_from_ledger(ledger: Any) -> list[dict[str, Any]]:
    if isinstance(ledger, list):
        entries = ledger
    elif isinstance(ledger, dict):
        entries = ledger.get("entries") or ledger.get("decisions") or []
    else:
        entries = []

    return [entry for entry in entries if isinstance(entry, dict)]


def _normalized_status(entry: dict[str, Any]) -> str:
    raw_status = entry.get("status") or entry.get("decision") or ""
    return str(raw_status).strip().lower()


def _decision_id(entry: dict[str, Any], index: int) -> str:
    value = entry.get("id") or entry.get("decision_id") or entry.get("review_id")
    if value:
        return str(value)
    return f"ledger-entry-{index + 1}"


def build_operator_signoff_readiness_packet(
    ledger_path: str | Path,
    prerequisite_packet_versions: dict[str, str] | None = None,
    production_promotion_enabled: bool = False,
) -> dict[str, Any]:
    """Build an offline readiness packet from an operator signoff ledger fixture."""
    source_path = Path(ledger_path)
    ledger = _load_json(source_path)
    entries = _entries_from_ledger(ledger)

    approved_review_decisions: list[dict[str, Any]] = []
    unresolved_blockers: list[dict[str, Any]] = []

    for index, entry in enumerate(entries):
        status = _normalized_status(entry)
        decision = {
            "id": _decision_id(entry, index),
            "status": status,
            "title": str(entry.get("title") or entry.get("summary") or ""),
            "operator": str(entry.get("operator") or entry.get("reviewer") or ""),
            "source": str(entry.get("source") or source_path.name),
        }

        has_unresolved_blocker = bool(entry.get("unresolved_blocker") or entry.get("blocker"))
        if status in BLOCKER_STATUSES or has_unresolved_blocker:
            blocker = dict(decision)
            blocker["reason"] = str(entry.get("reason") or entry.get("notes") or "unresolved operator signoff blocker")
            unresolved_blockers.append(blocker)
        elif status in APPROVED_STATUSES:
            approved_review_decisions.append(decision)

    exact_prerequisites = dict(DEFAULT_PREREQUISITE_PACKET_VERSIONS)
    if prerequisite_packet_versions:
        exact_prerequisites.update(prerequisite_packet_versions)

    promotion_enabled = bool(production_promotion_enabled)
    return {
        "schema_version": PACKET_SCHEMA_VERSION,
        "source_ledger": str(source_path),
        "fixture_first": True,
        "live_systems_touched": False,
        "production_promotion_enabled": promotion_enabled,
        "promotion_guard": "production promotion remains disabled unless an operator explicitly enables it outside this fixture packet",
        "exact_prerequisite_packet_versions": exact_prerequisites,
        "approved_review_decisions": approved_review_decisions,
        "unresolved_blockers": unresolved_blockers,
        "implementation_ready": bool(approved_review_decisions) and not unresolved_blockers and not promotion_enabled,
    }


def write_operator_signoff_readiness_packet(
    ledger_path: str | Path,
    output_path: str | Path,
    prerequisite_packet_versions: dict[str, str] | None = None,
) -> dict[str, Any]:
    packet = build_operator_signoff_readiness_packet(
        ledger_path=ledger_path,
        prerequisite_packet_versions=prerequisite_packet_versions,
        production_promotion_enabled=False,
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return packet
