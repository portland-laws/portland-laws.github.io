from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


REQUIRED_PACKET_TYPE = "ppd.devhub_read_only_pilot_result_intake.v1"
REQUIRED_MODE = "attended_read_only_pilot_result_intake"
REQUIRED_SOURCE_PACKET_IDS = {
    "operator_checklist": "devhub-read-only-pilot-operator-checklist-v1",
    "evidence_template": "devhub-attended-pilot-evidence-template-v1",
}

ALLOWED_TOP_LEVEL_KEYS = {
    "packet_id",
    "packet_type",
    "mode",
    "fixture_first",
    "attended_session",
    "read_only_only",
    "metadata_only",
    "automated_login",
    "mfa_automated",
    "captcha_automated",
    "account_creation_automated",
    "credential_prompted",
    "stores_browser_artifacts",
    "screenshots_captured",
    "traces_captured",
    "har_captured",
    "official_actions_completed",
    "source_packets",
    "redaction_attestations",
    "journal_event_ids",
    "observations",
    "abort_conditions",
    "consequential_controls",
    "post_action_hardening",
}
ALLOWED_OBSERVATION_KEYS = {
    "observation_id",
    "surface_id",
    "redacted_heading",
    "redacted_labels",
    "status_category",
    "scope_category",
    "journal_event_id",
}
ALLOWED_ABORT_KEYS = {"condition_id", "trigger", "operator_response", "journal_event_id"}
ALLOWED_CONTROL_KEYS = {"control_id", "status", "allowed", "official_action_completed"}
ALLOWED_HARDENING_KEYS = {
    "required",
    "official_state_changed",
    "official_actions_completed",
    "browser_artifacts_stored",
    "screenshots_stored",
    "traces_stored",
    "har_stored",
    "private_values_stored",
    "notes",
}
ALLOWED_STATUS_CATEGORIES = {
    "home_loaded",
    "permit_list_visible",
    "permit_detail_visible",
    "fees_notice_visible",
    "correction_notice_visible",
    "inspection_result_visible",
    "manual_abort",
    "not_observed",
}
ALLOWED_SCOPE_CATEGORIES = {"read_only", "metadata_only", "manual_abort"}
REQUIRED_REDACTION_ATTESTATIONS = (
    "no_automated_login",
    "no_mfa_automation",
    "no_captcha_automation",
    "no_account_creation_automation",
    "no_credential_prompts",
    "no_credentials",
    "no_cookies",
    "no_auth_state",
    "no_stored_browser_artifacts",
    "no_screenshots",
    "no_traces",
    "no_har_data",
    "no_private_field_values",
    "no_consequential_controls",
    "no_official_actions_completed",
)
REQUIRED_ABORT_TERMS = (
    "automated login",
    "credential",
    "mfa",
    "captcha",
    "account creation",
    "cookie",
    "auth state",
    "browser artifact",
    "screenshot",
    "trace",
    "har",
    "private field value",
    "upload",
    "submit",
    "certify",
    "payment",
    "schedule",
    "cancel",
    "official action",
)
CONSEQUENTIAL_TERMS = (
    "upload",
    "submit",
    "certify",
    "payment",
    "pay fee",
    "schedule inspection",
    "cancel",
    "withdraw",
    "request extension",
    "reactivate",
    "official action",
)
FORBIDDEN_KEYS = {
    "auth_state",
    "auth_state_path",
    "browser_context",
    "captcha_solution",
    "cookie",
    "cookies",
    "credential",
    "credential_prompt",
    "credentials",
    "field_value",
    "har",
    "har_data",
    "har_path",
    "mfa_code",
    "password",
    "private_field_value",
    "raw_authenticated_text",
    "raw_dom",
    "raw_field_value",
    "screenshot",
    "screenshot_path",
    "session_state",
    "storage_state",
    "storage_state_path",
    "trace",
    "trace_path",
}
FORBIDDEN_TEXT_PATTERNS = (
    re.compile(r"\bautomated login\b", re.IGNORECASE),
    re.compile(r"\blogin automation\b", re.IGNORECASE),
    re.compile(r"\bautomate(?:d)?\s+(?:mfa|captcha|account creation)\b", re.IGNORECASE),
    re.compile(r"\bprompt(?:ed)? for credentials\b", re.IGNORECASE),
    re.compile(r"\bcredential prompt\b", re.IGNORECASE),
    re.compile(r"\b(cookie|auth state|storage state|screenshot|trace|har)\b", re.IGNORECASE),
    re.compile(r"\bprivate field value\b", re.IGNORECASE),
    re.compile(r"\b(?:uploaded|submitted|certified|paid|scheduled|cancelled|canceled|withdrew|official action completed)\b", re.IGNORECASE),
)
JOURNAL_EVENT_ID_RE = re.compile(r"^JRN-[A-Z0-9][A-Z0-9-]*$")


