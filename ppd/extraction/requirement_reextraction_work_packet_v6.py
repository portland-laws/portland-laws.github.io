"""Fixture-first requirement re-extraction work packet v6.

This module intentionally consumes committed fixture data only. It does not crawl,
download, open DevHub, read private documents, upload, submit, certify, pay, or
schedule anything.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

FORBIDDEN_ACTIONS = {
    "crawl_live_sites",
    "download_documents",
    "store_raw_bodies",
    "open_devhub",
    "read_private_documents",
    "upload",
    "submit",
    "certify",
    "pay",
    "schedule",
    "legal_or_permitting_guarantees",
}

OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/extraction/requirement_reextraction_work_packet_v6.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_requirement_reextraction_work_packet_v6.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_FORBIDDEN_FLAG_KEYS = {
    "active_mutation",
    "active_mutation_enabled",
    "active_mutation_flags",
    "auth_artifact",
    "auth_artifacts",
    "auth_state",
    "downloaded_artifact",
    "downloaded_artifacts",
    "legal_guarantee",
    "live_crawl_completed",
    "live_crawl_executed",
    "mutation_enabled",
    "official_action_completed",
    "permitting_guarantee",
    "private_artifact",
    "private_artifacts",
    "raw_artifact",
    "raw_artifacts",
    "raw_crawl_artifact",
    "raw_crawl_artifacts",
    "session_artifact",
    "session_artifacts",
    "session_file",
    "session_files",
}

_FORBIDDEN_TEXT_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\blive crawl (?:completed|executed|ran|succeeded)\b",
        r"\b(?:fetched|crawled|recrawled) live\b",
        r"\bdownloaded (?:document|documents|pdf|pdfs|artifact|artifacts)\b",
        r"\braw crawl artifact\b",
        r"\braw (?:html|pdf|body|bodies) persisted\b",
        r"\b(?:private|session|auth) artifact\b",
        r"\b(?:auth state|session file|trace|har file|credential|cookie)\b",
        r"\bofficial action completed\b",
        r"\b(?:submitted|certified|uploaded|paid|scheduled) (?:the )?(?:permit|application|correction|fee|inspection)\b",
        r"\b(?:legal(?:ly)? sufficient|legal advice|permit approval guaranteed|permitting approval guaranteed|guaranteed approval|will be approved)\b",
        r"\b(?:active mutation enabled|mutation flag enabled|mutated live state|mutates live systems)\b",
    )
]


def load_batch_plan_fixture(fixture_path: Path | str) -> dict[str, Any]:
    """Load a committed requirement re-extraction batch plan v6 fixture."""
    path = Path(fixture_path)
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("batch plan fixture must be a JSON object")
    return payload


def build_work_packet_from_fixture(fixture_path: Path | str) -> dict[str, Any]:
    """Build a work packet from a batch-plan fixture path."""
    return build_work_packet(load_batch_plan_fixture(fixture_path))


def build_work_packet(batch_plan: dict[str, Any]) -> dict[str, Any]:
    """Stage requirement re-extraction work from fixture-only batch-plan data."""
    _validate_batch_plan(batch_plan)

    process_packets = [_stage_process(process) for process in batch_plan["processes"]]
    packet = {
        "packet_id": "requirement-reextraction-work-packet-v6",
        "packet_version": 6,
        "source_batch_plan_id": batch_plan["batch_plan_id"],
        "source_batch_plan_version": batch_plan["batch_plan_version"],
        "fixture_only": True,
        "live_access": {name: False for name in sorted(FORBIDDEN_ACTIONS)},
        "process_packets": process_packets,
        "validation_commands": expected_offline_validation_commands(),
    }
    validate_work_packet(packet)
    return packet


def expected_offline_validation_commands() -> list[list[str]]:
    """Return exact offline validation commands for this packet."""
    return [list(command) for command in OFFLINE_VALIDATION_COMMANDS]


def validate_work_packet(packet: dict[str, Any]) -> None:
    """Raise when a work packet omits required review rows or safety gates."""
    if not isinstance(packet, dict):
        raise ValueError("work packet must be a JSON object")
    _reject_forbidden_claims(packet)

    if packet.get("packet_version") != 6:
        raise ValueError("work packet version must be 6")
    _required_string(packet, "packet_id")
    _required_string(packet, "source_batch_plan_id")
    if packet.get("source_batch_plan_version") != 6:
        raise ValueError("work packet must reference requirement re-extraction batch plan v6")
    if packet.get("fixture_only") is not True:
        raise ValueError("work packet must remain fixture-only")

    live_access = packet.get("live_access")
    if not isinstance(live_access, dict):
        raise ValueError("work packet must declare live_access controls")
    missing_controls = sorted(FORBIDDEN_ACTIONS.difference(live_access))
    if missing_controls:
        raise ValueError(f"work packet missing live_access controls: {missing_controls}")
    enabled = [name for name, value in live_access.items() if value]
    if enabled:
        raise ValueError(f"live or consequential actions are not allowed: {enabled}")

    commands = packet.get("validation_commands")
    if commands != expected_offline_validation_commands():
        raise ValueError("work packet validation commands must match exact offline commands")

    process_packets = packet.get("process_packets")
    if not isinstance(process_packets, list) or not process_packets:
        raise ValueError("work packet must include per-process extraction packets")
    for index, process_packet in enumerate(process_packets):
        if not isinstance(process_packet, dict):
            raise ValueError(f"process packet {index} must be a JSON object")
        _validate_process_packet(process_packet)


def _validate_process_packet(process_packet: dict[str, Any]) -> None:
    process_id = _required_string(process_packet, "process_id")
    _required_string(process_packet, "permit_type")

    extraction_inputs = process_packet.get("extraction_inputs")
    if not isinstance(extraction_inputs, list) or not extraction_inputs:
        raise ValueError(f"{process_id} must include per-process extraction inputs")
    for item in extraction_inputs:
        if not isinstance(item, dict):
            raise ValueError(f"{process_id} extraction input must be a JSON object")
        _required_string(item, "fixture_document_id")
        _required_string(item, "source_id")
        _required_string(item, "source_kind")
        _required_string(item, "normalized_text_fixture_ref")
        if item.get("raw_body_ref") is not None:
            raise ValueError(f"{process_id} extraction inputs must not reference raw bodies")
        if item.get("requires_live_fetch") is not False:
            raise ValueError(f"{process_id} extraction inputs must not require live fetch")

    refresh_targets = process_packet.get("source_span_refresh_targets")
    if not isinstance(refresh_targets, list) or not refresh_targets:
        raise ValueError(f"{process_id} must include cited source-span refresh targets")
    for item in refresh_targets:
        if not isinstance(item, dict):
            raise ValueError(f"{process_id} refresh target must be a JSON object")
        _required_string(item, "requirement_id")
        _required_string(item, "source_evidence_id")
        _required_string(item, "fixture_document_id")
        _required_string(item, "refresh_goal")
        if item.get("requires_live_fetch") is not False:
            raise ValueError(f"{process_id} refresh targets must not require live fetch")
        span = item.get("current_citation_span")
        if not isinstance(span, dict) or not span:
            raise ValueError(f"{process_id} refresh targets must include cited source spans")
        _required_string(span, "section_id")
        if not isinstance(span.get("start_char"), int) or not isinstance(span.get("end_char"), int):
            raise ValueError(f"{process_id} citation spans must include integer start_char and end_char")

    placeholders = process_packet.get("requirement_placeholders")
    if not isinstance(placeholders, list) or not placeholders:
        raise ValueError(f"{process_id} must include old-vs-new requirement placeholders")
    for item in placeholders:
        if not isinstance(item, dict):
            raise ValueError(f"{process_id} placeholder must be a JSON object")
        _required_string(item, "requirement_id")
        old_value = _required_string(item, "old_requirement_placeholder")
        new_value = _required_string(item, "new_requirement_placeholder")
        if not old_value.startswith("OLD_REQUIREMENT_PLACEHOLDER:"):
            raise ValueError(f"{process_id} old requirement placeholder must be explicit")
        if not new_value.startswith("NEW_REQUIREMENT_PLACEHOLDER:"):
            raise ValueError(f"{process_id} new requirement placeholder must be explicit")
        if item.get("comparison_status") != "pending_fixture_review":
            raise ValueError(f"{process_id} placeholder comparison status must remain pending fixture review")
        if item.get("human_review_status") not in {"pending", "hold"}:
            raise ValueError(f"{process_id} placeholder human review status must be pending or hold")

    prompt = _required_string(process_packet, "reviewer_comparison_prompt")
    prompt_lower = prompt.lower()
    for phrase in ("compare", "old-vs-new", "source-span", "fixture"):
        if phrase not in prompt_lower:
            raise ValueError(f"{process_id} reviewer comparison prompt is missing {phrase!r}")

    hold = process_packet.get("human_review_hold")
    reasons = process_packet.get("human_review_hold_reasons")
    if not isinstance(hold, bool):
        raise ValueError(f"{process_id} must propagate human-review hold as a boolean")
    if not isinstance(reasons, list) or any(not isinstance(reason, str) or not reason for reason in reasons):
        raise ValueError(f"{process_id} must propagate human-review hold reasons")
    if hold and not reasons:
        raise ValueError(f"{process_id} human-review holds must include at least one reason")
    if not hold and reasons:
        raise ValueError(f"{process_id} human-review hold reasons must be empty when no hold is active")

    held_requirements = [
        item["requirement_id"]
        for item in placeholders
        if item.get("human_review_status") == "hold"
    ]
    for requirement_id in held_requirements:
        expected_reason = f"{requirement_id}:placeholder_human_review_hold"
        if expected_reason not in reasons:
            raise ValueError(f"{process_id} must propagate hold reason for {requirement_id}")

    if process_packet.get("inactive_guardrail_status") != "unchanged":
        raise ValueError(f"{process_id} must preserve inactive guardrail status unchanged")


def _validate_batch_plan(batch_plan: dict[str, Any]) -> None:
    _reject_forbidden_claims(batch_plan)
    _required_string(batch_plan, "batch_plan_id")
    if batch_plan.get("batch_plan_version") != 6:
        raise ValueError("only requirement re-extraction batch plan v6 fixtures are supported")
    if batch_plan.get("fixture_only") is not True:
        raise ValueError("batch plan must declare fixture_only=true")
    if batch_plan.get("allowed_inputs") != ["committed_batch_plan_v6_fixtures"]:
        raise ValueError("batch plan may only consume committed batch plan v6 fixtures")
    if batch_plan.get("forbidden_actions") != sorted(FORBIDDEN_ACTIONS):
        raise ValueError("batch plan forbidden actions do not match PP&D guardrails")
    if not isinstance(batch_plan.get("processes"), list) or not batch_plan["processes"]:
        raise ValueError("batch plan must include at least one process")


def _stage_process(process: dict[str, Any]) -> dict[str, Any]:
    process_id = _required_string(process, "process_id")
    permit_type = _required_string(process, "permit_type")
    extraction_inputs = process.get("extraction_inputs")
    refresh_targets = process.get("source_span_refresh_targets")
    placeholders = process.get("requirement_placeholders")

    if not isinstance(extraction_inputs, list) or not extraction_inputs:
        raise ValueError(f"{process_id} must include extraction inputs")
    if not isinstance(refresh_targets, list) or not refresh_targets:
        raise ValueError(f"{process_id} must include source-span refresh targets")
    if not isinstance(placeholders, list) or not placeholders:
        raise ValueError(f"{process_id} must include requirement placeholders")

    hold_reasons = _human_review_hold_reasons(process)
    return {
        "process_id": process_id,
        "permit_type": permit_type,
        "extraction_inputs": [_stage_extraction_input(item) for item in extraction_inputs],
        "source_span_refresh_targets": [_stage_refresh_target(item) for item in refresh_targets],
        "requirement_placeholders": [_stage_placeholder(item) for item in placeholders],
        "reviewer_comparison_prompt": _reviewer_prompt(process_id, permit_type, placeholders, refresh_targets),
        "human_review_hold": bool(hold_reasons),
        "human_review_hold_reasons": hold_reasons,
        "inactive_guardrail_status": "unchanged",
    }


def _stage_extraction_input(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "fixture_document_id": _required_string(item, "fixture_document_id"),
        "source_id": _required_string(item, "source_id"),
        "source_kind": _required_string(item, "source_kind"),
        "normalized_text_fixture_ref": _required_string(item, "normalized_text_fixture_ref"),
        "raw_body_ref": None,
        "requires_live_fetch": False,
    }


def _stage_refresh_target(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": _required_string(item, "requirement_id"),
        "source_evidence_id": _required_string(item, "source_evidence_id"),
        "fixture_document_id": _required_string(item, "fixture_document_id"),
        "current_citation_span": dict(item.get("current_citation_span", {})),
        "refresh_goal": _required_string(item, "refresh_goal"),
        "requires_live_fetch": False,
    }


def _stage_placeholder(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": _required_string(item, "requirement_id"),
        "old_requirement_placeholder": _required_string(item, "old_requirement_placeholder"),
        "new_requirement_placeholder": _required_string(item, "new_requirement_placeholder"),
        "comparison_status": "pending_fixture_review",
        "human_review_status": item.get("human_review_status", "pending"),
    }


def _human_review_hold_reasons(process: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if process.get("human_review_hold") is True:
        reasons.append("process_marked_for_human_review")
    for placeholder in process.get("requirement_placeholders", []):
        if placeholder.get("human_review_status") == "hold":
            requirement_id = placeholder.get("requirement_id", "unknown_requirement")
            reasons.append(f"{requirement_id}:placeholder_human_review_hold")
    return reasons


def _reviewer_prompt(
    process_id: str,
    permit_type: str,
    placeholders: list[dict[str, Any]],
    refresh_targets: list[dict[str, Any]],
) -> str:
    requirement_ids = ", ".join(_required_string(item, "requirement_id") for item in placeholders)
    evidence_ids = ", ".join(_required_string(item, "source_evidence_id") for item in refresh_targets)
    return (
        f"Compare fixture-only old-vs-new requirement placeholders for {permit_type} "
        f"({process_id}). Verify cited source-span refresh targets {evidence_ids}; "
        f"do not infer beyond fixtures; keep inactive guardrails unchanged; "
        f"leave requirements pending when human review is needed: {requirement_ids}."
    )


def _reject_forbidden_claims(value: Any, path: str = "packet") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            normalized_key = str(key).lower()
            if normalized_key in _FORBIDDEN_FLAG_KEYS and child not in (False, None, "", [], {}):
                raise ValueError(f"forbidden live, private, official-action, guarantee, or mutation flag at {child_path}")
            _reject_forbidden_claims(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden_claims(child, f"{path}[{index}]")
    elif isinstance(value, str):
        for pattern in _FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                raise ValueError(f"forbidden live, private, official-action, guarantee, or mutation claim at {path}")


def _required_string(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"missing required string field: {key}")
    return value
