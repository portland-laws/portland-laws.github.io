from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any


CONSEQUENTIAL_ACTION_KEYWORDS = (
    "submit",
    "submission",
    "upload",
    "certify",
    "certification",
    "acknowledge",
    "payment",
    "pay",
    "schedule",
    "cancel",
    "purchase",
)


def compile_guardrail_regeneration_candidate(
    process_model_change: Mapping[str, Any],
) -> dict[str, Any]:
    """Compile one process-model change into a draft guardrail candidate packet.

    The packet is intentionally review-oriented: it references the active bundle but
    never claims to replace it. Inputs are plain dictionaries so fixture tests can
    exercise regeneration without requiring live crawls or authenticated DevHub data.
    """

    change = dict(process_model_change)
    impacted_change = _as_mapping(change.get("impacted_change"))
    before = _as_mapping(change.get("before"))
    after = _as_mapping(change.get("after"))

    process_id = _string_value(change.get("process_id"), "unknown-process")
    active_bundle_id = _string_value(change.get("active_guardrail_bundle_id"), "unknown-active-bundle")
    change_id = _string_value(impacted_change.get("change_id"), "unknown-change")
    evidence_ids = _string_list(impacted_change.get("source_evidence_ids"))

    draft_predicates: list[dict[str, Any]] = []
    draft_predicates.extend(
        _added_value_predicates(
            process_id=process_id,
            change_id=change_id,
            evidence_ids=evidence_ids,
            field_name="required_user_facts",
            predicate_prefix="requires_user_fact",
            before_values=before.get("required_user_facts"),
            after_values=after.get("required_user_facts"),
        )
    )
    draft_predicates.extend(
        _added_value_predicates(
            process_id=process_id,
            change_id=change_id,
            evidence_ids=evidence_ids,
            field_name="required_documents",
            predicate_prefix="requires_document",
            before_values=before.get("required_documents"),
            after_values=after.get("required_documents"),
        )
    )
    draft_predicates.extend(
        _added_value_predicates(
            process_id=process_id,
            change_id=change_id,
            evidence_ids=evidence_ids,
            field_name="file_rules",
            predicate_prefix="requires_file_rule",
            before_values=before.get("file_rules"),
            after_values=after.get("file_rules"),
        )
    )

    action_gates = _added_dicts(
        before_values=before.get("action_gates"),
        after_values=after.get("action_gates"),
        identity_key="action",
    )
    for gate in action_gates:
        action = _string_value(gate.get("action"), "unknown_action")
        gate_id = _slug(action)
        draft_predicates.append(
            {
                "predicate_id": f"draft.{process_id}.{change_id}.action_gate.{gate_id}",
                "kind": "action_gate",
                "subject": process_id,
                "action": action,
                "conditions": _string_list(gate.get("conditions")),
                "source_evidence_ids": evidence_ids,
                "review_status": "draft_requires_human_review",
            }
        )

    exact_confirmation_predicates = [
        _exact_confirmation_predicate(process_id, change_id, gate, evidence_ids)
        for gate in action_gates
        if _requires_exact_confirmation(gate)
    ]
    refused_action_predicates = [
        _refused_action_predicate(process_id, change_id, gate, evidence_ids)
        for gate in action_gates
        if _requires_refusal_until_attended(gate)
    ]

    explanation_templates = _build_explanation_templates(
        process_id=process_id,
        change_id=change_id,
        draft_predicates=draft_predicates,
        exact_confirmation_predicates=exact_confirmation_predicates,
        refused_action_predicates=refused_action_predicates,
    )
    unresolved_review_notes = _build_unresolved_review_notes(change, impacted_change, draft_predicates)

    packet_basis = {
        "process_id": process_id,
        "active_guardrail_bundle_id": active_bundle_id,
        "change_id": change_id,
        "draft_predicates": draft_predicates,
        "exact_confirmation_predicates": exact_confirmation_predicates,
        "refused_action_predicates": refused_action_predicates,
        "unresolved_review_notes": unresolved_review_notes,
    }

    return {
        "candidate_id": "guardrail-candidate-" + _stable_hash(packet_basis),
        "candidate_status": "draft_review_required",
        "source_process_model_id": process_id,
        "impacted_change_id": change_id,
        "active_guardrail_bundle_id": active_bundle_id,
        "does_not_replace_active_bundle": True,
        "source_evidence_ids": evidence_ids,
        "draft_predicates": draft_predicates,
        "explanation_templates": explanation_templates,
        "refused_action_predicates": refused_action_predicates,
        "exact_confirmation_predicates": exact_confirmation_predicates,
        "unresolved_review_notes": unresolved_review_notes,
    }


def _added_value_predicates(
    *,
    process_id: str,
    change_id: str,
    evidence_ids: list[str],
    field_name: str,
    predicate_prefix: str,
    before_values: Any,
    after_values: Any,
) -> list[dict[str, Any]]:
    before_set = set(_string_list(before_values))
    predicates: list[dict[str, Any]] = []
    for value in _string_list(after_values):
        if value in before_set:
            continue
        predicates.append(
            {
                "predicate_id": f"draft.{process_id}.{change_id}.{predicate_prefix}.{_slug(value)}",
                "kind": predicate_prefix,
                "process_id": process_id,
                "field": field_name,
                "value": value,
                "source_evidence_ids": evidence_ids,
                "review_status": "draft_requires_human_review",
            }
        )
    return predicates


