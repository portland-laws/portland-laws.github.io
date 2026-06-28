"""Fixture-first DevHub read-only surface delta packet v1.

This module intentionally accepts only synthetic observation evidence rows and
produces review packets. It does not open DevHub, persist auth state, crawl,
submit forms, upload files, schedule inspections, or promote surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

PACKET_VERSION = "devhub_surface_delta_packet_v1"
OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/devhub_surface_delta_v1.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_devhub_surface_delta_v1.py"],
]
PRIVATE_FIELD_NAMES = {"applicant_name", "email", "phone", "address", "permit_number", "account_id"}
SUPPORTED_SOURCE_KINDS = {"synthetic_observation"}


@dataclass(frozen=True)
class ObservationRow:
    row_id: str
    source_kind: str
    surface_key: str
    observed_label: str
    selector: str
    selector_hits: int
    action_text: str
    requires_login: bool = False
    requires_attendance: bool = False
    exact_confirmation_text: str = ""
    contains_private_value: bool = False
    private_field_names: tuple[str, ...] = ()
    unsupported_reason: str = ""
    reviewer_hold_reason: str = ""

    @classmethod
    def from_mapping(cls, row: dict[str, Any]) -> "ObservationRow":
        return cls(
            row_id=str(row["row_id"]),
            source_kind=str(row.get("source_kind", "synthetic_observation")),
            surface_key=str(row["surface_key"]),
            observed_label=str(row.get("observed_label", "")),
            selector=str(row.get("selector", "")),
            selector_hits=int(row.get("selector_hits", 0)),
            action_text=str(row.get("action_text", "")),
            requires_login=bool(row.get("requires_login", False)),
            requires_attendance=bool(row.get("requires_attendance", False)),
            exact_confirmation_text=str(row.get("exact_confirmation_text", "")),
            contains_private_value=bool(row.get("contains_private_value", False)),
            private_field_names=tuple(str(name) for name in row.get("private_field_names", ())),
            unsupported_reason=str(row.get("unsupported_reason", "")),
            reviewer_hold_reason=str(row.get("reviewer_hold_reason", "")),
        )


def build_devhub_surface_delta_packet(rows: list[dict[str, Any]]) -> dict[str, Any]:
    observations = [ObservationRow.from_mapping(row) for row in rows]
    candidate_surface_changes = []
    selector_confidence_notes = []
    action_classification_checks = []
    redaction_policy_impacts = []
    attendance_requirements = []
    exact_confirmation_requirements = []
    unsupported_manual_handoff_paths = []
    reviewer_holds = []

    for row in observations:
        if row.source_kind not in SUPPORTED_SOURCE_KINDS:
            unsupported_manual_handoff_paths.append(_manual_handoff(row, "unsupported source_kind"))
            continue

        candidate_surface_changes.append(
            {
                "row_id": row.row_id,
                "surface_key": row.surface_key,
                "candidate_change": "add_or_update_read_only_surface_observation",
                "observed_label": row.observed_label,
                "promotion_allowed": False,
                "evidence_source": "synthetic_fixture_only",
            }
        )
        selector_confidence_notes.append(_selector_note(row))
        action_classification_checks.append(_action_check(row))

        if row.contains_private_value or set(row.private_field_names) & PRIVATE_FIELD_NAMES:
            redaction_policy_impacts.append(
                {
                    "row_id": row.row_id,
                    "surface_key": row.surface_key,
                    "impact": "redact_private_values_before_review",
                    "private_field_names": sorted(set(row.private_field_names) & PRIVATE_FIELD_NAMES),
                    "raw_values_stored": False,
                }
            )

        if row.requires_attendance:
            attendance_requirements.append(
                {
                    "row_id": row.row_id,
                    "surface_key": row.surface_key,
                    "requirement": "manual_attendance_required",
                    "automation_allowed": False,
                }
            )

        if row.exact_confirmation_text:
            exact_confirmation_requirements.append(
                {
                    "row_id": row.row_id,
                    "surface_key": row.surface_key,
                    "exact_confirmation_text": row.exact_confirmation_text,
                    "must_match_before_any_future_action": True,
                }
            )

        if row.unsupported_reason:
            unsupported_manual_handoff_paths.append(_manual_handoff(row, row.unsupported_reason))

        if row.reviewer_hold_reason:
            reviewer_holds.append(
                {
                    "row_id": row.row_id,
                    "surface_key": row.surface_key,
                    "hold_reason": row.reviewer_hold_reason,
                    "release_requires_human_review": True,
                }
            )

    return {
        "packet_version": PACKET_VERSION,
        "source_policy": "synthetic_fixture_read_only_no_live_devhub_access",
        "candidate_surface_changes": candidate_surface_changes,
        "selector_confidence_notes": selector_confidence_notes,
        "action_classification_checks": action_classification_checks,
        "redaction_policy_impacts": redaction_policy_impacts,
        "attendance_requirements": attendance_requirements,
        "exact_confirmation_requirements": exact_confirmation_requirements,
        "unsupported_manual_handoff_paths": unsupported_manual_handoff_paths,
        "reviewer_holds": reviewer_holds,
        "offline_validation_commands": OFFLINE_VALIDATION_COMMANDS,
    }


def _selector_note(row: ObservationRow) -> dict[str, Any]:
    if not row.selector:
        confidence = "none"
        note = "missing selector requires manual review"
    elif row.selector_hits == 1:
        confidence = "high"
        note = "selector matched exactly one synthetic fixture element"
    elif row.selector_hits > 1:
        confidence = "low"
        note = "selector is ambiguous in synthetic fixture evidence"
    else:
        confidence = "none"
        note = "selector did not match synthetic fixture evidence"
    return {
        "row_id": row.row_id,
        "surface_key": row.surface_key,
        "selector": row.selector,
        "selector_hits": row.selector_hits,
        "confidence": confidence,
        "note": note,
    }


def _action_check(row: ObservationRow) -> dict[str, Any]:
    lowered = row.action_text.lower()
    blocked_terms = ("submit", "upload", "pay", "schedule", "cancel", "certify", "create account")
    classification = "read_only_navigation_or_information"
    automation_allowed = True
    matched_blocked_terms = [term for term in blocked_terms if term in lowered]
    if row.requires_login or matched_blocked_terms:
        classification = "unsupported_action_requires_manual_handoff"
        automation_allowed = False
    return {
        "row_id": row.row_id,
        "surface_key": row.surface_key,
        "action_text": row.action_text,
        "classification": classification,
        "matched_blocked_terms": matched_blocked_terms,
        "automation_allowed": automation_allowed,
    }


def _manual_handoff(row: ObservationRow, reason: str) -> dict[str, Any]:
    return {
        "row_id": row.row_id,
        "surface_key": row.surface_key,
        "reason": reason,
        "manual_handoff_required": True,
        "automation_allowed": False,
    }
