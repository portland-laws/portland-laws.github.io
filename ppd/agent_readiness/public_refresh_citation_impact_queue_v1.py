"""Fixture-first public refresh citation impact queue v1.

This module consumes only synthetic metadata manifest dry-run plan rows and
produces an offline reviewer queue for citation-span refresh impacts. It does
not crawl, download, extract live content, open DevHub, store raw output, mutate
active requirements, mutate process models, mutate guardrails, or perform any
official action.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

QUEUE_VERSION = "public-refresh-citation-impact-queue-v1"

EXACT_OFFLINE_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "-m", "py_compile", "ppd/agent_readiness/public_refresh_citation_impact_queue_v1.py"),
    ("python3", "-m", "pytest", "ppd/tests/test_public_refresh_citation_impact_queue_v1.py"),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

REFRESH_SIGNALS = frozenset(
    {
        "changed_hash",
        "citation_gap",
        "missing_citation_span",
        "processor_handoff_failure",
        "redirect_change",
        "source_removed",
        "stale_source",
    }
)

PROHIBITED_ACTIONS: tuple[str, ...] = (
    "live_extraction",
    "live_crawling",
    "document_download",
    "raw_output_storage",
    "devhub_access",
    "active_requirement_mutation",
    "active_process_model_mutation",
    "active_guardrail_mutation",
    "official_action",
    "submission",
    "certification",
    "upload",
    "payment",
    "inspection_scheduling",
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
        "active mutation enabled",
        "active process model mutation",
        "active requirement mutation",
        "certification completed",
        "devhub opened",
        "downloaded artifact",
        "downloaded document",
        "guaranteed approval",
        "guaranteed permit",
        "legal advice",
        "live crawl completed",
        "live crawl performed",
        "official action completed",
        "payment completed",
        "permit guaranteed",
        "raw artifact stored",
        "raw output stored",
        "submission completed",
        "upload completed",
    }
)

REQUIRED_FALSE_FLAGS = (
    "active_guardrail_mutation",
    "active_mutation",
    "active_process_model_mutation",
    "active_requirement_mutation",
    "devhub_opened",
    "document_download",
    "legal_or_permitting_guarantee",
    "live_crawl",
    "live_extraction",
    "official_action_completed",
    "raw_output_stored",
)


@dataclass(frozen=True)
class SyntheticMetadataManifestDryRunPlanRow:
    """Synthetic manifest row used to plan citation refresh review."""

    row_id: str
    plan_id: str
    metadata_dry_run_reference_id: str
    source_id: str
    canonical_url: str
    manifest_id: str
    document_id: str
    citation_span_ids: tuple[str, ...]
    affected_requirement_ids: tuple[str, ...]
    affected_process_model_ids: tuple[str, ...]
    affected_guardrail_bundle_ids: tuple[str, ...]
    refresh_signal: str
    stale_source_hold_impact: str
    extraction_confidence_placeholder: str
    human_review_route: str
    rollback_note: str
    dry_run_evidence: str

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "SyntheticMetadataManifestDryRunPlanRow":
        _reject_runtime_or_private_content(row)
        if row.get("synthetic_metadata_manifest_dry_run_plan_row") is not True:
            raise ValueError("row must declare synthetic_metadata_manifest_dry_run_plan_row true")
        for flag in REQUIRED_FALSE_FLAGS:
            if row.get(flag) is not False:
                raise ValueError(f"row must declare {flag} false")

        refresh_signal = _required_text(row, "refresh_signal")
        if refresh_signal not in REFRESH_SIGNALS:
            raise ValueError(f"unsupported refresh_signal: {refresh_signal}")

        return cls(
            row_id=_required_text(row, "row_id"),
            plan_id=_required_text(row, "plan_id"),
            metadata_dry_run_reference_id=_required_text(row, "metadata_dry_run_reference_id"),
            source_id=_required_text(row, "source_id"),
            canonical_url=_required_text(row, "canonical_url"),
            manifest_id=_required_text(row, "manifest_id"),
            document_id=_required_text(row, "document_id"),
            citation_span_ids=_required_text_tuple(row, "citation_span_ids"),
            affected_requirement_ids=_required_text_tuple(row, "affected_requirement_ids"),
            affected_process_model_ids=_required_text_tuple(row, "affected_process_model_ids"),
            affected_guardrail_bundle_ids=_required_text_tuple(row, "affected_guardrail_bundle_ids"),
            refresh_signal=refresh_signal,
            stale_source_hold_impact=_required_text(row, "stale_source_hold_impact"),
            extraction_confidence_placeholder=_required_text(row, "extraction_confidence_placeholder"),
            human_review_route=_required_text(row, "human_review_route"),
            rollback_note=_required_text(row, "rollback_note"),
            dry_run_evidence=_required_text(row, "dry_run_evidence"),
        )


def build_public_refresh_citation_impact_queue(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Build a deterministic offline citation impact queue from synthetic rows."""

    normalized_rows = tuple(SyntheticMetadataManifestDryRunPlanRow.from_mapping(row) for row in rows)
    if not normalized_rows:
        raise ValueError("at least one citation-span refresh candidate row is required")

    candidates = [_candidate_from_row(row) for row in normalized_rows]
    candidates = sorted(candidates, key=lambda item: item["candidate_id"])

    queue = {
        "queue_version": QUEUE_VERSION,
        "mode": "fixture_first_offline_review_only",
        "input_contract": "synthetic_metadata_manifest_dry_run_plan_rows_only",
        "input_row_count": len(normalized_rows),
        "candidate_count": len(candidates),
        "metadata_dry_run_reference_ids": _sorted_unique(row.metadata_dry_run_reference_id for row in normalized_rows),
        "affected_requirement_ids": _sorted_unique(_flatten(row.affected_requirement_ids for row in normalized_rows)),
        "affected_process_model_ids": _sorted_unique(_flatten(row.affected_process_model_ids for row in normalized_rows)),
        "affected_guardrail_bundle_ids": _sorted_unique(_flatten(row.affected_guardrail_bundle_ids for row in normalized_rows)),
        "citation_span_refresh_candidates": candidates,
        "stale_source_hold_impacts": _hold_impacts(normalized_rows),
        "human_review_routes": _review_routes(normalized_rows),
        "rollback_notes": _rollback_notes(normalized_rows),
        "exact_offline_validation_commands": [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS],
        "prohibited_actions": list(PROHIBITED_ACTIONS),
        "attestations": {
            "fixture_first": True,
            "synthetic_metadata_only": True,
            "no_live_extraction": True,
            "no_live_crawling": True,
            "no_document_downloads": True,
            "no_raw_output_storage": True,
            "no_devhub_access": True,
            "no_active_requirement_mutation": True,
            "no_active_process_model_mutation": True,
            "no_active_guardrail_mutation": True,
            "no_official_actions": True,
            "no_legal_or_permitting_guarantees": True,
        },
    }
    validate_public_refresh_citation_impact_queue(queue)
    return queue


