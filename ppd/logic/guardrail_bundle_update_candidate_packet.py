"""Fixture-first guardrail bundle update candidate packets.

This module assembles a review-only guardrail bundle update candidate from
requirement rerun review dispositions, process-model update candidates, and a
guardrail recompilation rehearsal packet. It records cited predicate additions,
predicate removals, explanation-template updates, blocked-action expectations,
exact-confirmation checkpoints, manual-handoff notes, and rollback notes without
compiling, promoting, or mutating any active guardrail bundle.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


PACKET_TYPE = "fixture_first_guardrail_bundle_update_candidate_packet"
PACKET_MODE = "candidate_packet_no_compile_no_promotion"

_FALSE_ATTESTATIONS = (
    "compiled_guardrail_bundle",
    "promoted_guardrail_bundle",
    "mutated_active_guardrail_bundle",
    "active_guardrail_bundle_replaced",
    "live_guardrail_compiler_invoked",
)

_TRUE_ATTESTATIONS = (
    "fixture_first",
    "review_packet_only",
    "no_active_guardrail_mutation",
)

_PROHIBITED_KEYS = {
    "compiled_guardrail_bundle",
    "compiled_guardrail_bundle_path",
    "promoted_guardrail_bundle",
    "replacement_guardrail_bundle",
    "active_guardrail_bundle_patch",
    "active_guardrail_bundle_mutation",
    "guardrail_bundle_promotion",
}


@dataclass(frozen=True)
class GuardrailBundleUpdateCandidateFinding:
    code: str
    path: str
    message: str


class GuardrailBundleUpdateCandidatePacketError(ValueError):
    """Raised when a guardrail bundle update candidate packet is invalid."""


def build_guardrail_bundle_update_candidate_packet(
    requirement_rerun_review_disposition_packet: Mapping[str, Any],
    process_model_update_candidate_packet: Mapping[str, Any],
    guardrail_recompilation_rehearsal_packet: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build a deterministic review-only guardrail bundle update candidate."""

    _require_mapping(requirement_rerun_review_disposition_packet, "requirement rerun review disposition packet")
    _require_mapping(process_model_update_candidate_packet, "process-model update candidate packet")
    _require_mapping(guardrail_recompilation_rehearsal_packet, "guardrail recompilation rehearsal packet")

    predicate_additions = _predicate_additions(process_model_update_candidate_packet, guardrail_recompilation_rehearsal_packet)
    predicate_removals = _predicate_removals(requirement_rerun_review_disposition_packet)
    explanation_template_updates = _explanation_template_updates(predicate_additions, predicate_removals, guardrail_recompilation_rehearsal_packet)
    blocked_action_expectations = _copy_mapping_list(guardrail_recompilation_rehearsal_packet.get("blocked_action_expectations"))
    exact_confirmation_checkpoints = _copy_mapping_list(guardrail_recompilation_rehearsal_packet.get("exact_confirmation_checkpoints"))
    manual_handoff_notes = _copy_mapping_list(guardrail_recompilation_rehearsal_packet.get("manual_handoff_notes"))
    rollback_notes = _rollback_notes(process_model_update_candidate_packet, predicate_removals, blocked_action_expectations)

    basis = {
        "requirement_packet_id": _text(requirement_rerun_review_disposition_packet.get("packet_id")),
        "process_packet_id": _text(process_model_update_candidate_packet.get("packet_id")),
        "rehearsal_packet_id": _text(guardrail_recompilation_rehearsal_packet.get("packet_id")),
        "generated_at": generated_at,
        "predicate_additions": predicate_additions,
        "predicate_removals": predicate_removals,
        "blocked_action_expectations": blocked_action_expectations,
    }

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_id": "guardrail-bundle-update-candidate-" + _stable_hash(basis),
        "packet_mode": PACKET_MODE,
        "candidate_status": "draft_requires_human_review",
        "generated_at": generated_at,
        "input_packet_refs": {
            "requirement_rerun_review_disposition_packet_id": basis["requirement_packet_id"],
            "process_model_update_candidate_packet_id": basis["process_packet_id"],
            "guardrail_recompilation_rehearsal_packet_id": basis["rehearsal_packet_id"],
        },
        "active_guardrail_bundle_id": _text(guardrail_recompilation_rehearsal_packet.get("active_guardrail_bundle_id")),
        "active_guardrail_bundle_revision": _text(guardrail_recompilation_rehearsal_packet.get("active_guardrail_bundle_revision")),
        "affected_process_ids": sorted(_strings(guardrail_recompilation_rehearsal_packet.get("affected_process_ids"))),
        "cited_predicate_additions": predicate_additions,
        "cited_predicate_removals": predicate_removals,
        "explanation_template_updates": explanation_template_updates,
        "blocked_action_expectations": blocked_action_expectations,
        "exact_confirmation_checkpoints": exact_confirmation_checkpoints,
        "manual_handoff_notes": manual_handoff_notes,
        "rollback_notes": rollback_notes,
        "no_active_guardrail_mutation_attestations": {
            "fixture_first": True,
            "review_packet_only": True,
            "compiled_guardrail_bundle": False,
            "promoted_guardrail_bundle": False,
            "mutated_active_guardrail_bundle": False,
            "active_guardrail_bundle_replaced": False,
            "live_guardrail_compiler_invoked": False,
            "no_active_guardrail_mutation": True,
            "attestation_basis": "requirement disposition, process-model candidate, and recompilation rehearsal fixtures only",
        },
    }
    require_valid_guardrail_bundle_update_candidate_packet(packet)
    return packet


