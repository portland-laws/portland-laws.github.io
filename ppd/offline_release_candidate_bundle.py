"""Fixture-first offline PP&D release candidate bundle.

This module assembles committed metadata packets into a review-only release
candidate bundle. It does not perform live crawls, authenticate to DevHub, read
private artifacts, or claim production readiness.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


PACKET_TYPE = "ppd.offline_release_candidate_bundle.v1"
REQUIRED_INPUTS = {
    "post_decision_release_readiness_digest",
    "public_recrawl_rehearsal_plan",
    "regenerated_requirement_candidate",
    "guardrail_recompilation_rehearsal_packet",
    "agent_regression_matrix",
}
LIVE_CAPABILITIES = (
    ("source_registry.live_mutation", "Mutating the live SourceRegistry."),
    ("public_crawl.live_recrawl", "Running a live public crawl or recrawl."),
    ("guardrails.live_activation", "Activating regenerated guardrails for live agent traffic."),
    ("devhub.authenticated_automation", "Opening or automating authenticated DevHub."),
    ("official.consequential_actions", "Submitting, uploading, paying, scheduling, cancelling, or certifying."),
)
FORBIDDEN_KEYS = {
    "auth_state",
    "browser_session",
    "cookie",
    "credentials",
    "downloaded_document_path",
    "field_value",
    "har",
    "known_facts",
    "local_path",
    "password",
    "private_case_fact",
    "raw_archive_ref",
    "raw_body",
    "raw_crawl_output",
    "raw_download_ref",
    "raw_html",
    "screenshot",
    "session_state",
    "storage_state",
    "trace",
    "value",
    "warc_path",
}
FORBIDDEN_TEXT = (
    "/home/",
    "/Users/",
    "auth-state",
    "cookie=",
    "password=",
    "session=",
    "storage_state",
    "trace.zip",
    ".har",
    ".warc",
    "raw-crawl/",
    "raw-download/",
)
LIVE_EXECUTION_KEYS = {
    "authenticated_devhub_automation",
    "authenticated_automation",
    "devhub_execution_performed",
    "live_actions_performed",
    "live_crawl_executed",
    "live_network_execution",
    "live_network_called",
    "launch_devhub",
    "calls_llm",
    "uses_authenticated_session",
    "reads_private_files",
}
PRODUCTION_READY_LABELS = {
    "production-ready",
    "production_ready",
    "ready_for_production",
    "release_ready",
    "production ready",
}


class OfflineReleaseCandidateBundleError(ValueError):
    """Raised when the offline release candidate bundle is unsafe."""


def load_fixture(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise OfflineReleaseCandidateBundleError("fixture must be a JSON object")
    return data


def build_offline_release_candidate_bundle(inputs: Mapping[str, Any]) -> dict[str, Any]:
    input_map = _mapping(inputs.get("inputs")) if "inputs" in inputs else _mapping(inputs)
    errors = _input_errors(input_map)
    if errors:
        raise OfflineReleaseCandidateBundleError("invalid release candidate inputs: " + "; ".join(errors))

    consumed = _inputs_consumed(input_map)
    links = _prerequisite_links(consumed)
    bundle = {
        "packet_type": PACKET_TYPE,
        "packet_id": "ppd-offline-release-candidate-2026-05-28",
        "bundle_status": "review_candidate_only",
        "fixture_first": True,
        "metadata_only": True,
        "generated_from_fixtures": True,
        "live_actions_performed": False,
        "private_artifacts_included": False,
        "no_production_readiness_claim": True,
        "inputs_consumed": consumed,
        "prerequisite_links": links,
        "disabled_live_capabilities": _disabled_live_capabilities(),
        "rollback_references": _rollback_references(input_map, consumed),
        "reviewer_prompts": _reviewer_prompts(),
        "release_limitations": [
            "Candidate is limited to offline metadata review and deterministic fixture validation.",
            "Live crawl, DevHub, registry mutation, guardrail activation, and official actions remain disabled.",
            "A later attended review must decide whether any live action may be planned.",
        ],
        "validation_summary": {
            "all_required_inputs_linked": True,
            "live_capabilities_disabled": True,
            "rollback_references_present": True,
            "reviewer_prompts_present": True,
        },
    }
    assert_valid_offline_release_candidate_bundle(bundle)
    return bundle


def validate_offline_release_candidate_bundle(bundle: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if bundle.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    if bundle.get("bundle_status") != "review_candidate_only":
        errors.append("bundle_status must be review_candidate_only")
    for key in ("fixture_first", "metadata_only", "generated_from_fixtures", "no_production_readiness_claim"):
        if bundle.get(key) is not True:
            errors.append(f"{key} must be true")
    if bundle.get("live_actions_performed") is not False:
        errors.append("live_actions_performed must be false")
    if bundle.get("private_artifacts_included") is not False:
        errors.append("private_artifacts_included must be false")

    consumed = [_mapping(item) for item in _sequence(bundle.get("inputs_consumed"))]
    roles = {str(item.get("input_role") or "") for item in consumed}
    for role in sorted(REQUIRED_INPUTS - roles):
        errors.append(f"inputs_consumed missing {role}")

    link_roles = {str(item.get("input_role") or "") for item in _sequence(bundle.get("prerequisite_links")) if isinstance(item, Mapping)}
    for role in sorted(REQUIRED_INPUTS - link_roles):
        errors.append(f"prerequisite_links missing {role}")

    for index, capability in enumerate(_sequence(bundle.get("disabled_live_capabilities"))):
        record = _mapping(capability)
        if record.get("enabled") is not False:
            errors.append(f"disabled_live_capabilities[{index}].enabled must be false")
        if record.get("allowed_now") is not False:
            errors.append(f"disabled_live_capabilities[{index}].allowed_now must be false")
        if record.get("requires_future_attended_review") is not True:
            errors.append(f"disabled_live_capabilities[{index}].requires_future_attended_review must be true")
    if not _sequence(bundle.get("disabled_live_capabilities")):
        errors.append("disabled_live_capabilities must be non-empty")
    if not _sequence(bundle.get("reviewer_prompts")):
        errors.append("reviewer_prompts must be non-empty")

    rollback_packet_ids = {str(item.get("source_packet_id") or "") for item in _sequence(bundle.get("rollback_references")) if isinstance(item, Mapping)}
    for consumed_item in consumed:
        packet_id = str(consumed_item.get("packet_id") or "")
        if packet_id and packet_id not in rollback_packet_ids:
            errors.append(f"rollback_references missing source packet {packet_id}")
    if not rollback_packet_ids:
        errors.append("rollback_references must be non-empty")

    errors.extend(_walk_safety_errors(bundle, "$"))
    return _dedupe(errors)


def assert_valid_offline_release_candidate_bundle(bundle: Mapping[str, Any]) -> None:
    errors = validate_offline_release_candidate_bundle(bundle)
    if errors:
        raise OfflineReleaseCandidateBundleError("invalid offline release candidate bundle: " + "; ".join(errors))


def _input_errors(input_map: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_INPUTS - set(input_map))
    if missing:
        errors.append("missing required inputs: " + ", ".join(missing))
    for role in sorted(REQUIRED_INPUTS & set(input_map)):
        packet = _mapping(input_map.get(role))
        if not _text(packet.get("packet_id")):
            errors.append(f"{role} missing packet_id")
    errors.extend(_walk_safety_errors(input_map, "inputs"))
    return _dedupe(errors)


def _inputs_consumed(input_map: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for role in sorted(REQUIRED_INPUTS):
        packet = _mapping(input_map[role])
        record = {
            "input_role": role,
            "packet_id": _text(packet.get("packet_id"), role),
            "fixture_path": _text(packet.get("fixture_path"), "ppd/tests/fixtures/release_candidate_bundle/input_packets.json"),
            "metadata_only": packet.get("metadata_only", True) is True,
        }
        for optional_key in ("decision_link_id", "reconciliation_link_id", "rehearsal_link_id", "candidate_link_id", "matrix_link_id"):
            if _text(packet.get(optional_key)):
                record[optional_key] = _text(packet.get(optional_key))
        records.append(record)
    return records


def _prerequisite_links(consumed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    links = []
    for item in consumed:
        role = _text(item.get("input_role"), "input")
        links.append(
            {
                "link_id": f"prereq.{role}",
                "input_role": role,
                "source_packet_id": _text(item.get("packet_id"), role),
                "fixture_path": _text(item.get("fixture_path")),
                "required_before_live_action": True,
            }
        )
    return links


def _disabled_live_capabilities() -> list[dict[str, Any]]:
    return [
        {
            "capability_id": capability_id,
            "summary": summary,
            "enabled": False,
            "allowed_now": False,
            "requires_future_attended_review": True,
        }
        for capability_id, summary in LIVE_CAPABILITIES
    ]


def _rollback_references(input_map: Mapping[str, Any], consumed: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for role in sorted(REQUIRED_INPUTS):
        packet = _mapping(input_map[role])
        for index, ref in enumerate(_sequence(packet.get("rollback_references"))):
            record = _mapping(ref)
            packet_id = _text(record.get("source_packet_id"), _text(packet.get("packet_id"), role))
            rollback_id = _text(record.get("rollback_id") or record.get("rollback_ref_id"), f"rollback.{role}.{index}")
            seen.add(packet_id)
            refs.append(
                {
                    "rollback_id": rollback_id,
                    "source_input_role": role,
                    "source_packet_id": packet_id,
                    "summary": _text(record.get("summary") or record.get("restore_action"), "Discard this offline candidate and keep prior reviewed metadata."),
                    "live_cleanup_required": False,
                }
            )
    for item in consumed:
        packet_id = _text(item.get("packet_id"))
        role = _text(item.get("input_role"), "input")
        if packet_id and packet_id not in seen:
            refs.append(
                {
                    "rollback_id": f"rollback.{role}.discard_offline_candidate_reference",
                    "source_input_role": role,
                    "source_packet_id": packet_id,
                    "summary": "Discard the offline candidate reference; no live artifact cleanup is required.",
                    "live_cleanup_required": False,
                }
            )
    return refs


def _reviewer_prompts() -> list[dict[str, Any]]:
    return [
        {
            "prompt_id": "review.prerequisites",
            "question": "Are all prerequisite packets linked and still fixture-backed?",
            "required_before_live_action": True,
        },
        {
            "prompt_id": "review.disabled_capabilities",
            "question": "Do all live and consequential capabilities remain disabled in this candidate?",
            "required_before_live_action": True,
        },
        {
            "prompt_id": "review.rollback",
            "question": "Does each consumed packet have a clear discard or retain-current-state rollback reference?",
            "required_before_live_action": True,
        },
    ]


def _walk_safety_errors(value: Any, path: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            key_lower = key_text.lower()
            if key_lower in FORBIDDEN_KEYS and child not in (None, "", [], {}):
                errors.append(f"{child_path} uses forbidden private artifact field")
            if key_lower in LIVE_EXECUTION_KEYS and child is True:
                errors.append(f"{child_path} claims live execution")
            errors.extend(_walk_safety_errors(child, child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            errors.extend(_walk_safety_errors(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.strip().lower()
        if any(marker in value for marker in FORBIDDEN_TEXT):
            errors.append(f"{path} references forbidden private artifact text")
        if lowered in PRODUCTION_READY_LABELS:
            errors.append(f"{path} makes a forbidden readiness label claim")
    return errors


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> list[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return list(value)
    return []


def _text(value: Any, fallback: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
