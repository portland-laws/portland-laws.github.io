"""Metadata-only public source refresh tranche proposal helpers.

This module intentionally does not fetch, download, run processors, or mutate any
source schedule. It converts already-reviewed fixture packets into a deterministic
proposal packet for human review.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


REQUIRED_ATTESTATIONS = (
    "no_fetch_performed",
    "no_download_performed",
    "no_processor_invoked",
    "no_schedule_mutation_performed",
)


@dataclass(frozen=True)
class TrancheSource:
    """One source proposed for a metadata-only refresh tranche."""

    source_id: str
    canonical_url: str
    refresh_reason: str
    proposed_frequency: str
    owner: str
    reviewer: str
    allowlist_evidence_ref: str
    robots_evidence_ref: str
    abort_criteria: tuple[str, ...]
    runbook_step_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "canonical_url": self.canonical_url,
            "refresh_reason": self.refresh_reason,
            "proposed_frequency": self.proposed_frequency,
            "owner": self.owner,
            "reviewer": self.reviewer,
            "allowlist_evidence_ref": self.allowlist_evidence_ref,
            "robots_evidence_ref": self.robots_evidence_ref,
            "abort_criteria": list(self.abort_criteria),
            "runbook_step_refs": list(self.runbook_step_refs),
        }


def build_refresh_tranche_proposal(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Build and validate a metadata-only refresh tranche proposal.

    The input packet is expected to contain three fixture-backed upstream packets:
    an evidence freshness watchlist reviewer disposition packet, a source registry
    schedule update candidate, and a source refresh runbook candidate.
    """

    evidence_packet = _mapping(packet, "evidence_freshness_watchlist_reviewer_disposition_packet")
    schedule_packet = _mapping(packet, "source_registry_schedule_update_candidate")
    runbook_packet = _mapping(packet, "source_refresh_runbook_candidate")

    dispositions = _index_by_source(evidence_packet.get("source_dispositions", ()), "source_dispositions")
    schedule_sources = _index_by_source(schedule_packet.get("sources", ()), "sources")
    runbook_sources = _index_by_source(runbook_packet.get("source_steps", ()), "source_steps")

    ordered_ids = _ordered_source_ids(runbook_packet, schedule_packet, dispositions)
    tranche_sources = []
    for source_id in ordered_ids:
        disposition = _source(dispositions, source_id, "evidence freshness disposition")
        schedule = _source(schedule_sources, source_id, "schedule update candidate")
        runbook = _source(runbook_sources, source_id, "runbook candidate")
        tranche_sources.append(_merge_source(source_id, disposition, schedule, runbook))

    proposal = {
        "packet_type": "ppd_public_source_refresh_tranche_proposal",
        "packet_version": "1.0",
        "tranche_id": _required_text(packet, "tranche_id"),
        "proposal_status": "metadata_only_review_required",
        "consumes_packet_ids": [
            _required_text(evidence_packet, "packet_id"),
            _required_text(schedule_packet, "packet_id"),
            _required_text(runbook_packet, "packet_id"),
        ],
        "ordered_sources": [source.to_dict() for source in tranche_sources],
        "attestations": {
            "no_fetch_performed": True,
            "no_download_performed": True,
            "no_processor_invoked": True,
            "no_schedule_mutation_performed": True,
        },
        "reviewer_owner_fields_required": True,
    }
    validate_refresh_tranche_proposal(proposal)
    return proposal


