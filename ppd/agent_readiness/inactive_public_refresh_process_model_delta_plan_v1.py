"""Validation for inactive public refresh ProcessModel delta plan v1.

The packet validated here is fixture-first and offline-only. It may describe
inactive ProcessModel delta placeholders caused by a public refresh requirement
re-extraction queue, but it must not claim live extraction, crawling, DevHub
access, official actions, legal guarantees, or active ProcessModel/guardrail
mutation.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PACKET_TYPE = "ppd.inactive_public_refresh_process_model_delta_plan.v1"
PACKET_VERSION = "v1"
PLAN_MODE = "fixture_first_inactive_public_refresh_process_model_delta_plan_only"
VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

REQUIRED_TOP_LEVEL_SEQUENCES = (
    "requirement_reextraction_queue_refs",
    "inactive_process_model_delta_placeholders",
    "stage_level_eligibility_changes",
    "document_requirement_changes",
    "unsupported_path_notes",
    "stale_or_conflicting_evidence_holds",
    "affected_guardrail_bundle_refs",
    "reviewer_routing",
    "rollback_notes",
    "validation_commands",
)

REQUIRED_PLACEHOLDER_FIELDS = (
    "placeholder_id",
    "process_model_id",
    "permit_type",
    "requirement_reextraction_queue_refs",
    "stage_level_eligibility_change_refs",
    "document_requirement_change_refs",
    "unsupported_path_note_refs",
    "stale_or_conflicting_evidence_hold_refs",
    "affected_guardrail_bundle_refs",
    "reviewer_routing_refs",
    "rollback_note_refs",
    "validation_commands",
    "status",
    "activation_allowed",
)

ACTIVE_MUTATION_FLAGS = (
    "active_mutation",
    "active_process_model_mutation",
    "active_process_model_promotion",
    "active_guardrail_mutation",
    "active_guardrail_promotion",
    "active_requirement_mutation",
    "active_source_registry_mutation",
    "mutates_active_process_models",
    "mutates_active_guardrails",
    "mutates_active_requirements",
    "official_action_completed",
    "devhub_opened",
    "live_extraction",
    "live_crawl",
    "raw_output_stored",
    "downloaded_artifact_stored",
    "private_artifact_stored",
    "legal_or_permitting_guarantee",
)

PRIVATE_RAW_OR_RUNTIME_KEYS = frozenset(
    {
        "auth_state",
        "browser_state",
        "browser_trace",
        "cookie",
        "credential",
        "devhub_session",
        "downloaded_artifact",
        "downloaded_document",
        "downloaded_pdf",
        "har",
        "html_body",
        "local_private_path",
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

FORBIDDEN_CLAIM_PHRASES = (
    "active guardrail mutation",
    "active guardrail promoted",
    "active process model mutation",
    "active process model promoted",
    "application submitted",
    "certification completed",
    "certified acknowledgement",
    "correction uploaded",
    "devhub claim verified",
    "devhub opened",
    "devhub portal verified",
    "downloaded artifact",
    "downloaded document",
    "guaranteed approval",
    "guaranteed permit",
    "inspection scheduled",
    "legal advice",
    "legally sufficient",
    "live crawl completed",
    "live extraction completed",
    "official action completed",
    "payment completed",
    "permit approval guaranteed",
    "permit guaranteed",
    "raw artifact stored",
    "raw crawl output",
    "raw output stored",
    "submission completed",
    "upload completed",
)


@dataclass(frozen=True)
class InactivePublicRefreshProcessModelDeltaPlanV1ValidationResult:
    valid: bool
    problems: tuple[str, ...]


class InactivePublicRefreshProcessModelDeltaPlanV1Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid inactive public refresh ProcessModel delta plan v1: " + "; ".join(self.problems))


def load_inactive_public_refresh_process_model_delta_plan_v1(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("inactive public refresh ProcessModel delta plan v1 fixture must be a JSON object")
    assert_valid_inactive_public_refresh_process_model_delta_plan_v1(loaded)
    return loaded


def assert_valid_inactive_public_refresh_process_model_delta_plan_v1(packet: Mapping[str, Any]) -> None:
    result = validate_inactive_public_refresh_process_model_delta_plan_v1(packet)
    if not result.valid:
        raise InactivePublicRefreshProcessModelDeltaPlanV1Error(result.problems)


def validate_inactive_public_refresh_process_model_delta_plan_v1(
    packet: Mapping[str, Any],
) -> InactivePublicRefreshProcessModelDeltaPlanV1ValidationResult:
    problems: list[str] = []
    if not isinstance(packet, Mapping):
        return InactivePublicRefreshProcessModelDeltaPlanV1ValidationResult(False, ("packet must be an object",))

    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v1")
    if packet.get("fixture_first") is not True:
        problems.append("fixture_first must be true")
    if packet.get("plan_mode") != PLAN_MODE:
        problems.append(f"plan_mode must be {PLAN_MODE}")
    if packet.get("validation_commands") != VALIDATION_COMMANDS:
        problems.append("validation_commands must contain only the PP&D daemon self-test command")

    for key in REQUIRED_TOP_LEVEL_SEQUENCES:
        if not _non_empty_sequence(packet.get(key)):
            problems.append(f"{key} must be a non-empty list")

    for flag in ACTIVE_MUTATION_FLAGS:
        if packet.get(flag) is not False:
            problems.append(f"{flag} must be false")

    _validate_simple_id_rows(packet.get("requirement_reextraction_queue_refs"), "queue_ref_id", problems)
    _validate_simple_id_rows(packet.get("stage_level_eligibility_changes"), "stage_change_id", problems)
    _validate_simple_id_rows(packet.get("document_requirement_changes"), "document_change_id", problems)
    _validate_simple_id_rows(packet.get("unsupported_path_notes"), "unsupported_path_note_id", problems)
    _validate_simple_id_rows(packet.get("stale_or_conflicting_evidence_holds"), "evidence_hold_id", problems)
    _validate_simple_id_rows(packet.get("affected_guardrail_bundle_refs"), "guardrail_bundle_ref_id", problems)
    _validate_simple_id_rows(packet.get("reviewer_routing"), "reviewer_route_id", problems)
    _validate_simple_id_rows(packet.get("rollback_notes"), "rollback_note_id", problems)
    _validate_placeholders(packet, problems)
    _reject_private_runtime_or_forbidden_claims(packet, problems)
    return InactivePublicRefreshProcessModelDeltaPlanV1ValidationResult(not problems, tuple(problems))


def _validate_placeholders(packet: Mapping[str, Any], problems: list[str]) -> None:
    allowed_refs = {
        "requirement_reextraction_queue_refs": _ids(packet.get("requirement_reextraction_queue_refs"), "queue_ref_id"),
        "stage_level_eligibility_change_refs": _ids(packet.get("stage_level_eligibility_changes"), "stage_change_id"),
        "document_requirement_change_refs": _ids(packet.get("document_requirement_changes"), "document_change_id"),
        "unsupported_path_note_refs": _ids(packet.get("unsupported_path_notes"), "unsupported_path_note_id"),
        "stale_or_conflicting_evidence_hold_refs": _ids(packet.get("stale_or_conflicting_evidence_holds"), "evidence_hold_id"),
        "affected_guardrail_bundle_refs": _ids(packet.get("affected_guardrail_bundle_refs"), "guardrail_bundle_ref_id"),
        "reviewer_routing_refs": _ids(packet.get("reviewer_routing"), "reviewer_route_id"),
        "rollback_note_refs": _ids(packet.get("rollback_notes"), "rollback_note_id"),
    }
    covered_queue_refs: set[str] = set()

    for index, row in enumerate(_mapping_sequence(packet.get("inactive_process_model_delta_placeholders"))):
        prefix = f"inactive_process_model_delta_placeholders[{index}]"
        for field in REQUIRED_PLACEHOLDER_FIELDS:
            if field not in row:
                problems.append(f"{prefix}.{field} is required")
        if row.get("status") != "inactive_process_model_delta_placeholder_only":
            problems.append(f"{prefix}.status must be inactive_process_model_delta_placeholder_only")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        if row.get("validation_commands") != VALIDATION_COMMANDS:
            problems.append(f"{prefix}.validation_commands must contain only the PP&D daemon self-test command")
        for field, allowed in allowed_refs.items():
            refs = _require_refs(prefix, field, row.get(field), allowed, problems)
            if field == "requirement_reextraction_queue_refs":
                covered_queue_refs.update(refs)

    for ref in sorted(allowed_refs["requirement_reextraction_queue_refs"] - covered_queue_refs):
        problems.append(f"requirement_reextraction_queue_refs contains unreferenced queue ref {ref}")


def _validate_simple_id_rows(value: Any, id_field: str, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        if not _text(row.get(id_field)):
            problems.append(f"{id_field}[{index}].{id_field} is required")


def _reject_private_runtime_or_forbidden_claims(value: Any, problems: list[str], path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in PRIVATE_RAW_OR_RUNTIME_KEYS:
                problems.append(f"{child_path} must not contain private, raw, downloaded, or runtime artifacts")
            if key in ACTIVE_MUTATION_FLAGS and child is not False:
                problems.append(f"{child_path} must be false")
            _reject_private_runtime_or_forbidden_claims(child, problems, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _reject_private_runtime_or_forbidden_claims(child, problems, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        if any(phrase in lowered for phrase in FORBIDDEN_CLAIM_PHRASES):
            problems.append(
                f"{path} must not contain live extraction, crawl, DevHub, active mutation, official-action, legal, or permitting guarantee claims"
            )


def _require_refs(prefix: str, field: str, value: Any, allowed: set[str], problems: list[str]) -> set[str]:
    refs = {item for item in _text_sequence(value) if item}
    if not refs:
        problems.append(f"{prefix}.{field} must be a non-empty list")
        return set()
    for ref in sorted(refs):
        if ref not in allowed:
            problems.append(f"{prefix}.{field} contains unknown ref {ref}")
    return refs


def _ids(value: Any, field: str) -> set[str]:
    return {_text(row.get(field)) for row in _mapping_sequence(value) if _text(row.get(field))}


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text_sequence(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in (_text(item) for item in value) if item]


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and len(value) > 0


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""