def validate_guardrail_bundle_update_candidate_packet(packet: Mapping[str, Any]) -> list[GuardrailBundleUpdateCandidateFinding]:
    """Return validation findings for a review-only update candidate packet."""

    if not isinstance(packet, Mapping):
        return [GuardrailBundleUpdateCandidateFinding("invalid_packet", "$", "Packet must be an object.")]

    findings: list[GuardrailBundleUpdateCandidateFinding] = []
    if packet.get("packet_type") != PACKET_TYPE:
        findings.append(GuardrailBundleUpdateCandidateFinding("invalid_packet_type", "$.packet_type", "Unexpected packet type."))
    if packet.get("packet_mode") != PACKET_MODE:
        findings.append(GuardrailBundleUpdateCandidateFinding("invalid_packet_mode", "$.packet_mode", "Packet must remain candidate-only."))
    if packet.get("candidate_status") != "draft_requires_human_review":
        findings.append(GuardrailBundleUpdateCandidateFinding("candidate_not_review_blocked", "$.candidate_status", "Candidate status must require human review."))

    _validate_attestations(packet.get("no_active_guardrail_mutation_attestations"), findings)
    _validate_predicates(packet.get("cited_predicate_additions"), "cited_predicate_additions", findings)
    _validate_predicates(packet.get("cited_predicate_removals"), "cited_predicate_removals", findings)
    _validate_explanation_templates(packet.get("explanation_template_updates"), findings)
    _validate_action_gates(packet, findings)
    _validate_rollback_notes(packet.get("rollback_notes"), findings)
    _reject_prohibited_active_outputs(packet, findings)
    return findings


def require_valid_guardrail_bundle_update_candidate_packet(packet: Mapping[str, Any]) -> None:
    findings = validate_guardrail_bundle_update_candidate_packet(packet)
    if findings:
        detail = "; ".join(f"{finding.code} at {finding.path}: {finding.message}" for finding in findings)
        raise GuardrailBundleUpdateCandidatePacketError("invalid guardrail bundle update candidate packet: " + detail)


def finding_codes(findings: Sequence[GuardrailBundleUpdateCandidateFinding]) -> set[str]:
    return {finding.code for finding in findings}


