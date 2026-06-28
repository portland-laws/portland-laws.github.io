"""Fixture-first guardrail recompilation rehearsal packet assembly.

This module turns reviewed synthetic requirement candidates and existing
process-model fixtures into a cited, disabled rehearsal packet. The packet is
intended for reviewer rehearsal only: it records predicate-diff candidates,
affected processes, blocked-action expectations, exact-confirmation checkpoints,
and manual-handoff notes without compiling or promoting active guardrail bundles.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


_REVIEWED_STATUSES = {
    "reviewed",
    "reviewed_synthetic",
    "accepted_for_rehearsal",
    "human_reviewed",
}

_STAGE_ACTIONS = {
    "acknowledgment_certification_review": "certify acknowledgement",
    "certification_review": "certify acknowledgement",
    "submission": "submit permit request",
    "upload_staging": "upload permit documents",
    "fee_payment": "submit payment",
    "corrections_checksheets": "upload corrections",
    "inspection_scheduling": "schedule inspection",
}

_ACTION_GATE_PHRASES = {
    "attach": "upload permit documents",
    "upload": "upload permit documents",
    "submit": "submit permit request",
    "certif": "certify acknowledgement",
    "payment": "submit payment",
    "pay": "submit payment",
    "schedule": "schedule inspection",
    "cancel": "cancel permit request",
}

_BLOCKED_ACTIONS = {
    "cancel permit request",
    "certify acknowledgement",
    "schedule inspection",
    "submit payment",
    "submit permit request",
    "upload corrections",
    "upload permit documents",
}

_PROHIBITED_ACTIVE_KEYS = {
    "active_guardrail_bundle_patch",
    "compiled_guardrail_bundle",
    "guardrail_bundle_promotion",
    "promoted_guardrail_bundle",
    "replacement_guardrail_bundle",
}


@dataclass(frozen=True)
class GuardrailRecompilationPacketFinding:
    code: str
    path: str
    message: str


class GuardrailRecompilationPacketError(ValueError):
    """Raised when a fixture-first rehearsal packet is malformed."""


def build_guardrail_recompilation_rehearsal_packet(
    reviewed_requirement_candidate_packet: Mapping[str, Any],
    process_model_fixtures: Sequence[Mapping[str, Any]],
    *,
    active_guardrail_bundle_id: str = "active-guardrail-bundle-retained",
    active_guardrail_bundle_revision: str = "active-revision-retained",
) -> dict[str, Any]:
    """Build a disabled rehearsal packet from reviewed candidates and fixtures."""

    if not isinstance(reviewed_requirement_candidate_packet, Mapping):
        raise GuardrailRecompilationPacketError("reviewed requirement candidate packet must be an object")
    if not isinstance(process_model_fixtures, Sequence) or isinstance(process_model_fixtures, (str, bytes)):
        raise GuardrailRecompilationPacketError("process model fixtures must be a sequence")

    process_index = _process_index(process_model_fixtures)
    if not process_index:
        raise GuardrailRecompilationPacketError("at least one process model fixture is required")

    candidates = _reviewed_candidates(reviewed_requirement_candidate_packet)
    if not candidates:
        raise GuardrailRecompilationPacketError("at least one reviewed synthetic requirement candidate is required")

    affected_process_ids = sorted(
        process_id
        for candidate in candidates
        for process_id in _candidate_process_ids(candidate, process_index)
    )
    if not affected_process_ids:
        affected_process_ids = sorted(process_index)

    predicate_diff_candidates = _predicate_diff_candidates(candidates, process_index, affected_process_ids)
    blocked_action_expectations = _blocked_action_expectations(predicate_diff_candidates, process_index)
    exact_confirmation_checkpoints = _exact_confirmation_checkpoints(blocked_action_expectations)
    manual_handoff_notes = _manual_handoff_notes(blocked_action_expectations, predicate_diff_candidates)

    basis = {
        "source_packet_id": _text(reviewed_requirement_candidate_packet.get("packet_id")) or _text(reviewed_requirement_candidate_packet.get("candidate_id")),
        "active_guardrail_bundle_id": active_guardrail_bundle_id,
        "active_guardrail_bundle_revision": active_guardrail_bundle_revision,
        "affected_process_ids": affected_process_ids,
        "predicate_diff_candidates": predicate_diff_candidates,
        "blocked_action_expectations": blocked_action_expectations,
        "exact_confirmation_checkpoints": exact_confirmation_checkpoints,
    }

    packet = {
        "packet_type": "fixture_first_guardrail_recompilation_rehearsal_packet",
        "packet_id": "fixture-first-guardrail-rehearsal-" + _stable_hash(basis),
        "packet_mode": "fixture_first_rehearsal_only",
        "candidate_status": "draft_requires_human_review",
        "source_requirement_candidate_packet_id": basis["source_packet_id"] or "reviewed-requirement-candidates",
        "source_process_model_fixture_ids": sorted(process_index),
        "affected_process_ids": affected_process_ids,
        "active_guardrail_bundle_id": active_guardrail_bundle_id,
        "active_guardrail_bundle_revision": active_guardrail_bundle_revision,
        "predicate_diff_candidates": predicate_diff_candidates,
        "blocked_action_expectations": blocked_action_expectations,
        "exact_confirmation_checkpoints": exact_confirmation_checkpoints,
        "manual_handoff_notes": manual_handoff_notes,
        "activation_state": {
            "compile_attempted": False,
            "active_bundle_promoted": False,
            "active_bundle_mutated": False,
            "promotion_target": "none",
            "rehearsal_only": True,
            "requires_human_review_before_activation": True,
        },
    }

    findings = validate_guardrail_recompilation_rehearsal_packet(packet)
    if findings:
        detail = "; ".join(f"{item.code} at {item.path}: {item.message}" for item in findings)
        raise GuardrailRecompilationPacketError("invalid guardrail recompilation rehearsal packet: " + detail)
    return packet


def validate_guardrail_recompilation_rehearsal_packet(packet: Mapping[str, Any]) -> list[GuardrailRecompilationPacketFinding]:
    """Return validation findings for a disabled rehearsal packet."""

    if not isinstance(packet, Mapping):
        return [GuardrailRecompilationPacketFinding("invalid_packet", "$", "Packet must be an object.")]

    findings: list[GuardrailRecompilationPacketFinding] = []
    if packet.get("packet_type") != "fixture_first_guardrail_recompilation_rehearsal_packet":
        findings.append(GuardrailRecompilationPacketFinding("invalid_packet_type", "$.packet_type", "Packet type must be fixture_first_guardrail_recompilation_rehearsal_packet."))
    if packet.get("packet_mode") != "fixture_first_rehearsal_only":
        findings.append(GuardrailRecompilationPacketFinding("not_rehearsal_only", "$.packet_mode", "Packet must stay fixture-first and rehearsal-only."))

    activation = packet.get("activation_state")
    if not isinstance(activation, Mapping):
        findings.append(GuardrailRecompilationPacketFinding("missing_activation_state", "$.activation_state", "Activation state is required."))
    else:
        expected_false = ("compile_attempted", "active_bundle_promoted", "active_bundle_mutated")
        for key in expected_false:
            if activation.get(key) is not False:
                findings.append(GuardrailRecompilationPacketFinding("unsafe_activation_state", f"$.activation_state.{key}", f"{key} must be false."))
        if activation.get("promotion_target") != "none":
            findings.append(GuardrailRecompilationPacketFinding("promotion_target_enabled", "$.activation_state.promotion_target", "Promotion target must be none."))
        if activation.get("rehearsal_only") is not True:
            findings.append(GuardrailRecompilationPacketFinding("not_rehearsal_only", "$.activation_state.rehearsal_only", "Rehearsal-only flag must be true."))

    affected_process_ids = set(_strings(packet.get("affected_process_ids")))
    if not affected_process_ids:
        findings.append(GuardrailRecompilationPacketFinding("missing_affected_process_ids", "$.affected_process_ids", "At least one affected process ID is required."))

    predicate_diffs = _mapping_list(packet.get("predicate_diff_candidates"))
    if not predicate_diffs:
        findings.append(GuardrailRecompilationPacketFinding("missing_predicate_diff_candidates", "$.predicate_diff_candidates", "Predicate-diff candidates are required."))
    for index, diff in enumerate(predicate_diffs):
        path = f"$.predicate_diff_candidates[{index}]"
        if not _text(diff.get("predicate_diff_id")):
            findings.append(GuardrailRecompilationPacketFinding("missing_predicate_diff_id", f"{path}.predicate_diff_id", "Predicate diff must have an ID."))
        if not _strings(diff.get("source_evidence_ids")):
            findings.append(GuardrailRecompilationPacketFinding("uncited_predicate_diff", f"{path}.source_evidence_ids", "Predicate diff must cite source evidence."))
        if diff.get("activation_allowed") is not False:
            findings.append(GuardrailRecompilationPacketFinding("predicate_activation_allowed", f"{path}.activation_allowed", "Predicate diff activation must be false."))
        diff_process_ids = set(_strings(diff.get("affected_process_ids")))
        if not diff_process_ids:
            findings.append(GuardrailRecompilationPacketFinding("missing_predicate_process_ids", f"{path}.affected_process_ids", "Predicate diff must name affected process IDs."))
        elif not diff_process_ids.issubset(affected_process_ids):
            findings.append(GuardrailRecompilationPacketFinding("unknown_predicate_process_id", f"{path}.affected_process_ids", "Predicate diff references a process outside affected_process_ids."))

    blocked_actions = _mapping_list(packet.get("blocked_action_expectations"))
    if not blocked_actions:
        findings.append(GuardrailRecompilationPacketFinding("missing_blocked_action_expectations", "$.blocked_action_expectations", "Blocked-action expectations are required."))
    blocked_action_names = {_text(item.get("action")) for item in blocked_actions if _text(item.get("action"))}
    for index, item in enumerate(blocked_actions):
        path = f"$.blocked_action_expectations[{index}]"
        if item.get("expected_decision") != "block_until_attended_exact_confirmation":
            findings.append(GuardrailRecompilationPacketFinding("invalid_blocked_action_expectation", f"{path}.expected_decision", "Consequential actions must block until attended exact confirmation."))
        if not _strings(item.get("source_predicate_diff_ids")):
            findings.append(GuardrailRecompilationPacketFinding("uncited_blocked_action", f"{path}.source_predicate_diff_ids", "Blocked action must cite predicate diffs."))

    checkpoints = _mapping_list(packet.get("exact_confirmation_checkpoints"))
    checkpoint_actions = {_text(item.get("action")) for item in checkpoints if _text(item.get("action"))}
    if blocked_action_names and not blocked_action_names.issubset(checkpoint_actions):
        findings.append(GuardrailRecompilationPacketFinding("missing_exact_confirmation_checkpoint", "$.exact_confirmation_checkpoints", "Every blocked action must have an exact-confirmation checkpoint."))
    for index, item in enumerate(checkpoints):
        path = f"$.exact_confirmation_checkpoints[{index}]"
        if item.get("requires_user_attendance") is not True:
            findings.append(GuardrailRecompilationPacketFinding("checkpoint_not_attended", f"{path}.requires_user_attendance", "Checkpoint must require user attendance."))
        if not _text(item.get("exact_confirmation_text")):
            findings.append(GuardrailRecompilationPacketFinding("missing_exact_confirmation_text", f"{path}.exact_confirmation_text", "Checkpoint must include exact confirmation text."))

    if not _mapping_list(packet.get("manual_handoff_notes")):
        findings.append(GuardrailRecompilationPacketFinding("missing_manual_handoff_notes", "$.manual_handoff_notes", "Manual-handoff notes are required."))

    for path, _value in _walk(packet):
        if path.rsplit(".", 1)[-1] in _PROHIBITED_ACTIVE_KEYS:
            findings.append(GuardrailRecompilationPacketFinding("active_bundle_output_present", path, "Rehearsal packets must not include active, compiled, promoted, or replacement guardrail bundle outputs."))

    return findings


def require_valid_guardrail_recompilation_rehearsal_packet(packet: Mapping[str, Any]) -> None:
    findings = validate_guardrail_recompilation_rehearsal_packet(packet)
    if findings:
        detail = "; ".join(f"{item.code} at {item.path}: {item.message}" for item in findings)
        raise GuardrailRecompilationPacketError("invalid guardrail recompilation rehearsal packet: " + detail)


def finding_codes(findings: Iterable[GuardrailRecompilationPacketFinding]) -> set[str]:
    return {finding.code for finding in findings}


def _reviewed_candidates(packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    raw = packet.get("reviewed_requirement_candidates")
    if raw is None:
        raw = packet.get("regenerated_requirement_candidates")
    if raw is None:
        raw = packet.get("requirement_diffs")
    candidates = _mapping_list(raw)
    reviewed = []
    for candidate in candidates:
        status = _text(candidate.get("human_review_status")) or _text(candidate.get("review_status"))
        if not status:
            new_requirement = candidate.get("new_requirement")
            if isinstance(new_requirement, Mapping):
                status = _text(new_requirement.get("human_review_status")) or _text(new_requirement.get("review_status"))
        if status in _REVIEWED_STATUSES:
            reviewed.append(candidate)
    return reviewed


def _process_index(process_model_fixtures: Sequence[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    index: dict[str, Mapping[str, Any]] = {}
    for fixture in process_model_fixtures:
        if not isinstance(fixture, Mapping):
            continue
        process_id = _process_id(fixture)
        if process_id:
            index[process_id] = fixture
    return index


def _process_id(process_model: Mapping[str, Any]) -> str:
    return _text(process_model.get("process_id")) or _text(process_model.get("processId")) or _text(process_model.get("process_model_id"))


def _candidate_process_ids(candidate: Mapping[str, Any], process_index: Mapping[str, Mapping[str, Any]]) -> list[str]:
    explicit = _strings(candidate.get("affected_process_ids")) or _strings(candidate.get("affected_process_model_ids"))
    if explicit:
        return sorted(process_id for process_id in explicit if process_id in process_index) or sorted(explicit)
    return sorted(process_index)


def _predicate_diff_candidates(
    candidates: Sequence[Mapping[str, Any]],
    process_index: Mapping[str, Mapping[str, Any]],
    fallback_process_ids: Sequence[str],
) -> list[dict[str, Any]]:
    diffs = []
    for index, candidate in enumerate(candidates):
        candidate_id = _candidate_id(candidate, index)
        requirement = candidate.get("new_requirement") if isinstance(candidate.get("new_requirement"), Mapping) else candidate
        assert isinstance(requirement, Mapping)
        requirement_type = _text(candidate.get("requirement_type")) or _text(requirement.get("requirement_type")) or _text(candidate.get("impact_kind")) or "obligation"
        source_evidence_ids = _source_evidence_ids(candidate, requirement)
        process_ids = _candidate_process_ids(candidate, process_index) or list(fallback_process_ids)
        stages = _candidate_stages(candidate, requirement)
        action = _text(requirement.get("action")) or _text(candidate.get("action")) or requirement_type.replace("_", " ")
        changed_fields = []
        diff = candidate.get("old_to_new_requirement_diff")
        if isinstance(diff, Mapping):
            changed_fields = _strings(field.get("field") for field in _mapping_list(diff.get("changed_fields")))
        if not changed_fields:
            changed_fields = ["requirement"]
        diffs.append(
            {
                "predicate_diff_id": "predicate-diff." + _slug(candidate_id),
                "source_candidate_id": candidate_id,
                "predicate_kind": _predicate_kind(requirement_type),
                "requirement_type": requirement_type,
                "affected_process_ids": sorted(process_ids),
                "affected_stage_ids": stages,
                "changed_fields": sorted(changed_fields),
                "action_phrase": action,
                "source_evidence_ids": source_evidence_ids,
                "review_status": "draft_requires_human_review",
                "activation_allowed": False,
            }
        )
    return sorted(diffs, key=lambda item: item["predicate_diff_id"])


def _blocked_action_expectations(predicate_diffs: Sequence[Mapping[str, Any]], process_index: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for diff in predicate_diffs:
        actions = _actions_for_diff(diff)
        for process_id in _strings(diff.get("affected_process_ids")):
            for action in actions:
                key = (process_id, action)
                entry = by_key.setdefault(
                    key,
                    {
                        "blocked_action_id": "blocked-action." + _slug(process_id) + "." + _slug(action),
                        "process_id": process_id,
                        "action": action,
                        "expected_decision": "block_until_attended_exact_confirmation",
                        "source_predicate_diff_ids": [],
                        "source_evidence_ids": [],
                        "process_fixture_stop_gate_ids": _stop_gate_ids(process_index.get(process_id, {}), action),
                    },
                )
                _append_unique(entry["source_predicate_diff_ids"], _text(diff.get("predicate_diff_id")))
                for source_id in _strings(diff.get("source_evidence_ids")):
                    _append_unique(entry["source_evidence_ids"], source_id)
    return sorted(by_key.values(), key=lambda item: item["blocked_action_id"])


def _exact_confirmation_checkpoints(blocked_actions: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    checkpoints = []
    for item in blocked_actions:
        action = _text(item.get("action"))
        process_id = _text(item.get("process_id"))
        checkpoints.append(
            {
                "checkpoint_id": "exact-confirmation." + _slug(process_id) + "." + _slug(action),
                "process_id": process_id,
                "action": action,
                "requires_user_attendance": True,
                "exact_confirmation_text": "I confirm I am ready to " + action + " for this PP&D workflow.",
                "source_blocked_action_id": _text(item.get("blocked_action_id")),
                "source_predicate_diff_ids": sorted(_strings(item.get("source_predicate_diff_ids"))),
                "activation_allowed": False,
            }
        )
    return sorted(checkpoints, key=lambda item: item["checkpoint_id"])


def _manual_handoff_notes(blocked_actions: Sequence[Mapping[str, Any]], predicate_diffs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    notes = []
    for item in blocked_actions:
        action = _text(item.get("action"))
        process_id = _text(item.get("process_id"))
        notes.append(
            {
                "handoff_note_id": "manual-handoff." + _slug(process_id) + "." + _slug(action),
                "process_id": process_id,
                "handoff_reason": "Consequential PP&D action requires attended review and exact confirmation before any official action.",
                "blocked_action": action,
                "source_blocked_action_id": _text(item.get("blocked_action_id")),
                "source_predicate_diff_ids": sorted(_strings(item.get("source_predicate_diff_ids"))),
                "operator_instruction": "Do not compile or promote this rehearsal candidate; route it to human review with cited predicate diffs.",
            }
        )
    if not notes and predicate_diffs:
        process_id = _strings(predicate_diffs[0].get("affected_process_ids"))[0]
        notes.append(
            {
                "handoff_note_id": "manual-handoff." + _slug(process_id) + ".review-only",
                "process_id": process_id,
                "handoff_reason": "Reviewed requirement candidates produced predicate diffs but no consequential action mapping.",
                "blocked_action": "none",
                "source_blocked_action_id": "none",
                "source_predicate_diff_ids": sorted(_text(diff.get("predicate_diff_id")) for diff in predicate_diffs),
                "operator_instruction": "Keep the packet in review-only rehearsal until a reviewer resolves the predicate diffs.",
            }
        )
    return sorted(notes, key=lambda item: item["handoff_note_id"])


def _actions_for_diff(diff: Mapping[str, Any]) -> list[str]:
    actions = set()
    for stage_id in _strings(diff.get("affected_stage_ids")):
        action = _STAGE_ACTIONS.get(stage_id)
        if action:
            actions.add(action)
    phrase = _text(diff.get("action_phrase")).lower()
    kind = _text(diff.get("requirement_type")).lower()
    for needle, action in _ACTION_GATE_PHRASES.items():
        if needle in phrase or needle in kind:
            actions.add(action)
    if kind == "fee_trigger":
        actions.add("submit payment")
    return sorted(action for action in actions if action in _BLOCKED_ACTIONS)


def _stop_gate_ids(process_model: Mapping[str, Any], action: str) -> list[str]:
    gate_ids = []
    for gate in _mapping_list(process_model.get("stopGates")) + _mapping_list(process_model.get("stop_gates")):
        label = (_text(gate.get("label")) + " " + _text(gate.get("action"))).lower()
        if any(part in label for part in action.split()):
            gate_id = _text(gate.get("gateId")) or _text(gate.get("gate_id"))
            if gate_id:
                gate_ids.append(gate_id)
    return sorted(set(gate_ids))


def _candidate_id(candidate: Mapping[str, Any], index: int) -> str:
    return _text(candidate.get("candidate_id")) or _text(candidate.get("diff_id")) or "reviewed-candidate-" + str(index + 1)


def _candidate_stages(candidate: Mapping[str, Any], requirement: Mapping[str, Any]) -> list[str]:
    hints = candidate.get("impact_hints")
    if isinstance(hints, Mapping):
        stages = _strings(hints.get("process_stage_ids"))
        if stages:
            return sorted(stages)
    stage = _text(requirement.get("process_stage")) or _text(candidate.get("process_stage"))
    return [_slug(stage).replace("-", "_")] if stage else []


def _source_evidence_ids(candidate: Mapping[str, Any], requirement: Mapping[str, Any]) -> list[str]:
    source_ids = _strings(candidate.get("source_evidence_ids")) or _strings(requirement.get("source_evidence_ids"))
    if source_ids:
        return sorted(set(source_ids))
    citations = _mapping_list(candidate.get("citations")) + _mapping_list(requirement.get("citations"))
    values = []
    for citation in citations:
        values.append(_text(citation.get("source_evidence_id")) or _text(citation.get("url")))
    return sorted(value for value in set(values) if value)


def _predicate_kind(requirement_type: str) -> str:
    normalized = requirement_type.replace(" ", "_")
    if normalized == "document_requirement":
        return "document_requirement_predicate_diff"
    if normalized in {"action_gate", "action_gate_requirement"}:
        return "action_gate_predicate_diff"
    if normalized in {"fee", "fee_trigger"}:
        return "fee_gate_predicate_diff"
    return normalized + "_predicate_diff"


def _mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if not isinstance(value, Iterable) or isinstance(value, (bytes, Mapping)):
        return []
    return [_text(item) for item in value if _text(item)]


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


def _append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)
        values.sort()


def _slug(value: str) -> str:
    lowered = value.lower()
    chars = [char if char.isalnum() else "-" for char in lowered]
    return "-".join(part for part in "".join(chars).split("-") if part) or "unknown"


def _stable_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = path + "." + str(key)
            yield child_path, child
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, child
            yield from _walk(child, child_path)
