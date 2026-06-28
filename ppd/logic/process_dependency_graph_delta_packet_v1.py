"""Fixture-first PP&D process dependency graph delta packet v1.

This module maps synthetic requirement delta candidates into inactive process
dependency graph impact rows. It is intentionally offline-only: it does not
promote process models, update active requirements, crawl sources, open DevHub,
or write daemon/release state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


class ProcessDependencyGraphDeltaPacketV1Error(ValueError):
    """Raised when a dependency graph delta packet is incomplete or unsafe."""


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str


EXACT_OFFLINE_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "-m", "py_compile", "ppd/logic/process_dependency_graph_delta_packet_v1.py"),
    ("python3", "-m", "pytest", "ppd/tests/test_process_dependency_graph_delta_packet_v1.py"),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

_REQUIRED_PACKET_FIELDS = (
    "packet_version",
    "packet_id",
    "source_fixture_id",
    "dependency_delta_rows",
    "affected_permit_family_rows",
    "process_stage_rows",
    "required_user_fact_rows",
    "required_document_rows",
    "fee_deadline_trigger_rows",
    "unsupported_path_rows",
    "devhub_boundary_reference_rows",
    "reviewer_hold_rows",
    "validation_commands",
    "offline_validation_commands",
    "mutation_policy",
)

_REQUIRED_CANDIDATE_FIELDS = (
    "candidate_id",
    "requirement_id",
    "delta_type",
    "affected_permit_families",
    "process_stages",
    "required_user_facts",
    "required_documents",
    "fee_deadline_triggers",
    "unsupported_paths",
    "devhub_boundary_refs",
    "reviewer_holds",
)

_ROW_GROUPS = (
    ("affected_permit_family_rows", "permit_family"),
    ("process_stage_rows", "process_stage"),
    ("required_user_fact_rows", "required_user_fact"),
    ("required_document_rows", "required_document"),
    ("fee_deadline_trigger_rows", "trigger"),
    ("unsupported_path_rows", "unsupported_path"),
    ("devhub_boundary_reference_rows", "devhub_boundary_ref"),
    ("reviewer_hold_rows", "reviewer_hold"),
)

_PRIVATE_ARTIFACT_KEYWORDS = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "download_path",
    "downloaded_artifact",
    "downloaded_document",
    "downloaded_file",
    "har",
    "local_private_path",
    "playwright_trace",
    "private_artifact",
    "raw_body",
    "raw_crawl_output",
    "raw_download",
    "raw_html",
    "screenshot",
    "session_file",
    "session_state",
    "trace_zip",
)

_PRIVATE_ARTIFACT_VALUE_MARKERS = (
    ".har",
    "trace.zip",
    "storage_state.json",
    "auth-state",
    "browser-state",
    "downloaded document",
    "downloaded/",
    "/downloads/",
    "/private/",
    "/session/",
    "raw crawl output",
    "raw-crawl-output",
    "raw_body",
    "raw_html",
)

_LIVE_OR_DEVHUB_CLAIM_MARKERS = (
    "authenticated devhub",
    "crawled live",
    "devhub login",
    "devhub session",
    "fetched live",
    "live crawl",
    "live devhub",
    "observed in devhub",
    "queried devhub",
    "ran playwright",
    "real browser session",
)

_GUARANTEE_MARKERS = (
    "guarantee",
    "guaranteed",
    "guarantees compliance",
    "legal advice",
    "legally sufficient",
    "official legal determination",
    "permit approval is assured",
    "permit is guaranteed",
    "permit will be approved",
    "permit will be issued",
    "will pass inspection",
)

_OFFICIAL_ACTION_COMPLETION_MARKERS = (
    "application submitted",
    "cancelled the permit",
    "certified the application",
    "completed official action",
    "inspection scheduled",
    "official record updated",
    "paid the fee",
    "payment submitted",
    "permit submitted",
    "scheduled inspection",
    "submitted application",
    "submitted the permit",
    "uploaded correction",
    "uploaded to devhub",
)

_ACTIVE_MUTATION_KEYS = (
    "active_mutation",
    "active_mutation_enabled",
    "allow_live_mutation",
    "live_mutation_enabled",
    "mutates_live_state",
    "official_action_enabled",
    "promotes_process_model",
    "writes_to_devhub",
)


def build_process_dependency_graph_delta_packet_v1(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Build an inactive dependency graph delta packet from synthetic candidates."""

    if not isinstance(fixture, Mapping):
        raise ProcessDependencyGraphDeltaPacketV1Error("fixture must be a mapping")

    candidates = fixture.get("requirement_delta_candidates")
    if not isinstance(candidates, Sequence) or isinstance(candidates, (str, bytes)) or not candidates:
        raise ProcessDependencyGraphDeltaPacketV1Error("requirement_delta_candidates must be a non-empty list")

    commands = [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]
    packet: dict[str, Any] = {
        "packet_version": "process_dependency_graph_delta_packet_v1",
        "packet_id": str(fixture.get("fixture_id", "synthetic-process-dependency-graph-delta-v1")),
        "source_fixture_id": str(fixture.get("fixture_id", "synthetic-process-dependency-graph-delta-v1")),
        "dependency_delta_rows": [],
        "affected_permit_family_rows": [],
        "process_stage_rows": [],
        "required_user_fact_rows": [],
        "required_document_rows": [],
        "fee_deadline_trigger_rows": [],
        "unsupported_path_rows": [],
        "devhub_boundary_reference_rows": [],
        "reviewer_hold_rows": [],
        "validation_commands": commands,
        "offline_validation_commands": commands,
        "mutation_policy": "inactive_fixture_review_only",
        "promotion_status": "not_promoted",
    }

    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, Mapping):
            raise ProcessDependencyGraphDeltaPacketV1Error(f"requirement_delta_candidates[{index}] must be a mapping")
        _require_candidate(candidate, index)
        candidate_id = _required_string(candidate, "candidate_id", index)
        requirement_id = _required_string(candidate, "requirement_id", index)
        delta_type = _required_string(candidate, "delta_type", index)

        packet["dependency_delta_rows"].append(
            {
                "candidate_id": candidate_id,
                "requirement_id": requirement_id,
                "delta_type": delta_type,
                "review_status": "pending_reviewer_disposition",
                "promotion_status": "inactive_review_only",
            }
        )
        _append_rows(packet["affected_permit_family_rows"], candidate, candidate_id, "affected_permit_families", "permit_family")
        _append_rows(packet["process_stage_rows"], candidate, candidate_id, "process_stages", "process_stage")
        _append_rows(packet["required_user_fact_rows"], candidate, candidate_id, "required_user_facts", "required_user_fact")
        _append_rows(packet["required_document_rows"], candidate, candidate_id, "required_documents", "required_document")
        _append_rows(packet["fee_deadline_trigger_rows"], candidate, candidate_id, "fee_deadline_triggers", "trigger")
        _append_rows(packet["unsupported_path_rows"], candidate, candidate_id, "unsupported_paths", "unsupported_path")
        _append_rows(packet["devhub_boundary_reference_rows"], candidate, candidate_id, "devhub_boundary_refs", "devhub_boundary_ref")
        _append_rows(packet["reviewer_hold_rows"], candidate, candidate_id, "reviewer_holds", "reviewer_hold")

    validate_process_dependency_graph_delta_packet_v1(packet)
    return packet


