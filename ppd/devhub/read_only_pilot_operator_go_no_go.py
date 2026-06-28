from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.devhub.read_only_pilot_reconciliation import validate_reconciliation_packet
from ppd.post_decision_release_readiness_digest import validate_digest


REQUIRED_PACKET_ID = "devhub-read-only-pilot-operator-go-no-go-v1"
REQUIRED_PACKET_TYPE = "ppd.devhub_read_only_pilot_operator_go_no_go.v1"
REQUIRED_SECTIONS = (
    "operator_prerequisites",
    "redaction_checklist",
    "safe_read_only_observation_scope",
    "abort_triggers",
    "manual_login_boundaries",
    "journal_event_templates",
    "disabled_consequential_controls",
)
REQUIRED_REDACTION_ITEMS = (
    "no_credentials",
    "no_credential_prompts",
    "no_cookies",
    "no_auth_state",
    "no_screenshots",
    "no_traces",
    "no_har_files",
    "no_private_values",
    "no_raw_authenticated_text",
    "no_local_private_paths",
)
REQUIRED_ABORT_TERMS = (
    "credential",
    "automated login",
    "mfa",
    "captcha",
    "account creation",
    "private value",
    "screenshot",
    "trace",
    "har",
    "cookie",
    "auth state",
    "upload",
    "submit",
    "certify",
    "payment",
    "schedule",
    "cancel",
)
REQUIRED_DISABLED_CONTROLS = (
    "upload",
    "submission",
    "certification",
    "payment",
    "scheduling",
    "cancellation",
)
ALLOWED_JOURNAL_EVENT_TYPES = {
    "DevHub attended preflight",
    "manual handoff",
    "redacted read-only observation",
    "refused action",
    "post-action hardening review",
    "completion evidence",
}
FORBIDDEN_KEYS = {
    "auth_state",
    "auth_state_path",
    "browser_context",
    "captcha_response",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "field_value",
    "har",
    "har_path",
    "local_path",
    "mfa_code",
    "password",
    "private_field_value",
    "raw_authenticated_text",
    "raw_dom",
    "screenshot",
    "screenshot_path",
    "session_state",
    "storage_state",
    "storage_state_path",
    "trace",
    "trace_path",
}
FORBIDDEN_TEXT_PATTERNS = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b"),
    re.compile(r"/(?:home|Users|tmp|var/tmp)/"),
    re.compile(r"\b(?:auth_state\.json|storage_state\.json|trace\.zip)\b", re.IGNORECASE),
    re.compile(r"\.har\b", re.IGNORECASE),
)
CLAIM_FIELD_MARKERS = ("claim", "claims", "assertion", "attestation")
COMPLETION_FIELD_MARKERS = (
    "official_action_completed",
    "official_actions_completed",
    "completed_official_action",
    "action_completed",
    "official_completion",
    "completion_claim",
)
FORBIDDEN_CLAIM_PATTERNS = {
    "credential collection claim": re.compile(r"\b(?:collect(?:ed|ion)?|capture(?:d)?|ask(?:ed)? for|store(?:d)?)\s+(?:user\s+)?credentials?\b|\bcredential collection\b", re.IGNORECASE),
    "automated login claim": re.compile(r"\b(?:automated|automate|scripted|bot-driven)\s+login\b", re.IGNORECASE),
    "automated mfa claim": re.compile(r"\b(?:automated|automate|answered|solved|completed)\s+(?:an?\s+)?mfa\b", re.IGNORECASE),
    "automated captcha claim": re.compile(r"\b(?:automated|automate|answered|solved|completed)\s+(?:an?\s+)?captcha\b", re.IGNORECASE),
    "account creation claim": re.compile(r"\b(?:created|create|automated|automate|completed)\b.{0,40}\baccount\b|\baccount creation\b", re.IGNORECASE),
    "browser artifact claim": re.compile(r"\b(?:screenshot|trace|har|cookie|cookies|auth state|storage state|private value|private values)\b", re.IGNORECASE),
    "official action completion claim": re.compile(r"\b(?:completed|performed|finished|executed)\b.{0,50}\b(?:upload|submission|submit|certification|certify|payment|paid|scheduling|scheduled|cancellation|cancelled|canceled)\b|\b(?:uploaded|submitted|certified|paid|scheduled|cancelled|canceled)\b", re.IGNORECASE),
}


