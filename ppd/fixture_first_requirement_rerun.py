"""Fixture-first requirement rerun work-queue packet builder.

This module only transforms already-provided packet dictionaries. It does not fetch
sources, read raw archives, invoke processors, or mutate requirement records.
"""

from __future__ import annotations

from typing import Any, Iterable


RequirementPacket = dict[str, Any]


def build_requirement_rerun_work_queue_packet(
    freshness_drift_escalation: RequirementPacket,
    requirement_rerun_disposition: RequirementPacket,
    guardrail_bundle_update_candidate: RequirementPacket,
) -> RequirementPacket:
    """Build a metadata-only requirement rerun work-queue packet.

    The packet is intentionally fixture-first: callers pass parsed fixture data in
    memory, and this function emits a deterministic work-queue packet for review.
    """

    cited_requirement_ids = _ordered_unique(
        _extract_values_by_key(
            (
                freshness_drift_escalation,
                requirement_rerun_disposition,
                guardrail_bundle_update_candidate,
            ),
            {
                "requirement_id",
                "requirement_ids",
                "cited_requirement_id",
                "cited_requirement_ids",
                "affected_requirement_ids",
            },
        )
    )
    affected_process_refs = _ordered_unique(
        _extract_values_by_key(
            (freshness_drift_escalation, requirement_rerun_disposition),
            {"process_ref", "process_refs", "affected_process_refs", "process_id", "process_ids"},
        )
    )
    affected_guardrail_refs = _ordered_unique(
        _extract_values_by_key(
            (guardrail_bundle_update_candidate, requirement_rerun_disposition),
            {"guardrail_ref", "guardrail_refs", "affected_guardrail_refs", "guardrail_id", "guardrail_ids"},
        )
    )

    return {
        "packet_type": "fixture_first_requirement_rerun_work_queue",
        "schema_version": 1,
        "source_packets": {
            "freshness_drift_escalation": freshness_drift_escalation.get("packet_id", "fixture:freshness-drift-escalation"),
            "requirement_rerun_disposition": requirement_rerun_disposition.get("packet_id", "fixture:requirement-rerun-disposition"),
            "guardrail_bundle_update_candidate": guardrail_bundle_update_candidate.get("packet_id", "fixture:guardrail-bundle-update-candidate"),
        },
        "cited_requirement_ids": cited_requirement_ids,
        "affected_process_refs": affected_process_refs,
        "affected_guardrail_refs": affected_guardrail_refs,
        "ordered_rerun_steps": [
            {
                "step": 1,
                "name": "fixture_packet_intake",
                "action": "Read committed fixture packets from ppd/tests/fixtures only.",
                "live_extraction_allowed": False,
                "processor_invocation_allowed": False,
                "requirement_mutation_allowed": False,
            },
            {
                "step": 2,
                "name": "metadata_crosswalk",
                "action": "Crosswalk cited requirement IDs to affected process and guardrail references.",
                "live_extraction_allowed": False,
                "processor_invocation_allowed": False,
                "requirement_mutation_allowed": False,
            },
            {
                "step": 3,
                "name": "reviewer_owner_disposition",
                "action": "Assign reviewer-owner fields and emit metadata-only rerun disposition artifacts.",
                "live_extraction_allowed": False,
                "processor_invocation_allowed": False,
                "requirement_mutation_allowed": False,
            },
        ],
        "reviewer_owner_fields": {
            "reviewer_owner": _first_present(
                requirement_rerun_disposition,
                ("reviewer_owner", "owner", "assigned_reviewer"),
                "ppd-requirement-reviewer",
            ),
            "escalation_owner": _first_present(
                freshness_drift_escalation,
                ("escalation_owner", "owner", "assigned_owner"),
                "ppd-freshness-reviewer",
            ),
            "guardrail_owner": _first_present(
                guardrail_bundle_update_candidate,
                ("guardrail_owner", "owner", "assigned_owner"),
                "ppd-guardrail-reviewer",
            ),
        },
        "expected_outputs": [
            "metadata_only_requirement_rerun_packet",
            "metadata_only_reviewer_disposition",
            "metadata_only_guardrail_reference_update_candidate",
        ],
        "attestations": {
            "no_live_extraction": True,
            "no_source_fetching": True,
            "no_processor_invocation": True,
            "no_raw_archive_reads": True,
            "no_requirement_record_mutation": True,
            "metadata_only_outputs": True,
        },
    }


def _extract_values_by_key(items: Iterable[Any], keys: set[str]) -> list[str]:
    values: list[str] = []
    for item in items:
        if isinstance(item, dict):
            for key, value in item.items():
                if key in keys:
                    values.extend(_string_values(value))
                values.extend(_extract_values_by_key((value,), keys))
        elif isinstance(item, list):
            values.extend(_extract_values_by_key(item, keys))
    return values


def _string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        result: list[str] = []
        for item in value:
            result.extend(_string_values(item))
        return result
    if isinstance(value, dict):
        for candidate_key in ("id", "ref", "name"):
            candidate = value.get(candidate_key)
            if isinstance(candidate, str):
                return [candidate]
    return []


def _ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result


def _first_present(packet: RequirementPacket, keys: tuple[str, ...], default: str) -> str:
    for key in keys:
        value = packet.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return default
