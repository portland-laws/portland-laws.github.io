"""Fixture-first DevHub read-only observation redaction acceptance packet v3.

This module consumes only synthetic DevHub read-only observation intake schema v3
rows. It assembles an offline reviewer packet for redaction coverage, private
value omission evidence, route-pattern normalization, selector confidence,
manual handoff reminders, fixture promotion holds, reviewer routing, rollback
notes, and exact offline validation commands.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import re
from typing import Any

from ppd.devhub.read_only_observation_intake_schema_v3 import assert_valid_observation_intake_v3

PACKET_SCHEMA_VERSION = "devhub_observation_redaction_acceptance_packet_v3"
INTAKE_SCHEMA_VERSION = "devhub_read_only_observation_intake_schema_v3"

OFFLINE_VALIDATION_COMMANDS: list[list[str]] = [
    ["python3", "-m", "py_compile", "ppd/devhub/observation_redaction_acceptance_packet_v3.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_devhub_observation_redaction_acceptance_packet_v3.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_PRIVATE_CLASSES = {
    "account_identifier",
    "address",
    "applicant_name",
    "case_number",
    "contractor_license",
    "email",
    "financial",
    "full_name",
    "government_id",
    "phone",
    "private_page_value",
    "property_identifier",
    "tax_lot",
    "upload_filename",
}
_SAFE_REDACTIONS = {"label_only", "omit_private_value", "placeholder_only", "public_label"}
_PRIVATE_REDACTIONS = {"label_only", "omit_private_value", "placeholder_only"}
_PROHIBITED_INPUT_KEYS = {
    "actual_value",
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "downloaded_document",
    "filled_value",
    "har",
    "password",
    "private_page_value",
    "raw_value",
    "screenshot",
    "session_state",
    "storage_state",
    "submitted_value",
    "token",
    "trace",
    "uploaded_file",
    "value",
}
_PROHIBITED_TEXT_RE = re.compile(
    r"(bearer\s+[a-z0-9._-]+|password\s*=|token\s*=|authorization:|storage-state\.json|trace\.zip|\.har\b|screenshot\.(png|jpg|jpeg)|clicked submit|payment completed|inspection scheduled|application submitted)",
    re.IGNORECASE,
)
_ROUTE_TOKEN_RE = re.compile(r"\{[a-zA-Z0-9_]+\}|:[a-zA-Z0-9_]+|]+>")
_NUMERIC_SEGMENT_RE = re.compile(r"/\d+(?=/|$)")
_UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


class ObservationRedactionAcceptancePacketV3Error(ValueError):
    """Raised when a synthetic intake payload cannot produce packet v3."""


def build_acceptance_packet_v3(intake: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic offline acceptance packet from synthetic intake rows."""

    normalized = _normalize_intake(intake)
    rows = normalized["rows"]
    route_checks = [_route_check(row, normalized["surface_url_pattern"]) for row in rows]
    redaction_checks = [_redaction_check(row) for row in rows]
    selector_summaries = _selector_summaries(rows, normalized["selector_confidence_notes"])

    packet = {
        "schema_version": PACKET_SCHEMA_VERSION,
        "packet_id": f"redaction-acceptance-v3-{normalized['intake_id']}",
        "mode": "fixture_first_offline_acceptance",
        "source_intake": {
            "schema_version": INTAKE_SCHEMA_VERSION,
            "intake_id": normalized["intake_id"],
            "synthetic_fixture_only": True,
            "surface_title": normalized["surface_title"],
            "surface_url_pattern": normalized["surface_url_pattern"],
        },
        "devhub_access": "not_opened",
        "browser_artifacts": "not_created",
        "official_actions": "blocked",
        "redaction_coverage_checks": redaction_checks,
        "private_value_omission_evidence": _private_value_omission_evidence(redaction_checks),
        "route_pattern_normalization_checks": route_checks,
        "selector_evidence_confidence_summaries": selector_summaries,
        "unsupported_manual_handoff_reminders": _manual_handoff_reminders(normalized),
        "fixture_promotion_holds": _fixture_promotion_holds(normalized, redaction_checks, selector_summaries),
        "reviewer_routing": _reviewer_routing(redaction_checks, selector_summaries),
        "rollback_notes": _rollback_notes(normalized),
        "exact_offline_validation_commands": deepcopy(OFFLINE_VALIDATION_COMMANDS),
    }
    assert_acceptance_packet_v3(packet)
    return packet