@dataclass(frozen=True)
class GoNoGoValidationResult:
    packet_id: str
    ok: bool
    errors: tuple[str, ...]


def load_go_no_go_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise ValueError("operator go/no-go packet must be a JSON object")
    return packet


def assert_valid_go_no_go_packet(
    packet: Mapping[str, Any],
    reconciliation_packet: Mapping[str, Any],
    post_decision_digest: Mapping[str, Any],
    operator_checklist: Mapping[str, Any],
    pilot_result_intake: Mapping[str, Any],
    release_gate_status: Mapping[str, Any],
) -> None:
    result = validate_go_no_go_packet(
        packet,
        reconciliation_packet,
        post_decision_digest,
        operator_checklist,
        pilot_result_intake,
        release_gate_status,
    )
    if not result.ok:
        raise AssertionError("; ".join(result.errors))


def validate_go_no_go_packet(
    packet: Mapping[str, Any],
    reconciliation_packet: Mapping[str, Any],
    post_decision_digest: Mapping[str, Any],
    operator_checklist: Mapping[str, Any],
    pilot_result_intake: Mapping[str, Any],
    release_gate_status: Mapping[str, Any],
) -> GoNoGoValidationResult:
    errors: list[str] = []
    packet_id = _text(packet.get("packet_id"))

    reconciliation_result = validate_reconciliation_packet(
        reconciliation_packet,
        operator_checklist,
        pilot_result_intake,
        release_gate_status,
    )
    for error in reconciliation_result.errors:
        errors.append("readiness_reconciliation: " + error)
    for error in validate_digest(post_decision_digest):
        errors.append("post_decision_digest: " + error)

    _require(errors, packet_id == REQUIRED_PACKET_ID, "packet_id must identify the operator go/no-go packet")
    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    _require(errors, packet.get("mode") == "fixture_first_operator_go_no_go", "mode must be fixture_first_operator_go_no_go")
    _require(errors, packet.get("fixture_first") is True, "fixture_first must be true")
    _require(errors, packet.get("metadata_only") is True, "metadata_only must be true")
    _require(errors, packet.get("read_only_only") is True, "read_only_only must be true")
    _require(errors, packet.get("launches_devhub") is False, "launches_devhub must be false")
    _require(errors, packet.get("launches_playwright") is False, "launches_playwright must be false")
    _require(errors, packet.get("live_session_authorized") is False, "live_session_authorized must be false")
    _require(errors, packet.get("official_actions_enabled") is False, "official_actions_enabled must be false")
    _require(errors, packet.get("stores_private_values") is False, "stores_private_values must be false")
    _require(errors, packet.get("stores_browser_artifacts") is False, "stores_browser_artifacts must be false")

    _validate_source_packets(errors, packet.get("source_packets"), reconciliation_packet, post_decision_digest)
    _validate_named_rows(errors, packet.get("operator_prerequisites"), "operator_prerequisites", ("prerequisite_id", "description", "go_no_go_effect"))
    _validate_redaction_checklist(errors, packet.get("redaction_checklist"))
    _validate_observation_scope(errors, packet.get("safe_read_only_observation_scope"))
    _validate_abort_triggers(errors, packet.get("abort_triggers"))
    _validate_manual_login_boundaries(errors, packet.get("manual_login_boundaries"))
    _validate_journal_templates(errors, packet.get("journal_event_templates"))
    _validate_disabled_controls(errors, packet.get("disabled_consequential_controls"))
    _scan_for_forbidden_content(errors, packet, "packet")
    _scan_for_forbidden_claims(errors, packet, "packet", False)
    _scan_for_official_completion(errors, packet, "packet")

    return GoNoGoValidationResult(packet_id=packet_id, ok=not errors, errors=tuple(_dedupe(errors)))


