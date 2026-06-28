from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


REQUIRED_PACKET_ID = "devhub-read-only-pilot-operator-checklist-v1"
REQUIRED_SOURCE_PACKETS = {
    "attended_pilot_runbook": "devhub-attended-read-only-pilot-runbook-v1",
    "attended_dry_run_review": "attended_pilot_dry_run_review",
    "attended_evidence_template": "devhub-attended-pilot-evidence-template-v1",
}
REQUIRED_STEP_IDS = (
    "fixture_packet_review",
    "login_attendance_handoff",
    "observation_scope_confirmation",
    "redaction_preflight",
    "automation_refusal_gate",
    "abort_condition_gate",
    "journal_event_id_crosscheck",
    "evidence_template_entry",
    "post_action_hardening_review",
    "closeout_without_browser_artifacts",
)
REQUIRED_ABORT_TERMS = (
    "automated login",
    "credential",
    "mfa",
    "captcha",
    "account creation",
    "payment",
    "upload",
    "submit",
    "certify",
    "schedule",
    "cancel",
    "private value",
    "cookie",
    "auth state",
    "screenshot",
    "trace",
    "har",
    "browser artifact",
    "live evidence",
)
REQUIRED_FORBIDDEN_ARTIFACTS = (
    "credentials",
    "credential_prompts",
    "cookies",
    "auth_state",
    "session_state",
    "screenshots",
    "traces",
    "har_files",
    "raw_dom",
    "raw_authenticated_text",
    "private_field_values",
    "payment_details",
    "downloads",
    "local_private_file_paths",
)
REQUIRED_ALLOWED_OBSERVATIONS = (
    "stable_surface_id",
    "page_heading",
    "accessible_landmark_summary",
    "redacted_label_category",
    "synthetic_record_status_label",
    "operator_decision_code",
    "redacted_timestamp",
)
REQUIRED_PROHIBITED_AUTOMATION = (
    "automated_login",
    "credential_prompt_capture",
    "mfa_automation",
    "captcha_automation",
    "account_creation_automation",
    "password_recovery_automation",
)
REQUIRED_CONSEQUENTIAL_CONTROLS = (
    "upload",
    "submit",
    "certify",
    "payment",
    "schedule_inspection",
    "cancel",
    "withdraw",
    "request_extension",
    "reactivate",
    "account_security_change",
)
REQUIRED_REDACTION_ATTESTATIONS = (
    "no_credentials",
    "no_credential_prompts",
    "no_cookies",
    "no_auth_state",
    "no_screenshots",
    "no_traces",
    "no_har_files",
    "no_private_field_values",
    "no_consequential_controls",
    "no_live_evidence_captured",
)
ALLOWED_JOURNAL_EVENT_TYPES = {
    "DevHub attended preflight",
    "manual handoff",
    "redacted read-only observation",
    "refused action",
    "post-action hardening review",
    "completion evidence",
}
JOURNAL_EVENT_ID_RE = re.compile(r"^JRN-[A-Z0-9][A-Z0-9-]*$")


@dataclass(frozen=True)
class OperatorChecklistValidationResult:
    packet_id: str
    ok: bool
    errors: tuple[str, ...]


