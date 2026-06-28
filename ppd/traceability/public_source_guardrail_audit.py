"""Fixture-first public-source to guardrail traceability audit.

The audit intentionally accepts already-materialized packet dictionaries. It does
not fetch URLs, inspect live bundles, or mutate any active PP&D artifacts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

Packet = dict[str, Any]


def load_json_packet(path: str | Path) -> Packet:
    """Load a packet fixture from disk as a dictionary."""

    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"packet must be a JSON object: {path}")
    return data


def build_audit_packet(
    freshness_review_packet: Packet,
    requirement_promotion_packet: Packet,
    guardrail_activation_packet: Packet,
) -> Packet:
    """Build a deterministic traceability audit packet from three review packets."""

    freshness_sources = _index_by_id(
        freshness_review_packet.get("sources", []), "source_id", "freshness source"
    )
    requirements = _index_by_id(
        requirement_promotion_packet.get("requirements", []),
        "requirement_id",
        "requirement",
    )
    guardrail_bundles = _index_by_id(
        guardrail_activation_packet.get("guardrail_bundles", []),
        "guardrail_bundle_id",
        "guardrail bundle",
    )

    cited_source_ids: set[str] = set()
    promoted_requirement_ids: set[str] = set()
    activated_guardrail_bundle_ids: set[str] = set()
    reviewer_owners: set[str] = set()
    stale_acknowledgements: list[Packet] = []
    gaps: list[Packet] = []

    for source_id, source in freshness_sources.items():
        status = str(source.get("freshness_status", "")).strip().lower()
        acknowledgement = source.get("stale_source_acknowledgement")
        if status == "stale":
            if isinstance(acknowledgement, dict) and acknowledgement.get("reviewer_owner"):
                stale_acknowledgements.append(
                    {
                        "source_id": source_id,
                        "reviewer_owner": str(acknowledgement["reviewer_owner"]),
                        "acknowledged_at": str(acknowledgement.get("acknowledged_at", "")),
                        "rationale": str(acknowledgement.get("rationale", "")),
                    }
                )
                reviewer_owners.add(str(acknowledgement["reviewer_owner"]))
            else:
                gaps.append(
                    _gap(
                        "stale_source_without_acknowledgement",
                        source_id=source_id,
                        detail="Stale source is missing reviewer acknowledgement.",
                    )
                )

    for requirement_id, requirement in requirements.items():
        if requirement.get("promotion_decision") != "promote":
            continue
        promoted_requirement_ids.add(requirement_id)
        _add_owner(reviewer_owners, requirement.get("reviewer_owner"))
        evidence_ids = _string_list(requirement.get("source_evidence_ids", []))
        if not evidence_ids:
            gaps.append(
                _gap(
                    "requirement_without_source_evidence",
                    requirement_id=requirement_id,
                    detail="Promoted requirement has no cited public source evidence.",
                )
            )
        for source_id in evidence_ids:
            cited_source_ids.add(source_id)
            if source_id not in freshness_sources:
                gaps.append(
                    _gap(
                        "requirement_cites_unknown_source",
                        source_id=source_id,
                        requirement_id=requirement_id,
                        detail="Promoted requirement cites a source absent from the freshness packet.",
                    )
                )

    for bundle_id, bundle in guardrail_bundles.items():
        if bundle.get("activation_decision") != "activate":
            continue
        activated_guardrail_bundle_ids.add(bundle_id)
        _add_owner(reviewer_owners, bundle.get("reviewer_owner"))

        bundle_requirement_ids = _string_list(bundle.get("requirement_ids", []))
        if not bundle_requirement_ids:
            gaps.append(
                _gap(
                    "guardrail_bundle_without_requirements",
                    guardrail_bundle_id=bundle_id,
                    detail="Activated guardrail bundle has no requirement IDs.",
                )
            )
        for requirement_id in bundle_requirement_ids:
            if requirement_id not in promoted_requirement_ids:
                gaps.append(
                    _gap(
                        "guardrail_bundle_references_unpromoted_requirement",
                        guardrail_bundle_id=bundle_id,
                        requirement_id=requirement_id,
                        detail="Activated guardrail bundle references a missing or non-promoted requirement.",
                    )
                )

        bundle_source_ids = _string_list(bundle.get("source_evidence_ids", []))
        if not bundle_source_ids:
            gaps.append(
                _gap(
                    "guardrail_bundle_without_source_evidence",
                    guardrail_bundle_id=bundle_id,
                    detail="Activated guardrail bundle has no cited public source evidence.",
                )
            )
        for source_id in bundle_source_ids:
            cited_source_ids.add(source_id)
            if source_id not in freshness_sources:
                gaps.append(
                    _gap(
                        "guardrail_bundle_cites_unknown_source",
                        guardrail_bundle_id=bundle_id,
                        source_id=source_id,
                        detail="Activated guardrail bundle cites a source absent from the freshness packet.",
                    )
                )

    stale_acknowledgements.sort(key=lambda item: item["source_id"])
    gaps.sort(key=lambda item: json.dumps(item, sort_keys=True))

    return {
        "audit_packet_id": "public-source-to-guardrail-traceability-audit-fixture",
        "inputs": {
            "freshness_review_packet_id": freshness_review_packet.get("packet_id"),
            "requirement_promotion_packet_id": requirement_promotion_packet.get("packet_id"),
            "guardrail_activation_packet_id": guardrail_activation_packet.get("packet_id"),
        },
        "cited_source_ids": sorted(cited_source_ids),
        "requirement_ids": sorted(promoted_requirement_ids),
        "guardrail_bundle_ids": sorted(activated_guardrail_bundle_ids),
        "stale_source_acknowledgements": stale_acknowledgements,
        "reviewer_owners": sorted(reviewer_owners),
        "unresolved_traceability_gaps": gaps,
        "side_effects": {
            "fetched_urls": False,
            "mutated_active_bundles": False,
        },
    }


def _index_by_id(items: Any, id_field: str, label: str) -> dict[str, Packet]:
    if not isinstance(items, list):
        raise ValueError(f"{label} collection must be a list")
    indexed: dict[str, Packet] = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"{label} entry must be an object")
        item_id = item.get(id_field)
        if not isinstance(item_id, str) or not item_id:
            raise ValueError(f"{label} entry missing {id_field}")
        if item_id in indexed:
            raise ValueError(f"duplicate {label} id: {item_id}")
        indexed[item_id] = item
    return indexed


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _add_owner(owners: set[str], value: Any) -> None:
    if isinstance(value, str) and value:
        owners.add(value)


def _gap(gap_type: str, detail: str, **fields: str) -> Packet:
    gap: Packet = {"gap_type": gap_type, "detail": detail}
    gap.update({key: value for key, value in fields.items() if value})
    return gap