def validate_public_refresh_citation_impact_queue(queue: Mapping[str, Any]) -> None:
    """Reject incomplete or unsafe public refresh citation impact queues."""

    _reject_runtime_or_private_content(queue)
    if queue.get("queue_version") != QUEUE_VERSION:
        raise ValueError("queue_version must be public-refresh-citation-impact-queue-v1")
    if queue.get("mode") != "fixture_first_offline_review_only":
        raise ValueError("queue must remain fixture_first_offline_review_only")
    if not _non_empty_list_of_strings(queue.get("metadata_dry_run_reference_ids")):
        raise ValueError("queue must include metadata dry-run reference ids")
    if not _non_empty_list_of_mappings(queue.get("citation_span_refresh_candidates")):
        raise ValueError("queue must include citation-span refresh candidates")
    if not _non_empty_list_of_strings(queue.get("affected_requirement_ids")):
        raise ValueError("queue must include affected requirement identifiers")
    if not _non_empty_list_of_strings(queue.get("affected_process_model_ids")):
        raise ValueError("queue must include affected process-model identifiers")
    if not _non_empty_list_of_strings(queue.get("affected_guardrail_bundle_ids")):
        raise ValueError("queue must include affected guardrail identifiers")
    if not _non_empty_list_of_mappings(queue.get("stale_source_hold_impacts")):
        raise ValueError("queue must include stale-source hold impacts")
    if not _non_empty_list_of_mappings(queue.get("human_review_routes")):
        raise ValueError("queue must include human-review routing")
    if not _non_empty_list_of_mappings(queue.get("rollback_notes")):
        raise ValueError("queue must include rollback notes")
    if queue.get("exact_offline_validation_commands") != [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]:
        raise ValueError("queue must include exact offline validation commands")

    for candidate in queue["citation_span_refresh_candidates"]:
        _require_candidate_controls(candidate)

    attestations = queue.get("attestations")
    if not isinstance(attestations, Mapping):
        raise ValueError("queue must include attestations")
    for key in (
        "fixture_first",
        "synthetic_metadata_only",
        "no_live_extraction",
        "no_live_crawling",
        "no_document_downloads",
        "no_raw_output_storage",
        "no_devhub_access",
        "no_active_requirement_mutation",
        "no_active_process_model_mutation",
        "no_active_guardrail_mutation",
        "no_official_actions",
        "no_legal_or_permitting_guarantees",
    ):
        if attestations.get(key) is not True:
            raise ValueError(f"queue attestation {key} must be true")


