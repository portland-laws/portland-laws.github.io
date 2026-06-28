"""Fixture-first inactive GuardrailBundle recompile candidate v5.

This module consumes committed process model impact candidate v5 fixtures and
proposes inactive GuardrailBundle predicate deltas only. It does not mutate
active guardrails, open DevHub, read private documents, upload, submit, certify,
pay, schedule, or make legal/permitting guarantees.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
from typing import Any

PACKET_VERSION = "guardrail_bundle_recompile_candidate_v5"
SOURCE_MODE = "fixture_only_process_model_impact_candidate_v5"
PROCESS_MODEL_IMPACT_VERSION = "process_model_impact_candidate_v5"

REQUIRED_FIXTURE_KEYS = {
    "process_model_impact_candidate_v5",
    "prior_guardrail_bundle_placeholders",
}

REQUIRED_DELTA_SECTIONS = (
    "deterministic_predicate_deltas",
    "deontic_rule_deltas",
    "temporal_rule_deltas",
    "reversible_action_predicate_deltas",
    "exact_confirmation_predicate_deltas",
    "refused_action_predicate_deltas",
    "stale_evidence_blocks",
    "explanation_template_deltas",
    "source_evidence_references",
)

ALLOWED_IMPACT_AREAS = {
    "eligibility_rules",
    "required_facts",
    "required_documents",
    "file_rules",
    "fees",
    "deadlines",
    "unsupported_paths",
    "devhub_surface_refs",
}

ALLOWED_OPERATIONS = {"add", "change", "remove", "hold"}
ALLOWED_REVIEWER_HOLDS = {
    "needs_guardrail_reviewer",
    "needs_source_review",
    "needs_process_owner_review",
    "needs_temporal_review",
    "needs_rollback_review",
}

DEFAULT_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/guardrail_bundle_recompile_candidate_v5.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_guardrail_bundle_recompile_candidate_v5.py"],
    ["python3", "-m", "unittest", "ppd.tests.test_guardrail_bundle_recompile_candidate_v5"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

FORBIDDEN_MUTATION_TARGETS = {
    "active_guardrails",
    "active_guardrail_bundles",
    "active_process_models",
    "active_requirements",
    "active_devhub_surfaces",
    "release_state",
    "type_script_logic_daemon_ledgers",
}

PRIVATE_OR_LIVE_KEY_TOKENS = (
    "auth",
    "browser",
    "cookie",
    "credential",
    "download",
    "har",
    "password",
    "payment",
    "private",
    "session",
    "screenshot",
    "storage_state",
    "trace",
    "upload",
)

ACTIVE_MUTATION_FLAG_TOKENS = (
    "active_guardrails_mutated",
    "active_guardrail_bundles_mutated",
    "active_mutation",
    "mutates_active",
    "promote_to_active",
)

FORBIDDEN_VALUE_TOKENS = (
    "approval guaranteed",
    "certified submission",
    "completed official action",
    "downloaded document",
    "final payment",
    "guaranteed approval",
    "legal advice",
    "opened devhub",
    "permit will be approved",
    "permit will issue",
    "raw crawl output",
    "scheduled inspection",
    "submitted form",
)


def load_fixture(path: str | Path) -> dict[str, Any]:
    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("fixture must be a JSON object")
    return payload


def build_guardrail_bundle_recompile_candidate_v5(
    fixture: Mapping[str, Any],
    *,
    packet_id: str = "guardrail-bundle-recompile-candidate-v5-fixture",
    generated_at: str = "2026-06-01T00:00:00Z",
) -> dict[str, Any]:
    """Build an inactive guardrail recompile candidate from v5 process fixtures."""

    _validate_fixture_shape(fixture)
    impact_packet = _impact_packet(fixture)
    placeholders = _placeholder_map(fixture["prior_guardrail_bundle_placeholders"])

    candidate_deltas: list[dict[str, Any]] = []
    reviewer_holds: list[dict[str, Any]] = []
    rollback_notes: list[dict[str, Any]] = []

    for index, change_value in enumerate(impact_packet["inactive_changes"], start=1):
        change = _normalized_impact_change(index, change_value)
        guardrail_bundle_id = change["guardrail_bundle_id"]
        if guardrail_bundle_id not in placeholders:
            raise ValueError(f"impact change {change['change_id']} references unknown guardrail_bundle_id")
        placeholder = placeholders[guardrail_bundle_id]
        delta = _guardrail_delta(index, change, placeholder)
        candidate_deltas.append(delta)
        reviewer_holds.append(_reviewer_hold(delta, change))
        rollback_notes.append(_rollback_note(delta, change))

    packet = {
        "packet_version": PACKET_VERSION,
        "packet_id": packet_id,
        "generated_at": generated_at,
        "source_mode": SOURCE_MODE,
        "status": "inactive_candidate",
        "fixture_first": True,
        "input_fixture_refs": {
            "fixture_id": fixture.get("fixture_id", "inline_fixture"),
            "process_model_impact_candidate_v5": impact_packet.get("packet_id", "inline_process_model_impact_candidate_v5"),
            "prior_guardrail_bundle_placeholders": sorted(placeholders),
        },
        "side_effects": {
            "active_guardrails_mutated": False,
            "active_guardrail_bundles_mutated": False,
            "active_process_models_mutated": False,
            "active_requirements_mutated": False,
            "active_devhub_surfaces_mutated": False,
            "devhub_opened": False,
            "private_documents_read": False,
            "documents_downloaded": False,
            "uploads_performed": False,
            "forms_submitted": False,
            "certifications_performed": False,
            "fees_paid": False,
            "inspections_scheduled": False,
            "official_actions_completed": False,
        },
        "forbidden_mutation_targets": sorted(FORBIDDEN_MUTATION_TARGETS),
        "inactive_guardrail_bundle_deltas": candidate_deltas,
        "reviewer_holds": reviewer_holds,
        "rollback_notes": rollback_notes,
        "exact_offline_validation_commands": deepcopy(DEFAULT_VALIDATION_COMMANDS),
        "limitations": [
            "candidate packet only",
            "requires human review before any separate activation proposal",
            "does not determine permit eligibility or approval outcome",
            "does not complete official PP&D or DevHub actions",
        ],
    }
    validate_guardrail_bundle_recompile_candidate_v5(packet)
    return packet


def validate_guardrail_bundle_recompile_candidate_v5(packet: Mapping[str, Any]) -> None:
    _require(packet.get("packet_version") == PACKET_VERSION, "unexpected packet_version")
    _require(packet.get("source_mode") == SOURCE_MODE, "packet must use process model impact candidate v5 fixtures")
    _require(packet.get("status") == "inactive_candidate", "status must be inactive_candidate")
    _require(packet.get("fixture_first") is True, "packet must be fixture_first")

    refs = packet.get("input_fixture_refs")
    _require(isinstance(refs, Mapping), "input_fixture_refs must be an object")
    _require(_text(refs.get("process_model_impact_candidate_v5")), "missing process model impact fixture reference")
    _require(_string_sequence(refs.get("prior_guardrail_bundle_placeholders")), "missing guardrail placeholder references")

    side_effects = packet.get("side_effects")
    _require(isinstance(side_effects, Mapping), "side_effects must be an object")
    for key, value in side_effects.items():
        _require(value is False, f"side_effects.{key} must be false")

    forbidden_targets = set(packet.get("forbidden_mutation_targets", []))
    _require(FORBIDDEN_MUTATION_TARGETS.issubset(forbidden_targets), "missing forbidden mutation target")

    deltas = packet.get("inactive_guardrail_bundle_deltas")
    _require(isinstance(deltas, list) and deltas, "inactive_guardrail_bundle_deltas must be non-empty")
    seen_delta_ids: set[str] = set()
    for index, value in enumerate(deltas):
        _validate_delta(index, value, seen_delta_ids)

    _validate_reviewer_holds(packet.get("reviewer_holds"), seen_delta_ids)
    _validate_rollback_notes(packet.get("rollback_notes"), seen_delta_ids)
    _validate_commands(packet.get("exact_offline_validation_commands"))
    _validate_no_forbidden_payload(packet)


def _validate_fixture_shape(fixture: Mapping[str, Any]) -> None:
    missing = REQUIRED_FIXTURE_KEYS.difference(fixture)
    _require(not missing, f"fixture missing keys: {sorted(missing)}")
    impact = fixture["process_model_impact_candidate_v5"]
    placeholders = fixture["prior_guardrail_bundle_placeholders"]
    _require(isinstance(impact, Mapping), "process_model_impact_candidate_v5 must be an object")
    _require(isinstance(placeholders, list) and placeholders, "prior_guardrail_bundle_placeholders must be non-empty")


def _impact_packet(fixture: Mapping[str, Any]) -> Mapping[str, Any]:
    packet = fixture["process_model_impact_candidate_v5"]
    _require(packet.get("packet_version") == PROCESS_MODEL_IMPACT_VERSION, "process fixture must be v5")
    _require(packet.get("status") == "inactive_candidate", "process fixture must be inactive_candidate")
    _require(packet.get("fixture_first") is True, "process fixture must be fixture_first")
    changes = packet.get("inactive_changes")
    _require(isinstance(changes, list) and changes, "process fixture inactive_changes must be non-empty")
    for key, value in _mapping(packet.get("side_effects")).items():
        _require(value is False, f"process fixture side_effects.{key} must be false")
    return packet


def _placeholder_map(placeholders: Sequence[Any]) -> dict[str, dict[str, Any]]:
    mapped: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(placeholders):
        _require(isinstance(value, Mapping), f"prior_guardrail_bundle_placeholders[{index}] must be an object")
        bundle_id = _text(value.get("guardrail_bundle_id"))
        _require(bundle_id, f"placeholder {index} missing guardrail_bundle_id")
        _require(bundle_id not in mapped, f"duplicate guardrail_bundle_id: {bundle_id}")
        _require(value.get("placeholder_only") is True, f"placeholder {bundle_id} must be placeholder_only")
        _require(value.get("active_bundle_ref") in {None, ""}, f"placeholder {bundle_id} must not reference an active bundle")
        mapped[bundle_id] = dict(value)
    return mapped


def _normalized_impact_change(index: int, value: Any) -> dict[str, Any]:
    _require(isinstance(value, Mapping), f"inactive_changes[{index}] must be an object")
    change = dict(value)
    required = {
        "change_id",
        "process_model_id",
        "guardrail_bundle_id",
        "impact_area",
        "operation",
        "requirement_id",
        "candidate_text",
        "source_evidence_ids",
    }
    missing = required.difference(change)
    _require(not missing, f"impact change {index} missing keys: {sorted(missing)}")
    _require(_text(change["change_id"]).startswith("inactive-pm-impact-v5-"), f"invalid impact change_id at row {index}")
    _require(_text(change["process_model_id"]), f"impact change {index} missing process_model_id")
    _require(_text(change["guardrail_bundle_id"]), f"impact change {index} missing guardrail_bundle_id")
    _require(change["impact_area"] in ALLOWED_IMPACT_AREAS, f"impact change {index} has unsupported impact_area")
    _require(change["operation"] in ALLOWED_OPERATIONS, f"impact change {index} has unsupported operation")
    _require(_text(change["requirement_id"]), f"impact change {index} missing requirement_id")
    _require(_text(change["candidate_text"]), f"impact change {index} missing candidate_text")
    _require(_string_sequence(change["source_evidence_ids"]), f"impact change {index} missing source_evidence_ids")
    return change


def _guardrail_delta(index: int, change: Mapping[str, Any], placeholder: Mapping[str, Any]) -> dict[str, Any]:
    suffix = _text(change["change_id"]).removeprefix("inactive-pm-impact-v5-")
    delta_id = f"inactive-guardrail-recompile-v5-{suffix}"
    bundle_id = _text(change["guardrail_bundle_id"])
    process_id = _text(placeholder.get("process_id")) or _text(change["process_model_id"])
    evidence_ids = _string_sequence(change["source_evidence_ids"])
    requirement_id = _text(change["requirement_id"])
    impact_area = _text(change["impact_area"])
    operation = _text(change["operation"])

    return {
        "delta_id": delta_id,
        "status": "inactive_candidate",
        "guardrail_bundle_id": bundle_id,
        "prior_guardrail_bundle_placeholder_ref": bundle_id,
        "process_id": process_id,
        "process_model_impact_change_id": change["change_id"],
        "requirement_id": requirement_id,
        "impact_area": impact_area,
        "operation": operation,
        "activation_policy": "do_not_apply_without_human_review_and_separate_activation",
        "active_guardrail_bundle_mutation": False,
        "deterministic_predicate_deltas": [
            _predicate_delta("deterministic", delta_id, requirement_id, impact_area, operation, evidence_ids)
        ],
        "deontic_rule_deltas": [_predicate_delta("deontic", delta_id, requirement_id, impact_area, operation, evidence_ids)],
        "temporal_rule_deltas": [_predicate_delta("temporal", delta_id, requirement_id, impact_area, operation, evidence_ids)],
        "reversible_action_predicate_deltas": [
            _predicate_delta("reversible_action", delta_id, requirement_id, impact_area, operation, evidence_ids)
        ],
        "exact_confirmation_predicate_deltas": [
            _predicate_delta("exact_confirmation", delta_id, requirement_id, impact_area, operation, evidence_ids)
        ],
        "refused_action_predicate_deltas": [
            _predicate_delta("refused_action", delta_id, requirement_id, impact_area, operation, evidence_ids)
        ],
        "stale_evidence_blocks": [
            {
                "block_id": f"stale-evidence::{delta_id}",
                "requirement_id": requirement_id,
                "source_evidence_ids": evidence_ids,
                "block_condition": "block_activation_when_cited_source_is_stale_missing_ambiguous_or_conflicting",
                "review_status": "pending_source_reviewer",
            }
        ],
        "explanation_template_deltas": [
            {
                "template_id": f"explain::{delta_id}",
                "requirement_id": requirement_id,
                "template_status": "inactive_candidate",
                "template": "This guardrail candidate is based on cited PP&D fixture evidence and remains inactive until reviewer approval.",
                "source_evidence_ids": evidence_ids,
            }
        ],
        "source_evidence_references": [
            {
                "reference_id": f"source-ref::{delta_id}::{evidence_index:02d}",
                "source_evidence_id": evidence_id,
                "requirement_id": requirement_id,
                "usage": "guardrail_recompile_candidate_v5_fixture_evidence",
            }
            for evidence_index, evidence_id in enumerate(evidence_ids, start=1)
        ],
    }


def _predicate_delta(
    predicate_kind: str,
    delta_id: str,
    requirement_id: str,
    impact_area: str,
    operation: str,
    evidence_ids: Sequence[str],
) -> dict[str, Any]:
    return {
        "predicate_delta_id": f"{predicate_kind}::{delta_id}",
        "predicate_kind": predicate_kind,
        "requirement_id": requirement_id,
        "impact_area": impact_area,
        "operation": operation,
        "status": "inactive_candidate",
        "source_evidence_ids": list(evidence_ids),
        "proposed_effect": "review_only_no_active_guardrail_change",
    }


def _reviewer_hold(delta: Mapping[str, Any], change: Mapping[str, Any]) -> dict[str, Any]:
    hold_reason = _text(change.get("reviewer_hold")) or "needs_guardrail_reviewer"
    _require(hold_reason in ALLOWED_REVIEWER_HOLDS, f"delta {delta['delta_id']} has unsupported reviewer_hold")
    return {
        "delta_id": delta["delta_id"],
        "status": "held_for_review",
        "hold_reason": hold_reason,
        "reviewer": "unassigned",
        "notes": "Review predicate deltas, cited evidence, stale-evidence block, and rollback note before any separate activation proposal.",
    }


def _rollback_note(delta: Mapping[str, Any], change: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "delta_id": delta["delta_id"],
        "rollback_scope": "inactive_candidate_only",
        "rollback_note": _text(change.get("rollback_note"))
        or "Discard this inactive guardrail recompile candidate row; active GuardrailBundle state is unchanged.",
    }


def _validate_delta(index: int, value: Any, seen_delta_ids: set[str]) -> None:
    _require(isinstance(value, Mapping), f"inactive_guardrail_bundle_deltas[{index}] must be an object")
    delta_id = _text(value.get("delta_id"))
    _require(delta_id.startswith("inactive-guardrail-recompile-v5-"), f"invalid delta_id at row {index}")
    _require(delta_id not in seen_delta_ids, f"duplicate delta_id: {delta_id}")
    seen_delta_ids.add(delta_id)
    _require(value.get("status") == "inactive_candidate", f"{delta_id} must be inactive_candidate")
    _require(value.get("activation_policy") == "do_not_apply_without_human_review_and_separate_activation", f"{delta_id} has unsafe activation_policy")
    _require(value.get("active_guardrail_bundle_mutation") is False, f"{delta_id} must not mutate active guardrail bundles")
    _require(_text(value.get("guardrail_bundle_id")), f"{delta_id} missing guardrail_bundle_id")
    _require(_text(value.get("prior_guardrail_bundle_placeholder_ref")) == _text(value.get("guardrail_bundle_id")), f"{delta_id} missing prior placeholder reference")
    _require(_text(value.get("process_model_impact_change_id")).startswith("inactive-pm-impact-v5-"), f"{delta_id} missing process impact reference")
    _require(value.get("impact_area") in ALLOWED_IMPACT_AREAS, f"{delta_id} has unsupported impact_area")
    _require(value.get("operation") in ALLOWED_OPERATIONS, f"{delta_id} has unsupported operation")
    for section in REQUIRED_DELTA_SECTIONS:
        rows = value.get(section)
        _require(isinstance(rows, list) and rows, f"{delta_id} missing {section}")
        for row_index, row in enumerate(rows):
            _require(isinstance(row, Mapping), f"{delta_id}.{section}[{row_index}] must be an object")
            _require(_string_sequence(row.get("source_evidence_ids")) or _text(row.get("source_evidence_id")), f"{delta_id}.{section}[{row_index}] missing source evidence")


def _validate_reviewer_holds(value: Any, delta_ids: set[str]) -> None:
    _require(isinstance(value, list) and value, "reviewer_holds must be non-empty")
    hold_delta_ids = set()
    for index, hold in enumerate(value):
        _require(isinstance(hold, Mapping), f"reviewer_holds[{index}] must be an object")
        delta_id = _text(hold.get("delta_id"))
        _require(delta_id in delta_ids, f"reviewer hold references unknown delta_id: {delta_id}")
        _require(hold.get("status") == "held_for_review", f"reviewer hold {delta_id} must be held_for_review")
        _require(hold.get("hold_reason") in ALLOWED_REVIEWER_HOLDS, f"reviewer hold {delta_id} has unsupported hold_reason")
        _require(hold.get("reviewer") == "unassigned", f"reviewer hold {delta_id} must remain unassigned")
        hold_delta_ids.add(delta_id)
    _require(hold_delta_ids == delta_ids, "each inactive delta must have a reviewer hold")


def _validate_rollback_notes(value: Any, delta_ids: set[str]) -> None:
    _require(isinstance(value, list) and value, "rollback_notes must be non-empty")
    rollback_delta_ids = set()
    for index, note in enumerate(value):
        _require(isinstance(note, Mapping), f"rollback_notes[{index}] must be an object")
        delta_id = _text(note.get("delta_id"))
        _require(delta_id in delta_ids, f"rollback note references unknown delta_id: {delta_id}")
        _require(note.get("rollback_scope") == "inactive_candidate_only", f"rollback note {delta_id} has unsafe scope")
        _require(_text(note.get("rollback_note")), f"rollback note {delta_id} missing text")
        rollback_delta_ids.add(delta_id)
    _require(rollback_delta_ids == delta_ids, "each inactive delta must have a rollback note")


def _validate_commands(commands: Any) -> None:
    _require(isinstance(commands, list) and commands, "exact_offline_validation_commands must be non-empty")
    required = {tuple(command) for command in DEFAULT_VALIDATION_COMMANDS}
    actual = set()
    for command in commands:
        _require(isinstance(command, list) and command, "each validation command must be an argv list")
        _require(all(isinstance(part, str) and part for part in command), "validation command parts must be non-empty strings")
        actual.add(tuple(command))
    _require(required.issubset(actual), "missing validation commands")


def _validate_no_forbidden_payload(value: Any) -> None:
    for path, key, child in _walk(value):
        normalized_key = key.lower().replace("-", "_")
        if any(token in normalized_key for token in PRIVATE_OR_LIVE_KEY_TOKENS):
            _require(child is False or child in {None, ""}, f"{path} must not include private, live, financial, upload, or browser artifacts")
        if any(token in normalized_key for token in ACTIVE_MUTATION_FLAG_TOKENS):
            _require(child is False or child in {None, ""}, f"{path} must not include active mutation flags")
        if isinstance(child, str):
            text = child.lower()
            _require(not any(token in text for token in FORBIDDEN_VALUE_TOKENS), f"{path} contains forbidden live-action or guarantee text")


def _walk(value: Any, prefix: str = "packet", key: str = "packet") -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            child_path = f"{prefix}.{child_key_text}"
            rows.append((child_path, child_key_text, child_value))
            rows.extend(_walk(child_value, child_path, child_key_text))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child_value in enumerate(value):
            child_path = f"{prefix}[{index}]"
            rows.append((child_path, key, child_value))
            rows.extend(_walk(child_value, child_path, key))
    return rows


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string_sequence(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    rows = [item for item in value if isinstance(item, str) and item]
    return rows if len(rows) == len(value) else []


def _text(value: Any) -> str:
    return value if isinstance(value, str) else ""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and validate a fixture-first inactive GuardrailBundle recompile candidate v5 packet")
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    packet = build_guardrail_bundle_recompile_candidate_v5(load_fixture(args.fixture))
    if args.output:
        args.output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        print(json.dumps(packet, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
