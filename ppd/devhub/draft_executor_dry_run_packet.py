"""Validation for reversible DevHub draft executor dry-run packets.

The checks in this module are intentionally deterministic and side-effect free.
They validate packet-shaped dictionaries before any Playwright page, browser
state, upload control, payment control, or official DevHub action can be used.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MIN_SELECTOR_CONFIDENCE = 0.85
ALLOWED_DRAFT_CLASSES = {
    "reversible_draft",
    "reversible_draft_edit",
    "reversible_draft_fill",
    "reversible_draft_fill_preview",
}
ALLOWED_DRAFT_DECISIONS = {"allow_reversible_draft", "allow_dry_run_preview"}

PRIVATE_VALUE_KEYS = {
    "account_number",
    "bank_account",
    "card_number",
    "credential",
    "credentials",
    "credit_card",
    "cvc",
    "cvv",
    "date_of_birth",
    "dob",
    "field_value",
    "password",
    "payment_details",
    "private_value",
    "raw_private_value",
    "routing_number",
    "secret",
    "security_answer",
    "social_security_number",
    "ssn",
    "token",
    "value",
}

BROWSER_ARTIFACT_KEYS = {
    "auth_state",
    "browser_context",
    "browser_state",
    "cookie",
    "cookie_jar",
    "cookies",
    "download_path",
    "har",
    "har_data",
    "har_path",
    "network_har",
    "private_file_path",
    "raw_crawl_output",
    "screenshot",
    "screenshot_path",
    "screenshots",
    "session_file",
    "session_state",
    "storage_state",
    "trace",
    "trace_path",
    "traces",
}

CONSEQUENTIAL_CONTROL_WORDS = {
    "certify",
    "continue",
    "pay",
    "payment",
    "save",
    "schedule",
    "submit",
    "upload",
}

CONSEQUENTIAL_ACTIONS = {
    "accept_certification",
    "attach_document",
    "book_inspection",
    "certify",
    "continue",
    "continue_application",
    "continue_draft",
    "enter_card",
    "enter_payment_details",
    "official_attach",
    "official_upload",
    "pay_fee",
    "purchase_trade_permit",
    "save",
    "save_and_continue",
    "save_draft",
    "schedule",
    "schedule_inspection",
    "sign_certification",
    "submit",
    "submit_application",
    "submit_payment",
    "submit_permit_request",
    "upload",
    "upload_correction",
}

OFFICIAL_STATE_CLAIM_KEYS = {
    "changes_official_state",
    "devhub_state_changed",
    "made_official_change",
    "official_devhub_state_changed",
    "official_record_changed",
    "official_state_change",
    "official_state_changed",
    "state_changed",
}

STATE_CHANGED_WORDS = {"changed", "submitted", "saved", "uploaded", "scheduled", "paid", "certified"}
GENERIC_SELECTORS = {"a", "button", "input", "select", "textarea", "[role=button]"}


@dataclass(frozen=True)
class DryRunPacketIssue:
    code: str
    message: str
    location: str


def load_dry_run_packet(path: str | Path) -> Mapping[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, Mapping):
        raise ValueError("dry-run packet fixture must be a JSON object")
    return data


def validate_dry_run_packet_file(path: str | Path) -> list[DryRunPacketIssue]:
    return validate_dry_run_packet(load_dry_run_packet(path))


def assert_dry_run_packet_file(path: str | Path) -> None:
    assert_dry_run_packet(load_dry_run_packet(path))


def validate_dry_run_packet(packet: Mapping[str, Any]) -> list[DryRunPacketIssue]:
    """Return all safety issues found in a reversible draft dry-run packet."""

    issues: list[DryRunPacketIssue] = []
    _validate_header(packet, issues)
    _validate_action_classification(packet, issues)
    _validate_attendance(packet, issues)
    facts = _fact_provenance(packet, issues)
    steps = _sequence(packet.get("steps") or packet.get("actions") or packet.get("ordered_steps"))
    if not steps:
        issues.append(DryRunPacketIssue("missing_steps", "Dry-run packets must contain ordered reversible steps.", "steps"))

    saw_preview_diff = False
    for index, step in enumerate(steps):
        location = f"steps[{index}]"
        if not isinstance(step, Mapping):
            issues.append(DryRunPacketIssue("invalid_step", "Each dry-run step must be an object.", location))
            continue
        step_issues, has_preview_diff = _step_issues(step, location, facts)
        issues.extend(step_issues)
        saw_preview_diff = saw_preview_diff or has_preview_diff

    if not saw_preview_diff:
        issues.append(DryRunPacketIssue("missing_preview_diff", "At least one redacted preview diff is required.", "steps"))
    _validate_rollback(packet, issues)
    _reject_forbidden_payload_fields(packet, issues)
    return _dedupe(issues)


def assert_dry_run_packet(packet: Mapping[str, Any]) -> None:
    issues = validate_dry_run_packet(packet)
    if issues:
        detail = "; ".join(f"{issue.code} at {issue.location}" for issue in issues)
        raise ValueError(f"Invalid reversible DevHub draft executor dry-run packet: {detail}")


def _validate_header(packet: Mapping[str, Any], issues: list[DryRunPacketIssue]) -> None:
    if _text(packet.get("run_mode")) != "reversible_draft_executor_dry_run":
        issues.append(DryRunPacketIssue("invalid_run_mode", "run_mode must be reversible_draft_executor_dry_run.", "run_mode"))
    for key in ("live_devhub_session", "browser_launched", "auth_state_saved", "browser_artifacts_saved"):
        if packet.get(key) is not False:
            issues.append(DryRunPacketIssue("side_effect_risk", f"{key} must be false for fixture-first dry runs.", key))


def _validate_action_classification(packet: Mapping[str, Any], issues: list[DryRunPacketIssue]) -> None:
    classification = packet.get("allowed_action_classification") or packet.get("action_classification")
    if not isinstance(classification, Mapping):
        issues.append(DryRunPacketIssue("missing_action_classification", "Dry-run packets must classify the allowed action.", "allowed_action_classification"))
        return
    action_class = _normalized_key(classification.get("action_class"))
    decision = _normalized_key(classification.get("decision"))
    if action_class not in ALLOWED_DRAFT_CLASSES:
        issues.append(DryRunPacketIssue("unsafe_action_classification", "Allowed action must be a reversible draft class.", "allowed_action_classification.action_class"))
    if decision not in ALLOWED_DRAFT_DECISIONS:
        issues.append(DryRunPacketIssue("unsafe_action_classification", "Allowed action decision must permit only reversible dry-run draft preview.", "allowed_action_classification.decision"))
    if classification.get("may_execute_in_dry_run") is not True:
        issues.append(DryRunPacketIssue("unsafe_action_classification", "Allowed action must be explicitly dry-run executable.", "allowed_action_classification.may_execute_in_dry_run"))
    if classification.get("changes_official_state") is not False:
        issues.append(DryRunPacketIssue("official_state_changed", "Allowed action must not change official DevHub state.", "allowed_action_classification.changes_official_state"))
    if classification.get("requires_exact_confirmation") is not False:
        issues.append(DryRunPacketIssue("unsafe_action_classification", "Reversible preview must not require exact confirmation; consequential controls must be blocked instead.", "allowed_action_classification.requires_exact_confirmation"))


def _validate_attendance(packet: Mapping[str, Any], issues: list[DryRunPacketIssue]) -> None:
    attendance = packet.get("attendance_requirement")
    if not isinstance(attendance, Mapping):
        issues.append(DryRunPacketIssue("missing_attendance", "Dry-run packets must include attendance requirements.", "attendance_requirement"))
        return
    if attendance.get("requires_user_attendance") is not True:
        issues.append(DryRunPacketIssue("missing_attendance", "DevHub draft dry-runs must require user attendance.", "attendance_requirement.requires_user_attendance"))
    if attendance.get("unattended_execution_allowed") is not False:
        issues.append(DryRunPacketIssue("missing_attendance", "Unattended execution must be disallowed.", "attendance_requirement.unattended_execution_allowed"))
    if not _text(attendance.get("attendance_reason")):
        issues.append(DryRunPacketIssue("missing_attendance", "Attendance reason is required.", "attendance_requirement.attendance_reason"))


def _fact_provenance(packet: Mapping[str, Any], issues: list[DryRunPacketIssue]) -> set[str]:
    facts = _sequence(packet.get("required_user_facts") or packet.get("facts"))
    fact_ids: set[str] = set()
    if not facts:
        issues.append(DryRunPacketIssue("missing_fact_provenance", "Dry-run packets must include source-backed user fact provenance.", "required_user_facts"))
        return fact_ids
    for index, fact in enumerate(facts):
        location = f"required_user_facts[{index}]"
        if not isinstance(fact, Mapping):
            issues.append(DryRunPacketIssue("missing_fact_provenance", "Each required user fact must be an object with provenance.", location))
            continue
        fact_id = _text(fact.get("fact_id") or fact.get("id") or fact.get("user_fact_id"))
        if fact_id:
            fact_ids.add(fact_id)
        evidence = _sequence(fact.get("source_evidence_ids"))
        provenance = fact.get("provenance")
        if not evidence and isinstance(provenance, Mapping):
            evidence = _sequence(provenance.get("source_evidence_ids"))
        if not fact_id or not evidence or any(not _text(item) for item in evidence):
            issues.append(DryRunPacketIssue("missing_fact_provenance", "Each required user fact must cite source_evidence_ids.", location))
        if fact.get("value_policy") != "value_ref_only":
            issues.append(DryRunPacketIssue("private_value", "Required facts must use value_ref_only policy.", f"{location}.value_policy"))
    return fact_ids


def _step_issues(step: Mapping[str, Any], location: str, facts: set[str]) -> tuple[list[DryRunPacketIssue], bool]:
    issues: list[DryRunPacketIssue] = []
    action = _normalized_key(step.get("action") or step.get("action_type") or step.get("kind"))
    if action in CONSEQUENTIAL_ACTIONS:
        issues.append(DryRunPacketIssue("consequential_control", "Save, continue, submit, certify, upload, payment, and schedule controls are not reversible dry-run actions.", f"{location}.action"))
    for key in ("label", "button_text", "aria_label", "control_text", "description", "selector"):
        text = _normalized_key(step.get(key))
        if any(word in text.split("_") or word in text for word in CONSEQUENTIAL_CONTROL_WORDS):
            issues.append(DryRunPacketIssue("consequential_control", "Consequential DevHub controls must be blocked before dry-run execution.", f"{location}.{key}"))
    selector_issue = _selector_issue(step)
    if selector_issue:
        issues.append(DryRunPacketIssue("low_confidence_selector", selector_issue, f"{location}.selector"))
    value_ref = _text(step.get("value_ref") or step.get("user_fact_id") or step.get("fact_id"))
    if action in {"fill_field", "set_checkbox", "set_radio", "select_option", "select_permit_type"}:
        if not value_ref or value_ref not in facts:
            issues.append(DryRunPacketIssue("missing_fact_provenance", "Draft-fill steps must reference a required user fact with provenance.", f"{location}.value_ref"))
    if not _is_redacted_marker(step.get("field_label_redacted")):
        issues.append(DryRunPacketIssue("unredacted_field_label", "Draft-fill steps must use redacted field labels.", f"{location}.field_label_redacted"))
    preview_diff = step.get("preview_diff")
    has_preview_diff = isinstance(preview_diff, Mapping)
    if has_preview_diff:
        issues.extend(_preview_diff_issues(preview_diff, f"{location}.preview_diff", value_ref))
    return issues, has_preview_diff


def _preview_diff_issues(diff: Mapping[str, Any], location: str, value_ref: str) -> list[DryRunPacketIssue]:
    issues: list[DryRunPacketIssue] = []
    if _required_diff_text(diff.get("diff_kind")) not in {"redacted_field_fill", "redacted_option_select", "redacted_checkbox_set"}:
        issues.append(DryRunPacketIssue("missing_preview_diff", "Preview diff must use a redacted reversible diff kind.", f"{location}.diff_kind"))
    before = diff.get("before")
    after = diff.get("after")
    if not _is_redacted_marker(before) or not _is_redacted_marker(after):
        issues.append(DryRunPacketIssue("unredacted_preview_diff", "Preview diffs must contain only redacted before/after markers.", location))
    expected_ref = _text(diff.get("value_ref"))
    if value_ref and expected_ref and expected_ref != value_ref:
        issues.append(DryRunPacketIssue("missing_fact_provenance", "Preview diff value_ref must match the step value_ref.", f"{location}.value_ref"))
    return issues


def _validate_rollback(packet: Mapping[str, Any], issues: list[DryRunPacketIssue]) -> None:
    rollback = packet.get("rollback_evidence")
    if not isinstance(rollback, Mapping):
        issues.append(DryRunPacketIssue("missing_rollback_evidence", "Dry-run packets must include rollback and no-side-effect evidence.", "rollback_evidence"))
        return
    if rollback.get("official_state_changed") is not False:
        issues.append(DryRunPacketIssue("official_state_changed", "Rollback evidence must state that no official DevHub state changed.", "rollback_evidence.official_state_changed"))
    if rollback.get("browser_artifacts_saved") is not False:
        issues.append(DryRunPacketIssue("browser_artifact", "Rollback evidence must state that no browser artifacts were saved.", "rollback_evidence.browser_artifacts_saved"))
    if rollback.get("side_effects") != "none":
        issues.append(DryRunPacketIssue("side_effect_risk", "Rollback evidence must record side_effects as none.", "rollback_evidence.side_effects"))
    evidence = _sequence(rollback.get("evidence"))
    if not evidence or any(not _text(item) for item in evidence):
        issues.append(DryRunPacketIssue("missing_rollback_evidence", "Rollback evidence must include non-empty evidence notes.", "rollback_evidence.evidence"))


def _selector_issue(step: Mapping[str, Any]) -> str:
    selector = step.get("selector")
    selectors = step.get("selectors")
    if isinstance(selectors, Sequence) and not isinstance(selectors, str):
        concrete = [_text(item) for item in selectors if _text(item)]
        if len(concrete) != 1:
            return "Each dry-run step must identify exactly one stable selector."
        selector = concrete[0]
    if not _text(selector):
        return "Each dry-run step must include one stable selector."
    if _normalized_key(selector) in GENERIC_SELECTORS:
        return "Generic selectors are too ambiguous for draft execution."
    confidence = step.get("selector_confidence")
    if isinstance(confidence, str) and _normalized_key(confidence) == "high":
        return ""
    try:
        if not isinstance(confidence, bool) and float(confidence) >= MIN_SELECTOR_CONFIDENCE:
            return ""
    except (TypeError, ValueError):
        pass
    return "Low-confidence or unverified selectors are not allowed."


def _reject_forbidden_payload_fields(packet: Mapping[str, Any], issues: list[DryRunPacketIssue]) -> None:
    for location, value in _walk(packet):
        key = _normalized_key(location.rsplit(".", 1)[-1])
        if key in PRIVATE_VALUE_KEYS and _present(value):
            issues.append(DryRunPacketIssue("private_value", "Dry-run packets must reference user fact IDs, not private values.", location))
        if key in BROWSER_ARTIFACT_KEYS and _present(value):
            issues.append(DryRunPacketIssue("browser_artifact", "Browser state, screenshots, traces, HAR data, and cookies are not commit-safe dry-run data.", location))
        if key in OFFICIAL_STATE_CLAIM_KEYS and value is True:
            issues.append(DryRunPacketIssue("official_state_changed", "A reversible dry-run packet must not claim official DevHub state changed.", location))
        if key in {"state_change_result", "result", "outcome"} and isinstance(value, str):
            if _normalized_key(value) in STATE_CHANGED_WORDS:
                issues.append(DryRunPacketIssue("official_state_changed", "Dry-run outcomes must not claim official DevHub state changed.", location))


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, list) or isinstance(value, tuple):
        return value
    return ()


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def _text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip()


def _required_diff_text(value: Any) -> str:
    return _normalized_key(value)


def _normalized_key(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _is_redacted_marker(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    stripped = value.strip()
    return stripped.startswith("[REDACTED_") and stripped.endswith("]")


def _walk(value: Any, location: str = "packet") -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            yield child_location, child
            yield from _walk(child, child_location)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_location = f"{location}[{index}]"
            yield child_location, child
            yield from _walk(child, child_location)


def _dedupe(issues: Sequence[DryRunPacketIssue]) -> list[DryRunPacketIssue]:
    seen: set[tuple[str, str]] = set()
    deduped: list[DryRunPacketIssue] = []
    for issue in issues:
        key = (issue.code, issue.location)
        if key not in seen:
            seen.add(key)
            deduped.append(issue)
    return deduped
