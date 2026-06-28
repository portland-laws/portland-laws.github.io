"""Fixture-first PP&D release gate status packet validation.

This module validates a metadata-only release gate packet. The packet summarizes
source-registry rehearsal, guardrail activation rehearsal, agent API conformance,
and DevHub pilot result intake readiness without promoting production readiness
or enabling live capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re
from typing import Any, Mapping


REQUIRED_PACKET_TYPE = "ppd.release_gate_status_packet.v1"
REQUIRED_REHEARSAL_AREAS = {
    "source_registry_rehearsal",
    "guardrail_activation_rehearsal",
    "agent_api_conformance",
    "devhub_pilot_result_intake_readiness",
}
REQUIRED_DISABLED_CAPABILITIES = {
    "live_public_crawl",
    "authenticated_devhub_browser",
    "official_upload",
    "permit_submission",
    "certification",
    "fee_payment",
    "inspection_scheduling",
    "cancellation_or_withdrawal",
    "raw_document_download_persistence",
}
ALLOWED_REHEARSAL_STATUSES = {
    "fixture_validated",
    "metadata_only_ready",
    "review_required",
    "blocked_open",
}
ALLOWED_DISABLED_STATUSES = {"disabled", "refused", "manual_handoff_only", "blocked"}
PRODUCTION_READY_LABELS = {
    "production-ready",
    "production_ready",
    "production ready",
    "release-ready",
    "release_ready",
    "release ready",
    "ready for production",
}
FORBIDDEN_KEYS = {
    "auth_state",
    "auth_state_path",
    "browser_session",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "downloaded_document",
    "downloaded_document_path",
    "file_path",
    "har",
    "har_path",
    "local_path",
    "password",
    "private_field_value",
    "raw_body",
    "raw_crawl_output",
    "raw_crawl_output_ref",
    "raw_html",
    "raw_text",
    "screenshot",
    "screenshot_path",
    "session_artifact",
    "session_state",
    "storage_state",
    "trace",
    "trace_path",
}
PRIVATE_VALUE_RE = re.compile(
    r"(/home/|/Users/|auth[_-]?state|storage[_-]?state|cookie|credential|password|token|trace\.zip|\.har\b)",
    re.IGNORECASE,
)
RAW_CRAWL_REF_RE = re.compile(
    r"(raw[_ -]?(crawl|body|html|text|download)|warc|response[_ -]?body|downloaded[_ -]?document)",
    re.IGNORECASE,
)
CLAIM_KEYS = {"claim", "description", "question", "reason", "required_before", "summary"}
ENABLEMENT_TRUE_KEYS = {
    "allow_live_crawl",
    "allow_live_devhub",
    "automation_allowed",
    "certification_enabled",
    "cancellation_enabled",
    "devhub_capabilities_enabled",
    "enabled",
    "fee_payment_enabled",
    "inspection_scheduling_enabled",
    "live_capabilities_enabled",
    "live_capability_enabled",
    "live_crawl_enabled",
    "payment_enabled",
    "permit_submission_enabled",
    "scheduling_enabled",
    "submission_enabled",
    "upload_enabled",
}
FORBIDDEN_CAPABILITY_IDS = REQUIRED_DISABLED_CAPABILITIES | {
    "authenticated_devhub",
    "authenticated_devhub_automation",
    "cancellation",
    "cancel_inspection",
    "certify_acknowledgement",
    "devhub_live_session",
    "inspection_cancellation",
    "live_crawl",
    "payment",
    "schedule_inspection",
    "submit_payment",
    "upload",
}
FORBIDDEN_ACTION_WORDS = {
    "cancel",
    "cancellation",
    "certification",
    "certify",
    "fee_payment",
    "inspection_scheduling",
    "payment",
    "schedule",
    "scheduling",
    "submission",
    "submit",
    "upload",
}
ENABLED_STATUSES = {"allowed", "enabled", "live", "ready", "ready_for_live", "scheduled"}


@dataclass(frozen=True)
class ReleaseGateStatusValidationResult:
    """Validation result for a PP&D release gate status packet."""

    packet_id: str
    ok: bool
    errors: tuple[str, ...]


def load_release_gate_status_packet(path: str | Path) -> dict[str, Any]:
    """Load a committed fixture packet from JSON."""

    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("release gate status packet must be a JSON object")
    return data


def assert_valid_release_gate_status_packet(packet: Mapping[str, Any]) -> None:
    """Raise AssertionError when a packet violates the fixture-first gate."""

    result = validate_release_gate_status_packet(packet)
    if not result.ok:
        raise AssertionError("; ".join(result.errors))


def validate_release_gate_status_packet(packet: Mapping[str, Any]) -> ReleaseGateStatusValidationResult:
    """Return all release gate validation errors without side effects."""

    errors: list[str] = []
    packet_id = _text(packet.get("packet_id"))

    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    for key in ("fixture_first", "metadata_only", "generated_from_fixtures"):
        _require(errors, packet.get(key) is True, f"{key} must be true")
    _require(errors, packet.get("production_readiness") is False, "production_readiness must be false")
    _require(errors, packet.get("live_capabilities_enabled") is False, "live_capabilities_enabled must be false")
    _validate_not_production_ready(errors, packet)
    _validate_prerequisite_packet_links(errors, packet.get("prerequisite_packet_links"))
    _validate_rehearsal_summary(errors, _mapping(packet.get("source_rehearsals")))
    _validate_open_blockers(errors, packet.get("open_blockers"))
    _validate_metadata_only_next_steps(errors, packet.get("allowed_metadata_only_next_steps"))
    _validate_disabled_capabilities(errors, packet.get("disabled_live_capabilities"))
    _validate_reviewer_prompts(errors, packet.get("required_reviewer_prompts"))
    _validate_cited_readiness_claims(errors, packet)
    _validate_no_private_or_live_artifacts(errors, packet)
    _validate_no_forbidden_enablement(errors, packet)

    return ReleaseGateStatusValidationResult(packet_id=packet_id, ok=not errors, errors=tuple(_dedupe(errors)))


def _validate_not_production_ready(errors: list[str], packet: Mapping[str, Any]) -> None:
    has_open_blockers = any(_text(_mapping(item).get("status")) == "open" for item in _sequence(packet.get("open_blockers")))
    for key in ("release_status", "readiness_status", "status", "label"):
        value = _text(packet.get(key)).lower()
        if _is_production_ready_label(value):
            errors.append(f"{key} must not promote production readiness")
            if has_open_blockers:
                errors.append(f"{key} cannot be production-ready while unresolved blockers remain")


def _validate_prerequisite_packet_links(errors: list[str], value: Any) -> None:
    links = _sequence(value)
    if not links:
        errors.append("prerequisite_packet_links must include links for every required rehearsal area")
        return
    covered_areas: set[str] = set()
    for index, raw in enumerate(links):
        path = f"prerequisite_packet_links[{index}]"
        link = _mapping(raw)
        area = _text(link.get("area"))
        covered_areas.add(area)
        _require(errors, bool(_text(link.get("packet_id"))), f"{path}.packet_id is required")
        _require(errors, area in REQUIRED_REHEARSAL_AREAS, f"{path}.area must reference a required rehearsal area")
        _require(errors, bool(_text(link.get("path"))), f"{path}.path is required")
        _require(errors, _text(link.get("kind")) in {"fixture", "rehearsal_packet", "validation_fixture"}, f"{path}.kind is not allowed")
        _require(errors, _string_tuple(link.get("evidence_ids")) != (), f"{path}.evidence_ids must be non-empty")
    for area in sorted(REQUIRED_REHEARSAL_AREAS - covered_areas):
        errors.append(f"prerequisite_packet_links must include {area}")


def _validate_rehearsal_summary(errors: list[str], rehearsals: Mapping[str, Any]) -> None:
    if not rehearsals:
        errors.append("source_rehearsals must be present")
        return
    missing = sorted(REQUIRED_REHEARSAL_AREAS - set(rehearsals))
    for area in missing:
        errors.append(f"source_rehearsals.{area} is required")
    for area, raw in rehearsals.items():
        path = f"source_rehearsals.{area}"
        item = _mapping(raw)
        _require(errors, area in REQUIRED_REHEARSAL_AREAS, f"{path} is not a recognized rehearsal area")
        _require(errors, bool(_text(item.get("packet_id"))), f"{path}.packet_id is required")
        _require(errors, _text(item.get("status")) in ALLOWED_REHEARSAL_STATUSES, f"{path}.status is not allowed")
        _require(errors, item.get("promotes_production_readiness") is False, f"{path}.promotes_production_readiness must be false")
        _require(errors, _string_tuple(item.get("evidence_ids")) != (), f"{path}.evidence_ids must be non-empty")


def _validate_open_blockers(errors: list[str], value: Any) -> None:
    blockers = _sequence(value)
    if not blockers:
        errors.append("open_blockers must include at least one unresolved blocker")
        return
    covered_areas: set[str] = set()
    for index, raw in enumerate(blockers):
        path = f"open_blockers[{index}]"
        blocker = _mapping(raw)
        area = _text(blocker.get("area"))
        covered_areas.add(area)
        _require(errors, bool(_text(blocker.get("blocker_id"))), f"{path}.blocker_id is required")
        _require(errors, area in REQUIRED_REHEARSAL_AREAS, f"{path}.area must reference a required rehearsal area")
        _require(errors, _text(blocker.get("status")) == "open", f"{path}.status must be open")
        _require(errors, bool(_text(blocker.get("reason"))), f"{path}.reason is required")
        _require(errors, _string_tuple(blocker.get("evidence_ids")) != (), f"{path}.evidence_ids must be non-empty")
    for area in sorted(REQUIRED_REHEARSAL_AREAS - covered_areas):
        errors.append(f"open_blockers must include blocker for {area}")


def _validate_metadata_only_next_steps(errors: list[str], value: Any) -> None:
    steps = _sequence(value)
    if not steps:
        errors.append("allowed_metadata_only_next_steps must be non-empty")
        return
    for index, raw in enumerate(steps):
        path = f"allowed_metadata_only_next_steps[{index}]"
        step = _mapping(raw)
        _require(errors, bool(_text(step.get("step_id"))), f"{path}.step_id is required")
        _require(errors, _text(step.get("action_scope")) == "metadata_only", f"{path}.action_scope must be metadata_only")
        _require(errors, step.get("live_capability_enabled") is False, f"{path}.live_capability_enabled must be false")
        _require(errors, _string_tuple(step.get("evidence_ids")) != (), f"{path}.evidence_ids must be non-empty")


def _validate_disabled_capabilities(errors: list[str], value: Any) -> None:
    capabilities = _sequence(value)
    if not capabilities:
        errors.append("disabled_live_capabilities must be non-empty")
        return
    seen: set[str] = set()
    for index, raw in enumerate(capabilities):
        path = f"disabled_live_capabilities[{index}]"
        capability = _mapping(raw)
        capability_id = _text(capability.get("capability_id"))
        seen.add(capability_id)
        _require(errors, capability_id in REQUIRED_DISABLED_CAPABILITIES, f"{path}.capability_id is not required or recognized")
        _require(errors, capability.get("enabled") is False, f"{path}.enabled must be false")
        _require(errors, _text(capability.get("status")) in ALLOWED_DISABLED_STATUSES, f"{path}.status must be disabled, refused, manual_handoff_only, or blocked")
        _require(errors, bool(_text(capability.get("reason"))), f"{path}.reason is required")
        _require(errors, _string_tuple(capability.get("evidence_ids")) != (), f"{path}.evidence_ids must be non-empty")
    for capability_id in sorted(REQUIRED_DISABLED_CAPABILITIES - seen):
        errors.append(f"disabled_live_capabilities must include {capability_id}")


def _validate_reviewer_prompts(errors: list[str], value: Any) -> None:
    prompts = _sequence(value)
    if not prompts:
        errors.append("required_reviewer_prompts must be non-empty")
        return
    for index, raw in enumerate(prompts):
        path = f"required_reviewer_prompts[{index}]"
        prompt = _mapping(raw)
        _require(errors, bool(_text(prompt.get("prompt_id"))), f"{path}.prompt_id is required")
        _require(errors, bool(_text(prompt.get("reviewer_role"))), f"{path}.reviewer_role is required")
        _require(errors, bool(_text(prompt.get("question"))), f"{path}.question is required")
        _require(errors, bool(_text(prompt.get("required_before"))), f"{path}.required_before is required")
        _require(errors, _string_tuple(prompt.get("evidence_ids")) != (), f"{path}.evidence_ids must be non-empty")


def _validate_cited_readiness_claims(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        has_claim = any(str(key).lower() in CLAIM_KEYS and _text(child) for key, child in value.items())
        if has_claim and _string_tuple(value.get("evidence_ids")) == () and _string_tuple(value.get("source_evidence_ids")) == ():
            errors.append(f"{path} contains uncited readiness claim")
        for key, child in value.items():
            _validate_cited_readiness_claims(errors, child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_cited_readiness_claims(errors, child, f"{path}[{index}]")


def _validate_no_private_or_live_artifacts(errors: list[str], value: Any) -> None:
    for path, key, item in _walk(value):
        if key.lower() in FORBIDDEN_KEYS:
            errors.append(f"{path} uses forbidden private or raw artifact key {key}")
        if isinstance(item, str) and PRIVATE_VALUE_RE.search(item):
            errors.append(f"{path} references private/session artifact text")
        if isinstance(item, str) and RAW_CRAWL_REF_RE.search(item) and "raw_document_download_persistence" not in item:
            errors.append(f"{path} references raw crawl output or downloaded document material")


def _validate_no_forbidden_enablement(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        normalized = {str(key).lower(): child for key, child in value.items()}
        capability_id = _text(normalized.get("capability_id") or normalized.get("action_id") or normalized.get("step_id")).lower()
        status = _text(normalized.get("status") or normalized.get("decision")).lower()
        if capability_id in FORBIDDEN_CAPABILITY_IDS and normalized.get("enabled") is not False:
            errors.append(f"{path} may not enable forbidden capability {capability_id}")
        if capability_id in FORBIDDEN_CAPABILITY_IDS and status in ENABLED_STATUSES:
            errors.append(f"{path} gives forbidden capability enabled status {status}: {capability_id}")
        for key, child in value.items():
            key_text = str(key).lower()
            if key_text in ENABLEMENT_TRUE_KEYS and child is True:
                errors.append(f"{path}.{key} must not enable live or consequential capability")
            if child is True and any(word in key_text for word in FORBIDDEN_ACTION_WORDS):
                errors.append(f"{path}.{key} must not enable payment/upload/submission/scheduling/cancellation/certification")
            _validate_no_forbidden_enablement(errors, child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_forbidden_enablement(errors, child, f"{path}[{index}]")


def _walk(value: Any, path: str = "packet") -> tuple[tuple[str, str, Any], ...]:
    found: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            found.append((child_path, key_text, item))
            found.extend(_walk(item, child_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_walk(item, f"{path}[{index}]"))
    return tuple(found)


def _is_production_ready_label(value: str) -> bool:
    normalized = value.strip().lower().replace("_", "-")
    return value.strip().lower() in PRODUCTION_READY_LABELS or normalized in {"production-ready", "release-ready"}


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> tuple[Any, ...]:
    return tuple(value) if isinstance(value, list) else ()


def _string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped
