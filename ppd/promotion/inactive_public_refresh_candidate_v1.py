"""Fixture-first inactive public refresh promotion candidate assembly.

This module intentionally consumes only synthetic reviewer bundle packet rows.
It does not crawl, download, open DevHub, persist raw output, activate releases,
or perform official actions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

_ALLOWED_PACKET_KINDS = {
    "source_registry",
    "archive_manifest",
    "document_record",
    "requirement_node",
    "process_model",
    "guardrail_bundle",
    "agent_readiness_reference",
    "promotion_precondition",
    "reviewer_approval",
    "rollback_checkpoint",
}

_FORBIDDEN_PAYLOAD_KEYS = {
    "raw_output",
    "raw_body",
    "raw_html",
    "raw_pdf",
    "downloaded_document",
    "devhub_session",
    "auth_state",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "password",
    "trace",
    "har",
    "screenshot",
    "payment_details",
}

_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/promotion/inactive_public_refresh_candidate_v1.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_inactive_public_refresh_candidate_v1.py"],
]


@dataclass(frozen=True)
class ReviewerBundlePacketRow:
    """One synthetic row in a reviewer bundle packet fixture."""

    packet_id: str
    packet_kind: str
    payload: dict[str, Any]

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "ReviewerBundlePacketRow":
        packet_id = _require_text(row, "packet_id")
        packet_kind = _require_text(row, "packet_kind")
        if packet_kind not in _ALLOWED_PACKET_KINDS:
            raise ValueError(f"Unsupported packet_kind for {packet_id}: {packet_kind}")
        payload = row.get("payload")
        if not isinstance(payload, dict):
            raise ValueError(f"packet {packet_id} payload must be an object")
        _reject_forbidden_payload(packet_id, payload)
        if payload.get("synthetic") is not True:
            raise ValueError(f"packet {packet_id} must be marked synthetic")
        return cls(packet_id=packet_id, packet_kind=packet_kind, payload=payload)


def load_reviewer_bundle_packet_rows(path: Path) -> list[ReviewerBundlePacketRow]:
    """Load newline-delimited synthetic reviewer bundle packet rows."""

    rows: list[ReviewerBundlePacketRow] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number}: {exc.msg}") from exc
        if not isinstance(parsed, dict):
            raise ValueError(f"Line {line_number} must be a JSON object")
        rows.append(ReviewerBundlePacketRow.from_mapping(parsed))
    if not rows:
        raise ValueError("reviewer bundle packet fixture is empty")
    return rows


def assemble_inactive_public_refresh_candidate_v1(
    rows: Iterable[ReviewerBundlePacketRow],
) -> dict[str, Any]:
    """Assemble an inactive promotion candidate from synthetic packet rows only."""

    grouped: dict[str, list[dict[str, Any]]] = {kind: [] for kind in _ALLOWED_PACKET_KINDS}
    packet_ids: set[str] = set()

    for row in rows:
        if row.packet_id in packet_ids:
            raise ValueError(f"Duplicate packet_id: {row.packet_id}")
        packet_ids.add(row.packet_id)
        grouped[row.packet_kind].append(_without_synthetic_marker(row.payload))

    _require_non_empty(grouped, "source_registry", "SourceRegistry")
    _require_non_empty(grouped, "archive_manifest", "ArchiveManifest")
    _require_non_empty(grouped, "document_record", "DocumentRecord")
    _require_non_empty(grouped, "requirement_node", "RequirementNode")
    _require_non_empty(grouped, "process_model", "ProcessModel")
    _require_non_empty(grouped, "guardrail_bundle", "GuardrailBundle")
    _require_non_empty(grouped, "agent_readiness_reference", "agent-readiness reference")
    _require_non_empty(grouped, "promotion_precondition", "promotion precondition")
    _require_non_empty(grouped, "reviewer_approval", "reviewer approval")
    _require_non_empty(grouped, "rollback_checkpoint", "rollback checkpoint")

    approvals = grouped["reviewer_approval"]
    if not all(approval.get("approval_status") == "approved_for_inactive_candidate" for approval in approvals):
        raise ValueError("All reviewer approvals must be approved_for_inactive_candidate")

    preconditions = grouped["promotion_precondition"]
    if not all(precondition.get("satisfied") is True for precondition in preconditions):
        raise ValueError("All promotion preconditions must be satisfied")

    return {
        "candidate_id": "inactive-public-refresh-promotion-candidate-v1",
        "candidate_version": 1,
        "promotion_state": "inactive_candidate_only",
        "input_policy": {
            "source": "synthetic_reviewer_bundle_packet_rows_only",
            "live_crawling_allowed": False,
            "document_download_allowed": False,
            "raw_output_storage_allowed": False,
            "devhub_open_allowed": False,
            "active_artifact_promotion_allowed": False,
            "release_activation_allowed": False,
            "official_actions_allowed": False,
        },
        "manifests": {
            "source_registries": grouped["source_registry"],
            "archive_manifests": grouped["archive_manifest"],
            "document_records": grouped["document_record"],
            "requirement_nodes": grouped["requirement_node"],
            "process_models": grouped["process_model"],
            "guardrail_bundles": grouped["guardrail_bundle"],
            "agent_readiness_references": grouped["agent_readiness_reference"],
        },
        "promotion_preconditions": preconditions,
        "reviewer_approvals": approvals,
        "rollback_checkpoints": grouped["rollback_checkpoint"],
        "offline_validation_commands": _OFFLINE_VALIDATION_COMMANDS,
    }


def assemble_inactive_public_refresh_candidate_from_fixture(path: Path) -> dict[str, Any]:
    return assemble_inactive_public_refresh_candidate_v1(load_reviewer_bundle_packet_rows(path))


def _require_text(row: dict[str, Any], key: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _reject_forbidden_payload(packet_id: str, value: Any) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized_key = str(key).lower()
            if normalized_key in _FORBIDDEN_PAYLOAD_KEYS:
                raise ValueError(f"packet {packet_id} contains forbidden payload key: {key}")
            _reject_forbidden_payload(packet_id, child)
    elif isinstance(value, list):
        for child in value:
            _reject_forbidden_payload(packet_id, child)


def _without_synthetic_marker(payload: dict[str, Any]) -> dict[str, Any]:
    copied = dict(payload)
    copied.pop("synthetic", None)
    return copied


def _require_non_empty(grouped: dict[str, list[dict[str, Any]]], key: str, label: str) -> None:
    if not grouped[key]:
        raise ValueError(f"Missing required {label} packet")
