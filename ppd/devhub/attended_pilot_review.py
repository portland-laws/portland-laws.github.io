"""Fixture-first review checks for attended DevHub pilot dry-runs."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


JOURNAL_EVENT_ID_RE = re.compile(r"^JRN-[A-Z0-9][A-Z0-9-]*$")

REQUIRED_OPERATOR_CHECKS = {
    "operator_identity_recorded",
    "manual_read_only_scope_confirmed",
    "redaction_attestations_reviewed",
    "abort_conditions_reviewed",
    "journal_event_ids_cross_checked",
    "post_action_hardening_notes_reviewed",
}

REQUIRED_TEMPLATE_FIELDS = {
    "operator_name_or_role",
    "attended_read_only_scope",
    "redaction_attestation_summary",
    "observation_scope_summary",
    "abort_condition_summary",
    "journal_event_ids",
    "post_action_hardening_notes",
}

REQUIRED_PROHIBITED_ACTIONS = {
    "account_creation",
    "captcha_automation",
    "certification",
    "credential_entry",
    "mfa_automation",
    "payment",
    "schedule_or_cancel_inspection",
    "submission",
    "upload",
}

ALLOWED_JOURNAL_EVENT_TYPES = {
    "DevHub attended preflight",
    "manual handoff",
    "refused action",
    "post-action hardening review",
    "completion evidence",
    "exact-confirmation checkpoint",
}


@dataclass(frozen=True)
class AttendedPilotReviewFinding:
    """A deterministic finding produced by the review packet validator."""

    severity: str
    code: str
    message: str
    path: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "path": self.path,
        }


@dataclass(frozen=True)
class AttendedPilotReviewResult:
    """Validation result for a fixture-first attended pilot packet."""

    ok: bool
    findings: Sequence[AttendedPilotReviewFinding]
    journal_event_ids: Sequence[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "findings": [finding.to_dict() for finding in self.findings],
            "journal_event_ids": list(self.journal_event_ids),
        }


def load_review_packet(path: Path) -> Dict[str, Any]:
    """Load a JSON review packet from a committed fixture path."""

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("attended pilot review packet must be a JSON object")
    return data


def review_attended_pilot_packet(packet: Mapping[str, Any]) -> AttendedPilotReviewResult:
    """Validate a manual read-only attended pilot evidence review packet."""

    findings: List[AttendedPilotReviewFinding] = []

    _expect_equal(findings, packet, "packet_type", "attended_pilot_dry_run_review")
    _expect_equal(findings, packet, "review_mode", "fixture_first")
    _expect_equal(findings, packet, "pilot_mode", "manual_read_only_attended")
    if packet.get("live_session_authorized") is not False:
        _add(findings, "live_session_block", "live_session_authorized must be false for this dry-run packet", "live_session_authorized")

    operator = _mapping(findings, packet, "operator")
    _validate_operator(findings, operator)

    evidence_template = _mapping(findings, packet, "evidence_template")
    _validate_evidence_template(findings, evidence_template)

    redaction_attestations = _sequence(findings, packet, "redaction_attestations")
    _validate_redaction_attestations(findings, redaction_attestations)

    observation_scope = _mapping(findings, packet, "observation_scope")
    _validate_observation_scope(findings, observation_scope)

    journal_events = _sequence(findings, packet, "journal_events")
    journal_event_ids = _validate_journal_events(findings, journal_events)

    abort_conditions = _sequence(findings, packet, "abort_conditions")
    _validate_abort_conditions(findings, abort_conditions, set(journal_event_ids))

    hardening_notes = _mapping(findings, packet, "post_action_hardening_notes")
    _validate_hardening_notes(findings, hardening_notes)

    return AttendedPilotReviewResult(ok=not findings, findings=findings, journal_event_ids=journal_event_ids)


def _validate_operator(findings: List[AttendedPilotReviewFinding], operator: Mapping[str, Any]) -> None:
    _require_text(findings, operator, "name_or_role", "operator.name_or_role")
    _require_text(findings, operator, "reviewed_at", "operator.reviewed_at")
    if operator.get("attendance_required") is not True:
        _add(findings, "operator_attendance", "operator.attendance_required must be true", "operator.attendance_required")

    checklist = operator.get("completed_checklist")
    if not isinstance(checklist, list):
        _add(findings, "operator_checklist", "operator.completed_checklist must be a list", "operator.completed_checklist")
        return
    completed = {item for item in checklist if isinstance(item, str)}
    missing = sorted(REQUIRED_OPERATOR_CHECKS - completed)
    if missing:
        _add(findings, "operator_checklist_missing", "operator checklist is missing: " + ", ".join(missing), "operator.completed_checklist")


def _validate_evidence_template(findings: List[AttendedPilotReviewFinding], template: Mapping[str, Any]) -> None:
    _require_text(findings, template, "template_id", "evidence_template.template_id")
    _require_text(findings, template, "version", "evidence_template.version")
    fields = template.get("fields")
    if not isinstance(fields, list) or not fields:
        _add(findings, "template_fields", "evidence_template.fields must be a non-empty list", "evidence_template.fields")
        return

    by_id: Dict[str, Mapping[str, Any]] = {}
    for index, field in enumerate(fields):
        path = "evidence_template.fields[{}]".format(index)
        if not isinstance(field, Mapping):
            _add(findings, "template_field_type", "template field must be an object", path)
            continue
        field_id = field.get("id")
        if not isinstance(field_id, str) or not field_id.strip():
            _add(findings, "template_field_id", "template field id is required", path + ".id")
            continue
        by_id[field_id] = field
        if field.get("required") is True and not _has_text(field.get("value")):
            _add(findings, "template_required_value", "required template field must include a value", path + ".value")

    missing = sorted(REQUIRED_TEMPLATE_FIELDS - set(by_id))
    if missing:
        _add(findings, "template_required_fields", "evidence template is missing required fields: " + ", ".join(missing), "evidence_template.fields")


def _validate_redaction_attestations(findings: List[AttendedPilotReviewFinding], attestations: Sequence[Any]) -> None:
    if not attestations:
        _add(findings, "redaction_attestations_empty", "at least one redaction attestation is required", "redaction_attestations")
        return
    for index, attestation in enumerate(attestations):
        path = "redaction_attestations[{}]".format(index)
        if not isinstance(attestation, Mapping):
            _add(findings, "redaction_attestation_type", "redaction attestation must be an object", path)
            continue
        _require_text(findings, attestation, "attestation_id", path + ".attestation_id")
        _require_text(findings, attestation, "scope", path + ".scope")
        _require_text(findings, attestation, "statement", path + ".statement")
        if attestation.get("completed") is not True:
            _add(findings, "redaction_attestation_incomplete", "redaction attestation must be completed", path + ".completed")
        if attestation.get("prohibited_values_absent") is not True:
            _add(findings, "redaction_private_values", "redaction attestation must confirm prohibited values are absent", path + ".prohibited_values_absent")


def _validate_observation_scope(findings: List[AttendedPilotReviewFinding], scope: Mapping[str, Any]) -> None:
    if scope.get("read_only") is not True:
        _add(findings, "scope_read_only", "observation scope must be read-only", "observation_scope.read_only")
    if scope.get("no_private_values_recorded") is not True:
        _add(findings, "scope_private_values", "observation scope must confirm no private values are recorded", "observation_scope.no_private_values_recorded")
    allowed = scope.get("allowed")
    if not isinstance(allowed, list) or not allowed:
        _add(findings, "scope_allowed", "observation_scope.allowed must be a non-empty list", "observation_scope.allowed")
    prohibited = scope.get("prohibited")
    if not isinstance(prohibited, list):
        _add(findings, "scope_prohibited", "observation_scope.prohibited must be a list", "observation_scope.prohibited")
        return
    prohibited_set = {item for item in prohibited if isinstance(item, str)}
    missing = sorted(REQUIRED_PROHIBITED_ACTIONS - prohibited_set)
    if missing:
        _add(findings, "scope_missing_prohibitions", "observation scope is missing prohibited actions: " + ", ".join(missing), "observation_scope.prohibited")


def _validate_journal_events(findings: List[AttendedPilotReviewFinding], events: Sequence[Any]) -> List[str]:
    event_ids: List[str] = []
    seen = set()
    if not events:
        _add(findings, "journal_events_empty", "at least one journal event is required", "journal_events")
        return event_ids

    for index, event in enumerate(events):
        path = "journal_events[{}]".format(index)
        if not isinstance(event, Mapping):
            _add(findings, "journal_event_type", "journal event must be an object", path)
            continue
        event_id = event.get("event_id")
        if not isinstance(event_id, str) or not JOURNAL_EVENT_ID_RE.match(event_id):
            _add(findings, "journal_event_id", "journal event id must match JRN-* uppercase format", path + ".event_id")
        else:
            if event_id in seen:
                _add(findings, "journal_event_duplicate", "journal event id must be unique", path + ".event_id")
            seen.add(event_id)
            event_ids.append(event_id)
        event_type = event.get("event_type")
        if event_type not in ALLOWED_JOURNAL_EVENT_TYPES:
            _add(findings, "journal_event_type_unknown", "journal event type is not permitted for commit-safe pilot review", path + ".event_type")
        if event.get("contains_private_data") is not False:
            _add(findings, "journal_private_data", "journal event must confirm contains_private_data is false", path + ".contains_private_data")
        if event.get("redaction_status") not in {"redacted", "metadata_only"}:
            _add(findings, "journal_redaction_status", "journal event redaction_status must be redacted or metadata_only", path + ".redaction_status")
    return event_ids


def _validate_abort_conditions(findings: List[AttendedPilotReviewFinding], abort_conditions: Sequence[Any], journal_event_ids: set) -> None:
    if not abort_conditions:
        _add(findings, "abort_conditions_empty", "at least one abort condition is required", "abort_conditions")
        return
    for index, condition in enumerate(abort_conditions):
        path = "abort_conditions[{}]".format(index)
        if not isinstance(condition, Mapping):
            _add(findings, "abort_condition_type", "abort condition must be an object", path)
            continue
        _require_text(findings, condition, "condition_id", path + ".condition_id")
        _require_text(findings, condition, "trigger", path + ".trigger")
        _require_text(findings, condition, "operator_action", path + ".operator_action")
        event_id = condition.get("journal_event_id")
        if not isinstance(event_id, str) or event_id not in journal_event_ids:
            _add(findings, "abort_condition_journal_link", "abort condition must link to a known journal event id", path + ".journal_event_id")


def _validate_hardening_notes(findings: List[AttendedPilotReviewFinding], notes: Mapping[str, Any]) -> None:
    if notes.get("reviewed") is not True:
        _add(findings, "hardening_reviewed", "post-action hardening notes must be reviewed", "post_action_hardening_notes.reviewed")
    _require_text(findings, notes, "notes", "post_action_hardening_notes.notes")
    controls = notes.get("follow_up_controls")
    if not isinstance(controls, list) or not any(_has_text(item) for item in controls):
        _add(findings, "hardening_controls", "post-action hardening notes must include follow-up controls", "post_action_hardening_notes.follow_up_controls")


def _expect_equal(findings: List[AttendedPilotReviewFinding], packet: Mapping[str, Any], key: str, expected: str) -> None:
    if packet.get(key) != expected:
        _add(findings, "packet_" + key, key + " must be " + expected, key)


def _mapping(findings: List[AttendedPilotReviewFinding], packet: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = packet.get(key)
    if isinstance(value, Mapping):
        return value
    _add(findings, "missing_" + key, key + " must be an object", key)
    return {}


def _sequence(findings: List[AttendedPilotReviewFinding], packet: Mapping[str, Any], key: str) -> Sequence[Any]:
    value = packet.get(key)
    if isinstance(value, list):
        return value
    _add(findings, "missing_" + key, key + " must be a list", key)
    return []


def _require_text(findings: List[AttendedPilotReviewFinding], packet: Mapping[str, Any], key: str, path: str) -> None:
    if not _has_text(packet.get(key)):
        _add(findings, "required_text", path + " must be a non-empty string", path)


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _add(findings: List[AttendedPilotReviewFinding], code: str, message: str, path: str) -> None:
    findings.append(AttendedPilotReviewFinding(severity="error", code=code, message=message, path=path))


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an attended pilot dry-run review packet fixture.")
    parser.add_argument("packet", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)

    packet = load_review_packet(args.packet)
    result = review_attended_pilot_packet(packet)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