def load_operator_checklist(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("operator checklist packet must be a JSON object")
    return data


def validate_operator_checklist(packet: Mapping[str, Any]) -> OperatorChecklistValidationResult:
    errors: list[str] = []
    packet_id = _text(packet.get("packet_id"))

    _require(errors, packet_id == REQUIRED_PACKET_ID, "packet_id must identify the read-only pilot operator checklist")
    _require(errors, packet.get("packet_type") == "devhub_read_only_pilot_operator_checklist", "packet_type is invalid")
    _require(errors, packet.get("mode") == "fixture_first", "mode must be fixture_first")
    _require(errors, packet.get("manual_session_only") is True, "manual_session_only must be true")
    _require(errors, packet.get("read_only_only") is True, "read_only_only must be true")
    _require(errors, packet.get("launches_playwright") is False, "launches_playwright must be false")
    _require(errors, packet.get("live_session_authorized") is False, "live_session_authorized must be false in committed fixtures")
    _require(errors, packet.get("stores_private_session_state") is False, "stores_private_session_state must be false")
    _require(errors, packet.get("stores_browser_artifacts") is False, "stores_browser_artifacts must be false")

    source_packets = _mapping(packet.get("source_packets"))
    for key, expected in REQUIRED_SOURCE_PACKETS.items():
        _require(errors, source_packets.get(key) == expected, f"source_packets.{key} must be {expected}")

    steps = _sequence(packet.get("checklist_steps"))
    step_ids = tuple(_text(_mapping(step).get("step_id")) for step in steps)
    missing_steps = [step_id for step_id in REQUIRED_STEP_IDS if step_id not in step_ids]
    if missing_steps:
        errors.append("checklist_steps missing required steps: " + ", ".join(missing_steps))
    for index, step in enumerate(steps):
        _validate_step(errors, index, _mapping(step))

    redaction_policy = _mapping(packet.get("redaction_policy"))
    _require(errors, redaction_policy.get("enabled") is True, "redaction_policy.enabled must be true")
    _require(errors, redaction_policy.get("raw_values_allowed") is False, "redaction_policy.raw_values_allowed must be false")
    _require(errors, redaction_policy.get("browser_artifacts_allowed") is False, "redaction_policy.browser_artifacts_allowed must be false")
    _require_all_present(errors, _string_tuple(redaction_policy.get("forbidden_artifacts")), REQUIRED_FORBIDDEN_ARTIFACTS, "redaction_policy.forbidden_artifacts")
    _require_all_present(errors, _string_tuple(redaction_policy.get("allowed_observation_fields")), REQUIRED_ALLOWED_OBSERVATIONS, "redaction_policy.allowed_observation_fields")

    _validate_automation_policy(errors, _mapping(packet.get("automation_policy")))
    _validate_consequential_controls(errors, _sequence(packet.get("consequential_controls")))
    _validate_redaction_attestations(errors, _mapping(packet.get("redaction_attestations")))
    _validate_evidence_claims(errors, _mapping(packet.get("evidence_claims")))

    journal_event_ids = _validate_journal_events(errors, _sequence(packet.get("journal_events")))
    _validate_abort_conditions(errors, _sequence(packet.get("abort_conditions")), journal_event_ids)

    hardening = _mapping(packet.get("post_action_hardening"))
    _require(errors, hardening.get("required") is True, "post_action_hardening.required must be true")
    _require(errors, hardening.get("official_state_changed") is False, "post_action_hardening.official_state_changed must be false")
    _require(errors, hardening.get("browser_artifacts_created") is False, "post_action_hardening.browser_artifacts_created must be false")
    _require(errors, hardening.get("live_evidence_captured") is False, "post_action_hardening.live_evidence_captured must be false")
    _require(errors, hardening.get("next_actions_limited_to") == ["read_only", "local_preview"], "post_action_hardening.next_actions_limited_to must be read_only/local_preview")

    return OperatorChecklistValidationResult(packet_id=packet_id, ok=not errors, errors=tuple(errors))


def assert_valid_operator_checklist(packet: Mapping[str, Any]) -> None:
    result = validate_operator_checklist(packet)
    if not result.ok:
        raise AssertionError("; ".join(result.errors))


def _validate_step(errors: list[str], index: int, step: Mapping[str, Any]) -> None:
    prefix = f"checklist_steps[{index}]"
    _require(errors, bool(_text(step.get("step_id"))), f"{prefix}.step_id is required")
    _require(errors, bool(_text(step.get("manual_action"))), f"{prefix}.manual_action is required")
    _require(errors, step.get("requires_operator_attendance") is True, f"{prefix}.requires_operator_attendance must be true")
    _require(errors, step.get("automated") is False, f"{prefix}.automated must be false")
    _require(errors, step.get("playwright_allowed") is False, f"{prefix}.playwright_allowed must be false")
    _require(errors, step.get("stores_browser_artifacts") is False, f"{prefix}.stores_browser_artifacts must be false")
    _require(errors, step.get("stores_private_values") is False, f"{prefix}.stores_private_values must be false")
    _require(errors, step.get("captures_live_evidence") is False, f"{prefix}.captures_live_evidence must be false")
    _require(errors, step.get("allows_consequential_control") is False, f"{prefix}.allows_consequential_control must be false")


def _validate_automation_policy(errors: list[str], policy: Mapping[str, Any]) -> None:
    _require(errors, policy.get("automated_login_allowed") is False, "automation_policy.automated_login_allowed must be false")
    _require(errors, policy.get("credential_prompt_capture_allowed") is False, "automation_policy.credential_prompt_capture_allowed must be false")
    _require(errors, policy.get("mfa_automation_allowed") is False, "automation_policy.mfa_automation_allowed must be false")
    _require(errors, policy.get("captcha_automation_allowed") is False, "automation_policy.captcha_automation_allowed must be false")
    _require(errors, policy.get("account_creation_automation_allowed") is False, "automation_policy.account_creation_automation_allowed must be false")
    _require(errors, policy.get("password_recovery_automation_allowed") is False, "automation_policy.password_recovery_automation_allowed must be false")
    _require_all_present(errors, _string_tuple(policy.get("prohibited_automation")), REQUIRED_PROHIBITED_AUTOMATION, "automation_policy.prohibited_automation")


def _validate_consequential_controls(errors: list[str], controls: tuple[Any, ...]) -> None:
    if not controls:
        errors.append("consequential_controls must be non-empty")
        return
    by_id: dict[str, Mapping[str, Any]] = {}
    for index, control in enumerate(controls):
        control_map = _mapping(control)
        control_id = _text(control_map.get("control_id"))
        if control_id:
            by_id[control_id] = control_map
        path = f"consequential_controls[{index}]"
        _require(errors, bool(control_id), f"{path}.control_id is required")
        _require(errors, control_map.get("allowed_in_read_only_pilot") is False, f"{path}.allowed_in_read_only_pilot must be false")
        _require(errors, bool(_text(control_map.get("operator_action"))), f"{path}.operator_action is required")
    missing = [control_id for control_id in REQUIRED_CONSEQUENTIAL_CONTROLS if control_id not in by_id]
    if missing:
        errors.append("consequential_controls missing: " + ", ".join(missing))


def _validate_redaction_attestations(errors: list[str], attestations: Mapping[str, Any]) -> None:
    if not attestations:
        errors.append("redaction_attestations must be present")
        return
    for attestation in REQUIRED_REDACTION_ATTESTATIONS:
        _require(errors, attestations.get(attestation) is True, f"redaction_attestations.{attestation} must be true")


def _validate_evidence_claims(errors: list[str], claims: Mapping[str, Any]) -> None:
    _require(errors, claims.get("fixture_only") is True, "evidence_claims.fixture_only must be true")
    _require(errors, claims.get("live_evidence_captured") is False, "evidence_claims.live_evidence_captured must be false")
    _require(errors, claims.get("claims_live_evidence_was_captured") is False, "evidence_claims.claims_live_evidence_was_captured must be false")
    _require(errors, claims.get("screenshots_captured") is False, "evidence_claims.screenshots_captured must be false")
    _require(errors, claims.get("traces_captured") is False, "evidence_claims.traces_captured must be false")
    _require(errors, claims.get("har_captured") is False, "evidence_claims.har_captured must be false")
    _require(errors, claims.get("cookies_captured") is False, "evidence_claims.cookies_captured must be false")
    _require(errors, claims.get("auth_state_captured") is False, "evidence_claims.auth_state_captured must be false")


def _validate_journal_events(errors: list[str], events: tuple[Any, ...]) -> set[str]:
    ids: set[str] = set()
    if not events:
        errors.append("journal_events must be non-empty")
        return ids
    for index, event in enumerate(events):
        event_map = _mapping(event)
        path = f"journal_events[{index}]"
        event_id = _text(event_map.get("event_id"))
        if not JOURNAL_EVENT_ID_RE.match(event_id):
            errors.append(f"{path}.event_id must match JRN-* uppercase format")
        elif event_id in ids:
            errors.append(f"{path}.event_id must be unique")
        else:
            ids.add(event_id)
        event_type = _text(event_map.get("event_type"))
        _require(errors, event_type in ALLOWED_JOURNAL_EVENT_TYPES, f"{path}.event_type is not allowed")
        _require(errors, event_map.get("commit_safe") is True, f"{path}.commit_safe must be true")
        _require(errors, event_map.get("stores_private_values") is False, f"{path}.stores_private_values must be false")
        _require(errors, event_map.get("stores_browser_artifacts") is False, f"{path}.stores_browser_artifacts must be false")
        _require(errors, event_map.get("captures_live_evidence") is False, f"{path}.captures_live_evidence must be false")
    return ids


def _validate_abort_conditions(errors: list[str], conditions: tuple[Any, ...], journal_event_ids: set[str]) -> None:
    if not conditions:
        errors.append("abort_conditions must be non-empty")
        return
    condition_text = "\n".join(_text(_mapping(condition).get("trigger")) for condition in conditions).casefold()
    missing_terms = [term for term in REQUIRED_ABORT_TERMS if term.casefold() not in condition_text]
    if missing_terms:
        errors.append("abort_conditions missing required terms: " + ", ".join(missing_terms))
    for index, condition in enumerate(conditions):
        condition_map = _mapping(condition)
        path = f"abort_conditions[{index}]"
        _require(errors, bool(_text(condition_map.get("condition_id"))), f"{path}.condition_id is required")
        _require(errors, bool(_text(condition_map.get("operator_action"))), f"{path}.operator_action is required")
        event_id = _text(condition_map.get("journal_event_id"))
        _require(errors, event_id in journal_event_ids, f"{path}.journal_event_id must link to a known journal event")


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _string_tuple(value: Any) -> tuple[str, ...]:
    return tuple(item for item in _sequence(value) if isinstance(item, str))


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return ""


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _require_all_present(errors: list[str], values: tuple[str, ...], required: tuple[str, ...], label: str) -> None:
    present = {value.casefold() for value in values}
    missing = [value for value in required if value.casefold() not in present]
    if missing:
        errors.append(f"{label} missing: " + ", ".join(missing))
