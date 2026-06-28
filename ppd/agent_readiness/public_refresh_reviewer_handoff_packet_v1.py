"""Fixture-first public refresh reviewer handoff packet v1.

This module joins synthetic citation impact queue rows with public refresh
preflight checklist rows and emits a reviewer-ready handoff packet. It is
strictly offline and metadata-only: no crawling, document retrieval, DevHub
access, release activation, raw artifact persistence, or official action is
performed or represented as complete.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

PACKET_VERSION = "public-refresh-reviewer-handoff-packet-v1"

EXACT_OFFLINE_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "-m", "py_compile", "ppd/agent_readiness/public_refresh_reviewer_handoff_packet_v1.py"),
    ("python3", "-m", "pytest", "ppd/tests/test_public_refresh_reviewer_handoff_packet_v1.py"),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

PRIORITY_BY_SIGNAL = {
    "source_removed": 10,
    "stale_source": 90,
    "changed_hash": 80,
    "redirect_change": 70,
    "citation_gap": 60,
    "missing_citation_span": 60,
    "processor_handoff_failure": 50,
}

REQUIRED_FALSE_FLAGS = (
    "live_crawl",
    "live_extraction",
    "document_download",
    "raw_output_stored",
    "devhub_opened",
    "release_activation",
    "official_action_completed",
    "active_mutation",
    "active_requirement_mutation",
    "active_process_model_mutation",
    "active_guardrail_mutation",
)

SENSITIVE_OR_RUNTIME_KEYS = frozenset(
    {
        "auth_state",
        "browser_trace",
        "cookie",
        "credential",
        "downloaded_artifact",
        "downloaded_document",
        "downloaded_pdf",
        "har",
        "html_body",
        "local_path",
        "password",
        "private_artifact",
        "raw_artifact",
        "raw_body",
        "raw_crawl_output",
        "raw_download",
        "raw_html",
        "raw_output",
        "raw_pdf",
        "screenshot",
        "session_state",
        "trace",
        "warc_path",
    }
)

PROHIBITED_CLAIM_PHRASES = frozenset(
    {
        "active guardrail mutation",
        "active process model mutation",
        "active requirement mutation",
        "certification completed",
        "devhub opened",
        "downloaded document",
        "live crawl completed",
        "official action completed",
        "payment completed",
        "permit guaranteed",
        "raw output stored",
        "release activated",
        "submission completed",
        "upload completed",
    }
)


@dataclass(frozen=True)
class CitationImpactQueueRow:
    row_id: str
    source_id: str
    canonical_url: str
    metadata_dry_run_reference_id: str
    manifest_id: str
    document_id: str
    citation_span_ids: tuple[str, ...]
    affected_requirement_ids: tuple[str, ...]
    affected_process_model_ids: tuple[str, ...]
    affected_guardrail_bundle_ids: tuple[str, ...]
    refresh_signal: str
    stale_source_hold_impact: str
    human_review_route: str
    rollback_note: str

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "CitationImpactQueueRow":
        _reject_runtime_or_private_content(row)
        if row.get("synthetic_citation_impact_queue_row") is not True:
            raise ValueError("citation impact row must declare synthetic_citation_impact_queue_row true")
        for flag in REQUIRED_FALSE_FLAGS:
            if row.get(flag) is not False:
                raise ValueError(f"citation impact row must declare {flag} false")
        refresh_signal = _required_text(row, "refresh_signal")
        if refresh_signal not in PRIORITY_BY_SIGNAL:
            raise ValueError(f"unsupported refresh_signal: {refresh_signal}")
        return cls(
            row_id=_required_text(row, "row_id"),
            source_id=_required_text(row, "source_id"),
            canonical_url=_required_text(row, "canonical_url"),
            metadata_dry_run_reference_id=_required_text(row, "metadata_dry_run_reference_id"),
            manifest_id=_required_text(row, "manifest_id"),
            document_id=_required_text(row, "document_id"),
            citation_span_ids=_required_text_tuple(row, "citation_span_ids"),
            affected_requirement_ids=_required_text_tuple(row, "affected_requirement_ids"),
            affected_process_model_ids=_required_text_tuple(row, "affected_process_model_ids"),
            affected_guardrail_bundle_ids=_required_text_tuple(row, "affected_guardrail_bundle_ids"),
            refresh_signal=refresh_signal,
            stale_source_hold_impact=_required_text(row, "stale_source_hold_impact"),
            human_review_route=_required_text(row, "human_review_route"),
            rollback_note=_required_text(row, "rollback_note"),
        )


@dataclass(frozen=True)
class PublicRefreshPreflightChecklistRow:
    row_id: str
    source_id: str
    canonical_url: str
    official_anchor_citation: str
    seed_review_references: tuple[str, ...]
    metadata_only_archive_manifest_expectation: str
    skip_reason_expectation: str
    reviewer_routing: str
    rollback_note: str
    owner: str
    dependency_after: tuple[str, ...]

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "PublicRefreshPreflightChecklistRow":
        _reject_runtime_or_private_content(row)
        if row.get("synthetic_public_refresh_preflight_checklist_row") is not True:
            raise ValueError("preflight checklist row must declare synthetic_public_refresh_preflight_checklist_row true")
        for flag in REQUIRED_FALSE_FLAGS:
            if row.get(flag) is not False:
                raise ValueError(f"preflight checklist row must declare {flag} false")
        for flag in ("metadata_only_capture", "metadata_only_archive_manifest", "no_raw_body_persisted"):
            if row.get(flag) is not True:
                raise ValueError(f"preflight checklist row must declare {flag} true")
        return cls(
            row_id=_required_text(row, "row_id"),
            source_id=_required_text(row, "source_id"),
            canonical_url=_required_text(row, "canonical_url"),
            official_anchor_citation=_required_text(row, "official_anchor_citation"),
            seed_review_references=_required_text_tuple(row, "seed_review_references"),
            metadata_only_archive_manifest_expectation=_required_text(row, "metadata_only_archive_manifest_expectation"),
            skip_reason_expectation=_required_text(row, "skip_reason_expectation"),
            reviewer_routing=_required_text(row, "reviewer_routing"),
            rollback_note=_required_text(row, "rollback_note"),
            owner=_required_text(row, "owner"),
            dependency_after=_optional_text_tuple(row, "dependency_after"),
        )


def build_public_refresh_reviewer_handoff_packet(
    citation_impact_queue_rows: Iterable[Mapping[str, Any]],
    public_refresh_preflight_checklist_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Assemble the offline reviewer handoff packet from synthetic rows only."""

    citation_rows = tuple(CitationImpactQueueRow.from_mapping(row) for row in citation_impact_queue_rows)
    preflight_rows = tuple(PublicRefreshPreflightChecklistRow.from_mapping(row) for row in public_refresh_preflight_checklist_rows)
    if not citation_rows:
        raise ValueError("at least one synthetic citation impact queue row is required")
    if not preflight_rows:
        raise ValueError("at least one public refresh preflight checklist row is required")

    preflight_by_source = {row.source_id: row for row in preflight_rows}
    missing_preflight = sorted({row.source_id for row in citation_rows if row.source_id not in preflight_by_source})
    if missing_preflight:
        raise ValueError(f"citation rows missing preflight checklist rows: {missing_preflight}")

    decisions = [_seed_decision(row, preflight_by_source[row.source_id]) for row in citation_rows]
    packet = {
        "packet_version": PACKET_VERSION,
        "mode": "fixture_first_offline_reviewer_handoff_only",
        "input_contract": "synthetic_citation_impact_queue_rows_and_public_refresh_preflight_checklist_rows_only",
        "citation_impact_row_count": len(citation_rows),
        "preflight_checklist_row_count": len(preflight_rows),
        "reviewer_ready_seed_decisions": sorted(decisions, key=lambda item: item["decision_id"]),
        "metadata_only_archive_expectations": _archive_expectations(preflight_rows),
        "citation_refresh_priorities": _citation_priorities(citation_rows),
        "stale_source_hold_recommendations": _stale_source_holds(citation_rows),
        "owner_routing": _owner_routing(citation_rows, preflight_by_source),
        "dependency_ordering": _dependency_ordering(citation_rows, preflight_by_source),
        "rollback_checkpoints": _rollback_checkpoints(citation_rows, preflight_by_source),
        "exact_offline_validation_commands": [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS],
        "prohibited_actions": [
            "live_crawling",
            "live_extraction",
            "document_download",
            "raw_output_storage",
            "devhub_access",
            "release_activation",
            "active_requirement_mutation",
            "active_process_model_mutation",
            "active_guardrail_mutation",
            "official_action",
        ],
        "attestations": {
            "fixture_first": True,
            "synthetic_metadata_only": True,
            "no_live_crawling": True,
            "no_live_extraction": True,
            "no_document_downloads": True,
            "no_raw_output_storage": True,
            "no_devhub_access": True,
            "no_release_activation": True,
            "no_official_actions": True,
        },
    }
    validate_public_refresh_reviewer_handoff_packet(packet)
    return packet