def validate_acceptance_packet_v3(packet: Mapping[str, Any]) -> list[str]:
    """Return deterministic validation errors for a packet v3 object."""

    errors: list[str] = []
    if not isinstance(packet, Mapping):
        return ["packet_not_object"]
    if packet.get("schema_version") != PACKET_SCHEMA_VERSION:
        errors.append("unsupported_schema_version")
    if packet.get("mode") != "fixture_first_offline_acceptance":
        errors.append("mode_must_be_fixture_first_offline_acceptance")
    if packet.get("devhub_access") != "not_opened":
        errors.append("devhub_access_must_be_not_opened")
    if packet.get("browser_artifacts") != "not_created":
        errors.append("browser_artifacts_must_be_not_created")
    if packet.get("official_actions") != "blocked":
        errors.append("official_actions_must_be_blocked")

    required_lists = (
        "redaction_coverage_checks",
        "private_value_omission_evidence",
        "route_pattern_normalization_checks",
        "selector_evidence_confidence_summaries",
        "unsupported_manual_handoff_reminders",
        "fixture_promotion_holds",
        "reviewer_routing",
        "rollback_notes",
        "exact_offline_validation_commands",
    )
    for field in required_lists:
        if not _non_empty_sequence(packet.get(field)):
            errors.append(f"missing_{field}")

    if packet.get("exact_offline_validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        errors.append("offline_validation_commands_must_match_exact_packet_v3_commands")

    for index, check in enumerate(_mapping_sequence(packet.get("redaction_coverage_checks"))):
        if check.get("coverage_status") != "covered":
            errors.append(f"redaction_coverage_checks_{index}_not_covered")
        if check.get("stores_private_value") is not False:
            errors.append(f"redaction_coverage_checks_{index}_stores_private_value")

    for index, check in enumerate(_mapping_sequence(packet.get("route_pattern_normalization_checks"))):
        if check.get("normalization_status") != "normalized_route_pattern":
            errors.append(f"route_pattern_normalization_checks_{index}_not_normalized")

    if _contains_prohibited_text(packet):
        errors.append("prohibited_private_artifact_or_official_action_text")
    return sorted(set(errors))


def assert_acceptance_packet_v3(packet: Mapping[str, Any]) -> None:
    errors = validate_acceptance_packet_v3(packet)
    if errors:
        raise ObservationRedactionAcceptancePacketV3Error("invalid packet v3: " + ", ".join(errors))


def _normalize_intake(intake: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(intake, Mapping):
        raise ObservationRedactionAcceptancePacketV3Error("intake must be a mapping")
    _reject_prohibited_input(intake)
    assert_valid_observation_intake_v3(intake)

    if intake.get("schema_version") != INTAKE_SCHEMA_VERSION:
        raise ObservationRedactionAcceptancePacketV3Error("intake schema_version must be v3")
    if intake.get("synthetic_fixture_only") is not True:
        raise ObservationRedactionAcceptancePacketV3Error("intake must be marked synthetic_fixture_only")
    if intake.get("fixture_mode") != "synthetic_observation_intake_rows":
        raise ObservationRedactionAcceptancePacketV3Error("intake must use synthetic observation rows")

    surface = _required_mapping(intake, "surface")
    rows = [_normalize_row(row, index) for index, row in enumerate(_required_sequence(intake, "redacted_observation_rows"), start=1)]
    return {
        "intake_id": _text_or_default(intake.get("intake_id"), "synthetic-intake-v3"),
        "surface_title": _required_text(surface, "title"),
        "surface_url_pattern": _required_text(surface, "url_pattern"),
        "rows": rows,
        "selector_confidence_notes": list(_required_sequence(intake, "selector_confidence_notes")),
        "reviewer_holds": list(_required_sequence(intake, "reviewer_holds")),
        "state_transition_placeholders": list(_required_sequence(intake, "state_transition_placeholders")),
    }


def _normalize_row(row: Any, index: int) -> dict[str, Any]:
    if not isinstance(row, Mapping):
        raise ObservationRedactionAcceptancePacketV3Error(f"row {index} must be an object")
    field_class = _text_or_default(row.get("observed_field_class") or row.get("field_class"), "public_label")
    redaction = _text_or_default(row.get("redaction") or row.get("redaction_policy"), "label_only")
    if redaction not in _SAFE_REDACTIONS:
        raise ObservationRedactionAcceptancePacketV3Error(f"row {index} has unsupported redaction")
    return {
        "order": int(row.get("order", index)),
        "row_id": _text_or_default(row.get("row_id"), f"row-{index}"),
        "label": _required_text(row, "label"),
        "placeholder": _required_text(row, "placeholder"),
        "field_class": field_class,
        "redaction": redaction,
        "route_pattern": _text_or_default(row.get("route_pattern"), ""),
        "selector_ref": _text_or_default(row.get("selector_ref"), f"selector-{index}"),
        "selector_confidence": _confidence(row.get("selector_confidence")),
    }


def _redaction_check(row: Mapping[str, Any]) -> dict[str, Any]:
    private_class = row["field_class"] in _PRIVATE_CLASSES
    redaction = str(row["redaction"])
    covered = (private_class and redaction in _PRIVATE_REDACTIONS) or (not private_class and redaction in _SAFE_REDACTIONS)
    return {
        "order": row["order"],
        "row_id": row["row_id"],
        "label": row["label"],
        "field_class": row["field_class"],
        "redaction": redaction,
        "coverage_status": "covered" if covered else "review_required",
        "stores_private_value": False,
        "stored_evidence_shape": "placeholder_label_class_and_redaction_only",
    }


def _private_value_omission_evidence(redaction_checks: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    omitted_rows = [str(check["row_id"]) for check in redaction_checks if check.get("field_class") in _PRIVATE_CLASSES]
    return [
        {
            "evidence_id": "synthetic_rows_only",
            "status": "confirmed",
            "omitted_row_ids": omitted_rows,
            "stored_value_policy": "no_private_values_stored",
        },
        {
            "evidence_id": "artifact_absence",
            "status": "confirmed",
            "stored_value_policy": "no_browser_media_network_or_signin_materials_stored",
        },
    ]


def _route_check(row: Mapping[str, Any], surface_url_pattern: str) -> dict[str, Any]:
    source_pattern = str(row.get("route_pattern") or surface_url_pattern)
    normalized = _normalize_route_pattern(source_pattern)
    return {
        "order": row["order"],
        "row_id": row["row_id"],
        "source_route_pattern": source_pattern,
        "normalized_route_pattern": normalized,
        "normalization_status": "normalized_route_pattern" if _is_route_pattern(normalized) else "review_required",
    }


def _selector_summaries(rows: Sequence[Mapping[str, Any]], notes: Sequence[Any]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    note_count = len(notes)
    for row in rows:
        confidence = float(row["selector_confidence"])
        summaries.append(
            {
                "row_id": row["row_id"],
                "selector_ref": row["selector_ref"],
                "confidence": confidence,
                "confidence_band": _confidence_band(confidence),
                "selector_note_count": note_count,
                "review_status": "review_ready" if confidence >= 0.75 else "manual_review_required",
            }
        )
    return summaries


def _manual_handoff_reminders(normalized: Mapping[str, Any]) -> list[dict[str, Any]]:
    reminders = [
        {
            "reminder_id": "unsupported_or_uncertain_paths",
            "status": "manual_handoff_required",
            "source_count": len(normalized["reviewer_holds"]),
        },
        {
            "reminder_id": "consequential_actions_blocked",
            "status": "manual_handoff_required",
            "blocked_actions": ["form_fill", "upload", "submit", "pay", "schedule", "certify"],
        },
    ]
    return reminders


def _fixture_promotion_holds(normalized: Mapping[str, Any], redaction_checks: Sequence[Mapping[str, Any]], selector_summaries: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    holds = []
    if any(check.get("coverage_status") != "covered" for check in redaction_checks):
        holds.append({"hold_id": "redaction_coverage_gap", "status": "hold"})
    if any(summary.get("review_status") == "manual_review_required" for summary in selector_summaries):
        holds.append({"hold_id": "selector_confidence_review", "status": "hold"})
    for index, hold in enumerate(normalized["reviewer_holds"], start=1):
        hold_id = hold.get("hold_id") if isinstance(hold, Mapping) else None
        holds.append({"hold_id": _text_or_default(hold_id, f"reviewer_hold_{index}"), "status": "hold"})
    if not holds:
        holds.append({"hold_id": "reviewer_release_required", "status": "hold"})
    return holds


def _reviewer_routing(redaction_checks: Sequence[Mapping[str, Any]], selector_summaries: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    routes = [{"reviewer_queue": "devhub_surface_reviewer", "reason": "route_pattern_and_selector_review"}]
    if any(check.get("field_class") in _PRIVATE_CLASSES for check in redaction_checks):
        routes.append({"reviewer_queue": "privacy_reviewer", "reason": "private_value_omission_evidence"})
    if any(summary.get("review_status") == "manual_review_required" for summary in selector_summaries):
        routes.append({"reviewer_queue": "manual_handoff_reviewer", "reason": "selector_confidence_or_unsupported_path"})
    return routes


def _rollback_notes(normalized: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "rollback_id": "fixture_only_no_runtime_state",
            "note": "Remove this packet and fixture-derived references; no DevHub runtime state is created by this builder.",
        },
        {
            "rollback_id": "no_registry_mutation",
            "note": f"Do not promote {normalized['intake_id']} until reviewer holds are resolved in a later reviewed change.",
        },
    ]


def _normalize_route_pattern(value: str) -> str:
    normalized = _UUID_RE.sub("{id}", value.strip())
    normalized = _NUMERIC_SEGMENT_RE.sub("/{id}", normalized)
    normalized = re.sub(r"\{[a-zA-Z0-9_]+\}", "{id}", normalized)
    normalized = re.sub(r":[a-zA-Z0-9_]+", "{id}", normalized)
    normalized = re.sub(r"]+>", "{id}", normalized)
    return normalized


def _is_route_pattern(value: str) -> bool:
    return "{id}" in value or bool(_ROUTE_TOKEN_RE.search(value))


def _confidence(value: Any) -> float:
    if isinstance(value, (int, float)):
        bounded = float(value)
    else:
        bounded = 0.0
    return max(0.0, min(1.0, bounded))


def _confidence_band(value: float) -> str:
    if value >= 0.85:
        return "high"
    if value >= 0.75:
        return "medium"
    return "low"


def _reject_prohibited_input(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text.lower() in _PROHIBITED_INPUT_KEYS:
                raise ObservationRedactionAcceptancePacketV3Error(f"prohibited input key at {path}.{key_text}")
            _reject_prohibited_input(child, f"{path}.{key_text}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _reject_prohibited_input(child, f"{path}[{index}]")
    elif isinstance(value, str) and _PROHIBITED_TEXT_RE.search(value):
        raise ObservationRedactionAcceptancePacketV3Error(f"prohibited input text at {path}")


def _contains_prohibited_text(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_prohibited_text(child) for child in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_prohibited_text(child) for child in value)
    return isinstance(value, str) and bool(_PROHIBITED_TEXT_RE.search(value))


def _required_mapping(mapping: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = mapping.get(key)
    if not isinstance(value, Mapping):
        raise ObservationRedactionAcceptancePacketV3Error(f"{key} must be an object")
    return value


def _required_sequence(mapping: Mapping[str, Any], key: str) -> Sequence[Any]:
    value = mapping.get(key)
    if not _non_empty_sequence(value):
        raise ObservationRedactionAcceptancePacketV3Error(f"{key} must be a non-empty list")
    return value


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    return _text_or_default(mapping.get(key), "") or _raise_missing_text(key)


def _raise_missing_text(key: str) -> str:
    raise ObservationRedactionAcceptancePacketV3Error(f"{key} must be non-empty text")


def _text_or_default(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and bool(value)


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not _non_empty_sequence(value):
        return []
    return [item for item in value if isinstance(item, Mapping)]
