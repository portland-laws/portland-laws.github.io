"""Fixture-first stale predicate remediation candidate builder.

This module maps normalized public citation evidence into review-only draft fixes
for stale guardrail predicates, explanation templates, refused-action rules, and
exact-confirmation gates. It deliberately references the active bundle without
returning a replacement bundle or modifying the supplied fixture.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import Any


REMEDIATION_GROUPS: dict[str, str] = {
    "deterministic_predicates": "draft_predicate_fixes",
    "explanation_templates": "draft_explanation_template_fixes",
    "refused_action_predicates": "draft_refused_action_rule_fixes",
    "exact_confirmation_predicates": "draft_exact_confirmation_gate_fixes",
}


class StalePredicateRemediationCandidateError(ValueError):
    """Raised when a stale-predicate remediation fixture is malformed."""


def build_stale_predicate_remediation_candidate(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic remediation candidate from normalized evidence.

    The returned packet is a draft-only candidate. It keeps active bundle IDs and
    revisions for traceability, but it does not include replacement active-bundle
    content and does not mark human-review notes as resolved.
    """

    active_bundle = _mapping(fixture, "active_guardrail_bundle")
    evidence_rows = _list(fixture, "normalized_citation_evidence")
    evidence_by_target = _evidence_by_target(evidence_rows)

    original_active_bundle = deepcopy(active_bundle)
    candidate: dict[str, Any] = {
        "candidate_id": "stale-predicate-remediation-" + _stable_hash(fixture),
        "candidate_status": "draft_requires_human_review",
        "candidate_mode": "fixture_first_review_only",
        "active_guardrail_bundle_id": _required_text(active_bundle, "guardrail_bundle_id"),
        "active_bundle_revision": _required_text(active_bundle, "compiled_from_registry_revision"),
        "does_not_replace_active_bundle": True,
        "active_bundle_mutated": False,
        "source_evidence_ids": sorted(_evidence_ids(evidence_rows)),
    }

    for source_group, output_group in REMEDIATION_GROUPS.items():
        candidate[output_group] = _draft_fixes_for_group(
            active_bundle=active_bundle,
            source_group=source_group,
            evidence_by_target=evidence_by_target,
        )

    candidate["unresolved_human_review_notes"] = _unresolved_review_notes(fixture, evidence_rows)

    if active_bundle != original_active_bundle:
        raise StalePredicateRemediationCandidateError("active guardrail bundle input was mutated")

    return candidate


def _draft_fixes_for_group(
    *,
    active_bundle: Mapping[str, Any],
    source_group: str,
    evidence_by_target: Mapping[tuple[str, str], list[Mapping[str, Any]]],
) -> list[dict[str, Any]]:
    fixes: list[dict[str, Any]] = []
    for active_item in _list(active_bundle, source_group):
        if not isinstance(active_item, Mapping):
            raise StalePredicateRemediationCandidateError(f"{source_group} entries must be objects")
        item_id = _required_text(active_item, "id")
        evidence_items = evidence_by_target.get((source_group, item_id), [])
        if not evidence_items:
            continue
        source_evidence_ids = sorted(_evidence_ids(evidence_items))
        draft_fix = _merged_draft_fix(source_group, active_item, evidence_items)
        fixes.append(
            {
                "fix_id": f"draft-fix.{source_group}.{item_id}",
                "target_group": source_group,
                "target_item_id": item_id,
                "review_status": "draft_requires_human_review",
                "source_evidence_ids": source_evidence_ids,
                "normalized_citation_evidence": [_evidence_summary(item) for item in evidence_items],
                "draft_fix": draft_fix,
                "preserves_active_item": True,
            }
        )
    return sorted(fixes, key=lambda item: item["fix_id"])


def _merged_draft_fix(
    source_group: str,
    active_item: Mapping[str, Any],
    evidence_items: list[Mapping[str, Any]],
) -> dict[str, Any]:
    merged: dict[str, Any] = {
        "replaces_active_item": False,
        "basis": "normalized_citation_evidence",
    }
    if source_group == "deterministic_predicates":
        merged["predicate"] = _first_draft_value(evidence_items, "predicate") or _text(active_item.get("predicate"))
        merged["conditions"] = _combined_list(evidence_items, "conditions")
    elif source_group == "explanation_templates":
        merged["template"] = _first_draft_value(evidence_items, "template") or _text(active_item.get("template"))
        merged["variables"] = _combined_list(evidence_items, "variables")
    elif source_group == "refused_action_predicates":
        merged["predicate"] = _first_draft_value(evidence_items, "predicate") or _text(active_item.get("predicate"))
        merged["action"] = _first_draft_value(evidence_items, "action") or _text(active_item.get("action"))
        merged["refusal_reason"] = _first_draft_value(evidence_items, "refusal_reason") or "Official PP&D actions remain blocked until attended user review and exact confirmation."
    elif source_group == "exact_confirmation_predicates":
        merged["predicate"] = _first_draft_value(evidence_items, "predicate") or _text(active_item.get("predicate"))
        merged["action"] = _first_draft_value(evidence_items, "action") or _text(active_item.get("action"))
        merged["required_confirmation_text"] = _first_draft_value(evidence_items, "required_confirmation_text") or "I confirm I am ready to take this PP&D action."
    else:
        raise StalePredicateRemediationCandidateError(f"unsupported remediation group {source_group}")
    return merged


