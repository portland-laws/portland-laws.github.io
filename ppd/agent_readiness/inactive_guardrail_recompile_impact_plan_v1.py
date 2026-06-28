"""Fixture-first inactive guardrail recompile impact plan v1.

This module consumes only synthetic inactive process-model delta assembly rows
and maps them to inactive guardrail bundle patch placeholders plus deterministic,
deontic, temporal, reversible-action, exact-confirmation, refused-action, and
agent-facing explanation impact placeholders. It does not recompile, promote, or
mutate active guardrails, open DevHub, crawl sources, store private artifacts, or
perform official actions.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SOURCE_PACKET_TYPE = "ppd.synthetic_inactive_process_model_delta_assembly_rows.v1"
PLAN_TYPE = "ppd.inactive_guardrail_recompile_impact_plan.v1"
PLAN_VERSION = "v1"
EXACT_OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/inactive_guardrail_recompile_impact_plan_v1.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_inactive_guardrail_recompile_impact_plan_v1.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

REQUIRED_SOURCE_ROW_FIELDS = (
    "row_id",
    "process_id",
    "permit_type",
    "process_stage",
    "inactive_guardrail_bundle_id",
    "delta_kind",
    "synthetic_evidence_refs",
    "affected_predicate_keys",
    "impact_notes",
)

REQUIRED_PLAN_SECTIONS = (
    "source_delta_rows",
    "inactive_guardrail_bundle_patch_placeholders",
    "deterministic_predicate_impacts",
    "deontic_rule_impacts",
    "temporal_rule_impacts",
    "reversible_action_predicate_impacts",
    "exact_confirmation_predicate_impacts",
    "refused_action_predicate_impacts",
    "agent_facing_explanation_impacts",
    "reviewer_holds",
    "rollback_notes",
)

FALSE_GUARDRAIL_FLAGS = (
    "active_guardrails_recompiled",
    "active_guardrails_promoted",
    "active_guardrail_mutation",
    "active_process_model_mutation",
    "active_requirement_mutation",
    "active_release_state_mutation",
    "live_crawl_performed",
    "devhub_opened",
    "private_artifacts_stored",
    "official_actions_performed",
)

FORBIDDEN_TEXT = (
    "active guardrail changed",
    "active guardrail promoted",
    "active guardrails recompiled",
    "auth state",
    "browser state",
    "captcha",
    "cookie",
    "credential",
    "downloaded document",
    "har file",
    "live crawl",
    "opened devhub",
    "payment detail",
    "private artifact",
    "raw crawl",
    "session storage",
    "submitted permit",
    "uploaded correction",
)


@dataclass(frozen=True)
class InactiveGuardrailRecompileImpactPlanV1Result:
    valid: bool
    problems: tuple[str, ...]


class InactiveGuardrailRecompileImpactPlanV1Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid inactive guardrail recompile impact plan v1: " + "; ".join(self.problems))


def load_json_object(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"expected JSON object at {path}")
    return loaded


def build_inactive_guardrail_recompile_impact_plan_v1_from_file(path: str | Path) -> dict[str, Any]:
    return build_inactive_guardrail_recompile_impact_plan_v1(load_json_object(path))


def build_inactive_guardrail_recompile_impact_plan_v1(source_packet: Mapping[str, Any]) -> dict[str, Any]:
    source_errors = validate_synthetic_inactive_process_model_delta_assembly_rows_v1(source_packet)
    if source_errors:
        raise InactiveGuardrailRecompileImpactPlanV1Error(source_errors)

    rows = _mapping_sequence(source_packet.get("synthetic_inactive_process_model_delta_assembly_rows"))
    plan_rows = [_normalize_source_row(row) for row in rows]
    plan = {
        "plan_type": PLAN_TYPE,
        "plan_version": PLAN_VERSION,
        "plan_id": f"inactive-guardrail-recompile-impact-plan-v1-for-{_text(source_packet.get('fixture_id'), 'synthetic-delta-assembly-rows')}",
        "fixture_first": True,
        "impact_mode": "inactive_guardrail_bundle_patch_placeholders_only",
        "input_policy": "synthetic_inactive_process_model_delta_assembly_rows_only",
        "source_packet": {
            "packet_type": _text(source_packet.get("packet_type")),
            "fixture_id": _text(source_packet.get("fixture_id")),
        },
        "active_guardrails_recompiled": False,
        "active_guardrails_promoted": False,
        "active_guardrail_mutation": False,
        "active_process_model_mutation": False,
        "active_requirement_mutation": False,
        "active_release_state_mutation": False,
        "live_crawl_performed": False,
        "devhub_opened": False,
        "private_artifacts_stored": False,
        "official_actions_performed": False,
        "source_delta_rows": plan_rows,
        "inactive_guardrail_bundle_patch_placeholders": [_patch_placeholder(row) for row in plan_rows],
        "deterministic_predicate_impacts": [_impact(row, "deterministic", "deterministic_predicate_impact_placeholder") for row in plan_rows],
        "deontic_rule_impacts": [_impact(row, "deontic", "deontic_rule_impact_placeholder") for row in plan_rows],
        "temporal_rule_impacts": [_impact(row, "temporal", "temporal_rule_impact_placeholder") for row in plan_rows],
        "reversible_action_predicate_impacts": [_impact(row, "reversible-action", "reversible_action_predicate_impact_placeholder") for row in plan_rows],
        "exact_confirmation_predicate_impacts": [_impact(row, "exact-confirmation", "exact_confirmation_predicate_impact_placeholder") for row in plan_rows],
        "refused_action_predicate_impacts": [_impact(row, "refused-action", "refused_action_predicate_impact_placeholder") for row in plan_rows],
        "agent_facing_explanation_impacts": [_explanation_impact(row) for row in plan_rows],
        "reviewer_holds": [_reviewer_hold(row) for row in plan_rows],
        "rollback_notes": [_rollback_note(row) for row in plan_rows],
        "offline_validation_commands": EXACT_OFFLINE_VALIDATION_COMMANDS,
        "validation_commands": EXACT_OFFLINE_VALIDATION_COMMANDS,
    }
    assert_valid_inactive_guardrail_recompile_impact_plan_v1(plan)
    return plan


def validate_synthetic_inactive_process_model_delta_assembly_rows_v1(packet: Mapping[str, Any]) -> list[str]:
    problems: list[str] = []
    if not isinstance(packet, Mapping):
        return ["source packet must be an object"]
    if packet.get("packet_type") != SOURCE_PACKET_TYPE:
        problems.append(f"packet_type must be {SOURCE_PACKET_TYPE}")
    if packet.get("fixture_first") is not True:
        problems.append("fixture_first must be true")
    if packet.get("input_kind") != "synthetic_inactive_process_model_delta_assembly_rows_only":
        problems.append("input_kind must be synthetic_inactive_process_model_delta_assembly_rows_only")
    for flag in FALSE_GUARDRAIL_FLAGS:
        if packet.get(flag) is not False:
            problems.append(f"{flag} must be false")
    rows = _mapping_sequence(packet.get("synthetic_inactive_process_model_delta_assembly_rows"))
    if not rows:
        problems.append("synthetic_inactive_process_model_delta_assembly_rows must be a non-empty list")
    seen: set[str] = set()
    for index, row in enumerate(rows):
        prefix = f"synthetic_inactive_process_model_delta_assembly_rows[{index}]"
        for field in REQUIRED_SOURCE_ROW_FIELDS:
            if field not in row:
                problems.append(f"{prefix}.{field} is required")
        row_id = _text(row.get("row_id"))
        if row_id in seen:
            problems.append(f"{prefix}.row_id must be unique")
        seen.add(row_id)
        if not row_id.startswith("synthetic-"):
            problems.append(f"{prefix}.row_id must start with synthetic-")
        if not _synthetic_refs(row.get("synthetic_evidence_refs")):
            problems.append(f"{prefix}.synthetic_evidence_refs must contain only synthetic or fixture refs")
        if not _string_sequence(row.get("affected_predicate_keys")):
            problems.append(f"{prefix}.affected_predicate_keys must be a non-empty list")
    _validate_no_forbidden_payload(packet, problems)
    return problems


def assert_valid_inactive_guardrail_recompile_impact_plan_v1(packet: Mapping[str, Any]) -> None:
    result = validate_inactive_guardrail_recompile_impact_plan_v1(packet)
    if not result.valid:
        raise InactiveGuardrailRecompileImpactPlanV1Error(result.problems)


def validate_inactive_guardrail_recompile_impact_plan_v1(packet: Mapping[str, Any]) -> InactiveGuardrailRecompileImpactPlanV1Result:
    if not isinstance(packet, Mapping):
        return InactiveGuardrailRecompileImpactPlanV1Result(False, ("plan must be an object",))
    problems: list[str] = []
    if packet.get("plan_type") != PLAN_TYPE:
        problems.append(f"plan_type must be {PLAN_TYPE}")
    if packet.get("plan_version") != PLAN_VERSION:
        problems.append("plan_version must be v1")
    if packet.get("fixture_first") is not True:
        problems.append("fixture_first must be true")
    if packet.get("impact_mode") != "inactive_guardrail_bundle_patch_placeholders_only":
        problems.append("impact_mode must be inactive_guardrail_bundle_patch_placeholders_only")
    if packet.get("input_policy") != "synthetic_inactive_process_model_delta_assembly_rows_only":
        problems.append("input_policy must be synthetic_inactive_process_model_delta_assembly_rows_only")
    if packet.get("offline_validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("offline_validation_commands must exactly match the offline validation command bundle")
    if packet.get("validation_commands") != EXACT_OFFLINE_VALIDATION_COMMANDS:
        problems.append("validation_commands must exactly match the offline validation command bundle")
    for flag in FALSE_GUARDRAIL_FLAGS:
        if packet.get(flag) is not False:
            problems.append(f"{flag} must be false")
    for section in REQUIRED_PLAN_SECTIONS:
        if not _mapping_sequence(packet.get(section)):
            problems.append(f"{section} must be a non-empty list of objects")
    source_ids = {_text(row.get("row_id")) for row in _mapping_sequence(packet.get("source_delta_rows"))}
    for section in REQUIRED_PLAN_SECTIONS[1:]:
        for index, row in enumerate(_mapping_sequence(packet.get(section))):
            prefix = f"{section}[{index}]"
            row_ref = _text(row.get("source_delta_row_ref"))
            if row_ref not in source_ids:
                problems.append(f"{prefix}.source_delta_row_ref must reference source_delta_rows")
            status = _text(row.get("status"))
            if not status.endswith("placeholder") and status not in {"reviewer_hold_active", "rollback_note_only"}:
                problems.append(f"{prefix}.status must remain a placeholder, reviewer hold, or rollback note")
    for placeholder in _mapping_sequence(packet.get("inactive_guardrail_bundle_patch_placeholders")):
        if placeholder.get("activation_allowed") is not False:
            problems.append("inactive_guardrail_bundle_patch_placeholders.activation_allowed must be false")
        if placeholder.get("recompile_allowed") is not False:
            problems.append("inactive_guardrail_bundle_patch_placeholders.recompile_allowed must be false")
    _validate_no_forbidden_payload(packet, problems)
    return InactiveGuardrailRecompileImpactPlanV1Result(not problems, tuple(problems))


def _normalize_source_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "row_id": _text(row.get("row_id")),
        "process_id": _text(row.get("process_id")),
        "permit_type": _text(row.get("permit_type")),
        "process_stage": _text(row.get("process_stage")),
        "inactive_guardrail_bundle_id": _text(row.get("inactive_guardrail_bundle_id")),
        "delta_kind": _text(row.get("delta_kind")),
        "synthetic_evidence_refs": _string_sequence(row.get("synthetic_evidence_refs")),
        "affected_predicate_keys": _string_sequence(row.get("affected_predicate_keys")),
        "impact_notes": _string_sequence(row.get("impact_notes")),
        "status": "synthetic_inactive_delta_row_consumed",
    }


def _patch_placeholder(row: Mapping[str, Any]) -> dict[str, Any]:
    row_id = _text(row.get("row_id"))
    return {
        "patch_placeholder_id": f"inactive-guardrail-bundle-patch-placeholder-{row_id}",
        "source_delta_row_ref": row_id,
        "process_id": _text(row.get("process_id")),
        "inactive_guardrail_bundle_id": _text(row.get("inactive_guardrail_bundle_id")),
        "patch_scope": "placeholder_only_no_active_guardrail_recompile",
        "predicate_keys": _string_sequence(row.get("affected_predicate_keys")),
        "activation_allowed": False,
        "recompile_allowed": False,
        "status": "inactive_guardrail_bundle_patch_placeholder",
    }


def _impact(row: Mapping[str, Any], family: str, status: str) -> dict[str, Any]:
    row_id = _text(row.get("row_id"))
    safe_family = family.replace("-", "_")
    return {
        "impact_id": f"{safe_family}-impact-{row_id}",
        "source_delta_row_ref": row_id,
        "impact_family": family,
        "process_stage": _text(row.get("process_stage")),
        "predicate_keys": _string_sequence(row.get("affected_predicate_keys")),
        "impact_summary": f"Record inactive {family} impact placeholder for reviewer assessment only.",
        "status": status,
    }


def _explanation_impact(row: Mapping[str, Any]) -> dict[str, Any]:
    row_id = _text(row.get("row_id"))
    return {
        "impact_id": f"agent-facing-explanation-impact-{row_id}",
        "source_delta_row_ref": row_id,
        "template_key": f"inactive_guardrail_recompile_impact_{row_id}",
        "explanation_summary": "Agent-facing copy must explain that the row is synthetic, inactive, reviewer-held, and not authority to take official action.",
        "status": "agent_facing_explanation_impact_placeholder",
    }


def _reviewer_hold(row: Mapping[str, Any]) -> dict[str, Any]:
    row_id = _text(row.get("row_id"))
    return {
        "reviewer_hold_id": f"reviewer-hold-{row_id}",
        "source_delta_row_ref": row_id,
        "hold_reason": "Synthetic inactive process-model delta row requires human review before any active guardrail work is considered.",
        "release_condition": "Reviewer disposition plus exact offline validation commands; no live crawl or DevHub access.",
        "status": "reviewer_hold_active",
    }


def _rollback_note(row: Mapping[str, Any]) -> dict[str, Any]:
    row_id = _text(row.get("row_id"))
    return {
        "rollback_note_id": f"rollback-note-{row_id}",
        "source_delta_row_ref": row_id,
        "rollback_summary": "Discard the inactive impact placeholders for this synthetic row and leave active guardrails unchanged.",
        "verification_note": "Confirm no active guardrail bundle, prompt, release state, or DevHub surface artifact was changed.",
        "status": "rollback_note_only",
    }


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_sequence(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [_text(item) for item in value if _text(item)]


def _synthetic_refs(value: Any) -> bool:
    refs = _string_sequence(value)
    return bool(refs) and all(ref.startswith(("synthetic:", "fixture-source:")) for ref in refs)


def _text(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        return value.strip()
    if value is None:
        return default
    return str(value).strip()


def _validate_no_forbidden_payload(value: Any, problems: list[str], path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = _text(key)
            lowered_key = key_text.lower()
            if lowered_key in {"auth_state", "browser_state", "cookie", "credential", "raw_crawl_output", "private_artifact_path"}:
                problems.append(f"forbidden private or live artifact key at {path}.{key_text}")
            _validate_no_forbidden_payload(child, problems, f"{path}.{key_text}")
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            _validate_no_forbidden_payload(child, problems, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        for term in FORBIDDEN_TEXT:
            if term in lowered:
                problems.append(f"forbidden payload term at {path}: {term}")
