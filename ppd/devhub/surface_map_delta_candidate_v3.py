"""Fixture-first inactive DevHub surface-map delta candidate v3."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from ppd.devhub.observation_redaction_acceptance_v3 import assert_acceptance_packet_v3

DELTA_CANDIDATE_VERSION = "devhub_surface_map_delta_candidate_v3"

OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/devhub/surface_map_delta_candidate_v3.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_devhub_surface_map_delta_candidate_v3.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

ATTESTATIONS = {
    "no_live_devhub_opened": True,
    "no_login_attempted": True,
    "no_auth_or_session_artifacts": True,
    "no_screenshots_traces_or_har": True,
    "no_private_values": True,
    "no_active_surface_map_mutation": True,
    "no_form_fills_uploads_submissions_payments_scheduling_or_official_actions": True,
}

REQUIRED_SECTIONS = (
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

SECTION_REQUIRED_FIELDS = {
    "read_only_surface_delta_rows": (
        "prior_placeholder_id",
        "row_kind",
        "page_heading",
        "url_pattern",
        "candidate_label",
        "action_text",
        "selector_confidence",
        "validation_message",
        "requires_attendance",
        "requires_exact_confirmation",
    ),
    "accessible_landmark_delta_rows": ("landmarks", "accessible_name_policy"),
    "action_classification_delta_rows": ("action_text", "classification", "automation_allowed", "official_action_allowed"),
    "validation_message_delta_rows": ("message", "raw_message_captured"),
    "upload_control_evidence_delta_rows": ("upload_control_present", "evidence_policy", "file_interaction_allowed"),
    "state_transition_delta_rows": ("from_state", "to_state", "promotes_active_surface"),
    "redaction_policy_delta_rows": ("policy", "raw_values_stored"),
    "selector_confidence_delta_rows": ("confidence", "basis", "live_selector_verified"),
    "attendance_requirement_delta_rows": ("requires_attendance", "reason"),
    "exact_confirmation_requirement_delta_rows": ("requires_exact_confirmation", "confirmation_scope"),
    "reviewer_hold_delta_rows": ("hold_required", "reason"),
    "rollback_note_delta_rows": ("rollback_note", "active_surface_map_unchanged"),
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
    "active_source_mutation",
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
    "submitted",
    "payment completed",
    "scheduled inspection",
    "official action completed",
    "guaranteed approval",
    "permit guaranteed",
    "legal advice",
    "legally guaranteed",
)

VALID_ACTION_CLASSIFICATIONS = {"read_only_observation", "blocked_official_action"}


def build_surface_map_delta_candidate_v3(source: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(source, Mapping):
        raise ValueError("source fixture must be a mapping")

    acceptance = _mapping(source.get("redaction_acceptance_packet_v3"))
    assert_acceptance_packet_v3(dict(acceptance))

    placeholders = _list_of_mappings(source.get("prior_surface_map_fixture_placeholders"))
    if not placeholders:
        raise ValueError("prior_surface_map_fixture_placeholders must be non-empty")

    packet_id = _required_text(source, "packet_id")
    surface_id = _required_text(source, "surface_id")
    rows = [_surface_row(index + 1, surface_id, row) for index, row in enumerate(placeholders)]

    candidate = {
        "packet_version": DELTA_CANDIDATE_VERSION,
        "packet_id": packet_id,
        "mode": "fixture_first_inactive_devhub_surface_map_delta_candidate_v3",
        "source_inputs": {
            "redaction_acceptance_packet_id": _required_text(acceptance, "packet_id"),
            "redaction_acceptance_packet_version": _required_text(acceptance, "packet_version"),
            "prior_surface_map_fixture_placeholders": [
                {
                    "placeholder_id": _required_text(row, "placeholder_id"),
                    "row_kind": _required_text(row, "row_kind"),
                }
                for row in placeholders
            ],
            "prior_placeholder_count": len(placeholders),
            "synthetic_fixture_only": True,
        },
        "read_only_surface_delta_rows": rows,
        "accessible_landmark_delta_rows": [_landmark_row(row) for row in rows],
        "action_classification_delta_rows": [_action_row(row) for row in rows],
        "validation_message_delta_rows": [_validation_message_row(row) for row in rows],
        "upload_control_evidence_delta_rows": [_upload_control_row(row) for row in rows],
        "state_transition_delta_rows": [_state_transition_row(row) for row in rows],
        "redaction_policy_delta_rows": [_redaction_policy_row(row) for row in rows],
        "selector_confidence_delta_rows": [_selector_confidence_row(row) for row in rows],
        "attendance_requirement_delta_rows": [_attendance_row(row) for row in rows],
        "exact_confirmation_requirement_delta_rows": [_exact_confirmation_row(row) for row in rows],
        "reviewer_hold_delta_rows": [_reviewer_hold_row(row) for row in rows],
        "rollback_note_delta_rows": [_rollback_row(row) for row in rows],
        "attestations": dict(ATTESTATIONS),
        "validation_commands": deepcopy(OFFLINE_VALIDATION_COMMANDS),
    }
    assert_surface_map_delta_candidate_v3(candidate)
    return candidate


def validate_surface_map_delta_candidate_v3(candidate: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(candidate, Mapping):
        return ["candidate_not_object"]
    if candidate.get("packet_version") != DELTA_CANDIDATE_VERSION:
        errors.append("invalid_packet_version")
    if candidate.get("mode") != "fixture_first_inactive_devhub_surface_map_delta_candidate_v3":
        errors.append("invalid_mode")
    if candidate.get("attestations") != ATTESTATIONS:
        errors.append("missing_required_safety_attestations")
    if candidate.get("validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        errors.append("validation_commands_not_exact")

    _validate_source_inputs(candidate.get("source_inputs"), errors)
    _validate_delta_sections(candidate, errors)
    errors.extend(_unsafe_codes(candidate))
    return sorted(set(errors))


def assert_surface_map_delta_candidate_v3(candidate: Mapping[str, Any]) -> None:
    errors = validate_surface_map_delta_candidate_v3(candidate)
    if errors:
        raise ValueError("Invalid DevHub surface-map delta candidate v3: " + ", ".join(errors))


def _validate_source_inputs(value: Any, errors: list[str]) -> None:
    source_inputs = _mapping(value)
    if not source_inputs:
        errors.append("missing_source_inputs")
        return
    if not _text(source_inputs.get("redaction_acceptance_packet_id")):
        errors.append("missing_redaction_acceptance_reference")
    if source_inputs.get("redaction_acceptance_packet_version") != "devhub_read_only_observation_redaction_acceptance_v3":
        errors.append("missing_redaction_acceptance_reference")
    placeholders = _list_of_mappings(source_inputs.get("prior_surface_map_fixture_placeholders"))
    if not placeholders:
        errors.append("missing_prior_surface_map_fixture_placeholders")
    if source_inputs.get("prior_placeholder_count") != len(placeholders) or len(placeholders) == 0:
        errors.append("missing_prior_surface_map_fixture_placeholders")
    if source_inputs.get("synthetic_fixture_only") is not True:
        errors.append("source_inputs_not_fixture_only")
    for placeholder in placeholders:
        if not _text(placeholder.get("placeholder_id")) or not _text(placeholder.get("row_kind")):
            errors.append("prior_surface_map_fixture_placeholder_missing_identity")


def _validate_delta_sections(candidate: Mapping[str, Any], errors: list[str]) -> None:
    surface_rows = _list_of_mappings(candidate.get("read_only_surface_delta_rows"))
    surface_row_ids = {_text(row.get("delta_row_id")) for row in surface_rows if _text(row.get("delta_row_id"))}
    if not surface_rows:
        errors.append("missing_inactive_devhub_surface_map_delta_rows")

    for section in REQUIRED_SECTIONS:
        rows = candidate.get(section)
        if not isinstance(rows, list) or not rows:
            errors.append(f"missing_{section}")
            if section == "read_only_surface_delta_rows":
                errors.append("missing_inactive_devhub_surface_map_delta_rows")
            continue
        for row in rows:
            if not isinstance(row, Mapping):
                errors.append(f"{section}_row_not_object")
                continue
            _validate_common_row(section, row, surface_row_ids, errors)
            for field in SECTION_REQUIRED_FIELDS[section]:
                if not _present(row.get(field)):
                    errors.append(f"{section}_missing_{field}")
            _validate_section_specific_row(section, row, errors)


def _validate_common_row(section: str, row: Mapping[str, Any], surface_row_ids: set[str], errors: list[str]) -> None:
    if row.get("inactive") is not True or row.get("fixture_only") is not True:
        errors.append(f"{section}_row_not_inactive_fixture_only")
    if row.get("active_surface_map_mutation") is not False:
        errors.append(f"{section}_active_surface_map_mutation_not_false")
    if not _text(row.get("surface_id")) or not _text(row.get("delta_row_id")):
        errors.append(f"{section}_missing_identity")
    if section != "read_only_surface_delta_rows":
        surface_delta_row_id = _text(row.get("surface_delta_row_id"))
        if not surface_delta_row_id or surface_delta_row_id not in surface_row_ids:
            errors.append(f"{section}_missing_surface_delta_row_reference")


def _validate_section_specific_row(section: str, row: Mapping[str, Any], errors: list[str]) -> None:
    if section == "accessible_landmark_delta_rows" and not _non_empty_text_list(row.get("landmarks")):
        errors.append("accessible_landmark_delta_rows_missing_accessible_landmarks")
    if section == "action_classification_delta_rows":
        if row.get("classification") not in VALID_ACTION_CLASSIFICATIONS:
            errors.append("action_classification_delta_rows_missing_action_classification")
        if row.get("official_action_allowed") is not False:
            errors.append("action_classification_delta_rows_official_action_allowed_not_false")
    if section == "validation_message_delta_rows" and not _text(row.get("message")):
        errors.append("validation_message_delta_rows_missing_validation_message")
    if section == "upload_control_evidence_delta_rows":
        if row.get("evidence_policy") != "label_only_no_file_interaction":
            errors.append("upload_control_evidence_delta_rows_missing_upload_control_evidence")
        if row.get("file_interaction_allowed") is not False:
            errors.append("upload_control_evidence_delta_rows_file_interaction_allowed_not_false")
    if section == "state_transition_delta_rows":
        if not _text(row.get("from_state")) or not _text(row.get("to_state")):
            errors.append("state_transition_delta_rows_missing_state_transition")
        if row.get("promotes_active_surface") is not False:
            errors.append("state_transition_delta_rows_promotes_active_surface_not_false")
    if section == "redaction_policy_delta_rows":
        if not _text(row.get("policy")):
            errors.append("redaction_policy_delta_rows_missing_redaction_policy")
        if row.get("raw_values_stored") is not False:
            errors.append("redaction_policy_delta_rows_raw_values_stored_not_false")
    if section == "selector_confidence_delta_rows":
        if not _text(row.get("confidence")) or not _text(row.get("basis")):
            errors.append("selector_confidence_delta_rows_missing_selector_confidence")
        if row.get("live_selector_verified") is not False:
            errors.append("selector_confidence_delta_rows_live_selector_verified_not_false")
    if section == "attendance_requirement_delta_rows" and not isinstance(row.get("requires_attendance"), bool):
        errors.append("attendance_requirement_delta_rows_missing_attendance_requirement")
    if section == "exact_confirmation_requirement_delta_rows" and not isinstance(row.get("requires_exact_confirmation"), bool):
        errors.append("exact_confirmation_requirement_delta_rows_missing_exact_confirmation_requirement")
    if section == "reviewer_hold_delta_rows" and row.get("hold_required") is not True:
        errors.append("reviewer_hold_delta_rows_missing_reviewer_hold")
    if section == "rollback_note_delta_rows":
        if not _text(row.get("rollback_note")):
            errors.append("rollback_note_delta_rows_missing_rollback_note")
        if row.get("active_surface_map_unchanged") is not True:
            errors.append("rollback_note_delta_rows_active_surface_map_unchanged_not_true")


def _surface_row(order: int, surface_id: str, placeholder: Mapping[str, Any]) -> dict[str, Any]:
    placeholder_id = _required_text(placeholder, "placeholder_id")
    row_kind = _required_text(placeholder, "row_kind")
    action_text = _text(placeholder.get("action_text")) or _text(placeholder.get("label"))
    blocked = bool(placeholder.get("blocked_official_action"))
    return {
        "delta_row_id": f"delta-v3-{order:03d}-{_slug(placeholder_id)}",
        "surface_id": surface_id,
        "prior_placeholder_id": placeholder_id,
        "row_kind": row_kind,
        "page_heading": _text(placeholder.get("page_heading")) or "Synthetic read-only DevHub surface",
        "url_pattern": _text(placeholder.get("url_pattern")) or "/devhub/synthetic/{surface}",
        "candidate_label": _required_text(placeholder, "label"),
        "action_text": action_text,
        "blocked_official_action": blocked,
        "requires_attendance": bool(placeholder.get("requires_attendance")) or blocked,
        "requires_exact_confirmation": bool(placeholder.get("requires_exact_confirmation")) or blocked,
        "selector_confidence": _text(placeholder.get("selector_confidence")) or "placeholder_only",
        "validation_message": _text(placeholder.get("validation_message")) or "No live validation message captured; fixture placeholder only.",
        "fixture_only": True,
        "inactive": True,
        "active_surface_map_mutation": False,
    }


def _base(section: str, row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "delta_row_id": f"{section}-{row['delta_row_id']}",
        "surface_delta_row_id": row["delta_row_id"],
        "surface_id": row["surface_id"],
        "fixture_only": True,
        "inactive": True,
        "active_surface_map_mutation": False,
    }


def _landmark_row(row: Mapping[str, Any]) -> dict[str, Any]:
    data = _base("landmark", row)
    data.update({"landmarks": ["main", "navigation"], "accessible_name_policy": "synthetic_label_only"})
    return data


def _action_row(row: Mapping[str, Any]) -> dict[str, Any]:
    blocked = bool(row.get("blocked_official_action"))
    data = _base("action", row)
    data.update(
        {
            "action_text": row["action_text"],
            "classification": "blocked_official_action" if blocked else "read_only_observation",
            "automation_allowed": not blocked,
            "official_action_allowed": False,
        }
    )
    return data


def _validation_message_row(row: Mapping[str, Any]) -> dict[str, Any]:
    data = _base("validation", row)
    data.update({"message": row["validation_message"], "raw_message_captured": False})
    return data


def _upload_control_row(row: Mapping[str, Any]) -> dict[str, Any]:
    data = _base("upload-control", row)
    data.update(
        {
            "upload_control_present": row.get("row_kind") == "upload_control",
            "evidence_policy": "label_only_no_file_interaction",
            "file_interaction_allowed": False,
        }
    )
    return data


def _state_transition_row(row: Mapping[str, Any]) -> dict[str, Any]:
    data = _base("state-transition", row)
    data.update({"from_state": "prior_fixture_placeholder", "to_state": "inactive_delta_candidate", "promotes_active_surface": False})
    return data


def _redaction_policy_row(row: Mapping[str, Any]) -> dict[str, Any]:
    data = _base("redaction", row)
    data.update({"policy": "retain_labels_and_structure_only", "raw_values_stored": False})
    return data


def _selector_confidence_row(row: Mapping[str, Any]) -> dict[str, Any]:
    data = _base("selector", row)
    data.update({"confidence": row["selector_confidence"], "basis": "prior fixture placeholder only", "live_selector_verified": False})
    return data


def _attendance_row(row: Mapping[str, Any]) -> dict[str, Any]:
    data = _base("attendance", row)
    data.update({"requires_attendance": bool(row.get("requires_attendance")), "reason": "Required for any credentialed or consequential DevHub step."})
    return data


def _exact_confirmation_row(row: Mapping[str, Any]) -> dict[str, Any]:
    data = _base("exact-confirmation", row)
    data.update({"requires_exact_confirmation": bool(row.get("requires_exact_confirmation")), "confirmation_scope": "future_attended_action_only"})
    return data


def _reviewer_hold_row(row: Mapping[str, Any]) -> dict[str, Any]:
    data = _base("reviewer-hold", row)
    data.update({"hold_required": True, "reason": "Inactive fixture delta requires reviewer acceptance before any promotion."})
    return data


def _rollback_row(row: Mapping[str, Any]) -> dict[str, Any]:
    data = _base("rollback", row)
    data.update({"rollback_note": "Discard inactive delta rows and rebuild from accepted synthetic fixtures.", "active_surface_map_unchanged": True})
    return data


def _unsafe_codes(value: Any) -> list[str]:
    errors: list[str] = []
    for _path, child in _walk(value):
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


def _walk(value: Any, path: str = "$"):
    yield path, value
    if isinstance(value, Mapping):
        for key, child in value.items():
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")


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


def _non_empty_text_list(value: Any) -> bool:
    return isinstance(value, list) and any(_text(item) for item in value)


def _slug(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in cleaned.split("-") if part) or "row"
