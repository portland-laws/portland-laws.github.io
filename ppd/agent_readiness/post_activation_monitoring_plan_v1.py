"""Fixture-first post-activation monitoring plan v1.

This module consumes only synthetic inactive activation rehearsal checklist rows.
It builds offline monitoring probes, expected guardrail bundle identifiers,
agent API smoke checks, action journal redaction checks, stale-source holds,
reviewer escalation routes, rollback trigger thresholds, and exact offline
validation commands. It does not activate guardrails, run live crawls, open
DevHub, store private artifacts, or perform official actions.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PACKET_TYPE = "ppd.post_activation_monitoring_plan.v1"
PACKET_VERSION = "v1"
SOURCE_ROW_TYPE = "synthetic_inactive_activation_rehearsal_checklist_row"
MODE = "fixture_first_post_activation_monitoring_plan_only"
EXACT_OFFLINE_VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

REQUIRED_BOUNDARIES = {
    "fixture_first": True,
    "synthetic_rows_only": True,
    "inactive_activation_rehearsal_rows_only": True,
    "offline_monitoring_only": True,
    "guardrail_activation_enabled": False,
    "live_crawling_enabled": False,
    "devhub_opened": False,
    "private_artifact_storage_enabled": False,
    "official_action_enabled": False,
}

REQUIRED_PLAN_SECTIONS = (
    "offline_monitoring_probes",
    "expected_guardrail_bundle_identifiers",
    "expected_agent_api_smoke_checks",
    "action_journal_redaction_checks",
    "stale_source_hold_checks",
    "reviewer_escalation_routes",
    "rollback_trigger_thresholds",
)

REQUIRED_SECTION_REFERENCE_FIELDS = {
    "offline_monitoring_probes": "source_checklist_row_id",
    "expected_guardrail_bundle_identifiers": "source_checklist_row_id",
    "expected_agent_api_smoke_checks": "source_checklist_row_id",
    "action_journal_redaction_checks": "source_checklist_row_id",
    "stale_source_hold_checks": "source_checklist_row_id",
    "reviewer_escalation_routes": "source_checklist_row_id",
    "rollback_trigger_thresholds": "source_checklist_row_id",
}

FORBIDDEN_TRUE_FLAGS = {
    "active_guardrail_mutation",
    "active_mutation_enabled",
    "active_prompt_mutation",
    "approval_guaranteed",
    "browser_automation_enabled",
    "devhub_opened",
    "final_action_completed",
    "guardrail_activation_enabled",
    "legal_advice_provided",
    "live_crawling_enabled",
    "official_action_completed",
    "official_action_enabled",
    "permit_guaranteed",
    "private_artifact_storage_enabled",
    "promotion_completed",
    "release_state_update_enabled",
}

FORBIDDEN_KEY_MARKERS = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "downloaded_artifact",
    "downloaded_document",
    "downloaded_file",
    "har",
    "private_artifact",
    "raw_artifact",
    "raw_body",
    "raw_crawl",
    "raw_download",
    "raw_html",
    "raw_pdf",
    "screenshot",
    "session_state",
    "storage_state",
    "trace",
)

FORBIDDEN_TEXT_RE = re.compile(
    r"\b("
    r"activated guardrails|activation completed|approval is guaranteed|browser state|certification completed|"
    r"devhub claim|downloaded document|downloaded file|final payment executed|guardrail activation|"
    r"guardrails activated|har file|legal advice|live crawl|live devhub|opened devhub|"
    r"official action completed|payment completed|permit approval guaranteed|permit is guaranteed|"
    r"private artifact|promoted to active|promotion completed|raw crawl|raw download|raw html|raw pdf|"
    r"release activated|release promoted|schedule inspection completed|storage state|submitted permit|"
    r"trace file|uploaded plans"
    r")\b",
    re.IGNORECASE,
)


class PostActivationMonitoringPlanV1Error(ValueError):
    """Raised when a post-activation monitoring plan is not fixture-safe."""

    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("invalid post-activation monitoring plan v1: " + "; ".join(self.errors))


def load_source_rows(path: str | Path) -> list[dict[str, Any]]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping):
        raise ValueError("source fixture must be an object")
    rows = loaded.get("inactive_activation_rehearsal_checklist_rows")
    if not isinstance(rows, list):
        raise ValueError("inactive_activation_rehearsal_checklist_rows must be a list")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("inactive_activation_rehearsal_checklist_rows entries must be objects")
    return rows


def build_post_activation_monitoring_plan_v1_from_fixture(path: str | Path) -> dict[str, Any]:
    return build_post_activation_monitoring_plan_v1(load_source_rows(path))


def load_post_activation_monitoring_plan_v1(path: str | Path) -> dict[str, Any]:
    packet = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(packet, dict):
        raise PostActivationMonitoringPlanV1Error(["packet must be an object"])
    assert_valid_post_activation_monitoring_plan_v1(packet)
    return packet


def build_post_activation_monitoring_plan_v1(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    checklist_rows = _validated_rows(rows)
    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "post-activation-monitoring-plan-v1",
        "mode": MODE,
        "boundaries": dict(REQUIRED_BOUNDARIES),
        "consumed_inactive_activation_rehearsal_checklist_row_ids": [str(row["checklist_row_id"]) for row in checklist_rows],
        "offline_monitoring_probes": [_offline_monitoring_probe(row) for row in checklist_rows],
        "expected_guardrail_bundle_identifiers": [_guardrail_bundle_identifier(row) for row in checklist_rows],
        "expected_agent_api_smoke_checks": [_agent_api_smoke_check(row) for row in checklist_rows],
        "action_journal_redaction_checks": [_action_journal_redaction_check(row) for row in checklist_rows],
        "stale_source_hold_checks": [_stale_source_hold_check(row) for row in checklist_rows],
        "reviewer_escalation_routes": [_reviewer_escalation_route(row) for row in checklist_rows],
        "rollback_trigger_thresholds": [_rollback_trigger_threshold(row) for row in checklist_rows],
        "exact_offline_validation_commands": EXACT_OFFLINE_VALIDATION_COMMANDS,
        "validation_commands": EXACT_OFFLINE_VALIDATION_COMMANDS,
    }
    assert_valid_post_activation_monitoring_plan_v1(packet)
    return packet


def validate_post_activation_monitoring_plan_v1(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        errors.append("packet_version must be v1")
    if packet.get("mode") != MODE:
        errors.append(f"mode must be {MODE}")
    if packet.get("boundaries") != REQUIRED_BOUNDARIES:
        errors.append("boundaries must exactly keep monitoring fixture-only, synthetic, inactive, offline, non-activating, non-DevHub, non-private, and non-official")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append("exact_offline_validation_commands must contain only the daemon self-test command")
    if packet.get("validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append("validation_commands must contain only the daemon self-test command")

    consumed_ids = _string_list(packet.get("consumed_inactive_activation_rehearsal_checklist_row_ids"))
    if not consumed_ids:
        errors.append("consumed_inactive_activation_rehearsal_checklist_row_ids must be non-empty")
    if len(consumed_ids) != len(set(consumed_ids)):
        errors.append("consumed_inactive_activation_rehearsal_checklist_row_ids must not contain duplicates")

    for section in REQUIRED_PLAN_SECTIONS:
        value = packet.get(section)
        if not isinstance(value, list) or not value:
            errors.append(f"{section} must be a non-empty list")
            continue
        for index, item in enumerate(value):
            if not isinstance(item, Mapping):
                errors.append(f"{section}[{index}] must be an object")

    _validate_required_checklist_references(packet, consumed_ids, errors)
    _validate_monitoring_probes(packet.get("offline_monitoring_probes"), errors)
    _validate_bundle_ids(packet.get("expected_guardrail_bundle_identifiers"), errors)
    _validate_agent_api_smoke_checks(packet.get("expected_agent_api_smoke_checks"), errors)
    _validate_redaction_checks(packet.get("action_journal_redaction_checks"), errors)
    _validate_stale_source_holds(packet.get("stale_source_hold_checks"), errors)
    _validate_escalation_routes(packet.get("reviewer_escalation_routes"), errors)
    _validate_rollback_thresholds(packet.get("rollback_trigger_thresholds"), errors)
    _scan_for_forbidden_payload(packet, "$", errors)
    return sorted(set(errors))


def assert_valid_post_activation_monitoring_plan_v1(packet: Mapping[str, Any]) -> None:
    errors = validate_post_activation_monitoring_plan_v1(packet)
    if errors:
        raise PostActivationMonitoringPlanV1Error(errors)


def _validated_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    if not rows:
        raise ValueError("at least one synthetic inactive activation rehearsal checklist row is required")
    validated: list[Mapping[str, Any]] = []
    for index, row in enumerate(rows):
        prefix = f"checklist row {index}"
        if row.get("row_type") != SOURCE_ROW_TYPE:
            raise ValueError(f"{prefix} must have row_type {SOURCE_ROW_TYPE}")
        if row.get("synthetic") is not True:
            raise ValueError(f"{prefix} must be synthetic")
        if row.get("release_state") != "inactive":
            raise ValueError(f"{prefix} must remain inactive")
        if row.get("activation_enabled") is not False:
            raise ValueError(f"{prefix} must keep activation_enabled false")
        for field in (
            "checklist_row_id",
            "scenario_key",
            "offline_probe",
            "guardrail_bundle_id",
            "agent_api_smoke_check",
            "action_journal_redaction_check",
            "stale_source_hold_check",
            "reviewer_escalation_route",
            "rollback_trigger_threshold",
        ):
            if not _text(row.get(field)):
                raise ValueError(f"{prefix}.{field} must be non-empty")
        if not _string_list(row.get("source_evidence_placeholder_ids")):
            raise ValueError(f"{prefix}.source_evidence_placeholder_ids must be non-empty")
        validated.append(row)
    return sorted(validated, key=lambda row: str(row["checklist_row_id"]))


def _offline_monitoring_probe(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "probe_id": f"offline-probe-{row['scenario_key']}",
        "source_checklist_row_id": str(row["checklist_row_id"]),
        "description": str(row["offline_probe"]),
        "source_evidence_placeholder_ids": _string_list(row.get("source_evidence_placeholder_ids")),
        "execution_mode": "offline_fixture_probe_only",
        "status": "planned_only",
    }


def _guardrail_bundle_identifier(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "bundle_ref_id": f"expected-bundle-{row['scenario_key']}",
        "source_checklist_row_id": str(row["checklist_row_id"]),
        "guardrail_bundle_id": str(row["guardrail_bundle_id"]),
        "expected_state": "inactive_candidate_reference_only",
    }


def _agent_api_smoke_check(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "smoke_check_id": f"agent-api-smoke-{row['scenario_key']}",
        "source_checklist_row_id": str(row["checklist_row_id"]),
        "description": str(row["agent_api_smoke_check"]),
        "expected_result": "offline_pass_or_reviewer_hold",
    }


def _action_journal_redaction_check(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "redaction_check_id": f"action-journal-redaction-{row['scenario_key']}",
        "source_checklist_row_id": str(row["checklist_row_id"]),
        "description": str(row["action_journal_redaction_check"]),
        "expected_result": "private_values_absent",
    }


def _stale_source_hold_check(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "hold_check_id": f"stale-source-hold-{row['scenario_key']}",
        "source_checklist_row_id": str(row["checklist_row_id"]),
        "description": str(row["stale_source_hold_check"]),
        "expected_result": "agent_holds_until_reviewer_resolves_placeholder",
    }


def _reviewer_escalation_route(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "route_id": f"reviewer-escalation-{row['scenario_key']}",
        "source_checklist_row_id": str(row["checklist_row_id"]),
        "route": str(row["reviewer_escalation_route"]),
        "status": "reviewer_placeholder_only",
    }


def _rollback_trigger_threshold(row: Mapping[str, Any]) -> dict[str, str]:
    return {
        "threshold_id": f"rollback-threshold-{row['scenario_key']}",
        "source_checklist_row_id": str(row["checklist_row_id"]),
        "threshold": str(row["rollback_trigger_threshold"]),
        "status": "offline_threshold_only",
    }


def _validate_required_checklist_references(packet: Mapping[str, Any], consumed_ids: Sequence[str], errors: list[str]) -> None:
    expected_ids = set(consumed_ids)
    if not expected_ids:
        return
    for section, ref_field in REQUIRED_SECTION_REFERENCE_FIELDS.items():
        value = packet.get(section)
        if not isinstance(value, list):
            continue
        observed_ids: set[str] = set()
        for index, item in enumerate(value):
            if not isinstance(item, Mapping):
                continue
            ref = item.get(ref_field)
            if not _text(ref):
                errors.append(f"{section}[{index}].{ref_field} must reference a consumed inactive activation checklist row")
                continue
            ref_text = str(ref)
            observed_ids.add(ref_text)
            if ref_text not in expected_ids:
                errors.append(f"{section}[{index}].{ref_field} references unknown checklist row {ref_text}")
        missing_ids = sorted(expected_ids - observed_ids)
        for missing_id in missing_ids:
            errors.append(f"{section} missing required checklist row reference {missing_id}")


def _validate_monitoring_probes(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"offline_monitoring_probes[{index}]"
        _require_text_fields(row, prefix, ("probe_id", "source_checklist_row_id", "description", "execution_mode", "status"), errors)
        if row.get("execution_mode") != "offline_fixture_probe_only":
            errors.append(f"{prefix}.execution_mode must be offline_fixture_probe_only")
        if row.get("status") != "planned_only":
            errors.append(f"{prefix}.status must be planned_only")
        if not _string_list(row.get("source_evidence_placeholder_ids")):
            errors.append(f"{prefix}.source_evidence_placeholder_ids must be non-empty")


def _validate_bundle_ids(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"expected_guardrail_bundle_identifiers[{index}]"
        _require_text_fields(row, prefix, ("bundle_ref_id", "source_checklist_row_id", "guardrail_bundle_id", "expected_state"), errors)
        if row.get("expected_state") != "inactive_candidate_reference_only":
            errors.append(f"{prefix}.expected_state must be inactive_candidate_reference_only")


def _validate_agent_api_smoke_checks(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"expected_agent_api_smoke_checks[{index}]"
        _require_text_fields(row, prefix, ("smoke_check_id", "source_checklist_row_id", "description", "expected_result"), errors)
        if row.get("expected_result") != "offline_pass_or_reviewer_hold":
            errors.append(f"{prefix}.expected_result must be offline_pass_or_reviewer_hold")


def _validate_redaction_checks(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"action_journal_redaction_checks[{index}]"
        _require_text_fields(row, prefix, ("redaction_check_id", "source_checklist_row_id", "description", "expected_result"), errors)
        if row.get("expected_result") != "private_values_absent":
            errors.append(f"{prefix}.expected_result must be private_values_absent")


def _validate_stale_source_holds(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"stale_source_hold_checks[{index}]"
        _require_text_fields(row, prefix, ("hold_check_id", "source_checklist_row_id", "description", "expected_result"), errors)
        if row.get("expected_result") != "agent_holds_until_reviewer_resolves_placeholder":
            errors.append(f"{prefix}.expected_result must be agent_holds_until_reviewer_resolves_placeholder")


def _validate_escalation_routes(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"reviewer_escalation_routes[{index}]"
        _require_text_fields(row, prefix, ("route_id", "source_checklist_row_id", "route", "status"), errors)
        if row.get("status") != "reviewer_placeholder_only":
            errors.append(f"{prefix}.status must be reviewer_placeholder_only")


def _validate_rollback_thresholds(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"rollback_trigger_thresholds[{index}]"
        _require_text_fields(row, prefix, ("threshold_id", "source_checklist_row_id", "threshold", "status"), errors)
        if row.get("status") != "offline_threshold_only":
            errors.append(f"{prefix}.status must be offline_threshold_only")


def _scan_for_forbidden_payload(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            child_path = f"{path}.{key}"
            if normalized_key in FORBIDDEN_TRUE_FLAGS and child is True:
                errors.append(f"forbidden live/private/official/activation true flag at {child_path}")
            if any(marker in normalized_key for marker in FORBIDDEN_KEY_MARKERS) and child not in (None, False, "", [], {}):
                errors.append(f"forbidden private/session/browser/raw artifact field at {child_path}")
            _scan_for_forbidden_payload(child, child_path, errors)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_payload(child, f"{path}[{index}]", errors)
    elif isinstance(value, str) and FORBIDDEN_TEXT_RE.search(value):
        errors.append(f"forbidden live/private/official/activation claim at {path}")


def _require_text_fields(row: Mapping[str, Any], prefix: str, fields: Sequence[str], errors: list[str]) -> None:
    for field in fields:
        if not _text(row.get(field)):
            errors.append(f"{prefix}.{field} must be non-empty")


def _mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
