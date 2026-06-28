"""Fixture-first inactive DevHub surface-map delta reviewer packet v3.

The builder accepts only committed inactive surface-map delta candidate v3
fixtures. It assembles reviewer-ready read-only rows and review evidence without
opening DevHub, creating browser artifacts, storing private values, or mutating
active surface maps.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

from ppd.devhub.surface_map_delta_candidate_v3 import validate_surface_map_delta_candidate_v3

REVIEWER_PACKET_VERSION = "devhub_surface_map_delta_reviewer_packet_v3"

OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/devhub/surface_map_delta_reviewer_packet_v3.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_devhub_surface_map_delta_reviewer_packet_v3.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

SAFETY_ATTESTATIONS = {
    "committed_inactive_candidate_fixtures_only": True,
    "no_live_devhub_opened": True,
    "no_login_attempted": True,
    "no_auth_or_session_artifacts": True,
    "no_screenshots_traces_or_har": True,
    "no_private_values": True,
    "no_active_surface_map_mutation": True,
    "no_form_fills_uploads_submissions_payments_scheduling_or_official_actions": True,
}

PROHIBITED_KEYS = {
    "auth_state",
    "authorization",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "har",
    "password",
    "private_value",
    "private_values",
    "screenshot",
    "session",
    "session_state",
    "storage_state",
    "token",
    "trace",
}

ACTIVE_MUTATION_KEYS = {
    "active_surface_map_mutation",
    "active_devhub_mutation",
    "active_guardrail_mutation",
    "active_prompt_mutation",
    "active_release_state_mutation",
    "mutation_enabled",
    "writes_enabled",
}

PROHIBITED_TEXT = (
    "opened devhub",
    "live devhub interaction",
    "logged in",
    "auth state",
    "session state",
    "storage state",
    "screenshot",
    "trace.zip",
    "har file",
    "private value stored",
    "mutated active surface map",
    "active surface-map mutation",
    "active surface map mutation",
    "form filled",
    "filled the form",
    "uploaded file",
    "uploaded plans",
    "payment completed",
    "scheduled inspection",
    "official action completed",
    "guaranteed approval",
    "permit guaranteed",
    "legal advice",
    "legally guaranteed",
)


def build_surface_map_delta_reviewer_packet_v3(candidate_fixtures: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Build a reviewer packet from inactive candidate v3 fixture objects."""

    if not isinstance(candidate_fixtures, Sequence) or isinstance(candidate_fixtures, (str, bytes)):
        raise ValueError("candidate_fixtures must be a sequence of mappings")

    candidates = [_mapping(candidate) for candidate in candidate_fixtures]
    if not candidates or any(not candidate for candidate in candidates):
        raise ValueError("candidate_fixtures must contain candidate mapping fixtures")

    for candidate in candidates:
        errors = validate_surface_map_delta_candidate_v3(candidate)
        if errors:
            raise ValueError("Invalid inactive surface-map delta candidate fixture: " + ", ".join(errors))

    references = [_candidate_reference(candidate) for candidate in candidates]
    evidence_references = _evidence_references(candidates)
    evidence_by_surface = _evidence_ids_by_surface(evidence_references)
    reviewer_rows = _reviewer_surface_rows(candidates, evidence_by_surface)

    packet = {
        "packet_version": REVIEWER_PACKET_VERSION,
        "mode": "fixture_first_inactive_devhub_surface_map_delta_reviewer_packet_v3",
        "delta_candidate_references": references,
        "reviewer_ready_surface_rows": reviewer_rows,
        "evidence_references": evidence_references,
        "safety_attestations": dict(SAFETY_ATTESTATIONS),
        "selector_confidence_notes": _selector_confidence_notes(candidates),
        "unresolved_reviewer_holds": _unresolved_reviewer_holds(candidates),
        "rollback_notes": _rollback_notes(candidates),
        "validation_commands": deepcopy(OFFLINE_VALIDATION_COMMANDS),
    }
    assert_surface_map_delta_reviewer_packet_v3(packet)
    return packet


