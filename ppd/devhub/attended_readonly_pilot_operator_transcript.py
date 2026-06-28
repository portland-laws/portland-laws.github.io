from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


REQUIRED_PACKET_TYPE = "devhub_attended_readonly_pilot_operator_transcript_packet"
REQUIRED_SOURCE_PACKET_TYPE = "devhub_attended_readonly_pilot_launch_readiness_packet"
REQUIRED_MODE = "fixture_first_attended_readonly_simulation"
REQUIRED_ATTENDANCE_KINDS = {"manual_user_attendance_checkpoint"}
REQUIRED_REDACTION_KINDS = {"redacted_page_state_summary"}
REQUIRED_SELECTOR_KIND = "selector_confidence_confirmation"
REQUIRED_GUARDRAIL_TRUE = (
    "no_browser_launched",
    "no_auth_state_created_or_read",
    "no_private_devhub_data_read",
    "no_screenshots_captured",
    "no_traces_captured",
    "no_downloads_created",
    "no_official_action_taken",
)
REQUIRED_EMPTY_ARTIFACT_LISTS = (
    "browser_sessions",
    "auth_state_files",
    "screenshots",
    "traces",
    "raw_crawl_outputs",
    "downloaded_documents",
)
CONSEQUENTIAL_TERMS = (
    "upload",
    "submit",
    "certify",
    "payment",
    "pay",
    "purchase",
    "schedule",
    "cancel",
    "withdraw",
    "extension",
    "reactivate",
)
FORBIDDEN_KEY_FRAGMENTS = (
    "auth_state",
    "session_state",
    "storage_state",
    "cookie",
    "credential",
    "password",
    "mfa_code",
    "captcha_solution",
    "raw_authenticated",
    "raw_dom",
    "raw_value",
    "field_value",
    "private_value",
    "screenshot",
    "trace_path",
    "har_path",
    "har_file",
    "browser_context",
)
FORBIDDEN_VALUE_FRAGMENTS = (
    "/home/",
    "/users/",
    "c:\\users\\",
    "file://",
    "~/",
    "auth_state.json",
    "storage_state.json",
    "session_state.json",
    "trace.zip",
    ".har",
    "screenshot.png",
    "screenshot.jpg",
    "screenshot.jpeg",
    "screenshot.webp",
    "raw authenticated value",
    "raw authenticated text",
    "private field value",
)
LIVE_EXECUTION_TERMS = (
    "launched live browser",
    "live browser launched",
    "ran playwright",
    "playwright executed",
    "clicked in devhub",
    "filled in devhub",
    "captured screenshot",
    "captured trace",
    "captured har",
    "stored auth state",
    "saved auth state",
)
MUTATION_FLAG_NAMES = (
    "mutates_surface_registry",
    "surface_registry_mutation_enabled",
    "active_surface_registry_mutation",
    "mutates_agent_state",
    "agent_state_mutation_enabled",
    "active_agent_state_mutation",
)


@dataclass(frozen=True)
class OperatorTranscriptValidationResult:
    packet_id: str
    ok: bool
    errors: tuple[str, ...]


def load_operator_transcript_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("operator transcript packet must be a JSON object")
    return data


def assert_valid_operator_transcript_packet(packet: Mapping[str, Any]) -> None:
    result = validate_operator_transcript_packet(packet)
    if not result.ok:
        raise AssertionError("; ".join(result.errors))


