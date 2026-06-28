"""Fixture-first stale guardrail audit packet builder.

This module compares already-active guardrail bundle inputs with a source
registry update candidate and an invalidation decision queue. It intentionally
reports stale guardrail inputs without invoking the guardrail compiler or
rewriting the active bundle.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping


STALE_SOURCE_STATUSES = frozenset({"changed", "stale", "needs_review", "removed"})
INVALIDATION_DECISIONS = frozenset({"invalidate", "human_review", "hold"})


class StaleGuardrailAuditError(ValueError):
    """Raised when an audit fixture is malformed."""


def build_stale_guardrail_audit_packet(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic stale guardrail audit packet from fixture data."""

    active_bundle = _mapping(fixture, "active_guardrail_bundle_inputs")
    registry_candidate = _mapping(fixture, "source_registry_update_candidate")
    decision_queue = _mapping(fixture, "invalidation_decision_queue")

    changed_sources = _changed_sources(registry_candidate)
    invalidation_by_source = _invalidation_by_source(decision_queue)
    invalidated_item_ids = _invalidated_item_ids(invalidation_by_source)

    stale_predicates = _stale_guardrail_items(
        active_bundle.get("deterministic_predicates", []),
        changed_sources,
        invalidated_item_ids,
    )
    stale_explanations = _stale_guardrail_items(
        active_bundle.get("explanation_templates", []),
        changed_sources,
        invalidated_item_ids,
    )
    stale_refused_rules = _stale_guardrail_items(
        active_bundle.get("refused_action_predicates", []),
        changed_sources,
        invalidated_item_ids,
    )
    stale_confirmation_gates = _stale_guardrail_items(
        active_bundle.get("exact_confirmation_predicates", []),
        changed_sources,
        invalidated_item_ids,
    )

    stale_by_source = _stale_items_by_source(
        stale_predicates + stale_explanations + stale_refused_rules + stale_confirmation_gates
    )
    required_human_review = _required_human_review(invalidation_by_source, stale_by_source)

    return {
        "packet_id": _required_text(fixture, "packet_id"),
        "guardrail_bundle_id": _required_text(active_bundle, "guardrail_bundle_id"),
        "active_bundle_revision": _required_text(active_bundle, "compiled_from_registry_revision"),
        "registry_candidate_revision": _required_text(registry_candidate, "registry_revision_candidate"),
        "decision_queue_id": _required_text(decision_queue, "queue_id"),
        "audit_mode": "fixture_first_no_recompile",
        "recompiled_active_guardrails": False,
        "changed_sources": list(changed_sources.values()),
        "stale_predicates": stale_predicates,
        "stale_explanations": stale_explanations,
        "stale_refused_action_rules": stale_refused_rules,
        "stale_exact_confirmation_gates": stale_confirmation_gates,
        "required_human_review": required_human_review,
    }