@dataclass(frozen=True)
class PilotResultIntakeValidationResult:
    packet_id: str
    ok: bool
    errors: tuple[str, ...]


def load_pilot_result_intake(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("pilot result intake packet must be a JSON object")
    return data


def assert_valid_pilot_result_intake(packet: Mapping[str, Any]) -> None:
    result = validate_pilot_result_intake(packet)
    if not result.ok:
        raise AssertionError("; ".join(result.errors))


def validate_pilot_result_intake(packet: Mapping[str, Any]) -> PilotResultIntakeValidationResult:
    errors: list[str] = []
    packet_id = _text(packet.get("packet_id"))
    unknown_top_level = sorted(set(packet) - ALLOWED_TOP_LEVEL_KEYS)
    if unknown_top_level:
        errors.append("packet contains disallowed field(s): " + ", ".join(unknown_top_level))
    forbidden_top_level = sorted(key for key in packet if str(key).casefold() in FORBIDDEN_KEYS)
    if forbidden_top_level:
        errors.append("packet contains forbidden private/session field(s): " + ", ".join(forbidden_top_level))

    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    _require(errors, packet.get("mode") == REQUIRED_MODE, f"mode must be {REQUIRED_MODE}")
    for key in ("fixture_first", "attended_session", "read_only_only", "metadata_only"):
        _require(errors, packet.get(key) is True, f"{key} must be true")
    for key in (
        "automated_login",
        "mfa_automated",
        "captcha_automated",
        "account_creation_automated",
        "credential_prompted",
        "stores_browser_artifacts",
        "screenshots_captured",
        "traces_captured",
        "har_captured",
        "official_actions_completed",
    ):
        _require(errors, packet.get(key) is False, f"{key} must be false")

    source_packets = _mapping(packet.get("source_packets"))
    for key, expected in REQUIRED_SOURCE_PACKET_IDS.items():
        _require(errors, source_packets.get(key) == expected, f"source_packets.{key} must be {expected}")

    _validate_redaction_attestations(errors, _mapping(packet.get("redaction_attestations")))
    journal_ids = _validate_journal_event_ids(errors, packet.get("journal_event_ids"))
    _validate_observations(errors, packet.get("observations"), journal_ids)
    _validate_abort_conditions(errors, packet.get("abort_conditions"), journal_ids)
    _validate_consequential_controls(errors, packet.get("consequential_controls"))
    _validate_post_action_hardening(errors, _mapping(packet.get("post_action_hardening")))
    return PilotResultIntakeValidationResult(packet_id=packet_id, ok=not errors, errors=tuple(_dedupe(errors)))


def _validate_redaction_attestations(errors: list[str], attestations: Mapping[str, Any]) -> None:
    if not attestations:
        errors.append("redaction_attestations must be present")
        return
    unknown = sorted(set(attestations) - set(REQUIRED_REDACTION_ATTESTATIONS))
    if unknown:
        errors.append("redaction_attestations contains disallowed field(s): " + ", ".join(unknown))
    for field in REQUIRED_REDACTION_ATTESTATIONS:
        _require(errors, attestations.get(field) is True, f"redaction_attestations.{field} must be true")


def _validate_journal_event_ids(errors: list[str], value: Any) -> set[str]:
    ids = _string_tuple(value)
    if not ids:
        errors.append("journal_event_ids must be non-empty")
        return set()
    seen: set[str] = set()
    for index, event_id in enumerate(ids):
        if not JOURNAL_EVENT_ID_RE.match(event_id):
            errors.append(f"journal_event_ids[{index}] must match JRN-* uppercase format")
        elif event_id in seen:
            errors.append(f"journal_event_ids[{index}] must be unique")
        else:
            seen.add(event_id)
    return seen


def _validate_observations(errors: list[str], value: Any, journal_ids: set[str]) -> None:
    observations = _sequence(value)
    if not observations:
        errors.append("observations must be non-empty")
        return
    for index, item in enumerate(observations):
        path = f"observations[{index}]"
        observation = _mapping(item)
        unknown = sorted(set(observation) - ALLOWED_OBSERVATION_KEYS)
        if unknown:
            errors.append(f"{path} contains disallowed field(s): " + ", ".join(unknown))
        forbidden = sorted(key for key in observation if str(key).casefold() in FORBIDDEN_KEYS)
        if forbidden:
            errors.append(f"{path} contains forbidden private/session field(s): " + ", ".join(forbidden))
        _require(errors, bool(_text(observation.get("observation_id"))), f"{path}.observation_id is required")
        _require(errors, bool(_text(observation.get("surface_id"))), f"{path}.surface_id is required")
        _require(errors, bool(_text(observation.get("redacted_heading"))), f"{path}.redacted_heading is required")
        _require(errors, _string_tuple(observation.get("redacted_labels")) != (), f"{path}.redacted_labels must be non-empty")
        _require(errors, _text(observation.get("status_category")) in ALLOWED_STATUS_CATEGORIES, f"{path}.status_category is not allowed")
        _require(errors, _text(observation.get("scope_category")) in ALLOWED_SCOPE_CATEGORIES, f"{path}.scope_category is not allowed")
        _require(errors, _text(observation.get("journal_event_id")) in journal_ids, f"{path}.journal_event_id must link to a known journal event")
        errors.extend(_unsafe_text_errors(observation, path))


def _validate_abort_conditions(errors: list[str], value: Any, journal_ids: set[str]) -> None:
    conditions = _sequence(value)
    if not conditions:
        errors.append("abort_conditions must be non-empty")
        return
    all_text = "\n".join(_text(_mapping(condition).get("trigger")) for condition in conditions).casefold()
    missing = [term for term in REQUIRED_ABORT_TERMS if term.casefold() not in all_text]
    if missing:
        errors.append("abort_conditions missing required terms: " + ", ".join(missing))
    for index, item in enumerate(conditions):
        path = f"abort_conditions[{index}]"
        condition = _mapping(item)
        unknown = sorted(set(condition) - ALLOWED_ABORT_KEYS)
        if unknown:
            errors.append(f"{path} contains disallowed field(s): " + ", ".join(unknown))
        _require(errors, bool(_text(condition.get("condition_id"))), f"{path}.condition_id is required")
        _require(errors, bool(_text(condition.get("trigger"))), f"{path}.trigger is required")
        _require(errors, bool(_text(condition.get("operator_response"))), f"{path}.operator_response is required")
        _require(errors, _text(condition.get("journal_event_id")) in journal_ids, f"{path}.journal_event_id must link to a known journal event")


def _validate_consequential_controls(errors: list[str], value: Any) -> None:
    controls = _sequence(value)
    if not controls:
        errors.append("consequential_controls must list refused controls")
        return
    control_text = "\n".join(_text(_mapping(control).get("control_id")) + " " + _text(_mapping(control).get("status")) for control in controls).casefold()
    missing = [term for term in CONSEQUENTIAL_TERMS if term not in control_text]
    if missing:
        errors.append("consequential_controls missing refused terms: " + ", ".join(missing))
    for index, item in enumerate(controls):
        path = f"consequential_controls[{index}]"
        control = _mapping(item)
        unknown = sorted(set(control) - ALLOWED_CONTROL_KEYS)
        if unknown:
            errors.append(f"{path} contains disallowed field(s): " + ", ".join(unknown))
        _require(errors, bool(_text(control.get("control_id"))), f"{path}.control_id is required")
        _require(errors, control.get("allowed") is False, f"{path}.allowed must be false")
        _require(errors, _text(control.get("status")) == "refused", f"{path}.status must be refused")
        _require(errors, control.get("official_action_completed") is False, f"{path}.official_action_completed must be false")


def _validate_post_action_hardening(errors: list[str], hardening: Mapping[str, Any]) -> None:
    unknown = sorted(set(hardening) - ALLOWED_HARDENING_KEYS)
    if unknown:
        errors.append("post_action_hardening contains disallowed field(s): " + ", ".join(unknown))
    _require(errors, hardening.get("required") is True, "post_action_hardening.required must be true")
    for flag in (
        "official_state_changed",
        "official_actions_completed",
        "browser_artifacts_stored",
        "screenshots_stored",
        "traces_stored",
        "har_stored",
        "private_values_stored",
    ):
        _require(errors, hardening.get(flag) is False, f"post_action_hardening.{flag} must be false")
    notes = _string_tuple(hardening.get("notes"))
    _require(errors, bool(notes), "post_action_hardening.notes must be non-empty")
    for index, note in enumerate(notes):
        if any(pattern.search(note) for pattern in FORBIDDEN_TEXT_PATTERNS):
            errors.append(f"post_action_hardening.notes[{index}] contains prohibited live/session/action content")


def _unsafe_text_errors(value: Mapping[str, Any], path: str) -> list[str]:
    errors: list[str] = []
    for key, item in value.items():
        if isinstance(item, str) and any(pattern.search(item) for pattern in FORBIDDEN_TEXT_PATTERNS):
            errors.append(f"{path}.{key} contains prohibited live/session/action content")
        elif isinstance(item, Sequence) and not isinstance(item, (str, bytes, bytearray)):
            for index, child in enumerate(item):
                if isinstance(child, str) and any(pattern.search(child) for pattern in FORBIDDEN_TEXT_PATTERNS):
                    errors.append(f"{path}.{key}[{index}] contains prohibited live/session/action content")
    return errors


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _string_tuple(value: Any) -> tuple[str, ...]:
    return tuple(item for item in _sequence(value) if isinstance(item, str))


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return tuple(output)