def validate_process_dependency_graph_delta_packet_v1(packet: Mapping[str, Any]) -> None:
    """Raise when a packet is incomplete, unsafe, or not offline-only."""

    issues = list(iter_process_dependency_graph_delta_packet_v1_issues(packet))
    if issues:
        detail = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise ProcessDependencyGraphDeltaPacketV1Error(detail)


def iter_process_dependency_graph_delta_packet_v1_issues(packet: Mapping[str, Any]) -> Iterable[ValidationIssue]:
    if not isinstance(packet, Mapping):
        yield ValidationIssue("$", "packet must be a mapping")
        return

    for field in _REQUIRED_PACKET_FIELDS:
        if field not in packet:
            yield ValidationIssue(field, "missing required field")

    if packet.get("packet_version") != "process_dependency_graph_delta_packet_v1":
        yield ValidationIssue("packet_version", "must be process_dependency_graph_delta_packet_v1")

    candidate_ids = _row_ids(packet.get("dependency_delta_rows"), "candidate_id")
    if candidate_ids is None:
        yield ValidationIssue("dependency_delta_rows", "must contain dependency rows with candidate_id")
        candidate_ids = set()

    for field, value_field in _ROW_GROUPS:
        yield from _row_group_issues(packet, field, value_field, candidate_ids)

    exact_commands = [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]
    if packet.get("validation_commands") != exact_commands:
        yield ValidationIssue("validation_commands", "must match exact offline validation commands")
    if packet.get("offline_validation_commands") != exact_commands:
        yield ValidationIssue("offline_validation_commands", "must match exact offline validation commands")

    if packet.get("mutation_policy") != "inactive_fixture_review_only":
        yield ValidationIssue("mutation_policy", "must be inactive_fixture_review_only")
    if packet.get("promotion_status") not in (None, "not_promoted"):
        yield ValidationIssue("promotion_status", "must not promote process models")

    yield from _safety_issues(packet, "$.")