def _mapping(raw: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = raw.get(key)
    if not isinstance(value, Mapping):
        raise StaleGuardrailAuditError(f"{key} must be an object")
    return value


def _required_text(raw: Mapping[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise StaleGuardrailAuditError(f"{key} must be a non-empty string")
    return value.strip()


def _list(raw: Mapping[str, Any], key: str) -> list[Any]:
    value = raw.get(key, [])
    if not isinstance(value, list):
        raise StaleGuardrailAuditError(f"{key} must be a list")
    return value


def _text_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise StaleGuardrailAuditError(f"{field_name} must be a list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise StaleGuardrailAuditError(f"{field_name} entries must be non-empty strings")
        result.append(item.strip())
    return result


def _changed_sources(registry_candidate: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    changed: dict[str, dict[str, Any]] = {}
    for source in _list(registry_candidate, "sources"):
        if not isinstance(source, Mapping):
            raise StaleGuardrailAuditError("source registry entries must be objects")
        source_id = _required_text(source, "source_id")
        previous_hash = str(source.get("previous_content_hash", "")).strip()
        current_hash = str(source.get("current_content_hash", "")).strip()
        status = str(source.get("freshness_status", "")).strip().lower()
        hash_changed = bool(previous_hash and current_hash and previous_hash != current_hash)
        if status in STALE_SOURCE_STATUSES or hash_changed:
            changed[source_id] = {
                "source_id": source_id,
                "canonical_url": _required_text(source, "canonical_url"),
                "freshness_status": status or "changed_hash",
                "previous_content_hash": previous_hash,
                "current_content_hash": current_hash,
                "change_reason": str(source.get("update_explanation", "source content changed")).strip(),
            }
    return changed


def _invalidation_by_source(decision_queue: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    decisions: dict[str, dict[str, Any]] = {}
    for decision in _list(decision_queue, "decisions"):
        if not isinstance(decision, Mapping):
            raise StaleGuardrailAuditError("invalidation decisions must be objects")
        source_id = _required_text(decision, "source_id")
        decision_name = _required_text(decision, "decision").lower()
        if decision_name not in INVALIDATION_DECISIONS:
            continue
        decisions[source_id] = {
            "source_id": source_id,
            "decision": decision_name,
            "affected_item_ids": _text_list(decision.get("affected_item_ids"), "affected_item_ids"),
            "rationale": str(decision.get("rationale", "invalidation queue requested review")).strip(),
            "requires_human_review": bool(decision.get("requires_human_review")),
        }
    return decisions


def _invalidated_item_ids(invalidation_by_source: Mapping[str, Mapping[str, Any]]) -> set[str]:
    invalidated: set[str] = set()
    for decision in invalidation_by_source.values():
        invalidated.update(_text_list(decision.get("affected_item_ids"), "affected_item_ids"))
    return invalidated


def _stale_guardrail_items(
    raw_items: Any,
    changed_sources: Mapping[str, Mapping[str, Any]],
    invalidated_item_ids: set[str],
) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        raise StaleGuardrailAuditError("guardrail item groups must be lists")

    stale: list[dict[str, Any]] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, Mapping):
            raise StaleGuardrailAuditError("guardrail items must be objects")
        item_id = _required_text(raw_item, "id")
        evidence_source_ids = _text_list(raw_item.get("source_evidence_ids"), "source_evidence_ids")
        stale_source_ids = [source_id for source_id in evidence_source_ids if source_id in changed_sources]
        invalidated = item_id in invalidated_item_ids
        if not stale_source_ids and not invalidated:
            continue

        reasons = []
        for source_id in stale_source_ids:
            reason = deepcopy(dict(changed_sources[source_id]))
            reasons.append(reason)
        if invalidated:
            reasons.append({"reason": "invalidation_decision_queue", "item_id": item_id})

        stale.append(
            {
                "id": item_id,
                "predicate": str(raw_item.get("predicate", raw_item.get("template", ""))).strip(),
                "source_evidence_ids": evidence_source_ids,
                "stale_source_ids": stale_source_ids,
                "staleness_reasons": reasons,
            }
        )

    return sorted(stale, key=lambda item: item["id"])


def _stale_items_by_source(stale_items: list[Mapping[str, Any]]) -> dict[str, list[str]]:
    by_source: dict[str, list[str]] = {}
    for item in stale_items:
        item_id = _required_text(item, "id")
        for source_id in _text_list(item.get("stale_source_ids"), "stale_source_ids"):
            by_source.setdefault(source_id, []).append(item_id)
    for item_ids in by_source.values():
        item_ids.sort()
    return by_source


def _required_human_review(
    invalidation_by_source: Mapping[str, Mapping[str, Any]],
    stale_by_source: Mapping[str, list[str]],
) -> list[dict[str, Any]]:
    review: list[dict[str, Any]] = []
    for source_id, decision in invalidation_by_source.items():
        if not bool(decision.get("requires_human_review")):
            continue
        stale_item_ids = list(stale_by_source.get(source_id, []))
        for item_id in _text_list(decision.get("affected_item_ids"), "affected_item_ids"):
            if item_id not in stale_item_ids:
                stale_item_ids.append(item_id)
        stale_item_ids.sort()
        review.append(
            {
                "source_id": source_id,
                "decision": str(decision.get("decision", "human_review")),
                "stale_item_ids": stale_item_ids,
                "review_reason": str(decision.get("rationale", "human review required")).strip(),
            }
        )
    return sorted(review, key=lambda item: item["source_id"])