def _evidence_by_target(evidence_rows: list[Any]) -> dict[tuple[str, str], list[Mapping[str, Any]]]:
    grouped: dict[tuple[str, str], list[Mapping[str, Any]]] = {}
    for row in evidence_rows:
        if not isinstance(row, Mapping):
            raise StalePredicateRemediationCandidateError("normalized citation evidence entries must be objects")
        target_group = _required_text(row, "target_group")
        if target_group not in REMEDIATION_GROUPS:
            raise StalePredicateRemediationCandidateError(f"unsupported target_group {target_group}")
        for target_id in _text_list(row.get("target_item_ids"), "target_item_ids"):
            grouped.setdefault((target_group, target_id), []).append(row)
    for rows in grouped.values():
        rows.sort(key=lambda item: _required_text(item, "evidence_id"))
    return grouped


def _evidence_summary(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "evidence_id": _required_text(row, "evidence_id"),
        "source_id": _required_text(row, "source_id"),
        "canonical_url": _required_text(row, "canonical_url"),
        "citation_span_id": _required_text(row, "citation_span_id"),
        "normalized_claim": _required_text(row, "normalized_claim"),
    }


def _unresolved_review_notes(fixture: Mapping[str, Any], evidence_rows: list[Any]) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for note in _list(fixture, "unresolved_human_review_notes"):
        if not isinstance(note, Mapping):
            raise StalePredicateRemediationCandidateError("unresolved human-review notes must be objects")
        note_id = _required_text(note, "note_id")
        notes.append(
            {
                "note_id": note_id,
                "status": "unresolved",
                "severity": _text(note.get("severity")) or "blocks_activation",
                "message": _required_text(note, "message"),
                "source_evidence_ids": sorted(_text_list(note.get("source_evidence_ids"), "source_evidence_ids")),
            }
        )
    for row in evidence_rows:
        if not isinstance(row, Mapping):
            continue
        review_note = _text(row.get("human_review_note"))
        if not review_note:
            continue
        evidence_id = _required_text(row, "evidence_id")
        notes.append(
            {
                "note_id": f"review-{evidence_id}",
                "status": "unresolved",
                "severity": "needs_review",
                "message": review_note,
                "source_evidence_ids": [evidence_id],
            }
        )
    return sorted(notes, key=lambda item: item["note_id"])


def _first_draft_value(evidence_items: list[Mapping[str, Any]], key: str) -> str:
    for item in evidence_items:
        draft_fix = item.get("draft_fix")
        if isinstance(draft_fix, Mapping):
            value = _text(draft_fix.get(key))
            if value:
                return value
    return ""


def _combined_list(evidence_items: list[Mapping[str, Any]], key: str) -> list[str]:
    values: list[str] = []
    for item in evidence_items:
        draft_fix = item.get("draft_fix")
        if not isinstance(draft_fix, Mapping):
            continue
        for value in _text_list(draft_fix.get(key), key):
            if value not in values:
                values.append(value)
    return values


def _mapping(raw: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = raw.get(key)
    if not isinstance(value, Mapping):
        raise StalePredicateRemediationCandidateError(f"{key} must be an object")
    return value


def _list(raw: Mapping[str, Any], key: str) -> list[Any]:
    value = raw.get(key, [])
    if not isinstance(value, list):
        raise StalePredicateRemediationCandidateError(f"{key} must be a list")
    return value


def _required_text(raw: Mapping[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise StalePredicateRemediationCandidateError(f"{key} must be a non-empty string")
    return value.strip()


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _text_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise StalePredicateRemediationCandidateError(f"{field_name} must be a list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise StalePredicateRemediationCandidateError(f"{field_name} entries must be non-empty strings")
        result.append(item.strip())
    return result


def _evidence_ids(rows: Iterable[Any]) -> set[str]:
    ids: set[str] = set()
    for row in rows:
        if isinstance(row, Mapping):
            ids.add(_required_text(row, "evidence_id"))
    return ids


def _stable_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]