def validate_surface_map_delta_reviewer_packet_v3(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(packet, Mapping):
        return ["packet_not_object"]
    if packet.get("packet_version") != REVIEWER_PACKET_VERSION:
        errors.append("invalid_packet_version")
    if packet.get("mode") != "fixture_first_inactive_devhub_surface_map_delta_reviewer_packet_v3":
        errors.append("invalid_mode")
    if packet.get("safety_attestations") != SAFETY_ATTESTATIONS:
        errors.append("missing_required_safety_attestations")
    if packet.get("validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        errors.append("validation_commands_not_exact")

    if not _list_of_mappings(packet.get("delta_candidate_references")):
        errors.append("missing_delta_candidate_references")
    _validate_reviewer_rows(packet.get("reviewer_ready_surface_rows"), errors)
    _validate_evidence_references(packet.get("evidence_references"), errors)
    _validate_selector_notes(packet.get("selector_confidence_notes"), errors)
    _validate_holds(packet.get("unresolved_reviewer_holds"), errors)
    _validate_rollback_notes(packet.get("rollback_notes"), errors)
    errors.extend(_unsafe_codes(packet))
    return sorted(set(errors))


def assert_surface_map_delta_reviewer_packet_v3(packet: Mapping[str, Any]) -> None:
    errors = validate_surface_map_delta_reviewer_packet_v3(packet)
    if errors:
        raise ValueError("Invalid DevHub surface-map delta reviewer packet v3: " + ", ".join(errors))


def _candidate_reference(candidate: Mapping[str, Any]) -> dict[str, Any]:
    surface_rows = _list_of_mappings(candidate.get("read_only_surface_delta_rows"))
    return {
        "candidate_packet_id": _required_text(candidate, "packet_id"),
        "candidate_packet_version": _required_text(candidate, "packet_version"),
        "candidate_mode": _required_text(candidate, "mode"),
        "fixture_only": True,
        "inactive": True,
        "read_only_surface_delta_row_count": len(surface_rows),
    }


def _reviewer_surface_rows(candidates: Sequence[Mapping[str, Any]], evidence_by_surface: Mapping[str, list[str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        actions = _index_by_surface_delta_row_id(candidate.get("action_classification_delta_rows"))
        selectors = _index_by_surface_delta_row_id(candidate.get("selector_confidence_delta_rows"))
        holds = _index_by_surface_delta_row_id(candidate.get("reviewer_hold_delta_rows"))
        packet_id = _required_text(candidate, "packet_id")
        for surface in _list_of_mappings(candidate.get("read_only_surface_delta_rows")):
            delta_row_id = _required_text(surface, "delta_row_id")
            action = actions.get(delta_row_id, {})
            selector = selectors.get(delta_row_id, {})
            hold = holds.get(delta_row_id, {})
            rows.append(
                {
                    "reviewer_row_id": f"reviewer-v3-{packet_id}-{delta_row_id}",
                    "candidate_packet_id": packet_id,
                    "surface_delta_row_id": delta_row_id,
                    "surface_id": _required_text(surface, "surface_id"),
                    "candidate_label": _required_text(surface, "candidate_label"),
                    "page_heading": _required_text(surface, "page_heading"),
                    "url_pattern": _required_text(surface, "url_pattern"),
                    "action_text": _required_text(surface, "action_text"),
                    "action_classification": _text(action.get("classification")) or "read_only_observation",
                    "automation_allowed": action.get("automation_allowed") is True,
                    "official_action_allowed": False,
                    "read_only": True,
                    "fixture_only": True,
                    "inactive": True,
                    "surface_map_update_allowed": False,
                    "selector_confidence": _text(selector.get("confidence")) or _required_text(surface, "selector_confidence"),
                    "selector_confidence_basis": _text(selector.get("basis")) or "candidate fixture evidence only",
                    "evidence_reference_ids": evidence_by_surface.get(delta_row_id, []),
                    "unresolved_hold_required": hold.get("hold_required") is True,
                }
            )
    return rows


def _evidence_references(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    sections = (
        "read_only_surface_delta_rows",
        "accessible_landmark_delta_rows",
        "action_classification_delta_rows",
        "validation_message_delta_rows",
        "upload_control_evidence_delta_rows",
        "state_transition_delta_rows",
        "redaction_policy_delta_rows",
        "selector_confidence_delta_rows",
        "attendance_requirement_delta_rows",
        "exact_confirmation_requirement_delta_rows",
        "reviewer_hold_delta_rows",
        "rollback_note_delta_rows",
    )
    references: list[dict[str, Any]] = []
    for candidate in candidates:
        packet_id = _required_text(candidate, "packet_id")
        for section in sections:
            for row in _list_of_mappings(candidate.get(section)):
                surface_delta_row_id = _text(row.get("surface_delta_row_id")) or _required_text(row, "delta_row_id")
                row_id = _required_text(row, "delta_row_id")
                references.append(
                    {
                        "evidence_reference_id": f"{packet_id}:{section}:{row_id}",
                        "candidate_packet_id": packet_id,
                        "section": section,
                        "candidate_row_id": row_id,
                        "surface_delta_row_id": surface_delta_row_id,
                        "fixture_only": True,
                        "inactive": True,
                        "raw_private_values_stored": False,
                    }
                )
    return references


def _selector_confidence_notes(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for candidate in candidates:
        packet_id = _required_text(candidate, "packet_id")
        for row in _list_of_mappings(candidate.get("selector_confidence_delta_rows")):
            notes.append(
                {
                    "note_id": f"selector-note-{packet_id}-{_required_text(row, 'surface_delta_row_id')}",
                    "candidate_packet_id": packet_id,
                    "surface_delta_row_id": _required_text(row, "surface_delta_row_id"),
                    "confidence": _required_text(row, "confidence"),
                    "basis": _required_text(row, "basis"),
                    "live_selector_verified": False,
                    "review_required_before_live_use": True,
                }
            )
    return notes


def _unresolved_reviewer_holds(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    holds: list[dict[str, Any]] = []
    for candidate in candidates:
        packet_id = _required_text(candidate, "packet_id")
        for row in _list_of_mappings(candidate.get("reviewer_hold_delta_rows")):
            holds.append(
                {
                    "hold_id": f"hold-{packet_id}-{_required_text(row, 'surface_delta_row_id')}",
                    "candidate_packet_id": packet_id,
                    "surface_delta_row_id": _required_text(row, "surface_delta_row_id"),
                    "reason": _required_text(row, "reason"),
                    "unresolved": True,
                    "release_requires_human_review": True,
                }
            )
    return holds


def _rollback_notes(candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for candidate in candidates:
        packet_id = _required_text(candidate, "packet_id")
        for row in _list_of_mappings(candidate.get("rollback_note_delta_rows")):
            notes.append(
                {
                    "rollback_note_id": f"rollback-{packet_id}-{_required_text(row, 'surface_delta_row_id')}",
                    "candidate_packet_id": packet_id,
                    "surface_delta_row_id": _required_text(row, "surface_delta_row_id"),
                    "rollback_note": _required_text(row, "rollback_note"),
                    "active_surface_map_unchanged": True,
                }
            )
    return notes


def _validate_reviewer_rows(value: Any, errors: list[str]) -> None:
    rows = _list_of_mappings(value)
    if not rows:
        errors.append("missing_reviewer_ready_surface_rows")
        return
    for row in rows:
        for field in ("reviewer_row_id", "candidate_packet_id", "surface_delta_row_id", "surface_id", "candidate_label", "evidence_reference_ids"):
            if not _present(row.get(field)):
                errors.append(f"reviewer_ready_surface_rows_missing_{field}")
        if row.get("read_only") is not True or row.get("fixture_only") is not True or row.get("inactive") is not True:
            errors.append("reviewer_ready_surface_rows_not_read_only_inactive_fixture")
        if row.get("official_action_allowed") is not False or row.get("surface_map_update_allowed") is not False:
            errors.append("reviewer_ready_surface_rows_allow_prohibited_action_or_mutation")


def _validate_evidence_references(value: Any, errors: list[str]) -> None:
    rows = _list_of_mappings(value)
    if not rows:
        errors.append("missing_evidence_references")
        return
    for row in rows:
        for field in ("evidence_reference_id", "candidate_packet_id", "section", "candidate_row_id", "surface_delta_row_id"):
            if not _present(row.get(field)):
                errors.append(f"evidence_references_missing_{field}")
        if row.get("raw_private_values_stored") is not False:
            errors.append("evidence_references_store_private_values")


def _validate_selector_notes(value: Any, errors: list[str]) -> None:
    rows = _list_of_mappings(value)
    if not rows:
        errors.append("missing_selector_confidence_notes")
        return
    for row in rows:
        if not _present(row.get("confidence")) or not _present(row.get("basis")):
            errors.append("selector_confidence_notes_missing_confidence_or_basis")
        if row.get("live_selector_verified") is not False:
            errors.append("selector_confidence_notes_live_selector_verified_not_false")


def _validate_holds(value: Any, errors: list[str]) -> None:
    rows = _list_of_mappings(value)
    if not rows:
        errors.append("missing_unresolved_reviewer_holds")
        return
    for row in rows:
        if not _present(row.get("reason")) or row.get("unresolved") is not True:
            errors.append("unresolved_reviewer_holds_missing_reason_or_unresolved_flag")


def _validate_rollback_notes(value: Any, errors: list[str]) -> None:
    rows = _list_of_mappings(value)
    if not rows:
        errors.append("missing_rollback_notes")
        return
    for row in rows:
        if not _present(row.get("rollback_note")):
            errors.append("rollback_notes_missing_note")
        if row.get("active_surface_map_unchanged") is not True:
            errors.append("rollback_notes_active_surface_map_unchanged_not_true")


def _unsafe_codes(value: Any) -> list[str]:
    errors: list[str] = []
    for child in _walk(value):
        if isinstance(child, Mapping):
            for key, nested in child.items():
                normalized = str(key).lower().replace("-", "_")
                if normalized in PROHIBITED_KEYS and _present(nested):
                    errors.append("private_auth_or_browser_artifact_key")
                if normalized in ACTIVE_MUTATION_KEYS and _active(nested):
                    errors.append("active_mutation_flag")
        elif isinstance(child, str):
            lowered = " ".join(child.lower().split())
            if any(term in lowered for term in PROHIBITED_TEXT):
                errors.append("prohibited_live_private_or_official_action_claim")
    return errors


def _evidence_ids_by_surface(references: Sequence[Mapping[str, Any]]) -> dict[str, list[str]]:
    by_surface: dict[str, list[str]] = {}
    for reference in references:
        surface_delta_row_id = _required_text(reference, "surface_delta_row_id")
        by_surface.setdefault(surface_delta_row_id, []).append(_required_text(reference, "evidence_reference_id"))
    return by_surface


def _index_by_surface_delta_row_id(value: Any) -> dict[str, Mapping[str, Any]]:
    return {_required_text(row, "surface_delta_row_id"): row for row in _list_of_mappings(value)}


def _walk(value: Any):
    yield value
    if isinstance(value, Mapping):
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list_of_mappings(value: Any) -> list[Mapping[str, Any]]:
    return [item for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    value = _text(mapping.get(key))
    if not value:
        raise ValueError(f"{key} must be present")
    return value


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _active(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "enabled", "active", "1"}
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return value is not None
