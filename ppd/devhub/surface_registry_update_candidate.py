from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from ppd.devhub.observed_surface_drift_review import assert_valid_observed_surface_drift_review


REQUIRED_PACKET_TYPE = "ppd.devhub_surface_registry_update_candidate.v1"
REQUIRED_MODE = "fixture_first_devhub_surface_registry_update_candidate"
REQUIRED_SCOPE_FLAGS = (
    "consumes_observed_surface_drift_review",
    "consumes_read_only_pilot_readiness_reconciliation",
    "records_only_redacted_route_patterns",
    "records_only_redacted_headings",
    "records_only_redacted_labels",
    "records_read_only_status_categories",
    "records_selector_confidence_deltas",
    "records_manual_handoff_prompts",
    "records_disabled_consequential_controls",
    "no_live_browser_launch",
    "no_browser_artifact_storage",
)
REQUIRED_REDACTION_ATTESTATIONS = (
    "no_devhub_launch",
    "no_playwright_launch",
    "no_browser_artifacts",
    "no_screenshots",
    "no_traces",
    "no_har_data",
    "no_cookies",
    "no_auth_state",
    "no_credentials",
    "no_private_values",
    "no_raw_authenticated_text",
    "no_consequential_controls_enabled",
    "no_official_actions_completed",
)
FORBIDDEN_BROWSER_ARTIFACT_FIELDS = (
    "screenshot",
    "screenshots",
    "screenshot_path",
    "trace",
    "traces",
    "trace_path",
    "har",
    "har_file",
    "har_path",
    "cookies",
    "cookie_jar",
    "auth_state",
    "storage_state",
    "browser_state",
    "session_state",
)
FORBIDDEN_PRIVATE_FIELDS = (
    "credential_prompt",
    "credential_prompts",
    "credentials",
    "password",
    "private_value",
    "private_values",
    "raw_authenticated_text",
    "authenticated_text",
    "payment_details",
)
FORBIDDEN_AUTOMATION_CLAIM_FIELDS = (
    "automated_login",
    "automates_login",
    "login_automated",
    "automated_mfa",
    "automates_mfa",
    "mfa_automated",
    "automated_captcha",
    "automates_captcha",
    "captcha_automated",
    "automated_account_creation",
    "automates_account_creation",
    "account_creation_automated",
)
FORBIDDEN_OFFICIAL_ACTION_FIELDS = (
    "official_action_completed",
    "official_actions_completed",
    "completed_official_actions",
    "completed_action",
    "completed_actions",
)
FORBIDDEN_ENABLED_CONTROL_FIELDS = (
    "enabled_consequential_controls",
    "enabled_upload_controls",
    "enabled_submission_controls",
    "enabled_payment_controls",
    "enabled_scheduling_controls",
    "enabled_cancellation_controls",
    "enabled_certification_controls",
)
CONSEQUENTIAL_CONTROL_TERMS = (
    "upload",
    "submit",
    "submission",
    "payment",
    "pay-fee",
    "schedule",
    "scheduling",
    "schedule-inspection",
    "cancel",
    "cancellation",
    "certify",
    "certification",
)