def validate_refresh_tranche_proposal(proposal: Mapping[str, Any]) -> None:
    """Raise ValueError if a proposal is not safe to commit as metadata."""

    if proposal.get("packet_type") != "ppd_public_source_refresh_tranche_proposal":
        raise ValueError("unexpected packet_type")
    attestations = _mapping(proposal, "attestations")
    for key in REQUIRED_ATTESTATIONS:
        if attestations.get(key) is not True:
            raise ValueError(f"required attestation is missing or false: {key}")

    ordered_sources = proposal.get("ordered_sources")
    if not isinstance(ordered_sources, list) or not ordered_sources:
        raise ValueError("ordered_sources must be a non-empty list")

    seen = set()
    for source in ordered_sources:
        if not isinstance(source, Mapping):
            raise ValueError("ordered_sources entries must be objects")
        source_id = _required_text(source, "source_id")
        if source_id in seen:
            raise ValueError(f"duplicate source_id in tranche: {source_id}")
        seen.add(source_id)
        _required_text(source, "canonical_url")
        _required_text(source, "refresh_reason")
        _required_text(source, "proposed_frequency")
        _required_text(source, "owner")
        _required_text(source, "reviewer")
        _required_text(source, "allowlist_evidence_ref")
        _required_text(source, "robots_evidence_ref")
        _required_non_empty_text_list(source, "abort_criteria")
        _required_non_empty_text_list(source, "runbook_step_refs")


def _merge_source(
    source_id: str,
    disposition: Mapping[str, Any],
    schedule: Mapping[str, Any],
    runbook: Mapping[str, Any],
) -> TrancheSource:
    if disposition.get("reviewer_disposition") != "approved_for_metadata_refresh_proposal":
        raise ValueError(f"source is not approved for metadata refresh proposal: {source_id}")
    return TrancheSource(
        source_id=source_id,
        canonical_url=_required_text(schedule, "canonical_url"),
        refresh_reason=_required_text(disposition, "freshness_reason"),
        proposed_frequency=_required_text(schedule, "proposed_frequency"),
        owner=_required_text(disposition, "owner"),
        reviewer=_required_text(disposition, "reviewer"),
        allowlist_evidence_ref=_required_text(disposition, "allowlist_evidence_ref"),
        robots_evidence_ref=_required_text(disposition, "robots_evidence_ref"),
        abort_criteria=tuple(_required_non_empty_text_list(runbook, "abort_criteria")),
        runbook_step_refs=tuple(_required_non_empty_text_list(runbook, "step_refs")),
    )


def _ordered_source_ids(
    runbook_packet: Mapping[str, Any],
    schedule_packet: Mapping[str, Any],
    dispositions: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    runbook_order = runbook_packet.get("ordered_source_ids")
    if isinstance(runbook_order, list) and runbook_order:
        ordered = [_text_value(value, "ordered_source_ids entry") for value in runbook_order]
    else:
        scheduled = schedule_packet.get("sources")
        if not isinstance(scheduled, list):
            raise ValueError("schedule sources must be a list")
        ordered = sorted(_required_text(source, "source_id") for source in scheduled if isinstance(source, Mapping))
    missing = [source_id for source_id in ordered if source_id not in dispositions]
    if missing:
        raise ValueError(f"ordered source lacks reviewer disposition: {', '.join(missing)}")
    return ordered


def _index_by_source(entries: Any, field_name: str) -> dict[str, Mapping[str, Any]]:
    if not isinstance(entries, list):
        raise ValueError(f"{field_name} must be a list")
    indexed: dict[str, Mapping[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError(f"{field_name} entries must be objects")
        source_id = _required_text(entry, "source_id")
        if source_id in indexed:
            raise ValueError(f"duplicate source_id in {field_name}: {source_id}")
        indexed[source_id] = entry
    return indexed


def _source(indexed: Mapping[str, Mapping[str, Any]], source_id: str, packet_name: str) -> Mapping[str, Any]:
    try:
        return indexed[source_id]
    except KeyError as exc:
        raise ValueError(f"source {source_id} missing from {packet_name}") from exc


def _mapping(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    child = value.get(key)
    if not isinstance(child, Mapping):
        raise ValueError(f"{key} must be an object")
    return child


def _required_text(value: Mapping[str, Any], key: str) -> str:
    return _text_value(value.get(key), key)


def _text_value(value: Any, key: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _required_non_empty_text_list(value: Mapping[str, Any], key: str) -> list[str]:
    items = value.get(key)
    if not isinstance(items, list) or not items:
        raise ValueError(f"{key} must be a non-empty list")
    return [_text_value(item, f"{key} entry") for item in items]