def _predicate_additions(process_packet: Mapping[str, Any], rehearsal_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    additions: list[dict[str, Any]] = []
    proposed_diffs = process_packet.get("proposed_diffs")
    if isinstance(proposed_diffs, Mapping):
        for diff_type in sorted(proposed_diffs):
            for diff in _copy_mapping_list(proposed_diffs.get(diff_type)):
                if _text(diff.get("operation")).lower() not in {"add", "record", "update"}:
                    continue
                additions.append(
                    {
                        "predicate_id": "predicate-addition." + _slug(diff_type) + "." + _slug(_text(diff.get("target_id"))),
                        "operation": "add",
                        "predicate_kind": _predicate_kind_for_diff_type(diff_type),
                        "source_kind": "process_model_update_candidate",
                        "source_diff_id": _text(diff.get("candidate_diff_id")),
                        "requirement_id": _text(diff.get("requirement_id")),
                        "target_id": _text(diff.get("target_id")),
                        "proposed": diff.get("proposed"),
                        "citations": _citations(diff),
                        "source_evidence_ids": _source_evidence_ids_from_citations(_citations(diff)),
                        "review_status": "draft_requires_human_review",
                        "activation_allowed": False,
                    }
                )
    for diff in _copy_mapping_list(rehearsal_packet.get("predicate_diff_candidates")):
        additions.append(
            {
                "predicate_id": "predicate-addition.rehearsal." + _slug(_text(diff.get("predicate_diff_id"))),
                "operation": "add",
                "predicate_kind": _text(diff.get("predicate_kind")) or "guardrail_rehearsal_predicate",
                "source_kind": "guardrail_recompilation_rehearsal",
                "source_predicate_diff_id": _text(diff.get("predicate_diff_id")),
                "requirement_type": _text(diff.get("requirement_type")),
                "action_phrase": _text(diff.get("action_phrase")),
                "affected_process_ids": sorted(_strings(diff.get("affected_process_ids"))),
                "source_evidence_ids": sorted(_strings(diff.get("source_evidence_ids"))),
                "citations": [{"source_id": source_id, "quote": ""} for source_id in sorted(_strings(diff.get("source_evidence_ids")))],
                "review_status": "draft_requires_human_review",
                "activation_allowed": False,
            }
        )
    return sorted(additions, key=lambda item: item["predicate_id"])


def _predicate_removals(requirement_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    removals: list[dict[str, Any]] = []
    for group_key in ("superseded_candidate_deltas", "withdrawn_candidate_deltas"):
        for row in _copy_mapping_list(requirement_packet.get(group_key)):
            disposition = _text(row.get("disposition"))
            removals.append(
                {
                    "predicate_id": "predicate-removal." + _slug(_text(row.get("candidate_id"))),
                    "operation": "remove_candidate_predicate",
                    "source_kind": "requirement_rerun_review_disposition",
                    "candidate_id": _text(row.get("candidate_id")),
                    "source_delta_id": _text(row.get("source_delta_id")),
                    "removal_reason": disposition,
                    "source_ids": sorted(_strings(row.get("source_ids"))),
                    "source_evidence_ids": sorted(_strings(row.get("citations"))),
                    "citations": [{"source_id": source_id, "quote": ""} for source_id in sorted(_strings(row.get("citations")))],
                    "reviewer_owner": _text(row.get("reviewer_owner")),
                    "review_status": "draft_requires_human_review",
                    "activation_allowed": False,
                }
            )
    return sorted(removals, key=lambda item: item["predicate_id"])


def _explanation_template_updates(
    additions: Sequence[Mapping[str, Any]],
    removals: Sequence[Mapping[str, Any]],
    rehearsal_packet: Mapping[str, Any],
) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    for predicate in additions:
        templates.append(
            {
                "template_id": "explain." + _slug(_text(predicate.get("predicate_id"))),
                "source_predicate_ids": [_text(predicate.get("predicate_id"))],
                "template_kind": "predicate_addition_review",
                "template_text": "A PP&D guardrail predicate update is proposed for reviewer approval before any bundle compilation.",
                "source_evidence_ids": sorted(_strings(predicate.get("source_evidence_ids"))),
                "activation_allowed": False,
            }
        )
    for predicate in removals:
        templates.append(
            {
                "template_id": "explain." + _slug(_text(predicate.get("predicate_id"))),
                "source_predicate_ids": [_text(predicate.get("predicate_id"))],
                "template_kind": "predicate_removal_review",
                "template_text": "A stale, superseded, or withdrawn candidate predicate is proposed for removal from the draft update candidate only.",
                "source_evidence_ids": sorted(_strings(predicate.get("source_evidence_ids"))),
                "activation_allowed": False,
            }
        )
    for action in _copy_mapping_list(rehearsal_packet.get("blocked_action_expectations")):
        templates.append(
            {
                "template_id": "explain.blocked-action." + _slug(_text(action.get("blocked_action_id"))),
                "source_blocked_action_id": _text(action.get("blocked_action_id")),
                "template_kind": "blocked_action_expectation",
                "template_text": "This PP&D action must remain blocked until the attended exact-confirmation checkpoint is satisfied.",
                "source_evidence_ids": sorted(_strings(action.get("source_evidence_ids"))),
                "activation_allowed": False,
            }
        )
    return sorted(templates, key=lambda item: item["template_id"])


def _rollback_notes(
    process_packet: Mapping[str, Any],
    removals: Sequence[Mapping[str, Any]],
    blocked_actions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for index, note in enumerate(_strings(process_packet.get("rollback_notes"))):
        notes.append(
            {
                "rollback_note_id": "rollback.process-model." + str(index + 1),
                "source_packet": "process_model_update_candidate",
                "note": note,
                "active_guardrail_bundle_mutated": False,
            }
        )
    for removal in removals:
        notes.append(
            {
                "rollback_note_id": "rollback." + _slug(_text(removal.get("predicate_id"))),
                "source_packet": "requirement_rerun_review_disposition",
                "note": "Drop this candidate removal if reviewer disposition changes; no active guardrail bundle was mutated.",
                "source_predicate_id": _text(removal.get("predicate_id")),
                "active_guardrail_bundle_mutated": False,
            }
        )
    for action in blocked_actions:
        notes.append(
            {
                "rollback_note_id": "rollback.blocked-action." + _slug(_text(action.get("blocked_action_id"))),
                "source_packet": "guardrail_recompilation_rehearsal",
                "note": "Keep the blocked-action expectation in rehearsal-only status until a separately reviewed guardrail bundle is compiled.",
                "source_blocked_action_id": _text(action.get("blocked_action_id")),
                "active_guardrail_bundle_mutated": False,
            }
        )
    return sorted(notes, key=lambda item: item["rollback_note_id"])


def _validate_attestations(value: Any, findings: list[GuardrailBundleUpdateCandidateFinding]) -> None:
    if not isinstance(value, Mapping):
        findings.append(GuardrailBundleUpdateCandidateFinding("missing_attestations", "$.no_active_guardrail_mutation_attestations", "No-active-guardrail-mutation attestations are required."))
        return
    for key in _TRUE_ATTESTATIONS:
        if value.get(key) is not True:
            findings.append(GuardrailBundleUpdateCandidateFinding("attestation_not_true", f"$.no_active_guardrail_mutation_attestations.{key}", f"{key} must be true."))
    for key in _FALSE_ATTESTATIONS:
        if value.get(key) is not False:
            findings.append(GuardrailBundleUpdateCandidateFinding("attestation_not_false", f"$.no_active_guardrail_mutation_attestations.{key}", f"{key} must be false."))


def _validate_predicates(value: Any, field: str, findings: list[GuardrailBundleUpdateCandidateFinding]) -> None:
    rows = _copy_mapping_list(value)
    if not rows:
        findings.append(GuardrailBundleUpdateCandidateFinding("missing_predicates", f"$.{field}", field + " must include at least one predicate."))
        return
    for index, row in enumerate(rows):
        path = f"$.{field}[{index}]"
        if not _text(row.get("predicate_id")):
            findings.append(GuardrailBundleUpdateCandidateFinding("missing_predicate_id", path + ".predicate_id", "Predicate ID is required."))
        if not _strings(row.get("source_evidence_ids")) and not _citations(row):
            findings.append(GuardrailBundleUpdateCandidateFinding("uncited_predicate", path, "Predicate additions and removals must cite source evidence."))
        if row.get("activation_allowed") is not False:
            findings.append(GuardrailBundleUpdateCandidateFinding("predicate_activation_allowed", path + ".activation_allowed", "Predicate activation must remain false."))


def _validate_explanation_templates(value: Any, findings: list[GuardrailBundleUpdateCandidateFinding]) -> None:
    rows = _copy_mapping_list(value)
    if not rows:
        findings.append(GuardrailBundleUpdateCandidateFinding("missing_explanation_templates", "$.explanation_template_updates", "Explanation-template updates are required."))
        return
    for index, row in enumerate(rows):
        path = f"$.explanation_template_updates[{index}]"
        if not _text(row.get("template_id")):
            findings.append(GuardrailBundleUpdateCandidateFinding("missing_template_id", path + ".template_id", "Template ID is required."))
        if not _text(row.get("template_text")):
            findings.append(GuardrailBundleUpdateCandidateFinding("missing_template_text", path + ".template_text", "Template text is required."))
        if row.get("activation_allowed") is not False:
            findings.append(GuardrailBundleUpdateCandidateFinding("template_activation_allowed", path + ".activation_allowed", "Template activation must remain false."))


def _validate_action_gates(packet: Mapping[str, Any], findings: list[GuardrailBundleUpdateCandidateFinding]) -> None:
    blocked = _copy_mapping_list(packet.get("blocked_action_expectations"))
    checkpoints = _copy_mapping_list(packet.get("exact_confirmation_checkpoints"))
    handoffs = _copy_mapping_list(packet.get("manual_handoff_notes"))
    if not blocked:
        findings.append(GuardrailBundleUpdateCandidateFinding("missing_blocked_action_expectations", "$.blocked_action_expectations", "Blocked-action expectations are required."))
    if not checkpoints:
        findings.append(GuardrailBundleUpdateCandidateFinding("missing_exact_confirmation_checkpoints", "$.exact_confirmation_checkpoints", "Exact-confirmation checkpoints are required."))
    if not handoffs:
        findings.append(GuardrailBundleUpdateCandidateFinding("missing_manual_handoff_notes", "$.manual_handoff_notes", "Manual-handoff notes are required."))

    checkpoint_actions = {_text(item.get("action")) for item in checkpoints if _text(item.get("action"))}
    handoff_actions = {_text(item.get("blocked_action")) for item in handoffs if _text(item.get("blocked_action"))}
    for index, item in enumerate(blocked):
        path = f"$.blocked_action_expectations[{index}]"
        action = _text(item.get("action"))
        if item.get("expected_decision") != "block_until_attended_exact_confirmation":
            findings.append(GuardrailBundleUpdateCandidateFinding("invalid_blocked_action_expectation", path + ".expected_decision", "Blocked actions must wait for attended exact confirmation."))
        if action not in checkpoint_actions:
            findings.append(GuardrailBundleUpdateCandidateFinding("missing_checkpoint_for_blocked_action", path + ".action", "Every blocked action needs a checkpoint."))
        if action not in handoff_actions:
            findings.append(GuardrailBundleUpdateCandidateFinding("missing_handoff_for_blocked_action", path + ".action", "Every blocked action needs a manual-handoff note."))


def _validate_rollback_notes(value: Any, findings: list[GuardrailBundleUpdateCandidateFinding]) -> None:
    rows = _copy_mapping_list(value)
    if not rows:
        findings.append(GuardrailBundleUpdateCandidateFinding("missing_rollback_notes", "$.rollback_notes", "Rollback notes are required."))
        return
    for index, row in enumerate(rows):
        path = f"$.rollback_notes[{index}]"
        if not _text(row.get("rollback_note_id")) or not _text(row.get("note")):
            findings.append(GuardrailBundleUpdateCandidateFinding("malformed_rollback_note", path, "Rollback notes need IDs and text."))
        if row.get("active_guardrail_bundle_mutated") is not False:
            findings.append(GuardrailBundleUpdateCandidateFinding("rollback_claims_active_mutation", path + ".active_guardrail_bundle_mutated", "Rollback notes must not claim active mutation."))


def _reject_prohibited_active_outputs(packet: Mapping[str, Any], findings: list[GuardrailBundleUpdateCandidateFinding]) -> None:
    for path, _value in _walk(packet):
        if path.rsplit(".", 1)[-1] in _PROHIBITED_KEYS:
            findings.append(GuardrailBundleUpdateCandidateFinding("active_guardrail_output_present", path, "Candidate packets must not include compiled, promoted, replacement, or active mutation outputs."))


def _require_mapping(value: Any, label: str) -> None:
    if not isinstance(value, Mapping):
        raise GuardrailBundleUpdateCandidatePacketError(label + " must be an object")


def _predicate_kind_for_diff_type(diff_type: str) -> str:
    return {
        "stage": "process_stage_predicate",
        "required_fact": "required_user_fact_predicate",
        "document_rule": "document_requirement_predicate",
        "deadline": "temporal_guardrail_predicate",
        "exception": "exception_predicate",
        "unsupported_path": "refused_action_predicate",
    }.get(diff_type, "process_model_predicate")


def _citations(row: Mapping[str, Any]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for item in _as_list(row.get("citations")):
        if isinstance(item, Mapping):
            source_id = _text(item.get("source_id") or item.get("source_evidence_id"))
            quote = _text(item.get("quote") or item.get("summary"))
            if source_id:
                result.append({"source_id": source_id, "quote": quote})
        elif _text(item):
            result.append({"source_id": _text(item), "quote": ""})
    return result


def _source_evidence_ids_from_citations(citations: Sequence[Mapping[str, Any]]) -> list[str]:
    return sorted({_text(item.get("source_id") or item.get("source_evidence_id")) for item in citations if _text(item.get("source_id") or item.get("source_evidence_id"))})


def _copy_mapping_list(value: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in _as_list(value):
        if isinstance(item, Mapping):
            rows.append(dict(item))
    return rows


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _strings(value: Any) -> list[str]:
    result = []
    for item in _as_list(value):
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _slug(value: str) -> str:
    lowered = value.lower()
    chars = [char if char.isalnum() else "-" for char in lowered]
    return "-".join(part for part in "".join(chars).split("-") if part) or "unknown"


def _stable_hash(value: Mapping[str, Any]) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _walk(value: Any, path: str = "$") -> list[tuple[str, Any]]:
    rows = [(path, value)]
    if isinstance(value, Mapping):
        for key, child in value.items():
            rows.extend(_walk(child, path + "." + str(key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            rows.extend(_walk(child, f"{path}[{index}]"))
    return rows