def load_json_packet(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("packet must be a JSON object")
    return data


def build_surface_registry_update_candidate_packet(
    observed_surface_drift_review: Mapping[str, Any],
    read_only_pilot_readiness_reconciliation: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a metadata-only DevHub surface registry update candidate."""

    assert_valid_observed_surface_drift_review(observed_surface_drift_review)
    _assert_reconciliation_packet_shape(read_only_pilot_readiness_reconciliation)

    readiness_by_surface = {
        _text(surface.get("surface_id")): surface
        for surface in _sequence(read_only_pilot_readiness_reconciliation.get("redacted_observed_surfaces"))
        if isinstance(surface, Mapping)
    }

    candidates = []
    for surface in _sequence(observed_surface_drift_review.get("observed_surfaces")):
        if not isinstance(surface, Mapping):
            continue
        surface_id = _text(surface.get("surface_id"))
        readiness = readiness_by_surface.get(surface_id, {})
        candidates.append(_candidate_from_surface(surface, readiness))

    return {
        "packet_id": "devhub-surface-registry-update-candidate-synthetic-v1",
        "packet_type": REQUIRED_PACKET_TYPE,
        "mode": REQUIRED_MODE,
        "fixture_first": True,
        "launches_devhub": False,
        "launches_playwright": False,
        "stores_browser_artifacts": False,
        "source_packets": {
            "observed_surface_drift_review": {
                "packet_id": _text(observed_surface_drift_review.get("packet_id")),
                "consumed": True,
            },
            "read_only_pilot_readiness_reconciliation": {
                "packet_id": _text(read_only_pilot_readiness_reconciliation.get("packet_id")),
                "consumed": True,
            },
        },
        "candidate_scope": {flag: True for flag in REQUIRED_SCOPE_FLAGS},
        "registry_update_candidates": candidates,
        "blocked_registry_changes": [
            {
                "change_id": "block-selector-upgrades-without-live-evidence",
                "reason": "Selector confidence may not be upgraded from this fixture packet; attended evidence is required before promotion.",
                "blocked": True,
            },
            {
                "change_id": "block-consequential-control-enablement",
                "reason": "Upload, submission, payment, scheduling, cancellation, and certification controls remain disabled in every candidate.",
                "blocked": True,
            },
        ],
        "redaction_attestations": {field: True for field in REQUIRED_REDACTION_ATTESTATIONS},
    }


def assert_valid_surface_registry_update_candidate_packet(packet: Mapping[str, Any]) -> None:
    errors = validate_surface_registry_update_candidate_packet(packet)
    if errors:
        raise AssertionError("; ".join(errors))


def validate_surface_registry_update_candidate_packet(packet: Mapping[str, Any]) -> tuple[str, ...]:
    errors: list[str] = []
    _require(errors, packet.get("packet_type") == REQUIRED_PACKET_TYPE, f"packet_type must be {REQUIRED_PACKET_TYPE}")
    _require(errors, packet.get("mode") == REQUIRED_MODE, f"mode must be {REQUIRED_MODE}")
    _require(errors, packet.get("fixture_first") is True, "fixture_first must be true")
    _require(errors, packet.get("launches_devhub") is False, "launches_devhub must be false")
    _require(errors, packet.get("launches_playwright") is False, "launches_playwright must be false")
    _require(errors, packet.get("stores_browser_artifacts") is False, "stores_browser_artifacts must be false")
    _validate_forbidden_packet_content(errors, packet)

    source_packets = _mapping(packet.get("source_packets"))
    for key in ("observed_surface_drift_review", "read_only_pilot_readiness_reconciliation"):
        source = _mapping(source_packets.get(key))
        _require(errors, bool(_text(source.get("packet_id"))), f"source_packets.{key}.packet_id is required")
        _require(errors, source.get("consumed") is True, f"source_packets.{key}.consumed must be true")

    scope = _mapping(packet.get("candidate_scope"))
    for flag in REQUIRED_SCOPE_FLAGS:
        _require(errors, scope.get(flag) is True, f"candidate_scope.{flag} must be true")

    candidates = _sequence(packet.get("registry_update_candidates"))
    _require(errors, bool(candidates), "registry_update_candidates must not be empty")
    for index, candidate in enumerate(candidates):
        _validate_candidate(errors, _mapping(candidate), f"registry_update_candidates[{index}]")

    attestations = _mapping(packet.get("redaction_attestations"))
    for field in REQUIRED_REDACTION_ATTESTATIONS:
        _require(errors, attestations.get(field) is True, f"redaction_attestations.{field} must be true")

    return _dedupe(errors)


def _candidate_from_surface(surface: Mapping[str, Any], readiness: Mapping[str, Any]) -> dict[str, Any]:
    confidence_notes = [_text(item) for item in _sequence(surface.get("selector_confidence_notes"))]
    observed_status = _text(readiness.get("status_category")) or _text(surface.get("read_only_status_category"))
    return {
        "surface_id": _text(surface.get("surface_id")),
        "candidate_registry_action": "update_redacted_surface_metadata_only",
        "route_pattern": _text(surface.get("route_pattern")),
        "redacted_heading": _text(surface.get("redacted_heading")),
        "redacted_labels": list(_sequence(surface.get("redacted_labels"))),
        "read_only_status_category": observed_status,
        "selector_confidence_delta": {
            "previous_confidence": "committed_registry_fixture",
            "observed_confidence": "redacted_fixture_review",
            "proposed_confidence": "attended_review_required",
            "delta_reason": "; ".join(confidence_notes) or "no selector confidence change requested",
            "upgrade_requested": False,
        },
        "manual_handoff_prompts": list(_sequence(surface.get("manual_handoff_prompts"))),
        "disabled_consequential_controls": list(_sequence(surface.get("disabled_consequential_controls"))),
    }


def _validate_candidate(errors: list[str], candidate: Mapping[str, Any], path: str) -> None:
    for field in ("surface_id", "candidate_registry_action", "route_pattern", "redacted_heading", "read_only_status_category"):
        _require(errors, bool(_text(candidate.get(field))), f"{path}.{field} is required")
    _require(errors, _text(candidate.get("route_pattern")).startswith("/"), f"{path}.route_pattern must be a redacted route pattern")
    _require(errors, _text(candidate.get("redacted_heading")).startswith("[REDACTED_HEADING:"), f"{path}.redacted_heading must be redacted")
    for label_index, label in enumerate(_sequence(candidate.get("redacted_labels"))):
        _require(errors, _text(label).startswith("[REDACTED_LABEL:"), f"{path}.redacted_labels[{label_index}] must be redacted")
    delta = _mapping(candidate.get("selector_confidence_delta"))
    _require(errors, delta.get("upgrade_requested") is False, f"{path}.selector_confidence_delta.upgrade_requested must be false")
    _require(errors, _text(delta.get("proposed_confidence")) == "attended_review_required", f"{path}.selector_confidence_delta.proposed_confidence must require attended review")
    for control_index, control in enumerate(_sequence(candidate.get("disabled_consequential_controls"))):
        control_text = _text(control)
        _require(errors, control_text.startswith("disabled:"), f"{path}.disabled_consequential_controls[{control_index}] must remain disabled")
        _require(errors, not control_text.startswith("enabled:"), f"{path}.disabled_consequential_controls[{control_index}] must not enable consequential controls")


def _validate_forbidden_packet_content(errors: list[str], value: Any, path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _text(key)
            key_lower = key_text.lower()
            nested_path = f"{path}.{key_text}"
            if key_lower in FORBIDDEN_BROWSER_ARTIFACT_FIELDS and _has_present_value(nested):
                errors.append(f"{nested_path} must not include browser artifacts")
            if key_lower in FORBIDDEN_PRIVATE_FIELDS and _has_present_value(nested):
                errors.append(f"{nested_path} must not include credentials, prompts, or private values")
            if key_lower in FORBIDDEN_AUTOMATION_CLAIM_FIELDS and _has_present_value(nested):
                errors.append(f"{nested_path} must not claim automated login, MFA, CAPTCHA, or account creation")
            if key_lower in FORBIDDEN_OFFICIAL_ACTION_FIELDS and _has_present_value(nested):
                errors.append(f"{nested_path} must not claim official action completion")
            if key_lower in FORBIDDEN_ENABLED_CONTROL_FIELDS and _has_present_value(nested):
                errors.append(f"{nested_path} must not enable consequential controls")
            if key_lower == "control_state" and _text(nested).lower() == "enabled":
                errors.append(f"{nested_path} must not be enabled")
            if key_lower == "control" and _is_enabled_consequential_control(nested):
                errors.append(f"{nested_path} must not enable consequential controls")
            _validate_forbidden_packet_content(errors, nested, nested_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, item in enumerate(value):
            _validate_forbidden_packet_content(errors, item, f"{path}[{index}]")
    elif _is_enabled_consequential_control(value):
        errors.append(f"{path} must not enable consequential controls")


def _is_enabled_consequential_control(value: Any) -> bool:
    text = _text(value).lower()
    if not text.startswith("enabled:"):
        return False
    return any(term in text for term in CONSEQUENTIAL_CONTROL_TERMS)


def _has_present_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return bool(value)
    return True


def _assert_reconciliation_packet_shape(packet: Mapping[str, Any]) -> None:
    errors: list[str] = []
    _require(errors, packet.get("fixture_first") is True, "read-only pilot reconciliation must be fixture_first")
    _require(errors, packet.get("metadata_only") is True, "read-only pilot reconciliation must be metadata_only")
    _require(errors, packet.get("launches_devhub") is False, "read-only pilot reconciliation must not launch DevHub")
    _require(errors, packet.get("stores_browser_artifacts") is False, "read-only pilot reconciliation must not store browser artifacts")
    _require(errors, bool(_sequence(packet.get("redacted_observed_surfaces"))), "read-only pilot reconciliation must include redacted observed surfaces")
    if errors:
        raise AssertionError("; ".join(errors))


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
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
    result: list[str] = []
    for error in errors:
        if error not in seen:
            seen.add(error)
            result.append(error)
    return tuple(result)
