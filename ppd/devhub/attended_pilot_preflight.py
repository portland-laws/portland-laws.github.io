"""Fixture-first DevHub attended pilot preflight validation.

This module intentionally validates committed packet fixtures only. It does not
launch Playwright, read browser state, or create authenticated artifacts.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REQUIRED_PACKET_ID = "devhub-attended-pilot-synthetic-readonly-review-v1"
REQUIRED_JOURNAL_EVENTS = (
    "DevHub attended preflight",
    "manual handoff",
    "refused action",
    "post-action hardening review",
)
REQUIRED_OBSERVED_SURFACES = (
    "authenticated_landing",
    "account_summary",
    "readonly_record_list",
    "readonly_record_detail",
)
PROHIBITED_ACTION_TERMS = (
    "captcha",
    "mfa",
    "account creation",
    "payment",
    "submit",
    "certify",
    "upload",
    "schedule",
    "cancel",
    "password recovery",
)
PROHIBITED_ARTIFACT_TERMS = (
    "credential",
    "cookie",
    "auth state",
    "screenshot",
    "trace",
    "har",
    "raw private value",
    "payment detail",
    "local private file path",
)


@dataclass(frozen=True)
class PreflightValidationResult:
    """Validation result for a committed attended-pilot packet fixture."""

    packet_id: str
    ok: bool
    errors: tuple[str, ...]


def load_preflight_packet(path: str | Path) -> dict[str, Any]:
    """Load a JSON preflight packet from a committed fixture path."""

    packet_path = Path(path)
    with packet_path.open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise ValueError("preflight packet must be a JSON object")
    return packet


def validate_preflight_packet(packet: dict[str, Any]) -> PreflightValidationResult:
    """Return deterministic validation errors for an attended pilot packet."""

    errors: list[str] = []
    packet_id = _string(packet.get("packet_id"))

    _require(errors, packet_id == REQUIRED_PACKET_ID, "packet_id must identify the synthetic read-only attended pilot packet")
    _require(errors, packet.get("mode") == "fixture_first", "mode must be fixture_first")
    _require(errors, packet.get("live_automation_allowed") is False, "live automation must be disabled")
    _require(errors, packet.get("playwright_launch_allowed") is False, "Playwright launch must be disabled")
    _require(errors, packet.get("browser_artifacts_allowed") is False, "browser artifacts must be disabled")

    account_review = _mapping(packet.get("synthetic_account_review"))
    _require(errors, account_review.get("account_kind") == "synthetic", "account review must use a synthetic account")
    _require(errors, account_review.get("access_level") == "read_only", "account review must be read-only")
    _require(errors, account_review.get("review_count") == 1, "packet must cover exactly one synthetic account review")
    _require(errors, account_review.get("stores_private_values") is False, "packet must not store private values")

    handoff = _mapping(packet.get("manual_login_handoff"))
    _require(errors, handoff.get("required") is True, "manual login handoff must be required")
    _require(errors, handoff.get("operator_present") is True, "operator presence must be required")
    _require_contains(errors, _string_list(handoff.get("steps")), "user opens DevHub and completes PortlandOregon.gov login manually", "manual handoff must keep login fully manual")
    _require_contains(errors, _string_list(handoff.get("blocked_steps")), "agent does not enter credentials, solve MFA, or persist session state", "manual handoff must block credential, MFA, and session persistence handling")

    scope = _mapping(packet.get("allowed_observation_scope"))
    _require(errors, scope.get("read_only_only") is True, "observation scope must be read-only")
    allowed_items = _string_list(scope.get("allowed"))
    _require_contains(errors, allowed_items, "page headings and accessible landmarks", "scope must allow headings and landmarks")
    _require_contains(errors, allowed_items, "synthetic permit record metadata and status labels", "scope must allow synthetic record metadata and status labels")
    _require_all_terms(errors, _string_list(scope.get("prohibited")), PROHIBITED_ACTION_TERMS, "scope must prohibit consequential and auth-bound actions")

    redaction = _mapping(packet.get("redaction_checks"))
    _require(errors, redaction.get("before_journal_write") is True, "redaction must run before journal writes")
    _require_all_terms(errors, _string_list(redaction.get("must_exclude")), PROHIBITED_ARTIFACT_TERMS, "redaction must exclude private browser and account artifacts")
    _require_contains(errors, _string_list(redaction.get("allowed_commit_safe_fields")), "synthetic labels, stable surface ids, timestamps, and operator-visible decision codes", "redaction must identify commit-safe fields")

    surface_map = _mapping(packet.get("surface_map_expectations"))
    _require_all_terms(errors, _string_list(surface_map.get("expected_surfaces")), REQUIRED_OBSERVED_SURFACES, "surface map must include expected read-only surfaces")
    _require(errors, surface_map.get("requires_selector_capture") is False, "packet must not require selector capture")
    _require(errors, surface_map.get("requires_screenshot_capture") is False, "packet must not require screenshot capture")
    _require(errors, surface_map.get("requires_raw_dom_capture") is False, "packet must not require raw DOM capture")

    timeout = _mapping(packet.get("timeout_handling"))
    _require(errors, timeout.get("timeout_seconds") == 900, "timeout must be 900 seconds")
    _require(errors, timeout.get("on_timeout") == "stop_and_write_redacted_timeout_event", "timeout must stop and write a redacted timeout event")
    _require(errors, timeout.get("may_retry_without_operator") is False, "timeout retry must not proceed without operator")

    stop = _mapping(packet.get("manual_stop_conditions"))
    _require_all_terms(errors, _string_list(stop.get("conditions")), PROHIBITED_ACTION_TERMS, "manual stop conditions must cover prohibited consequential actions")
    _require_contains(errors, _string_list(stop.get("conditions")), "unexpected private account data appears outside the synthetic review", "manual stop must cover unexpected private account data")
    _require(errors, stop.get("on_stop") == "refuse_action_and_record_redacted_journal_event", "manual stop must refuse and journal a redacted event")

    journal = _mapping(packet.get("journal_event_templates"))
    for event_name in REQUIRED_JOURNAL_EVENTS:
        template = _mapping(journal.get(event_name))
        _require(errors, template.get("event_type") == event_name, f"journal template missing event_type {event_name}")
        _require(errors, template.get("commit_safe") is True, f"journal template {event_name} must be commit-safe")
        _require(errors, template.get("stores_browser_artifacts") is False, f"journal template {event_name} must not store browser artifacts")
        _require(errors, template.get("stores_private_values") is False, f"journal template {event_name} must not store private values")

    return PreflightValidationResult(packet_id=packet_id, ok=not errors, errors=tuple(errors))


def assert_valid_preflight_packet(packet: dict[str, Any]) -> None:
    """Raise AssertionError with stable messages if packet validation fails."""

    result = validate_preflight_packet(packet)
    if not result.ok:
        raise AssertionError("; ".join(result.errors))


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _string(value: Any) -> str:
    if isinstance(value, str):
        return value
    return ""


def _string_list(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str))


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _require_contains(errors: list[str], values: tuple[str, ...], expected: str, message: str) -> None:
    normalized_expected = expected.casefold()
    found = any(normalized_expected in value.casefold() for value in values)
    _require(errors, found, message)


def _require_all_terms(errors: list[str], values: tuple[str, ...], terms: tuple[str, ...], message: str) -> None:
    haystack = "\n".join(values).casefold()
    missing = [term for term in terms if term.casefold() not in haystack]
    if missing:
        errors.append(f"{message}: missing {', '.join(missing)}")