def validate_operator_transcript_packet(packet: Mapping[str, Any]) -> OperatorTranscriptValidationResult:
    errors: list[str] = []
    if not isinstance(packet, Mapping):
        return OperatorTranscriptValidationResult(packet_id="", ok=False, errors=("packet must be a JSON object",))

    packet_id = _text(packet.get("packet_id"))
    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    _require(errors, packet.get("source_packet_type") == REQUIRED_SOURCE_PACKET_TYPE, f"source_packet_type must be {REQUIRED_SOURCE_PACKET_TYPE}")
    _require(errors, packet.get("mode") == REQUIRED_MODE, f"mode must be {REQUIRED_MODE}")

    _validate_reviewer_owner_fields(errors, _mapping(packet.get("reviewer_owner_fields")))
    _validate_observations(errors, _sequence(packet.get("ordered_operator_observations")))
    _validate_guardrail_attestations(errors, _mapping(packet.get("guardrail_attestations")))
    _validate_prohibited_artifacts(errors, _mapping(packet.get("prohibited_artifacts")))
    _validate_source_launch_readiness(errors, _mapping(packet.get("source_launch_readiness_packet")))
    _scan_for_unsafe_content(errors, packet)
    _scan_for_consequential_controls(errors, packet)
    _scan_for_mutation_flags(errors, packet)

    return OperatorTranscriptValidationResult(packet_id=packet_id, ok=not errors, errors=tuple(_dedupe(errors)))


def _validate_reviewer_owner_fields(errors: list[str], fields: Mapping[str, Any]) -> None:
    _require(errors, bool(_text(fields.get("reviewer"))), "reviewer_owner_fields.reviewer is required")
    _require(errors, bool(_text(fields.get("owner"))), "reviewer_owner_fields.owner is required")
    _require(errors, fields.get("approval_required_before_live_use") is True, "reviewer_owner_fields.approval_required_before_live_use must be true")


def _validate_observations(errors: list[str], observations: Sequence[Any]) -> None:
    if not observations:
        errors.append("ordered_operator_observations must be non-empty")
        return

    expected_sequence = 1
    attendance_count = 0
    redaction_count = 0
    selector_count = 0
    for index, raw_observation in enumerate(observations):
        observation = _mapping(raw_observation)
        path = f"ordered_operator_observations[{index}]"
        sequence = observation.get("sequence")
        _require(errors, isinstance(sequence, int), f"{path}.sequence must be an integer")
        if isinstance(sequence, int):
            _require(errors, sequence == expected_sequence, f"{path}.sequence must be {expected_sequence}")
        expected_sequence += 1

        kind = _text(observation.get("kind"))
        _require(errors, bool(kind), f"{path}.kind is required")
        _require(errors, observation.get("simulated_only") is True, f"{path}.simulated_only must be true")

        if kind in REQUIRED_ATTENDANCE_KINDS:
            attendance_count += 1
            _require(errors, bool(_text(observation.get("checkpoint_id"))), f"{path}.checkpoint_id is required")
            _require(errors, observation.get("requires_live_user_presence") is True, f"{path}.requires_live_user_presence must be true")
        elif kind in REQUIRED_REDACTION_KINDS:
            redaction_count += 1
            _require(errors, bool(_text(observation.get("page_state_id"))), f"{path}.page_state_id is required")
            _require(errors, bool(_text(observation.get("redacted_summary"))), f"{path}.redacted_summary is required")
            _require(errors, bool(_sequence(observation.get("redactions_applied"))), f"{path}.redactions_applied must be non-empty")
            _require(errors, observation.get("contains_private_devhub_data") is False, f"{path}.contains_private_devhub_data must be false")
        elif kind == REQUIRED_SELECTOR_KIND:
            selector_count += 1
            _require(errors, bool(_text(observation.get("selector_id"))), f"{path}.selector_id is required")
            _require(errors, _text(observation.get("confidence")) in {"low", "medium", "high"}, f"{path}.confidence must be low, medium, or high")
            _require(errors, bool(_text(observation.get("basis"))), f"{path}.basis is required")
            _require(errors, observation.get("requires_live_verification_before_use") is True, f"{path}.requires_live_verification_before_use must be true")
            _require(errors, bool(_sequence(observation.get("citations"))), f"{path}.citations must be non-empty")
        else:
            errors.append(f"{path}.kind is not allowed")

    _require(errors, attendance_count > 0, "ordered_operator_observations must include an attendance checkpoint")
    _require(errors, redaction_count > 0, "ordered_operator_observations must include a redacted page state summary")
    _require(errors, selector_count > 0, "ordered_operator_observations must include a selector confidence confirmation")