def load_public_refresh_reviewer_handoff_fixture(path: Path) -> tuple[tuple[dict[str, Any], ...], tuple[dict[str, Any], ...]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fixture must be a JSON object")
    _reject_runtime_or_private_content(payload)
    citation_rows = payload.get("citation_impact_queue_rows")
    preflight_rows = payload.get("public_refresh_preflight_checklist_rows")
    if not isinstance(citation_rows, list) or not all(isinstance(row, dict) for row in citation_rows):
        raise ValueError("fixture must contain citation_impact_queue_rows objects")
    if not isinstance(preflight_rows, list) or not all(isinstance(row, dict) for row in preflight_rows):
        raise ValueError("fixture must contain public_refresh_preflight_checklist_rows objects")
    return tuple(citation_rows), tuple(preflight_rows)


def build_handoff_packet_from_fixture(path: Path) -> dict[str, Any]:
    citation_rows, preflight_rows = load_public_refresh_reviewer_handoff_fixture(path)
    return build_public_refresh_reviewer_handoff_packet(citation_rows, preflight_rows)


def validate_public_refresh_reviewer_handoff_packet(packet: Mapping[str, Any]) -> None:
    _reject_runtime_or_private_content(packet)
    if packet.get("packet_version") != PACKET_VERSION:
        raise ValueError("packet_version must be public-refresh-reviewer-handoff-packet-v1")
    if packet.get("mode") != "fixture_first_offline_reviewer_handoff_only":
        raise ValueError("packet must remain fixture_first_offline_reviewer_handoff_only")
    for key in (
        "reviewer_ready_seed_decisions",
        "metadata_only_archive_expectations",
        "citation_refresh_priorities",
        "stale_source_hold_recommendations",
        "owner_routing",
        "dependency_ordering",
        "rollback_checkpoints",
    ):
        if not _non_empty_list_of_mappings(packet.get(key)):
            raise ValueError(f"{key} must contain at least one reviewer-ready row")
    if packet.get("exact_offline_validation_commands") != [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]:
        raise ValueError("packet must include exact offline validation commands")
    attestations = packet.get("attestations")
    if not isinstance(attestations, Mapping):
        raise ValueError("packet must include attestations")
    for key in (
        "fixture_first",
        "synthetic_metadata_only",
        "no_live_crawling",
        "no_live_extraction",
        "no_document_downloads",
        "no_raw_output_storage",
        "no_devhub_access",
        "no_release_activation",
        "no_official_actions",
    ):
        if attestations.get(key) is not True:
            raise ValueError(f"packet attestation {key} must be true")
    for section in ("reviewer_ready_seed_decisions", "citation_refresh_priorities", "rollback_checkpoints"):
        for row in packet[section]:
            for flag in REQUIRED_FALSE_FLAGS:
                if row.get(flag) is not False:
                    raise ValueError(f"{section} row must declare {flag} false")


def _seed_decision(citation: CitationImpactQueueRow, preflight: PublicRefreshPreflightChecklistRow) -> dict[str, Any]:
    return {
        "decision_id": f"seed-decision::{citation.row_id}",
        "source_id": citation.source_id,
        "canonical_url": citation.canonical_url,
        "seed_decision": "reviewer_hold_pending_preflight_and_citation_confirmation",
        "decision_basis": "synthetic citation impact row joined to synthetic public refresh preflight checklist row",
        "seed_review_references": list(preflight.seed_review_references),
        "metadata_dry_run_reference_id": citation.metadata_dry_run_reference_id,
        "official_anchor_citation": preflight.official_anchor_citation,
        "owner": preflight.owner,
        "reviewer_route": citation.human_review_route,
        "live_crawl": False,
        "live_extraction": False,
        "document_download": False,
        "raw_output_stored": False,
        "devhub_opened": False,
        "release_activation": False,
        "official_action_completed": False,
        "active_mutation": False,
        "active_requirement_mutation": False,
        "active_process_model_mutation": False,
        "active_guardrail_mutation": False,
    }


def _archive_expectations(rows: Sequence[PublicRefreshPreflightChecklistRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "expectation_id": f"archive-expectation::{row.row_id}",
                "source_id": row.source_id,
                "canonical_url": row.canonical_url,
                "metadata_only_archive_manifest_expectation": row.metadata_only_archive_manifest_expectation,
                "skip_reason_expectation": row.skip_reason_expectation,
                "no_raw_body_persisted": True,
                "document_download": False,
                "live_crawl": False,
            }
            for row in rows
        ),
        key=lambda item: item["expectation_id"],
    )