def _validate_source_packets(errors: list[str], value: Any, reconciliation_packet: Mapping[str, Any], post_decision_digest: Mapping[str, Any]) -> None:
    links = _mapping(value)
    expected = {
        "devhub_read_only_pilot_readiness_reconciliation": _text(reconciliation_packet.get("packet_id")),
        "post_decision_release_readiness_digest": _text(post_decision_digest.get("packet_id")),
    }
    for key, packet_id in expected.items():
        link = _mapping(links.get(key))
        _require(errors, link.get("packet_id") == packet_id, f"source_packets.{key}.packet_id must match consumed packet")
        _require(errors, link.get("consumed") is True, f"source_packets.{key}.consumed must be true")
        _require(errors, _text(link.get("path")).startswith("ppd/tests/fixtures/"), f"source_packets.{key}.path must point to a committed PP&D fixture")


def _validate_named_rows(errors: list[str], value: Any, label: str, required_fields: Sequence[str]) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append(f"{label} must be a non-empty list")
        return
    for index, row in enumerate(rows):
        item = _mapping(row)
        for field in required_fields:
            _require(errors, bool(_text(item.get(field))), f"{label}[{index}].{field} is required")
        _require(errors, item.get("launches_devhub") is False, f"{label}[{index}].launches_devhub must be false")
        _require(errors, item.get("blocks_live_action") is True, f"{label}[{index}].blocks_live_action must be true")


def _validate_redaction_checklist(errors: list[str], value: Any) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append("redaction_checklist must be a non-empty list")
        return
    by_id = {_text(_mapping(row).get("item_id")): _mapping(row) for row in rows}
    for required in REQUIRED_REDACTION_ITEMS:
        item = by_id.get(required)
        if not item:
            errors.append("redaction_checklist missing: " + required)
            continue
        _require(errors, item.get("required") is True, f"redaction_checklist.{required}.required must be true")
        _require(errors, item.get("satisfied_by_fixture") is True, f"redaction_checklist.{required}.satisfied_by_fixture must be true")
        _require(errors, item.get("raw_value_allowed") is False, f"redaction_checklist.{required}.raw_value_allowed must be false")


def _validate_observation_scope(errors: list[str], value: Any) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append("safe_read_only_observation_scope must be a non-empty list")
        return
    for index, row in enumerate(rows):
        item = _mapping(row)
        path = f"safe_read_only_observation_scope[{index}]"
        for field in ("scope_id", "surface_category", "allowed_observation", "redaction_requirement"):
            _require(errors, bool(_text(item.get(field))), f"{path}.{field} is required")
        _require(errors, item.get("read_only") is True, f"{path}.read_only must be true")
        _require(errors, item.get("private_values_allowed") is False, f"{path}.private_values_allowed must be false")
        _require(errors, item.get("consequential_controls_allowed") is False, f"{path}.consequential_controls_allowed must be false")


def _validate_abort_triggers(errors: list[str], value: Any) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append("abort_triggers must be a non-empty list")
        return
    combined = "\n".join(_text(_mapping(row).get("trigger")) for row in rows).casefold()
    for term in REQUIRED_ABORT_TERMS:
        if term.casefold() not in combined:
            errors.append("abort_triggers missing required term: " + term)
    for index, row in enumerate(rows):
        item = _mapping(row)
        path = f"abort_triggers[{index}]"
        for field in ("trigger_id", "trigger", "operator_response", "journal_event_type"):
            _require(errors, bool(_text(item.get(field))), f"{path}.{field} is required")
        _require(errors, item.get("records_only_redacted_metadata") is True, f"{path}.records_only_redacted_metadata must be true")
        _require(errors, item.get("continues_session") is False, f"{path}.continues_session must be false")