def _exact_confirmation_predicate(
    process_id: str,
    change_id: str,
    gate: Mapping[str, Any],
    evidence_ids: list[str],
) -> dict[str, Any]:
    action = _string_value(gate.get("action"), "unknown_action")
    confirmation_text = _string_value(
        gate.get("confirmation_text"),
        f"I confirm I am ready to {action} for this PP&D permit workflow.",
    )
    return {
        "predicate_id": f"draft.{process_id}.{change_id}.exact_confirmation.{_slug(action)}",
        "kind": "exact_confirmation_required",
        "action": action,
        "required_confirmation_text": confirmation_text,
        "source_evidence_ids": evidence_ids,
        "review_status": "draft_requires_human_review",
    }


def _refused_action_predicate(
    process_id: str,
    change_id: str,
    gate: Mapping[str, Any],
    evidence_ids: list[str],
) -> dict[str, Any]:
    action = _string_value(gate.get("action"), "unknown_action")
    return {
        "predicate_id": f"draft.{process_id}.{change_id}.refuse_until_attended.{_slug(action)}",
        "kind": "refused_action_until_attended_confirmation",
        "action": action,
        "refusal_reason": _string_value(
            gate.get("refusal_reason"),
            "This official PP&D action is consequential and requires user attendance plus exact confirmation.",
        ),
        "source_evidence_ids": evidence_ids,
        "review_status": "draft_requires_human_review",
    }


def _build_explanation_templates(
    *,
    process_id: str,
    change_id: str,
    draft_predicates: list[dict[str, Any]],
    exact_confirmation_predicates: list[dict[str, Any]],
    refused_action_predicates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    for predicate in draft_predicates:
        templates.append(
            {
                "template_id": f"explain.{predicate['predicate_id']}",
                "predicate_id": predicate["predicate_id"],
                "message": "Draft guardrail candidate for {process_id}: {field_or_action} must be reviewed against cited PP&D evidence before activation.",
                "variables": ["process_id", "field_or_action", "source_evidence_ids"],
            }
        )
    for predicate in refused_action_predicates:
        templates.append(
            {
                "template_id": f"explain.{predicate['predicate_id']}",
                "predicate_id": predicate["predicate_id"],
                "message": "I cannot perform {action} automatically. This PP&D action requires user attendance and exact confirmation.",
                "variables": ["action", "source_evidence_ids"],
            }
        )
    for predicate in exact_confirmation_predicates:
        templates.append(
            {
                "template_id": f"explain.{predicate['predicate_id']}",
                "predicate_id": predicate["predicate_id"],
                "message": "Before {action}, the user must provide the exact confirmation text shown in the guardrail candidate.",
                "variables": ["action", "required_confirmation_text"],
            }
        )
    if not templates:
        templates.append(
            {
                "template_id": f"explain.draft.{process_id}.{change_id}.no_predicates",
                "predicate_id": None,
                "message": "No draft predicates were generated; the impacted process-model change needs manual review.",
                "variables": ["process_id", "impacted_change_id"],
            }
        )
    return templates


def _build_unresolved_review_notes(
    change: Mapping[str, Any],
    impacted_change: Mapping[str, Any],
    draft_predicates: list[dict[str, Any]],
) -> list[dict[str, str]]:
    notes: list[dict[str, str]] = []
    evidence_ids = _string_list(impacted_change.get("source_evidence_ids"))
    if not evidence_ids:
        notes.append(
            {
                "note_id": "missing-source-evidence",
                "severity": "blocks_activation",
                "message": "The impacted change has no source evidence IDs, so the candidate cannot be activated.",
            }
        )
    if not draft_predicates:
        notes.append(
            {
                "note_id": "no-draft-predicates",
                "severity": "needs_review",
                "message": "The impacted change did not map to a supported draft predicate category.",
            }
        )
    if _string_value(change.get("human_review_status"), "") not in {"reviewed", "source_verified"}:
        notes.append(
            {
                "note_id": "human-review-required",
                "severity": "blocks_activation",
                "message": "A reviewer must compare this candidate against the cited PP&D source before replacing any active guardrail bundle.",
            }
        )
    return notes


def _added_dicts(*, before_values: Any, after_values: Any, identity_key: str) -> list[Mapping[str, Any]]:
    before_identities = {
        _string_value(item.get(identity_key), "")
        for item in _mapping_list(before_values)
    }
    added: list[Mapping[str, Any]] = []
    for item in _mapping_list(after_values):
        identity = _string_value(item.get(identity_key), "")
        if identity and identity not in before_identities:
            added.append(item)
    return added


def _requires_exact_confirmation(gate: Mapping[str, Any]) -> bool:
    if gate.get("requires_exact_confirmation") is True:
        return True
    action = _string_value(gate.get("action"), "").lower()
    return any(keyword in action for keyword in CONSEQUENTIAL_ACTION_KEYWORDS)


def _requires_refusal_until_attended(gate: Mapping[str, Any]) -> bool:
    if gate.get("requires_attendance") is True:
        return True
    action = _string_value(gate.get("action"), "").lower()
    return any(keyword in action for keyword in CONSEQUENTIAL_ACTION_KEYWORDS)


def _mapping_list(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [_string_value(item, "") for item in value if _string_value(item, "")]


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _string_value(value: Any, default: str) -> str:
    if isinstance(value, str) and value:
        return value
    return default


def _slug(value: str) -> str:
    lowered = value.lower()
    chars = [char if char.isalnum() else "-" for char in lowered]
    slug = "-".join(part for part in "".join(chars).split("-") if part)
    return slug or "unknown"


def _stable_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]
