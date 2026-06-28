"""Fixture-first inactive activation rehearsal checklist v1.

This module consumes only synthetic approved inactive release decision rows and
inactive smoke replay rows. It assembles a checklist of activation prerequisites,
source-evidence placeholder checks, reviewer signoff placeholders, rollback
checkpoints, post-activation smoke requirements, hold conditions, release notes
placeholders, and exact offline validation commands. It does not activate
release guardrails, change active prompts, crawl sources, open DevHub, store
private artifacts, or perform official actions.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

PACKET_TYPE = "ppd.inactive_activation_rehearsal_checklist.v1"
PACKET_VERSION = "v1"
MODE = "fixture_first_inactive_activation_rehearsal_checklist_only"
SOURCE_KIND = "synthetic_approved_inactive_release_decision_rows_and_inactive_smoke_replay_rows"
DECISION_ROW_TYPE = "synthetic_approved_inactive_release_decision_row"
SMOKE_ROW_TYPE = "synthetic_inactive_smoke_replay_row"
EXACT_OFFLINE_VALIDATION_COMMANDS = [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]]

REQUIRED_BOUNDARIES = {
    "fixture_first": True,
    "synthetic_rows_only": True,
    "approved_inactive_decision_rows_only": True,
    "inactive_smoke_replay_rows_only": True,
    "activation_enabled": False,
    "guardrail_activation_enabled": False,
    "active_prompt_changes_enabled": False,
    "live_crawling_enabled": False,
    "devhub_opened": False,
    "private_artifact_storage_enabled": False,
    "official_action_enabled": False,
}

REQUIRED_CHECKLIST_SECTIONS = (
    "activation_prerequisites",
    "source_evidence_placeholder_checks",
    "reviewer_signoff_placeholders",
    "rollback_checkpoints",
    "post_activation_smoke_requirements",
    "hold_conditions",
    "release_notes_placeholders",
)

FORBIDDEN_KEY_MARKERS = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "downloaded_artifact",
    "downloaded_document",
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

FORBIDDEN_TRUE_FLAGS = (
    "activation_enabled",
    "active_guardrail_mutation",
    "active_prompt_changes_enabled",
    "active_prompt_mutation",
    "active_release_state_mutation",
    "browser_automation_enabled",
    "devhub_opened",
    "fixture_promotion_enabled",
    "guardrail_activation_enabled",
    "guardrail_mutation_enabled",
    "live_crawling_enabled",
    "official_action_enabled",
    "private_artifact_storage_enabled",
    "prompt_mutation_enabled",
    "release_state_update_enabled",
)

FORBIDDEN_TEXT_MARKERS = (
    "active prompt changed",
    "authenticated devhub",
    "browser state",
    "cookie",
    "credential",
    "devhub opened",
    "devhub session",
    "downloaded artifact",
    "downloaded document",
    "fee paid",
    "guardrails activated",
    "har file",
    "legal guarantee",
    "live crawl",
    "live devhub",
    "opened devhub",
    "official action completed",
    "official action performed",
    "payment completed",
    "permit approval guaranteed",
    "permit will be approved",
    "private artifact",
    "private file",
    "raw crawl",
    "raw download",
    "raw html",
    "raw pdf",
    "release activated",
    "release promoted",
    "screenshot",
    "session state",
    "storage state",
    "submitted permit",
    "trace file",
    "uploaded plans",
)

FORBIDDEN_TEXT_RE = re.compile(
    r"\b(approval is guaranteed|guaranteed approval|guaranteed issuance|legal advice|"
    r"promotion succeeded|release state updated|will pass plan review)\b",
    re.IGNORECASE,
)

ACTIVE_MUTATION_KEY_RE = re.compile(
    r"(^|_)(active_)?(guardrail|prompt|release_state|fixture|artifact|surface_registry)_"
    r"(activation|change|mutation|promotion|update|write)(_|$)",
    re.IGNORECASE,
)


class InactiveActivationRehearsalChecklistV1Error(ValueError):
    """Raised when the inactive activation rehearsal checklist is not fixture-safe."""

    def __init__(self, errors: Sequence[str]) -> None:
        self.errors = tuple(errors)
        super().__init__("invalid inactive activation rehearsal checklist v1: " + "; ".join(self.errors))


def load_source_rows(path: str | Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, Mapping):
        raise ValueError("source fixture must be an object")
    decision_rows = _dict_rows(loaded.get("approved_inactive_release_decision_rows"), "approved_inactive_release_decision_rows")
    smoke_rows = _dict_rows(loaded.get("inactive_smoke_replay_rows"), "inactive_smoke_replay_rows")
    return decision_rows, smoke_rows


def build_checklist_from_fixture(path: str | Path) -> dict[str, Any]:
    decision_rows, smoke_rows = load_source_rows(path)
    return build_checklist(decision_rows, smoke_rows)


def load_inactive_activation_rehearsal_checklist_v1(path: str | Path) -> dict[str, Any]:
    packet = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(packet, dict):
        raise InactiveActivationRehearsalChecklistV1Error(["packet must be an object"])
    assert_valid_inactive_activation_rehearsal_checklist_v1(packet)
    return packet


def build_checklist(
    decision_rows: Sequence[Mapping[str, Any]],
    smoke_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    decisions = _validated_decision_rows(decision_rows)
    smoke_by_key = _validated_smoke_rows(smoke_rows)
    _require_matching_smoke_rows(decisions, smoke_by_key)

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "inactive-activation-rehearsal-checklist-v1",
        "mode": MODE,
        "source_kind": SOURCE_KIND,
        "boundaries": dict(REQUIRED_BOUNDARIES),
        "consumed_approved_inactive_release_decision_row_ids": [str(row["decision_row_id"]) for row in decisions],
        "consumed_inactive_smoke_replay_row_ids": [str(smoke_by_key[str(row["scenario_key"])]["smoke_replay_row_id"]) for row in decisions],
        "activation_prerequisites": [_activation_prerequisite(row, smoke_by_key[str(row["scenario_key"])]) for row in decisions],
        "source_evidence_placeholder_checks": [_source_evidence_check(row) for row in decisions],
        "reviewer_signoff_placeholders": [_reviewer_signoff(row) for row in decisions],
        "rollback_checkpoints": [_rollback_checkpoint(row) for row in decisions],
        "post_activation_smoke_requirements": [_post_activation_smoke_requirement(row, smoke_by_key[str(row["scenario_key"])]) for row in decisions],
        "hold_conditions": [_hold_condition(row, smoke_by_key[str(row["scenario_key"])]) for row in decisions],
        "release_notes_placeholders": [_release_notes_placeholder(row) for row in decisions],
        "exact_offline_validation_commands": EXACT_OFFLINE_VALIDATION_COMMANDS,
        "validation_commands": EXACT_OFFLINE_VALIDATION_COMMANDS,
    }
    assert_valid_inactive_activation_rehearsal_checklist_v1(packet)
    return packet


def validate_inactive_activation_rehearsal_checklist_v1(packet: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        errors.append("packet_version must be v1")
    if packet.get("mode") != MODE:
        errors.append(f"mode must be {MODE}")
    if packet.get("source_kind") != SOURCE_KIND:
        errors.append(f"source_kind must be {SOURCE_KIND}")
    if packet.get("boundaries") != REQUIRED_BOUNDARIES:
        errors.append("boundaries must exactly keep the checklist fixture-only, synthetic, inactive, offline, non-mutating, and non-official")
    if packet.get("exact_offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append("exact_offline_validation_commands must contain only the daemon self-test command")
    if packet.get("validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        errors.append("validation_commands must contain only the daemon self-test command")

    for section in REQUIRED_CHECKLIST_SECTIONS:
        value = packet.get(section)
        if not isinstance(value, list) or not value:
            errors.append(f"{section} must be a non-empty list")

    _validate_consumed_rows(packet, errors)
    _validate_activation_prerequisites(packet.get("activation_prerequisites"), errors)
    _validate_source_evidence_checks(packet.get("source_evidence_placeholder_checks"), errors)
    _validate_reviewer_signoffs(packet.get("reviewer_signoff_placeholders"), errors)
    _validate_rollback_checkpoints(packet.get("rollback_checkpoints"), errors)
    _validate_post_activation_smoke(packet.get("post_activation_smoke_requirements"), errors)
    _validate_hold_conditions(packet.get("hold_conditions"), errors)
    _validate_release_notes(packet.get("release_notes_placeholders"), errors)
    _scan_for_forbidden_payload(packet, "$", errors)
    return sorted(set(errors))


def assert_valid_inactive_activation_rehearsal_checklist_v1(packet: Mapping[str, Any]) -> None:
    errors = validate_inactive_activation_rehearsal_checklist_v1(packet)
    if errors:
        raise InactiveActivationRehearsalChecklistV1Error(errors)


def _validated_decision_rows(rows: Sequence[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
    if not rows:
        raise ValueError("at least one synthetic approved inactive release decision row is required")
    validated: list[Mapping[str, Any]] = []
    for index, row in enumerate(rows):
        prefix = f"decision row {index}"
        if row.get("row_type") != DECISION_ROW_TYPE:
            raise ValueError(f"{prefix} must have row_type {DECISION_ROW_TYPE}")
        if row.get("synthetic") is not True:
            raise ValueError(f"{prefix} must be synthetic")
        if row.get("release_state") != "inactive":
            raise ValueError(f"{prefix} must remain inactive")
        if row.get("decision") != "approve":
            raise ValueError(f"{prefix} must be approved")
        if row.get("activation_enabled") is not False:
            raise ValueError(f"{prefix} must keep activation_enabled false")
        for field in ("decision_row_id", "scenario_key", "activation_prerequisite", "reviewer_role", "rollback_checkpoint", "hold_condition", "release_notes_placeholder"):
            if not _text(row.get(field)):
                raise ValueError(f"{prefix}.{field} must be non-empty")
        if not _string_list(row.get("source_evidence_placeholder_ids")):
            raise ValueError(f"{prefix}.source_evidence_placeholder_ids must be non-empty")
        validated.append(row)
    return sorted(validated, key=lambda row: str(row["decision_row_id"]))


def _validated_smoke_rows(rows: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    if not rows:
        raise ValueError("at least one synthetic inactive smoke replay row is required")
    by_key: dict[str, Mapping[str, Any]] = {}
    for index, row in enumerate(rows):
        prefix = f"smoke row {index}"
        if row.get("row_type") != SMOKE_ROW_TYPE:
            raise ValueError(f"{prefix} must have row_type {SMOKE_ROW_TYPE}")
        if row.get("synthetic") is not True:
            raise ValueError(f"{prefix} must be synthetic")
        if row.get("inactive_release_only") is not True:
            raise ValueError(f"{prefix} must be inactive_release_only")
        if row.get("offline_only") is not True:
            raise ValueError(f"{prefix} must be offline_only")
        for field in ("smoke_replay_row_id", "scenario_key", "post_activation_smoke_requirement"):
            if not _text(row.get(field)):
                raise ValueError(f"{prefix}.{field} must be non-empty")
        for field in ("expected_smoke_checks", "blocked_action_expectations", "citation_placeholder_checks"):
            if not _string_list(row.get(field)):
                raise ValueError(f"{prefix}.{field} must be a non-empty list of text")
        key = str(row["scenario_key"])
        if key in by_key:
            raise ValueError(f"duplicate smoke scenario_key {key}")
        by_key[key] = row
    return by_key


def _require_matching_smoke_rows(decisions: Sequence[Mapping[str, Any]], smoke_by_key: Mapping[str, Mapping[str, Any]]) -> None:
    for row in decisions:
        key = str(row["scenario_key"])
        if key not in smoke_by_key:
            raise ValueError(f"missing inactive smoke replay row for scenario_key {key}")


def _activation_prerequisite(decision: Mapping[str, Any], smoke: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "prerequisite_id": f"activation-prerequisite-{decision['scenario_key']}",
        "source_decision_row_id": str(decision["decision_row_id"]),
        "source_smoke_replay_row_id": str(smoke["smoke_replay_row_id"]),
        "description": str(decision["activation_prerequisite"]),
        "status": "placeholder_only",
        "required_before": "any_separate_activation_decision",
    }


def _source_evidence_check(decision: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "check_id": f"source-evidence-placeholder-{decision['scenario_key']}",
        "source_decision_row_id": str(decision["decision_row_id"]),
        "placeholder_ids": _string_list(decision.get("source_evidence_placeholder_ids")),
        "status": "placeholder_only",
        "requires_offline_reviewer_resolution": True,
    }


def _reviewer_signoff(decision: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "signoff_id": f"reviewer-signoff-{decision['scenario_key']}",
        "source_decision_row_id": str(decision["decision_row_id"]),
        "reviewer_role": str(decision["reviewer_role"]),
        "status": "not_signed",
        "signature_record": None,
        "required_before": "any_separate_activation_decision",
    }


def _rollback_checkpoint(decision: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "checkpoint_id": f"rollback-checkpoint-{decision['scenario_key']}",
        "source_decision_row_id": str(decision["decision_row_id"]),
        "description": str(decision["rollback_checkpoint"]),
        "status": "pending_rehearsal_review",
        "required_before": "any_separate_activation_decision",
    }


def _post_activation_smoke_requirement(decision: Mapping[str, Any], smoke: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": f"post-activation-smoke-{decision['scenario_key']}",
        "source_decision_row_id": str(decision["decision_row_id"]),
        "source_smoke_replay_row_id": str(smoke["smoke_replay_row_id"]),
        "description": str(smoke["post_activation_smoke_requirement"]),
        "expected_smoke_checks": _string_list(smoke.get("expected_smoke_checks")),
        "status": "placeholder_only",
        "offline_validation_commands": EXACT_OFFLINE_VALIDATION_COMMANDS,
    }


def _hold_condition(decision: Mapping[str, Any], smoke: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "hold_condition_id": f"hold-condition-{decision['scenario_key']}",
        "source_decision_row_id": str(decision["decision_row_id"]),
        "source_smoke_replay_row_id": str(smoke["smoke_replay_row_id"]),
        "description": str(decision["hold_condition"]),
        "blocked_action_expectations": _string_list(smoke.get("blocked_action_expectations")),
        "status": "active_for_rehearsal_only",
    }


def _release_notes_placeholder(decision: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "placeholder_id": f"release-notes-{decision['scenario_key']}",
        "source_decision_row_id": str(decision["decision_row_id"]),
        "description": str(decision["release_notes_placeholder"]),
        "status": "placeholder_only",
        "notes_text": None,
    }


def _validate_consumed_rows(packet: Mapping[str, Any], errors: list[str]) -> None:
    decision_ids = _string_list(packet.get("consumed_approved_inactive_release_decision_row_ids"))
    smoke_ids = _string_list(packet.get("consumed_inactive_smoke_replay_row_ids"))
    if not decision_ids:
        errors.append("consumed_approved_inactive_release_decision_row_ids must be non-empty")
    if not smoke_ids:
        errors.append("consumed_inactive_smoke_replay_row_ids must be non-empty")


def _validate_activation_prerequisites(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"activation_prerequisites[{index}]"
        _require_text_fields(row, prefix, ("prerequisite_id", "source_decision_row_id", "source_smoke_replay_row_id", "description"), errors)
        if row.get("status") != "placeholder_only":
            errors.append(f"{prefix}.status must be placeholder_only")
        if row.get("required_before") != "any_separate_activation_decision":
            errors.append(f"{prefix}.required_before must gate any separate activation decision")


def _validate_source_evidence_checks(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"source_evidence_placeholder_checks[{index}]"
        _require_text_fields(row, prefix, ("check_id", "source_decision_row_id", "status"), errors)
        if not _string_list(row.get("placeholder_ids")):
            errors.append(f"{prefix}.placeholder_ids must be a non-empty list of text")
        if row.get("status") != "placeholder_only":
            errors.append(f"{prefix}.status must be placeholder_only")
        if row.get("requires_offline_reviewer_resolution") is not True:
            errors.append(f"{prefix}.requires_offline_reviewer_resolution must be true")


def _validate_reviewer_signoffs(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"reviewer_signoff_placeholders[{index}]"
        _require_text_fields(row, prefix, ("signoff_id", "source_decision_row_id", "reviewer_role"), errors)
        if row.get("status") != "not_signed":
            errors.append(f"{prefix}.status must be not_signed")
        if row.get("signature_record") is not None:
            errors.append(f"{prefix}.signature_record must be null")
        if row.get("required_before") != "any_separate_activation_decision":
            errors.append(f"{prefix}.required_before must gate any separate activation decision")


def _validate_rollback_checkpoints(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"rollback_checkpoints[{index}]"
        _require_text_fields(row, prefix, ("checkpoint_id", "source_decision_row_id", "description"), errors)
        if row.get("status") != "pending_rehearsal_review":
            errors.append(f"{prefix}.status must be pending_rehearsal_review")
        if row.get("required_before") != "any_separate_activation_decision":
            errors.append(f"{prefix}.required_before must gate any separate activation decision")


def _validate_post_activation_smoke(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"post_activation_smoke_requirements[{index}]"
        _require_text_fields(row, prefix, ("requirement_id", "source_decision_row_id", "source_smoke_replay_row_id", "description"), errors)
        if not _string_list(row.get("expected_smoke_checks")):
            errors.append(f"{prefix}.expected_smoke_checks must be a non-empty list of text")
        if row.get("status") != "placeholder_only":
            errors.append(f"{prefix}.status must be placeholder_only")
        if row.get("offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
            errors.append(f"{prefix}.offline_validation_commands must contain only the daemon self-test command")


def _validate_hold_conditions(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"hold_conditions[{index}]"
        _require_text_fields(row, prefix, ("hold_condition_id", "source_decision_row_id", "source_smoke_replay_row_id", "description"), errors)
        if not _string_list(row.get("blocked_action_expectations")):
            errors.append(f"{prefix}.blocked_action_expectations must be a non-empty list of text")
        if row.get("status") != "active_for_rehearsal_only":
            errors.append(f"{prefix}.status must be active_for_rehearsal_only")


def _validate_release_notes(value: Any, errors: list[str]) -> None:
    for index, row in enumerate(_mapping_rows(value)):
        prefix = f"release_notes_placeholders[{index}]"
        _require_text_fields(row, prefix, ("placeholder_id", "source_decision_row_id", "description"), errors)
        if row.get("status") != "placeholder_only":
            errors.append(f"{prefix}.status must be placeholder_only")
        if row.get("notes_text") is not None:
            errors.append(f"{prefix}.notes_text must be null")


def _scan_for_forbidden_payload(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized_key = str(key).lower().replace("-", "_")
            child_path = f"{path}.{key}"
            if normalized_key in FORBIDDEN_TRUE_FLAGS and child is True:
                errors.append(f"forbidden active/live/private/official true flag at {child_path}")
            if ACTIVE_MUTATION_KEY_RE.search(normalized_key) and child is True:
                errors.append(f"forbidden active mutation flag at {child_path}")
            if any(marker in normalized_key for marker in FORBIDDEN_KEY_MARKERS) and child not in (None, False, "", [], {}):
                errors.append(f"forbidden private/session/browser/raw artifact field at {child_path}")
            _scan_for_forbidden_payload(child, child_path, errors)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_payload(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        lowered = value.lower()
        for marker in FORBIDDEN_TEXT_MARKERS:
            if marker in lowered:
                errors.append(f"forbidden live/private/official/release/legal guarantee claim at {path}: {marker}")
        if FORBIDDEN_TEXT_RE.search(value):
            errors.append(f"forbidden live/private/official/release/legal guarantee claim at {path}")


def _require_text_fields(row: Mapping[str, Any], prefix: str, fields: Sequence[str], errors: list[str]) -> None:
    for field in fields:
        if not _text(row.get(field)):
            errors.append(f"{prefix}.{field} must be non-empty")


def _mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _dict_rows(value: Any, field: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list")
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(value):
        if not isinstance(row, dict):
            raise ValueError(f"{field}[{index}] must be an object")
        rows.append(row)
    return rows


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