def _validate_guardrail_attestations(errors: list[str], attestations: Mapping[str, Any]) -> None:
    for key in REQUIRED_GUARDRAIL_TRUE:
        _require(errors, attestations.get(key) is True, f"guardrail_attestations.{key} must be true")


def _validate_prohibited_artifacts(errors: list[str], artifacts: Mapping[str, Any]) -> None:
    for key in REQUIRED_EMPTY_ARTIFACT_LISTS:
        _require(errors, artifacts.get(key) == [], f"prohibited_artifacts.{key} must be an empty list")
    _require(errors, artifacts.get("har_files", []) == [], "prohibited_artifacts.har_files must be an empty list when present")


def _validate_source_launch_readiness(errors: list[str], source: Mapping[str, Any]) -> None:
    _require(errors, source.get("packet_type") == REQUIRED_SOURCE_PACKET_TYPE, f"source_launch_readiness_packet.packet_type must be {REQUIRED_SOURCE_PACKET_TYPE}")
    _validate_reviewer_owner_fields(errors, _mapping(source.get("reviewer_owner_fields")))
    _require(errors, bool(_sequence(source.get("manual_user_attendance_checkpoints"))), "source_launch_readiness_packet.manual_user_attendance_checkpoints must be non-empty")
    _require(errors, bool(_sequence(source.get("redacted_page_state_summaries"))), "source_launch_readiness_packet.redacted_page_state_summaries must be non-empty")
    for index, summary in enumerate(_sequence(source.get("redacted_page_state_summaries"))):
        item = _mapping(summary)
        _require(errors, bool(_text(item.get("redacted_summary"))), f"source_launch_readiness_packet.redacted_page_state_summaries[{index}].redacted_summary is required")
        _require(errors, bool(_sequence(item.get("redactions_applied"))), f"source_launch_readiness_packet.redacted_page_state_summaries[{index}].redactions_applied must be non-empty")
    for index, confirmation in enumerate(_sequence(source.get("selector_confidence_confirmations"))):
        item = _mapping(confirmation)
        _require(errors, bool(_sequence(item.get("citations"))), f"source_launch_readiness_packet.selector_confidence_confirmations[{index}].citations must be non-empty")


def _scan_for_unsafe_content(errors: list[str], value: Any, path: str = "$", parent_key: str = "") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = _text(key)
            key_normalized = key_text.lower().replace("-", "_")
            child_path = f"{path}.{key_text}"
            if any(fragment in key_normalized for fragment in FORBIDDEN_KEY_FRAGMENTS):
                errors.append(f"{child_path} must not contain private/session artifact fields")
            _scan_for_unsafe_content(errors, child, child_path, key_text)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_unsafe_content(errors, child, f"{path}[{index}]", parent_key)
        return
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in FORBIDDEN_VALUE_FRAGMENTS):
            errors.append(f"{path} must not contain private paths, raw authenticated values, screenshots, traces, HAR paths, or stored auth state")
        if any(term in lowered for term in LIVE_EXECUTION_TERMS):
            errors.append(f"{path} must not claim live browser execution or captured browser artifacts")


def _scan_for_consequential_controls(errors: list[str], value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        label = " ".join(_text(value.get(key)) for key in ("control_id", "name", "label", "action", "kind")).lower()
        enabled = value.get("enabled") is True or value.get("allowed") is True or value.get("state") == "enabled"
        if enabled and any(term in label for term in CONSEQUENTIAL_TERMS):
            errors.append(f"{path} must not enable consequential controls")
        for key, child in value.items():
            _scan_for_consequential_controls(errors, child, f"{path}.{_text(key)}")
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_consequential_controls(errors, child, f"{path}[{index}]")


def _scan_for_mutation_flags(errors: list[str], value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = _text(key)
            normalized = key_text.lower().replace("-", "_")
            child_path = f"{path}.{key_text}"
            if normalized in MUTATION_FLAG_NAMES and child is True:
                errors.append(f"{child_path} must not enable surface-registry or agent-state mutation")
            _scan_for_mutation_flags(errors, child, child_path)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_mutation_flags(errors, child, f"{path}[{index}]")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return ()


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)
