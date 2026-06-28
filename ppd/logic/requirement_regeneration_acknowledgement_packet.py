"""Fixture-first requirement regeneration reviewer acknowledgement packets.

The packet consumes a requirement regeneration queue plan and a deterministic
reviewer-decision fixture. It records affected source decisions, required
synthetic fixtures, citation refresh scope, human-review owner acknowledgement,
and whether downstream activation remains blocked pending acknowledgement.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping


COMPLETE_REVIEWER_DECISIONS = {
    "accepted_for_regeneration",
    "deferred",
    "needs_revision",
}


def load_json_object(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object in {path}")
    return data


def build_requirement_regeneration_acknowledgement_packet(
    queue_plan: Mapping[str, Any],
    reviewer_decisions: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a deterministic acknowledgement packet from queue and review fixtures."""

    decisions_by_source = _index_decisions(reviewer_decisions.get("reviewer_decisions"))
    source_acknowledgements: list[dict[str, Any]] = []

    for item in _queue_items(queue_plan):
        source_id = _text(item.get("source_id"))
        decision = decisions_by_source.get(source_id, {})
        source_acknowledgements.append(_source_acknowledgement(item, decision))

    acknowledgement_complete = bool(source_acknowledgements) and all(
        acknowledgement["acknowledgement_complete"] for acknowledgement in source_acknowledgements
    )

    return {
        "packet_id": "requirement-regeneration-acknowledgement-" + _text(queue_plan.get("plan_id"), "unknown-plan"),
        "packet_type": "ppd.requirement_regeneration_reviewer_acknowledgement.v1",
        "mode": "fixture_first",
        "live_crawl_required": False,
        "private_artifact_persistence": "forbidden",
        "consumed_queue_plan": {
            "plan_id": _text(queue_plan.get("plan_id")),
            "drift_digest_id": _text(queue_plan.get("drift_digest_id")),
            "queue_item_count": len(source_acknowledgements),
        },
        "review_fixture": {
            "fixture_id": _text(reviewer_decisions.get("fixture_id")),
            "prepared_at": _text(reviewer_decisions.get("prepared_at")),
        },
        "source_acknowledgements": source_acknowledgements,
        "acknowledgement_complete": acknowledgement_complete,
        "downstream_activation_blocked": not acknowledgement_complete,
        "activation_block_reason": _activation_block_reason(acknowledgement_complete),
        "next_allowed_step": "validate_acknowledgement_packet_before_any_process_or_guardrail_activation",
    }


def build_requirement_regeneration_acknowledgement_packet_from_files(
    queue_plan_path: str | Path,
    reviewer_decisions_path: str | Path,
) -> dict[str, Any]:
    return build_requirement_regeneration_acknowledgement_packet(
        load_json_object(queue_plan_path),
        load_json_object(reviewer_decisions_path),
    )


def _source_acknowledgement(item: Mapping[str, Any], decision: Mapping[str, Any]) -> dict[str, Any]:
    source_id = _text(item.get("source_id"))
    required_fixtures = _sorted_strings(item.get("required_synthetic_fixtures"))
    acknowledged_fixtures = _string_set(decision.get("acknowledged_required_synthetic_fixtures"))
    owners = _sorted_strings(item.get("human_review_owners"))
    acknowledged_owners = _string_set(decision.get("acknowledged_human_review_owners"))
    citation_refresh_scope = _sorted_strings(decision.get("citation_refresh_scope") or item.get("change_kinds"))
    reviewer_decision = _text(decision.get("reviewer_decision"), "pending")

    missing_fixtures = tuple(fixture for fixture in required_fixtures if fixture not in acknowledged_fixtures)
    missing_owners = tuple(owner for owner in owners if owner not in acknowledged_owners)
    acknowledgement_complete = (
        reviewer_decision in COMPLETE_REVIEWER_DECISIONS
        and not missing_fixtures
        and not missing_owners
        and bool(citation_refresh_scope)
    )

    return {
        "source_id": source_id,
        "queue_item_id": _text(item.get("queue_item_id")),
        "reviewer_decision": reviewer_decision,
        "decision_rationale": _text(decision.get("decision_rationale")),
        "affected_requirement_ids": _sorted_strings(item.get("affected_requirement_ids")),
        "affected_process_model_ids": _sorted_strings(item.get("affected_process_model_ids")),
        "affected_guardrail_bundle_ids": _sorted_strings(item.get("affected_guardrail_bundle_ids")),
        "required_synthetic_fixtures": required_fixtures,
        "acknowledged_required_synthetic_fixtures": tuple(sorted(acknowledged_fixtures)),
        "missing_required_synthetic_fixtures": missing_fixtures,
        "citation_refresh_scope": citation_refresh_scope,
        "human_review_owners": owners,
        "acknowledged_human_review_owners": tuple(sorted(acknowledged_owners)),
        "missing_human_review_owner_acknowledgements": missing_owners,
        "inherited_queue_activation_block": bool(item.get("blocked_downstream_activation", True)),
        "blocked_downstream_activation_until_acknowledgement_complete": not acknowledgement_complete,
        "acknowledgement_complete": acknowledgement_complete,
    }


def _activation_block_reason(acknowledgement_complete: bool) -> str:
    if acknowledgement_complete:
        return "acknowledgement_complete_validation_required_before_activation"
    return "reviewer_acknowledgement_required_before_guardrail_or_process_activation"


def _index_decisions(value: Any) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    if not isinstance(value, list):
        return indexed
    for decision in value:
        if isinstance(decision, Mapping):
            source_id = _text(decision.get("source_id"))
            if source_id:
                indexed[source_id] = decision
    return indexed


def _queue_items(queue_plan: Mapping[str, Any]) -> Iterable[Mapping[str, Any]]:
    items = queue_plan.get("queue_items")
    if not isinstance(items, list):
        return ()
    return tuple(item for item in items if isinstance(item, Mapping))


def _sorted_strings(value: Any) -> tuple[str, ...]:
    return tuple(sorted(_string_set(value)))


def _string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        text = value.strip()
        return {text} if text else set()
    if isinstance(value, Mapping):
        return {_text(value.get("id"))} - {""}
    if isinstance(value, list) or isinstance(value, tuple) or isinstance(value, set):
        values: set[str] = set()
        for item in value:
            values.update(_string_set(item))
        return values
    return set()


def _text(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        text = value.strip()
        return text if text else default
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default
