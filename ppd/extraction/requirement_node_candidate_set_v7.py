"""Fixture-first RequirementNode candidate set v7 assembly.

This module consumes already re-extracted work-packet fixtures and produces
reviewable RequirementNode candidate rows. It performs no crawling, no DevHub
access, no downloads, and no consequential permitting actions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ALLOWED_PACKET_VERSION = "requirement-reextract-work-packet-v7"

STANDARD_PROCESS_STAGES = {
    "pre-application research",
    "account setup or manual login",
    "property lookup",
    "permit type selection",
    "eligibility screening",
    "document preparation",
    "application data entry",
    "upload staging",
    "acknowledgement/certification review",
    "submission",
    "prescreen/intake",
    "fee payment",
    "plan review",
    "corrections/checksheets",
    "approval/issuance",
    "inspections",
    "closeout, cancellation, expiration, extension, or reactivation",
}

REQUIRED_REVIEW_STATUSES = {"needs_review", "candidate_only"}


@dataclass(frozen=True)
class RequirementCandidateSetV7:
    """Normalized candidate output for review-only PP&D fixtures."""

    candidate_set_id: str
    packet_id: str
    rows: tuple[dict[str, Any], ...]
    evidence_continuity: tuple[dict[str, Any], ...]
    validation_notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_set_version": "requirement-node-candidate-set-v7",
            "candidate_set_id": self.candidate_set_id,
            "packet_id": self.packet_id,
            "rows": list(self.rows),
            "evidence_continuity": list(self.evidence_continuity),
            "validation_notes": list(self.validation_notes),
            "offline_only": True,
            "prohibited_actions": [
                "crawl_live_sites",
                "download_raw_artifacts",
                "open_devhub",
                "read_private_documents",
                "activate_guardrails",
                "upload",
                "submit",
                "certify",
                "pay",
                "schedule",
                "make_legal_or_permitting_guarantees",
            ],
        }


def load_work_packet(path: Path | str) -> dict[str, Any]:
    """Load a committed fixture work packet from disk."""

    packet_path = Path(path)
    with packet_path.open("r", encoding="utf-8") as packet_file:
        packet = json.load(packet_file)
    if not isinstance(packet, dict):
        raise ValueError("work packet fixture must be a JSON object")
    return packet


def build_candidate_set_v7(packet: dict[str, Any]) -> RequirementCandidateSetV7:
    """Build deterministic add/update/deprecate candidates from a v7 fixture."""

    _validate_packet_header(packet)
    packet_id = _required_string(packet, "packet_id")
    rows: list[dict[str, Any]] = []
    continuity: list[dict[str, Any]] = []
    notes: list[str] = []

    existing_by_id = {
        node["requirement_id"]: node
        for node in packet.get("existing_requirement_nodes", [])
        if isinstance(node, dict) and isinstance(node.get("requirement_id"), str)
    }

    for item in _require_list(packet, "reextracted_requirements"):
        row = _candidate_row(item, existing_by_id, packet)
        rows.append(row)
        continuity.append(_continuity_row(row, packet))
        notes.extend(_mapping_notes(row))

    for deprecated in _require_list(packet, "deprecated_requirements"):
        row = _deprecation_row(deprecated, packet)
        rows.append(row)
        continuity.append(_continuity_row(row, packet))
        notes.extend(_mapping_notes(row))

    rows.sort(key=lambda row: (row["candidate_action"], row["requirement_id"]))
    continuity.sort(key=lambda row: row["requirement_id"])

    return RequirementCandidateSetV7(
        candidate_set_id=f"candidate-set-v7::{packet_id}",
        packet_id=packet_id,
        rows=tuple(rows),
        evidence_continuity=tuple(continuity),
        validation_notes=tuple(sorted(set(notes))),
    )


def _candidate_row(
    item: dict[str, Any], existing_by_id: dict[str, dict[str, Any]], packet: dict[str, Any]
) -> dict[str, Any]:
    requirement_id = _required_string(item, "requirement_id")
    source_evidence_ids = _string_list(item, "source_evidence_ids")
    previous = existing_by_id.get(requirement_id)
    candidate_action = "update" if previous else "add"
    review_flags = sorted(set(_string_list(item, "review_flags", required=False)))

    if _has_conflict(item):
        review_flags.append("conflict_review")
    if _has_stale_evidence(item, packet):
        review_flags.append("stale_evidence_review")
    if not source_evidence_ids:
        review_flags.append("missing_source_evidence")

    permit_types = _string_list(item, "permit_types", required=False)
    process_stage = item.get("process_stage") or "mapping_placeholder"
    if process_stage not in STANDARD_PROCESS_STAGES:
        review_flags.append("process_stage_mapping_placeholder")
    if not permit_types:
        review_flags.append("permit_type_mapping_placeholder")

    return {
        "requirement_id": requirement_id,
        "candidate_action": candidate_action,
        "source_evidence_ids": source_evidence_ids,
        "previous_source_evidence_ids": _string_list(previous or {}, "source_evidence_ids", required=False),
        "requirement_type": item.get("requirement_type", "mapping_placeholder"),
        "subject": item.get("subject", "formalization_placeholder"),
        "action": item.get("action", "formalization_placeholder"),
        "object": item.get("object", "formalization_placeholder"),
        "conditions": item.get("conditions", []),
        "deadline_or_temporal_scope": item.get("deadline_or_temporal_scope"),
        "permit_types": permit_types or ["permit_type_mapping_placeholder"],
        "process_stage": process_stage,
        "confidence": item.get("confidence", "candidate_only"),
        "human_review_status": item.get("human_review_status", "needs_review"),
        "formalization_status": item.get("formalization_status", "formalization_placeholder"),
        "reviewer_owner": item.get("reviewer_owner", "reviewer_owner_placeholder"),
        "review_flags": sorted(set(review_flags)),
        "source_text_digest": item.get("source_text_digest", "fixture_digest_placeholder"),
        "offline_fixture_only": True,
    }


def _deprecation_row(item: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    requirement_id = _required_string(item, "requirement_id")
    source_evidence_ids = _string_list(item, "source_evidence_ids", required=False)
    review_flags = sorted(set(_string_list(item, "review_flags", required=False)))
    review_flags.append("deprecation_review")
    if not source_evidence_ids:
        review_flags.append("stale_evidence_review")

    return {
        "requirement_id": requirement_id,
        "candidate_action": "deprecate",
        "source_evidence_ids": source_evidence_ids,
        "previous_source_evidence_ids": _string_list(item, "previous_source_evidence_ids", required=False),
        "requirement_type": item.get("requirement_type", "formalization_placeholder"),
        "subject": item.get("subject", "formalization_placeholder"),
        "action": item.get("action", "deprecate"),
        "object": item.get("object", "formalization_placeholder"),
        "conditions": item.get("conditions", []),
        "deadline_or_temporal_scope": item.get("deadline_or_temporal_scope"),
        "permit_types": _string_list(item, "permit_types", required=False) or ["permit_type_mapping_placeholder"],
        "process_stage": item.get("process_stage", "mapping_placeholder"),
        "confidence": item.get("confidence", "candidate_only"),
        "human_review_status": item.get("human_review_status", "needs_review"),
        "formalization_status": item.get("formalization_status", "formalization_placeholder"),
        "reviewer_owner": item.get("reviewer_owner", "reviewer_owner_placeholder"),
        "review_flags": sorted(set(review_flags)),
        "source_text_digest": item.get("source_text_digest", "fixture_digest_placeholder"),
        "offline_fixture_only": True,
    }


def _continuity_row(row: dict[str, Any], packet: dict[str, Any]) -> dict[str, Any]:
    evidence_catalog = {
        evidence["evidence_id"]
        for evidence in packet.get("source_evidence", [])
        if isinstance(evidence, dict) and isinstance(evidence.get("evidence_id"), str)
    }
    current = set(row["source_evidence_ids"])
    previous = set(row["previous_source_evidence_ids"])
    missing = sorted(current - evidence_catalog)
    retained = sorted(current & previous)
    added = sorted(current - previous)
    removed = sorted(previous - current)
    return {
        "requirement_id": row["requirement_id"],
        "candidate_action": row["candidate_action"],
        "current_evidence_count": len(current),
        "previous_evidence_count": len(previous),
        "retained_evidence_ids": retained,
        "added_evidence_ids": added,
        "removed_evidence_ids": removed,
        "missing_catalog_evidence_ids": missing,
        "continuity_status": "needs_review" if missing or removed else "continuous",
    }


def _mapping_notes(row: dict[str, Any]) -> Iterable[str]:
    if "permit_type_mapping_placeholder" in row["review_flags"]:
        yield f"{row['requirement_id']}: permit type mapping placeholder requires reviewer assignment"
    if "process_stage_mapping_placeholder" in row["review_flags"]:
        yield f"{row['requirement_id']}: process-stage mapping placeholder requires reviewer assignment"
    if row["formalization_status"] == "formalization_placeholder":
        yield f"{row['requirement_id']}: formalization status placeholder requires reviewer decision"
    if row["reviewer_owner"] == "reviewer_owner_placeholder":
        yield f"{row['requirement_id']}: reviewer owner placeholder requires assignment"


def _validate_packet_header(packet: dict[str, Any]) -> None:
    version = _required_string(packet, "packet_version")
    if version != ALLOWED_PACKET_VERSION:
        raise ValueError(f"unsupported work packet version: {version}")
    if packet.get("source_mode") != "fixture_only":
        raise ValueError("candidate set v7 only accepts fixture_only source_mode")
    if packet.get("live_access_performed") is not False:
        raise ValueError("work packet must declare live_access_performed=false")


def _has_conflict(item: dict[str, Any]) -> bool:
    return bool(item.get("conflicting_evidence_ids") or item.get("conflict_notes"))


def _has_stale_evidence(item: dict[str, Any], packet: dict[str, Any]) -> bool:
    stale_ids = set(_string_list(packet, "stale_evidence_ids", required=False))
    return bool(stale_ids & set(_string_list(item, "source_evidence_ids", required=False)))


def _require_list(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    if not all(isinstance(item, dict) for item in value):
        raise ValueError(f"{key} must contain only objects")
    return value


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _string_list(data: dict[str, Any], key: str, *, required: bool = True) -> list[str]:
    value = data.get(key)
    if value is None and not required:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a list of strings")
    return list(value)
