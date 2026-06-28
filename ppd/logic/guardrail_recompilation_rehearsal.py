"""Fixture-first guardrail recompilation rehearsal packets.

This module consumes process model impact candidates and produces a disabled,
review-only rehearsal packet. It records the draft guardrail changes that would
need reviewer attention without replacing or activating an existing guardrail
bundle.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from ppd.logic.process_model_impact_candidate import validate_process_model_impact_candidate


_CONSEQUENTIAL_STAGE_ACTIONS: dict[str, str] = {
    "acknowledgment_certification_review": "certify acknowledgement",
    "certification_review": "certify acknowledgement",
    "submission": "submit permit request",
    "upload_staging": "upload permit documents",
    "fee_payment": "submit payment",
    "corrections_checksheets": "upload corrections",
    "inspection_scheduling": "schedule inspection",
}

_CONSEQUENTIAL_PATH_ACTIONS: dict[str, str] = {
    "unattended_certification": "certify acknowledgement",
    "unattended_submission": "submit permit request",
    "unattended_upload": "upload permit documents",
    "unattended_correction_upload": "upload corrections",
    "unattended_payment": "submit payment",
    "unattended_inspection_scheduling": "schedule inspection",
    "unattended_cancellation": "cancel permit request",
}


@dataclass(frozen=True)
class GuardrailRecompilationRehearsalFinding:
    code: str
    path: str
    message: str


class GuardrailRecompilationRehearsalError(ValueError):
    """Raised when a rehearsal packet is malformed or unsafe to review."""


def build_guardrail_recompilation_rehearsal(
    process_model_impact_candidate: Mapping[str, Any],
    *,
    active_guardrail_bundle_id: str,
    active_guardrail_bundle_revision: str,
) -> dict[str, Any]:
    """Build a deterministic disabled recompilation rehearsal packet."""

    findings = validate_process_model_impact_candidate(process_model_impact_candidate)
    if findings:
        detail = "; ".join(f"{item.code} at {item.path}: {item.message}" for item in findings)
        raise GuardrailRecompilationRehearsalError(f"invalid process model impact candidate: {detail}")

    impact_candidate_id = _text(process_model_impact_candidate.get("candidate_id"), "process-model-impact-candidate")
    diff_ids = sorted(_strings(process_model_impact_candidate.get("input_requirement_diff_ids")))
    process_ids = sorted(_strings(process_model_impact_candidate.get("affected_process_model_ids"))) or ["unknown-process-model"]

    draft_predicate_changes = _draft_predicate_changes(process_model_impact_candidate, diff_ids)
    exact_confirmation_gate_coverage = _exact_confirmation_gate_coverage(process_model_impact_candidate)
    refused_consequential_action_coverage = _refused_consequential_action_coverage(exact_confirmation_gate_coverage)
    explanation_template_deltas = _explanation_template_deltas(
        draft_predicate_changes,
        exact_confirmation_gate_coverage,
        refused_consequential_action_coverage,
    )
    rollback_references = [
        {
            "rollback_ref_id": f"rollback.{_slug(active_guardrail_bundle_id)}.{_slug(active_guardrail_bundle_revision)}",
            "active_guardrail_bundle_id": active_guardrail_bundle_id,
            "active_guardrail_bundle_revision": active_guardrail_bundle_revision,
            "restore_action": "retain_active_bundle_and_discard_rehearsal_candidate",
            "activation_blocked": True,
        }
    ]

    basis = {
        "impact_candidate_id": impact_candidate_id,
        "active_guardrail_bundle_id": active_guardrail_bundle_id,
        "active_guardrail_bundle_revision": active_guardrail_bundle_revision,
        "draft_predicate_changes": draft_predicate_changes,
        "exact_confirmation_gate_coverage": exact_confirmation_gate_coverage,
        "refused_consequential_action_coverage": refused_consequential_action_coverage,
        "explanation_template_deltas": explanation_template_deltas,
    }

    return {
        "packet_type": "guardrail_recompilation_rehearsal",
        "rehearsal_id": "guardrail-recompilation-rehearsal-" + _stable_hash(basis),
        "rehearsal_mode": "fixture_first_disabled_review_only",
        "candidate_status": "draft_rehearsal_only",
        "source_process_model_impact_candidate_id": impact_candidate_id,
        "source_requirement_diff_ids": diff_ids,
        "affected_process_model_ids": process_ids,
        "active_guardrail_bundle_id": active_guardrail_bundle_id,
        "active_guardrail_bundle_revision": active_guardrail_bundle_revision,
        "draft_predicate_changes": draft_predicate_changes,
        "exact_confirmation_gate_coverage": exact_confirmation_gate_coverage,
        "refused_consequential_action_coverage": refused_consequential_action_coverage,
        "explanation_template_deltas": explanation_template_deltas,
        "rollback_references": rollback_references,
        "activation_state": {
            "disabled": True,
            "activation_enabled": False,
            "promotion_target": "none",
            "requires_human_review_before_activation": True,
            "reason": "Recompilation rehearsal is fixture-first and must not replace the active guardrail bundle.",
        },
    }


def validate_guardrail_recompilation_rehearsal(packet: Mapping[str, Any]) -> list[GuardrailRecompilationRehearsalFinding]:
    """Validate that a recompilation rehearsal packet is complete and disabled."""

    if not isinstance(packet, Mapping):
        return [GuardrailRecompilationRehearsalFinding("invalid_packet", "$", "Packet must be an object.")]

    findings: list[GuardrailRecompilationRehearsalFinding] = []
    if packet.get("packet_type") != "guardrail_recompilation_rehearsal":
        findings.append(GuardrailRecompilationRehearsalFinding("invalid_packet_type", "$.packet_type", "Packet type must be guardrail_recompilation_rehearsal."))
    if packet.get("rehearsal_mode") != "fixture_first_disabled_review_only":
        findings.append(GuardrailRecompilationRehearsalFinding("not_fixture_first", "$.rehearsal_mode", "Rehearsal must be fixture-first and disabled."))
    if packet.get("candidate_status") != "draft_rehearsal_only":
        findings.append(GuardrailRecompilationRehearsalFinding("invalid_candidate_status", "$.candidate_status", "Rehearsal must remain draft_rehearsal_only."))

    activation = packet.get("activation_state")
    if not isinstance(activation, Mapping):
        findings.append(GuardrailRecompilationRehearsalFinding("missing_activation_state", "$.activation_state", "Activation state is required."))
    else:
        if activation.get("disabled") is not True:
            findings.append(GuardrailRecompilationRehearsalFinding("activation_not_disabled", "$.activation_state.disabled", "Activation must be disabled."))
        if activation.get("activation_enabled") is not False:
            findings.append(GuardrailRecompilationRehearsalFinding("activation_enabled", "$.activation_state.activation_enabled", "Rehearsal must not enable activation."))
        if activation.get("promotion_target") != "none":
            findings.append(GuardrailRecompilationRehearsalFinding("promotion_target_enabled", "$.activation_state.promotion_target", "Rehearsal must not target promotion."))
        if activation.get("requires_human_review_before_activation") is not True:
            findings.append(GuardrailRecompilationRehearsalFinding("missing_human_review_gate", "$.activation_state.requires_human_review_before_activation", "Human review must block activation."))

    source_diff_ids = set(_strings(packet.get("source_requirement_diff_ids")))
    draft_changes = _mapping_list(packet.get("draft_predicate_changes"))
    covered_diff_ids: set[str] = set()
    for index, change in enumerate(draft_changes):
        location = f"$.draft_predicate_changes[{index}]"
        predicate_id = _text(change.get("predicate_id"), "")
        if not predicate_id:
            findings.append(GuardrailRecompilationRehearsalFinding("missing_predicate_id", f"{location}.predicate_id", "Draft predicate change must name a predicate."))
        if change.get("review_status") != "draft_requires_human_review":
            findings.append(GuardrailRecompilationRehearsalFinding("predicate_not_draft_review", f"{location}.review_status", "Draft predicate changes must require human review."))
        covered_diff_ids.update(_strings(change.get("source_requirement_diff_ids")))
    if source_diff_ids and not source_diff_ids.issubset(covered_diff_ids):
        missing = sorted(source_diff_ids - covered_diff_ids)
        findings.append(GuardrailRecompilationRehearsalFinding("missing_draft_predicate_change", "$.draft_predicate_changes", "Every source requirement diff must be covered by a draft predicate change: " + ", ".join(missing)))

    exact_coverage = _mapping_list(packet.get("exact_confirmation_gate_coverage"))
    refused_coverage = _mapping_list(packet.get("refused_consequential_action_coverage"))
    exact_actions = {_text(item.get("action"), "") for item in exact_coverage if _text(item.get("action"), "")}
    refused_actions = {_text(item.get("action"), "") for item in refused_coverage if _text(item.get("action"), "")}
    if exact_actions and not exact_actions.issubset(refused_actions):
        missing = sorted(exact_actions - refused_actions)
        findings.append(GuardrailRecompilationRehearsalFinding("missing_refused_action_coverage", "$.refused_consequential_action_coverage", "Exact-confirmation actions must also have refusal coverage: " + ", ".join(missing)))
    for index, gate in enumerate(exact_coverage):
        if gate.get("requires_exact_confirmation") is not True:
            findings.append(GuardrailRecompilationRehearsalFinding("missing_exact_confirmation_gate", f"$.exact_confirmation_gate_coverage[{index}].requires_exact_confirmation", "Exact-confirmation coverage entries must require exact confirmation."))
        if not _text(gate.get("required_confirmation_text"), ""):
            findings.append(GuardrailRecompilationRehearsalFinding("missing_confirmation_text", f"$.exact_confirmation_gate_coverage[{index}].required_confirmation_text", "Exact-confirmation coverage must include confirmation text."))
    for index, refused in enumerate(refused_coverage):
        if refused.get("refuse_until_attended_exact_confirmation") is not True:
            findings.append(GuardrailRecompilationRehearsalFinding("refusal_not_attended_exact", f"$.refused_consequential_action_coverage[{index}].refuse_until_attended_exact_confirmation", "Refusal coverage must block until attended exact confirmation."))

    template_deltas = _mapping_list(packet.get("explanation_template_deltas"))
    if not template_deltas:
        findings.append(GuardrailRecompilationRehearsalFinding("missing_explanation_template_deltas", "$.explanation_template_deltas", "Rehearsal must record explanation-template deltas."))
    for index, delta in enumerate(template_deltas):
        if delta.get("review_status") != "draft_requires_human_review":
            findings.append(GuardrailRecompilationRehearsalFinding("template_delta_not_draft_review", f"$.explanation_template_deltas[{index}].review_status", "Explanation template deltas must require human review."))

    rollback_references = _mapping_list(packet.get("rollback_references"))
    if not rollback_references:
        findings.append(GuardrailRecompilationRehearsalFinding("missing_rollback_references", "$.rollback_references", "Rehearsal must include rollback references to the active bundle."))
    for index, ref in enumerate(rollback_references):
        if not _text(ref.get("active_guardrail_bundle_id"), ""):
            findings.append(GuardrailRecompilationRehearsalFinding("missing_active_bundle_ref", f"$.rollback_references[{index}].active_guardrail_bundle_id", "Rollback reference must name the active bundle."))
        if ref.get("activation_blocked") is not True:
            findings.append(GuardrailRecompilationRehearsalFinding("rollback_activation_not_blocked", f"$.rollback_references[{index}].activation_blocked", "Rollback reference must keep activation blocked."))

    return findings


def require_valid_guardrail_recompilation_rehearsal(packet: Mapping[str, Any]) -> None:
    findings = validate_guardrail_recompilation_rehearsal(packet)
    if findings:
        detail = "; ".join(f"{item.code} at {item.path}: {item.message}" for item in findings)
        raise GuardrailRecompilationRehearsalError(f"invalid guardrail recompilation rehearsal: {detail}")


def finding_codes(findings: Iterable[GuardrailRecompilationRehearsalFinding]) -> set[str]:
    return {finding.code for finding in findings}


def _draft_predicate_changes(packet: Mapping[str, Any], fallback_diff_ids: list[str]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for group_name, item_key, predicate_kind in (
        ("affected_process_stages", "stage_id", "process_stage_review_required"),
        ("affected_user_facts", "user_fact_id", "required_user_fact_review_required"),
        ("affected_required_documents", "required_document_id", "required_document_review_required"),
        ("affected_unsupported_paths", "unsupported_path_id", "unsupported_path_review_required"),
    ):
        for item in _mapping_list(packet.get(group_name)):
            process_id = _text(item.get("process_model_id"), "unknown-process-model")
            item_id = _text(item.get(item_key), "unknown")
            diff_ids = sorted(_strings(item.get("source_requirement_diff_ids"))) or fallback_diff_ids
            impact_kinds = sorted(_strings(item.get("impact_kinds")))
            changes.append(
                {
                    "predicate_id": f"draft.{_slug(process_id)}.{predicate_kind}.{_slug(item_id)}",
                    "change_type": "add_or_update_draft_predicate",
                    "predicate_kind": predicate_kind,
                    "process_model_id": process_id,
                    item_key: item_id,
                    "impact_kinds": impact_kinds,
                    "source_requirement_diff_ids": diff_ids,
                    "review_status": "draft_requires_human_review",
                    "activation_allowed": False,
                }
            )
    return sorted(changes, key=lambda item: item["predicate_id"])


def _exact_confirmation_gate_coverage(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    coverage_by_action: dict[str, dict[str, Any]] = {}
    for item in _mapping_list(packet.get("affected_process_stages")):
        stage_id = _text(item.get("stage_id"), "")
        action = _CONSEQUENTIAL_STAGE_ACTIONS.get(stage_id)
        if action:
            _merge_action_coverage(coverage_by_action, action, item)
    for item in _mapping_list(packet.get("affected_unsupported_paths")):
        path_id = _text(item.get("unsupported_path_id"), "")
        action = _CONSEQUENTIAL_PATH_ACTIONS.get(path_id) or path_id.replace("_", " ")
        _merge_action_coverage(coverage_by_action, action, item)
    return sorted(coverage_by_action.values(), key=lambda item: item["action"])


def _merge_action_coverage(target: dict[str, dict[str, Any]], action: str, item: Mapping[str, Any]) -> None:
    process_id = _text(item.get("process_model_id"), "unknown-process-model")
    entry = target.setdefault(
        action,
        {
            "gate_id": f"exact-confirmation.{_slug(process_id)}.{_slug(action)}",
            "process_model_id": process_id,
            "action": action,
            "requires_exact_confirmation": True,
            "required_confirmation_text": f"I confirm I am ready to {action} for this PP&D workflow.",
            "source_requirement_diff_ids": [],
            "covered_impact_refs": [],
            "review_status": "draft_requires_human_review",
            "activation_allowed": False,
        },
    )
    for diff_id in _strings(item.get("source_requirement_diff_ids")):
        _append_unique(entry["source_requirement_diff_ids"], diff_id)
    for key in ("stage_id", "unsupported_path_id"):
        value = _text(item.get(key), "")
        if value:
            _append_unique(entry["covered_impact_refs"], value)


def _refused_consequential_action_coverage(exact_coverage: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    coverage: list[dict[str, Any]] = []
    for gate in exact_coverage:
        action = _text(gate.get("action"), "unknown action")
        process_id = _text(gate.get("process_model_id"), "unknown-process-model")
        coverage.append(
            {
                "refusal_id": f"refuse.{_slug(process_id)}.{_slug(action)}",
                "process_model_id": process_id,
                "action": action,
                "refuse_until_attended_exact_confirmation": True,
                "refusal_reason": "Consequential PP&D actions require user attendance and exact confirmation before any official action.",
                "source_requirement_diff_ids": sorted(_strings(gate.get("source_requirement_diff_ids"))),
                "review_status": "draft_requires_human_review",
                "activation_allowed": False,
            }
        )
    return sorted(coverage, key=lambda item: item["refusal_id"])


def _explanation_template_deltas(
    draft_predicate_changes: list[Mapping[str, Any]],
    exact_confirmation_gate_coverage: list[Mapping[str, Any]],
    refused_consequential_action_coverage: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    deltas: list[dict[str, Any]] = []
    for change in draft_predicate_changes:
        predicate_id = _text(change.get("predicate_id"), "unknown")
        deltas.append(
            {
                "template_delta_id": f"template-delta.{predicate_id}",
                "delta_type": "draft_template_added_or_updated",
                "covers_ref": predicate_id,
                "template_role": "predicate_change_explanation",
                "draft_message": "This PP&D guardrail predicate changed during rehearsal and requires review against cited process-model impact evidence before activation.",
                "source_requirement_diff_ids": sorted(_strings(change.get("source_requirement_diff_ids"))),
                "review_status": "draft_requires_human_review",
            }
        )
    for gate in exact_confirmation_gate_coverage:
        gate_id = _text(gate.get("gate_id"), "unknown")
        deltas.append(
            {
                "template_delta_id": f"template-delta.{gate_id}",
                "delta_type": "draft_template_added_or_updated",
                "covers_ref": gate_id,
                "template_role": "exact_confirmation_explanation",
                "draft_message": "Before this PP&D action, the user must provide the exact confirmation text recorded in the draft gate.",
                "source_requirement_diff_ids": sorted(_strings(gate.get("source_requirement_diff_ids"))),
                "review_status": "draft_requires_human_review",
            }
        )
    for refusal in refused_consequential_action_coverage:
        refusal_id = _text(refusal.get("refusal_id"), "unknown")
        deltas.append(
            {
                "template_delta_id": f"template-delta.{refusal_id}",
                "delta_type": "draft_template_added_or_updated",
                "covers_ref": refusal_id,
                "template_role": "refused_consequential_action_explanation",
                "draft_message": "I cannot perform this consequential PP&D action automatically; user attendance and exact confirmation are required.",
                "source_requirement_diff_ids": sorted(_strings(refusal.get("source_requirement_diff_ids"))),
                "review_status": "draft_requires_human_review",
            }
        )
    return sorted(deltas, key=lambda item: item["template_delta_id"])


def _mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _strings(value: Any) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [_text(item, "") for item in value if _text(item, "")]


def _text(value: Any, default: str) -> str:
    if isinstance(value, str) and value:
        return value
    return default


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)
        values.sort()


def _slug(value: str) -> str:
    lowered = value.lower()
    chars = [char if char.isalnum() else "-" for char in lowered]
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug or "unknown"


def _stable_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]