def _citation_priorities(rows: Sequence[CitationImpactQueueRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "priority_id": f"citation-priority::{row.row_id}",
                "source_id": row.source_id,
                "citation_span_ids": list(row.citation_span_ids),
                "refresh_signal": row.refresh_signal,
                "priority_rank": PRIORITY_BY_SIGNAL[row.refresh_signal],
                "affected_requirement_ids": list(row.affected_requirement_ids),
                "affected_process_model_ids": list(row.affected_process_model_ids),
                "affected_guardrail_bundle_ids": list(row.affected_guardrail_bundle_ids),
                "live_crawl": False,
                "live_extraction": False,
                "document_download": False,
                "raw_output_stored": False,
                "devhub_opened": False,
                "release_activation": False,
                "official_action_completed": False,
                "active_mutation": False,
                "active_requirement_mutation": False,
                "active_process_model_mutation": False,
                "active_guardrail_mutation": False,
            }
            for row in rows
        ),
        key=lambda item: (item["priority_rank"], item["priority_id"]),
        reverse=True,
    )


def _stale_source_holds(rows: Sequence[CitationImpactQueueRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "hold_id": f"stale-source-hold::{row.row_id}",
                "source_id": row.source_id,
                "recommendation": "keep_agent_hold_until_reviewer_confirms_public_refresh",
                "stale_source_hold_impact": row.stale_source_hold_impact,
                "agent_may_treat_source_as_current": False,
            }
            for row in rows
        ),
        key=lambda item: item["hold_id"],
    )