def _validate_manual_login_boundaries(errors: list[str], value: Any) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append("manual_login_boundaries must be a non-empty list")
        return
    combined = "\n".join(_text(_mapping(row).get("boundary")) for row in rows).casefold()
    for term in ("operator opens devhub", "manual login", "mfa", "captcha", "credential", "no automation"):
        if term not in combined:
            errors.append("manual_login_boundaries missing required term: " + term)
    for index, row in enumerate(rows):
        item = _mapping(row)
        path = f"manual_login_boundaries[{index}]"
        _require(errors, bool(_text(item.get("boundary_id"))), f"{path}.boundary_id is required")
        _require(errors, item.get("automated") is False, f"{path}.automated must be false")
        _require(errors, item.get("operator_attended") is True, f"{path}.operator_attended must be true")
        _require(errors, item.get("stores_credentials") is False, f"{path}.stores_credentials must be false")


def _validate_journal_templates(errors: list[str], value: Any) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append("journal_event_templates must be a non-empty list")
        return
    for index, row in enumerate(rows):
        item = _mapping(row)
        path = f"journal_event_templates[{index}]"
        _require(errors, bool(_text(item.get("template_id"))), f"{path}.template_id is required")
        event_type = _text(item.get("event_type"))
        _require(errors, event_type in ALLOWED_JOURNAL_EVENT_TYPES, f"{path}.event_type is not allowed")
        _require(errors, item.get("commit_safe") is True, f"{path}.commit_safe must be true")
        _require(errors, item.get("stores_private_values") is False, f"{path}.stores_private_values must be false")
        _require(errors, item.get("stores_browser_artifacts") is False, f"{path}.stores_browser_artifacts must be false")
        allowed_fields = _sequence(item.get("allowed_fields"))
        _require(errors, bool(allowed_fields), f"{path}.allowed_fields must be non-empty")


def _validate_disabled_controls(errors: list[str], value: Any) -> None:
    rows = _sequence(value)
    if not rows:
        errors.append("disabled_consequential_controls must be a non-empty list")
        return
    by_id = {_text(_mapping(row).get("control_id")): _mapping(row) for row in rows}
    for required in REQUIRED_DISABLED_CONTROLS:
        item = by_id.get(required)
        if not item:
            errors.append("disabled_consequential_controls missing: " + required)
            continue
        _require(errors, item.get("enabled") is False, f"disabled_consequential_controls.{required}.enabled must be false")
        _require(errors, item.get("allowed_in_pilot") is False, f"disabled_consequential_controls.{required}.allowed_in_pilot must be false")
        _require(errors, item.get("requires_user_confirmation") is True, f"disabled_consequential_controls.{required}.requires_user_confirmation must be true")


def _scan_for_forbidden_content(errors: list[str], value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text.casefold() in FORBIDDEN_KEYS:
                errors.append(f"{path}.{key_text} contains forbidden private/session field")
            _scan_for_forbidden_content(errors, child, f"{path}.{key_text}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_content(errors, child, f"{path}[{index}]")
    elif isinstance(value, str):
        for pattern in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                errors.append(f"{path} contains private value or browser artifact reference")
                break


def _scan_for_forbidden_claims(errors: list[str], value: Any, path: str, in_claim_context: bool) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_claim_context = in_claim_context or any(marker in key_text.casefold() for marker in CLAIM_FIELD_MARKERS)
            _scan_for_forbidden_claims(errors, child, f"{path}.{key_text}", child_claim_context)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_claims(errors, child, f"{path}[{index}]", in_claim_context)
    elif in_claim_context and isinstance(value, str):
        for label, pattern in FORBIDDEN_CLAIM_PATTERNS.items():
            if pattern.search(value):
                errors.append(f"{path} contains forbidden {label}")


def _scan_for_official_completion(errors: list[str], value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.casefold() in COMPLETION_FIELD_MARKERS and _truthy_completion_value(child):
                errors.append(f"{child_path} claims official action completion")
            _scan_for_official_completion(errors, child, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_official_completion(errors, child, f"{path}[{index}]")


def _truthy_completion_value(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().casefold() not in {"false", "no", "none", "not_applicable", "not applicable"}
    if isinstance(value, Mapping):
        return any(_truthy_completion_value(child) for child in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_truthy_completion_value(child) for child in value)
    return False


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


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