def load_synthetic_metadata_manifest_dry_run_plan_rows(path: Path) -> tuple[dict[str, Any], ...]:
    """Load committed synthetic plan rows without touching live sources."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("fixture must be a JSON object")
    _reject_runtime_or_private_content(payload)
    rows = payload.get("synthetic_metadata_manifest_dry_run_plan_rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("fixture must contain non-empty synthetic_metadata_manifest_dry_run_plan_rows list")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("each synthetic metadata manifest dry-run plan row must be an object")
    return tuple(rows)


def build_queue_from_fixture(path: Path) -> dict[str, Any]:
    """Build the queue from a fixture path."""

    return build_public_refresh_citation_impact_queue(load_synthetic_metadata_manifest_dry_run_plan_rows(path))


def _candidate_from_row(row: SyntheticMetadataManifestDryRunPlanRow) -> dict[str, Any]:
    return {
        "candidate_id": f"citation-refresh::{row.row_id}",
        "metadata_dry_run_reference_id": row.metadata_dry_run_reference_id,
        "source_id": row.source_id,
        "canonical_url": row.canonical_url,
        "manifest_id": row.manifest_id,
        "document_id": row.document_id,
        "citation_span_ids": list(row.citation_span_ids),
        "refresh_signal": row.refresh_signal,
        "affected_requirement_ids": list(row.affected_requirement_ids),
        "affected_process_model_ids": list(row.affected_process_model_ids),
        "affected_guardrail_bundle_ids": list(row.affected_guardrail_bundle_ids),
        "stale_source_hold_impact": row.stale_source_hold_impact,
        "extraction_confidence_placeholder": row.extraction_confidence_placeholder,
        "human_review_route": row.human_review_route,
        "rollback_note": row.rollback_note,
        "dry_run_evidence": row.dry_run_evidence,
        "allowed_next_action": "human_review_of_fixture_queue_only",
        "requires_live_extraction": False,
        "requires_live_crawl": False,
        "requires_document_download": False,
        "stores_raw_output": False,
        "opens_devhub": False,
        "mutates_active_requirements": False,
        "mutates_active_process_models": False,
        "mutates_active_guardrails": False,
        "official_action_completed": False,
        "legal_or_permitting_guarantee": False,
    }


def _hold_impacts(rows: Sequence[SyntheticMetadataManifestDryRunPlanRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "hold_id": f"stale-source-hold::{row.row_id}",
                "source_id": row.source_id,
                "citation_span_ids": list(row.citation_span_ids),
                "impact": row.stale_source_hold_impact,
                "affected_requirement_ids": list(row.affected_requirement_ids),
                "affected_process_model_ids": list(row.affected_process_model_ids),
                "affected_guardrail_bundle_ids": list(row.affected_guardrail_bundle_ids),
                "agent_may_treat_source_as_current": False,
            }
            for row in rows
        ),
        key=lambda item: item["hold_id"],
    )


def _review_routes(rows: Sequence[SyntheticMetadataManifestDryRunPlanRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "route_id": f"human-review::{row.row_id}",
                "human_review_route": row.human_review_route,
                "candidate_id": f"citation-refresh::{row.row_id}",
                "required_review_decision": "confirm_refresh_candidate_or_keep_hold",
            }
            for row in rows
        ),
        key=lambda item: item["route_id"],
    )


def _rollback_notes(rows: Sequence[SyntheticMetadataManifestDryRunPlanRow]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "rollback_id": f"rollback-note::{row.row_id}",
                "candidate_id": f"citation-refresh::{row.row_id}",
                "rollback_note": row.rollback_note,
                "active_state_changed": False,
            }
            for row in rows
        ),
        key=lambda item: item["rollback_id"],
    )


def _require_candidate_controls(candidate: Mapping[str, Any]) -> None:
    for key in (
        "metadata_dry_run_reference_id",
        "candidate_id",
        "source_id",
        "manifest_id",
        "document_id",
        "refresh_signal",
        "stale_source_hold_impact",
        "extraction_confidence_placeholder",
        "human_review_route",
        "rollback_note",
        "dry_run_evidence",
    ):
        _required_text(candidate, key)
    for key in (
        "citation_span_ids",
        "affected_requirement_ids",
        "affected_process_model_ids",
        "affected_guardrail_bundle_ids",
    ):
        _required_text_tuple(candidate, key)
    for key in (
        "requires_live_extraction",
        "requires_live_crawl",
        "requires_document_download",
        "stores_raw_output",
        "opens_devhub",
        "mutates_active_requirements",
        "mutates_active_process_models",
        "mutates_active_guardrails",
        "official_action_completed",
        "legal_or_permitting_guarantee",
    ):
        if candidate.get(key) is not False:
            raise ValueError(f"candidate must declare {key} false")


def _reject_runtime_or_private_content(value: Any, path: str = "row") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key).lower()
            if key_text in SENSITIVE_OR_RUNTIME_KEYS:
                raise ValueError(f"{path} contains runtime, raw-output, downloaded, or private key: {key}")
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
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        raise ValueError(f"{key} must be a non-empty list of strings")
    output = tuple(item for item in value if isinstance(item, str) and item.strip())
    if len(output) != len(value):
        raise ValueError(f"{key} must contain only non-empty strings")
    return output


def _non_empty_list_of_strings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def _non_empty_list_of_mappings(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, Mapping) for item in value)


def _flatten(groups: Iterable[Iterable[str]]) -> tuple[str, ...]:
    return tuple(item for group in groups for item in group)


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted(set(values))