def _row_group_issues(packet: Mapping[str, Any], field: str, value_field: str, candidate_ids: set[str]) -> Iterable[ValidationIssue]:
    rows = packet.get(field)
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        yield ValidationIssue(field, "must contain at least one row")
        return

    seen_for_group: set[str] = set()
    for index, row in enumerate(rows):
        path = f"{field}[{index}]"
        if not isinstance(row, Mapping):
            yield ValidationIssue(path, "row must be a mapping")
            continue
        candidate_id = row.get("candidate_id")
        if not isinstance(candidate_id, str) or not candidate_id.strip():
            yield ValidationIssue(f"{path}.candidate_id", "missing candidate_id")
        elif candidate_ids and candidate_id not in candidate_ids:
            yield ValidationIssue(f"{path}.candidate_id", f"unknown candidate_id: {candidate_id}")
        else:
            seen_for_group.add(candidate_id)
        if not isinstance(row.get(value_field), str) or not row.get(value_field, "").strip():
            yield ValidationIssue(f"{path}.{value_field}", f"missing {value_field}")

    for candidate_id in sorted(candidate_ids - seen_for_group):
        yield ValidationIssue(field, f"missing row for candidate_id: {candidate_id}")


def _require_candidate(candidate: Mapping[str, Any], index: int) -> None:
    for field in _REQUIRED_CANDIDATE_FIELDS:
        if field not in candidate:
            raise ProcessDependencyGraphDeltaPacketV1Error(f"requirement_delta_candidates[{index}].{field} is required")
    for field in _REQUIRED_CANDIDATE_FIELDS[:3]:
        _required_string(candidate, field, index)
    for field in _REQUIRED_CANDIDATE_FIELDS[3:]:
        values = candidate.get(field)
        if not _string_list(values):
            raise ProcessDependencyGraphDeltaPacketV1Error(f"requirement_delta_candidates[{index}].{field} must be a non-empty string list")


def _required_string(candidate: Mapping[str, Any], field: str, index: int) -> str:
    value = candidate.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ProcessDependencyGraphDeltaPacketV1Error(f"requirement_delta_candidates[{index}].{field} must be a non-empty string")
    return value


def _append_rows(rows: list[dict[str, str]], candidate: Mapping[str, Any], candidate_id: str, source_field: str, target_field: str) -> None:
    for value in _string_list(candidate.get(source_field)):
        rows.append({"candidate_id": candidate_id, target_field: value})


def _row_ids(rows: Any, id_field: str) -> set[str] | None:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
        return None
    ids: set[str] = set()
    for row in rows:
        if not isinstance(row, Mapping):
            return None
        value = row.get(id_field)
        if not isinstance(value, str) or not value.strip():
            return None
        ids.add(value)
    return ids


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _safety_issues(value: Any, path: str) -> Iterable[ValidationIssue]:
    if isinstance(value, Mapping):
        for raw_key, nested_value in value.items():
            key = str(raw_key)
            key_lower = key.lower()
            nested_path = f"{path}{key}"
            if any(marker in key_lower for marker in _PRIVATE_ARTIFACT_KEYWORDS):
                yield ValidationIssue(nested_path, "private/session/browser/raw/downloaded artifact fields are not allowed")
            if key_lower in _ACTIVE_MUTATION_KEYS and bool(nested_value):
                yield ValidationIssue(nested_path, "active mutation flags are not allowed")
            yield from _safety_issues(nested_value, f"{nested_path}.")
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, item in enumerate(value):
            yield from _safety_issues(item, f"{path}[{index}].")
        return

    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _PRIVATE_ARTIFACT_VALUE_MARKERS):
            yield ValidationIssue(path.rstrip("."), "private/session/browser/raw/downloaded artifact references are not allowed")
        if any(marker in lowered for marker in _LIVE_OR_DEVHUB_CLAIM_MARKERS):
            yield ValidationIssue(path.rstrip("."), "live crawl or DevHub claims are not allowed")
        if any(marker in lowered for marker in _GUARANTEE_MARKERS):
            yield ValidationIssue(path.rstrip("."), "legal or permitting guarantees are not allowed")
        if any(marker in lowered for marker in _OFFICIAL_ACTION_COMPLETION_MARKERS):
            yield ValidationIssue(path.rstrip("."), "official-action completion claims are not allowed")


__all__ = [
    "EXACT_OFFLINE_VALIDATION_COMMANDS",
    "ProcessDependencyGraphDeltaPacketV1Error",
    "ValidationIssue",
    "build_process_dependency_graph_delta_packet_v1",
    "iter_process_dependency_graph_delta_packet_v1_issues",
    "validate_process_dependency_graph_delta_packet_v1",
]
