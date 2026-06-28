from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.devhub.read_only_pilot_result_intake import assert_valid_pilot_result_intake


REQUIRED_PACKET_TYPE = "ppd.devhub_observed_surface_drift_review.v1"
REQUIRED_MODE = "fixture_first_devhub_observed_surface_drift_review"
REQUIRED_SNAPSHOT_TYPE = "ppd.synthetic_devhub_surface_registry_snapshots.v1"

ALLOWED_TOP_LEVEL_KEYS = {
    "packet_id",
    "packet_type",
    "mode",
    "fixture_first",
    "launches_devhub",
    "source_packets",
    "review_scope",
    "observed_surfaces",
    "drift_findings",
    "redaction_attestations",
}
ALLOWED_SOURCE_PACKET_KEYS = {"pilot_evidence_packet_id", "surface_registry_snapshot_packet_id"}
ALLOWED_SCOPE_KEYS = {
    "records_only_redacted_headings",
    "records_only_redacted_labels",
    "records_route_patterns",
    "records_read_only_status_categories",
    "records_selector_confidence_notes",
    "records_manual_handoff_prompts",
    "records_disabled_consequential_controls",
    "no_live_browser_launch",
}
ALLOWED_SURFACE_KEYS = {
    "surface_id",
    "route_pattern",
    "redacted_heading",
    "redacted_labels",
    "read_only_status_category",
    "selector_confidence_notes",
    "manual_handoff_prompts",
    "disabled_consequential_controls",
}
ALLOWED_FINDING_KEYS = {
    "surface_id",
    "status",
    "reasons",
    "manual_handoff_prompts",
    "disabled_consequential_controls",
}
ALLOWED_SNAPSHOT_KEYS = {
    "packet_id",
    "snapshot_type",
    "fixture_first",
    "launches_devhub",
    "surfaces",
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
ALLOWED_REVIEW_STATUSES = {"no_drift", "attended_review", "blocked"}
REQUIRED_SCOPE_FLAGS = tuple(sorted(ALLOWED_SCOPE_KEYS))
REQUIRED_REDACTION_ATTESTATIONS = (
    "no_devhub_launch",
    "no_automated_login",
    "no_credentials",
    "no_cookies",
    "no_auth_state",
    "no_browser_artifacts",
    "no_screenshots",
    "no_traces",
    "no_har_data",
    "no_raw_dom",
    "no_raw_authenticated_text",
    "no_private_field_values",
    "no_consequential_controls_enabled",
    "no_official_actions_completed",
)
FORBIDDEN_KEYS = {
    "account_creation_claim",
    "auth_state",
    "auth_state_file",
    "auth_state_path",
    "automated_account_creation",
    "automated_captcha",
    "automated_login",
    "automated_mfa",
    "browser_context",
    "captcha_solution",
    "cookie",
    "cookie_jar",
    "cookies",
    "credential",
    "credential_prompt",
    "credential_prompts",
    "credentials",
    "enabled_certification_controls",
    "enabled_payment_controls",
    "enabled_scheduling_controls",
    "enabled_submission_controls",
    "enabled_upload_controls",
    "field_value",
    "har",
    "har_data",
    "har_file",
    "har_path",
    "mfa_code",
    "official_action_completed",
    "password",
    "private_field_value",
    "private_value",
    "private_values",
    "raw_authenticated_text",
    "raw_dom",
    "raw_field_value",
    "screenshot",
    "screenshot_file",
    "screenshot_path",
    "session_state",
    "storage_state",
    "storage_state_file",
    "storage_state_path",
    "trace",
    "trace_file",
    "trace_path",
    "value",
    "values",
}
FORBIDDEN_TEXT_PATTERNS = (
    re.compile(r"\b(cookie|auth state|storage state|screenshot|trace|har|raw dom)\b", re.IGNORECASE),
    re.compile(r"\b(password|credential prompt|credentials?|private field value|private value|field value)\b", re.IGNORECASE),
    re.compile(r"\b(automated|auto|bot|scripted)\s+(login|sign[- ]?in|mfa|captcha|account creation|account registration)\b", re.IGNORECASE),
    re.compile(r"\b(login|sign[- ]?in|mfa|captcha|account creation|account registration)\s+(was\s+)?(automated|completed by automation|scripted)\b", re.IGNORECASE),
    re.compile(r"\b(uploaded|submitted|certified|paid|scheduled|cancelled|canceled|official action completed|completed official action)\b", re.IGNORECASE),
    re.compile(r"\benabled[:\s-]*(upload|submission|submit|payment|pay|scheduling|schedule|cancellation|cancel|certification|certify)\b", re.IGNORECASE),
    re.compile(r"\b(upload|submission|submit|payment|pay|scheduling|schedule|cancellation|cancel|certification|certify)\s+(control|button|action)s?\s+(is\s+|are\s+)?enabled\b", re.IGNORECASE),
)
SELECTOR_UPGRADE_PATTERN = re.compile(r"\b(selector|locator).{0,40}\b(upgraded|promoted)\b|\b(upgraded|promoted).{0,40}\b(selector|locator)\b", re.IGNORECASE)
SELECTOR_EVIDENCE_PATTERN = re.compile(r"\bevidence[:=][A-Za-z0-9_.:-]+\b", re.IGNORECASE)
ROUTE_PATTERN_RE = re.compile(r"^/[-A-Za-z0-9_/{}/:?=&.*]+$")


@dataclass(frozen=True)
class ObservedSurfaceDriftReviewValidationResult:
    packet_id: str
    ok: bool
    errors: tuple[str, ...]


def load_json_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("packet must be a JSON object")
    return data


def build_observed_surface_drift_review_packet(
    pilot_evidence_packet: Mapping[str, Any],
    surface_registry_snapshots: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a commit-safe drift packet from fixtures only."""

    assert_valid_pilot_result_intake(pilot_evidence_packet)
    _assert_valid_surface_registry_snapshots(surface_registry_snapshots)

    surfaces = [_surface_for_packet(surface) for surface in surface_registry_snapshots["surfaces"]]
    findings = [_finding_for_surface(surface) for surface in surfaces]
    return {
        "packet_id": "devhub-observed-surface-drift-review-synthetic-v1",
        "packet_type": REQUIRED_PACKET_TYPE,
        "mode": REQUIRED_MODE,
        "fixture_first": True,
        "launches_devhub": False,
        "source_packets": {
            "pilot_evidence_packet_id": str(pilot_evidence_packet["packet_id"]),
            "surface_registry_snapshot_packet_id": str(surface_registry_snapshots["packet_id"]),
        },
        "review_scope": {flag: True for flag in REQUIRED_SCOPE_FLAGS},
        "observed_surfaces": surfaces,
        "drift_findings": findings,
        "redaction_attestations": {field: True for field in REQUIRED_REDACTION_ATTESTATIONS},
    }


def assert_valid_observed_surface_drift_review(packet: Mapping[str, Any]) -> None:
    result = validate_observed_surface_drift_review(packet)
    if not result.ok:
        raise AssertionError("; ".join(result.errors))


def validate_observed_surface_drift_review(packet: Mapping[str, Any]) -> ObservedSurfaceDriftReviewValidationResult:
    errors: list[str] = []
    packet_id = _text(packet.get("packet_id"))

    _validate_allowed_keys(errors, packet, ALLOWED_TOP_LEVEL_KEYS, "packet")
    _validate_no_forbidden_content(errors, packet, "packet")
    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    _require(errors, packet.get("mode") == REQUIRED_MODE, f"mode must be {REQUIRED_MODE}")
    _require(errors, packet.get("fixture_first") is True, "fixture_first must be true")
    _require(errors, packet.get("launches_devhub") is False, "launches_devhub must be false")

    _validate_source_packets(errors, _mapping(packet.get("source_packets")))
    _validate_review_scope(errors, _mapping(packet.get("review_scope")))
    _validate_surfaces(errors, packet.get("observed_surfaces"))
    _validate_findings(errors, packet.get("drift_findings"))
    _validate_redaction_attestations(errors, _mapping(packet.get("redaction_attestations")))
    return ObservedSurfaceDriftReviewValidationResult(packet_id=packet_id, ok=not errors, errors=tuple(_dedupe(errors)))


def _assert_valid_surface_registry_snapshots(packet: Mapping[str, Any]) -> None:
    errors: list[str] = []
    _validate_allowed_keys(errors, packet, ALLOWED_SNAPSHOT_KEYS, "surface_registry_snapshots")
    _validate_no_forbidden_content(errors, packet, "surface_registry_snapshots")
    _require(errors, packet.get("snapshot_type") == REQUIRED_SNAPSHOT_TYPE, f"snapshot_type must be {REQUIRED_SNAPSHOT_TYPE}")
    _require(errors, packet.get("fixture_first") is True, "surface registry snapshots must be fixture_first")
    _require(errors, packet.get("launches_devhub") is False, "surface registry snapshots must not launch DevHub")
    _validate_surfaces(errors, packet.get("surfaces"))
    if errors:
        raise AssertionError("; ".join(_dedupe(errors)))


def _surface_for_packet(surface: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_id": _text(surface.get("surface_id")),
        "route_pattern": _text(surface.get("route_pattern")),
        "redacted_heading": _text(surface.get("redacted_heading")),
        "redacted_labels": list(_sequence(surface.get("redacted_labels"))),
        "read_only_status_category": _text(surface.get("read_only_status_category")),
        "selector_confidence_notes": list(_sequence(surface.get("selector_confidence_notes"))),
        "manual_handoff_prompts": list(_sequence(surface.get("manual_handoff_prompts"))),
        "disabled_consequential_controls": list(_sequence(surface.get("disabled_consequential_controls"))),
    }


def _finding_for_surface(surface: Mapping[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    if _sequence(surface.get("selector_confidence_notes")):
        reasons.append("selector_confidence_review")
    if _sequence(surface.get("manual_handoff_prompts")):
        reasons.append("manual_handoff_prompt_present")
    if _sequence(surface.get("disabled_consequential_controls")):
        reasons.append("consequential_controls_disabled")
    status = "attended_review" if reasons else "no_drift"
    return {
        "surface_id": _text(surface.get("surface_id")),
        "status": status,
        "reasons": reasons,
        "manual_handoff_prompts": list(_sequence(surface.get("manual_handoff_prompts"))),
        "disabled_consequential_controls": list(_sequence(surface.get("disabled_consequential_controls"))),
    }


def _validate_source_packets(errors: list[str], source_packets: Mapping[str, Any]) -> None:
    _validate_allowed_keys(errors, source_packets, ALLOWED_SOURCE_PACKET_KEYS, "source_packets")
    for key in sorted(ALLOWED_SOURCE_PACKET_KEYS):
        _require(errors, bool(_text(source_packets.get(key))), f"source_packets.{key} must be present")


def _validate_review_scope(errors: list[str], scope: Mapping[str, Any]) -> None:
    _validate_allowed_keys(errors, scope, ALLOWED_SCOPE_KEYS, "review_scope")
    for flag in REQUIRED_SCOPE_FLAGS:
        _require(errors, scope.get(flag) is True, f"review_scope.{flag} must be true")


def _validate_surfaces(errors: list[str], surfaces: Any) -> None:
    if not isinstance(surfaces, Sequence) or isinstance(surfaces, (str, bytes)):
        errors.append("observed surfaces must be a list")
        return
    if not surfaces:
        errors.append("observed surfaces must not be empty")
        return
    for index, surface in enumerate(surfaces):
        path = f"observed_surfaces[{index}]"
        if not isinstance(surface, Mapping):
            errors.append(f"{path} must be an object")
            continue
        _validate_allowed_keys(errors, surface, ALLOWED_SURFACE_KEYS, path)
        _validate_no_forbidden_content(errors, surface, path)
        _require(errors, bool(_text(surface.get("surface_id"))), f"{path}.surface_id must be present")
        route_pattern = _text(surface.get("route_pattern"))
        _require(errors, bool(route_pattern), f"{path}.route_pattern must be present")
        if route_pattern and not ROUTE_PATTERN_RE.match(route_pattern):
            errors.append(f"{path}.route_pattern must be a route pattern, not a full URL or private value")
        _require_redacted_token(errors, surface.get("redacted_heading"), f"{path}.redacted_heading")
        _validate_redacted_list(errors, surface.get("redacted_labels"), f"{path}.redacted_labels")
        status = _text(surface.get("read_only_status_category"))
        _require(errors, status in ALLOWED_STATUS_CATEGORIES, f"{path}.read_only_status_category must be an allowed category")
        for key in ("selector_confidence_notes", "manual_handoff_prompts", "disabled_consequential_controls"):
            _validate_text_list(errors, surface.get(key), f"{path}.{key}")
        _validate_selector_notes(errors, surface.get("selector_confidence_notes"), f"{path}.selector_confidence_notes")
        _validate_disabled_controls(errors, surface.get("disabled_consequential_controls"), f"{path}.disabled_consequential_controls")


def _validate_findings(errors: list[str], findings: Any) -> None:
    if not isinstance(findings, Sequence) or isinstance(findings, (str, bytes)):
        errors.append("drift_findings must be a list")
        return
    for index, finding in enumerate(findings):
        path = f"drift_findings[{index}]"
        if not isinstance(finding, Mapping):
            errors.append(f"{path} must be an object")
            continue
        _validate_allowed_keys(errors, finding, ALLOWED_FINDING_KEYS, path)
        _validate_no_forbidden_content(errors, finding, path)
        _require(errors, bool(_text(finding.get("surface_id"))), f"{path}.surface_id must be present")
        _require(errors, _text(finding.get("status")) in ALLOWED_REVIEW_STATUSES, f"{path}.status must be allowed")
        for key in ("reasons", "manual_handoff_prompts", "disabled_consequential_controls"):
            _validate_text_list(errors, finding.get(key), f"{path}.{key}")
        _validate_disabled_controls(errors, finding.get("disabled_consequential_controls"), f"{path}.disabled_consequential_controls")


def _validate_redaction_attestations(errors: list[str], attestations: Mapping[str, Any]) -> None:
    _validate_allowed_keys(errors, attestations, set(REQUIRED_REDACTION_ATTESTATIONS), "redaction_attestations")
    for field in REQUIRED_REDACTION_ATTESTATIONS:
        _require(errors, attestations.get(field) is True, f"redaction_attestations.{field} must be true")


def _validate_allowed_keys(errors: list[str], packet: Mapping[str, Any], allowed: set[str], path: str) -> None:
    unknown = sorted(str(key) for key in set(packet) - allowed)
    if unknown:
        errors.append(f"{path} contains disallowed field(s): " + ", ".join(unknown))
    forbidden = sorted(str(key) for key in packet if str(key).casefold() in FORBIDDEN_KEYS)
    if forbidden:
        errors.append(f"{path} contains forbidden private/session/action field(s): " + ", ".join(forbidden))


def _validate_no_forbidden_content(errors: list[str], value: Any, path: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            child = f"{path}.{key_text}" if path else key_text
            if key_text.casefold() in FORBIDDEN_KEYS:
                errors.append(f"{child} is forbidden private/session/action content")
            _validate_no_forbidden_content(errors, item, child)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, item in enumerate(value):
            _validate_no_forbidden_content(errors, item, f"{path}[{index}]")
        return
    if isinstance(value, str):
        for pattern in FORBIDDEN_TEXT_PATTERNS:
            if pattern.search(value):
                errors.append(f"{path} contains prohibited live/session/action content")
                return


def _validate_selector_notes(errors: list[str], value: Any, path: str) -> None:
    for index, item in enumerate(_sequence(value)):
        text = _text(item)
        if SELECTOR_UPGRADE_PATTERN.search(text) and not SELECTOR_EVIDENCE_PATTERN.search(text):
            errors.append(f"{path}[{index}] claims a selector upgrade without evidence")


def _validate_disabled_controls(errors: list[str], value: Any, path: str) -> None:
    for index, control in enumerate(_sequence(value)):
        if not _text(control).startswith("disabled:"):
            errors.append(f"{path}[{index}] entries must start with disabled:")


def _validate_redacted_list(errors: list[str], value: Any, path: str) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        errors.append(f"{path} must be a list")
        return
    if not value:
        errors.append(f"{path} must not be empty")
    for index, item in enumerate(value):
        _require_redacted_token(errors, item, f"{path}[{index}]")


def _require_redacted_token(errors: list[str], value: Any, path: str) -> None:
    text = _text(value)
    if not text.startswith("[REDACTED_") or not text.endswith("]"):
        errors.append(f"{path} must be a redacted token")


def _validate_text_list(errors: list[str], value: Any, path: str) -> None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        errors.append(f"{path} must be a list")
        return
    for index, item in enumerate(value):
        text = _text(item)
        if not text:
            errors.append(f"{path}[{index}] must not be blank")
        _validate_no_forbidden_content(errors, text, f"{path}[{index}]")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return value
    return ()


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _dedupe(errors: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    deduped: list[str] = []
    for error in errors:
        if error not in seen:
            seen.add(error)
            deduped.append(error)
    return tuple(deduped)