def _owner_routing(rows: Sequence[CitationImpactQueueRow], preflight_by_source: Mapping[str, PublicRefreshPreflightChecklistRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "route_id": f"owner-route::{row.row_id}",
                "source_id": row.source_id,
                "owner": preflight_by_source[row.source_id].owner,
                "reviewer_route": row.human_review_route,
                "routing_reason": "citation impact and preflight checklist both require reviewer disposition",
            }
            for row in rows
        ),
        key=lambda item: item["route_id"],
    )


def _dependency_ordering(rows: Sequence[CitationImpactQueueRow], preflight_by_source: Mapping[str, PublicRefreshPreflightChecklistRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "dependency_id": f"dependency::{row.row_id}",
                "source_id": row.source_id,
                "ordered_steps": list(preflight_by_source[row.source_id].dependency_after)
                + [
                    "confirm metadata-only archive expectation",
                    "confirm citation refresh priority",
                    "confirm stale-source hold disposition",
                    "record reviewer seed decision",
                ],
            }
            for row in rows
        ),
        key=lambda item: item["dependency_id"],
    )


def _rollback_checkpoints(rows: Sequence[CitationImpactQueueRow], preflight_by_source: Mapping[str, PublicRefreshPreflightChecklistRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "rollback_id": f"rollback::{row.row_id}",
                "source_id": row.source_id,
                "citation_rollback_note": row.rollback_note,
                "preflight_rollback_note": preflight_by_source[row.source_id].rollback_note,
                "active_state_changed": False,
                "live_crawl": False,
                "live_extraction": False,
                "document_download": False,
                "raw_output_stored": False,
                "devhub_opened": False,
                "release_activation": False,
                "official_action_completed": False,
                "active_mutation": False,
                "active_requirement_mutation": False,
                "active_process_model_mutation": False,
                "active_guardrail_mutation": False,
            }
            for row in rows
        ),
        key=lambda item: item["rollback_id"],
    )


def _reject_runtime_or_private_content(value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key).lower()
            if key_text in SENSITIVE_OR_RUNTIME_KEYS:
                raise ValueError(f"{path} contains runtime, raw, downloaded, or private key: {key}")
            _reject_runtime_or_private_content(nested, f"{path}.{key}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested in enumerate(value):
            _reject_runtime_or_private_content(nested, f"{path}[{index}]")
    elif isinstance(value, str):
        normalized = " ".join(value.lower().replace("_", " ").replace("-", " ").split())
        for phrase in PROHIBITED_CLAIM_PHRASES:
            if phrase in normalized:
                raise ValueError(f"{path} contains prohibited claim phrase: {phrase}")


def _required_text(row: Mapping[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _required_text_tuple(row: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = row.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)) or not value:
        raise ValueError(f"{key} must be a non-empty list of strings")
    output = tuple(item for item in value if isinstance(item, str) and item.strip())
    if len(output) != len(value):
        raise ValueError(f"{key} must contain only non-empty strings")
    return output


def _optional_text_tuple(row: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = row.get(key, ())
    if value in (None, ()):
        return ()
    return _required_text_tuple(row, key)


def _non_empty_list_of_mappings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, Mapping) for item in value)
