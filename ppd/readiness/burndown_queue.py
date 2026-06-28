"""Build fixture-first PP&D release-blocker burn-down queues.

The queue consumes the implementation readiness reconciliation packet and emits
metadata-only burn-down items. It does not crawl, open DevHub, create browser
state, or mark any release path production-ready.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .reconciliation import REQUIRED_DISABLED_CAPABILITIES, validate_packet

_DIMENSION_ORDER = {
    "source_freshness": 0,
    "guardrail_staleness": 1,
    "regression_coverage": 2,
    "attended_pilot_evidence_readiness": 3,
    "owner_prompt": 4,
    "prerequisite_packet_id": 5,
}

_DIMENSION_BY_EVIDENCE = {
    "source-registry-candidate-packet": "source_freshness",
    "stale-guardrail-audit-packet": "guardrail_staleness",
    "agent-regression-matrix-packet": "regression_coverage",
    "attended-pilot-evidence-template-packet": "attended_pilot_evidence_readiness",
}

_PREREQUISITE_BY_DIMENSION = {
    "source_freshness": "source_registry_update_candidate",
    "guardrail_staleness": "stale_guardrail_audit",
    "regression_coverage": "agent_response_regression_matrix",
    "attended_pilot_evidence_readiness": "attended_pilot_evidence_template",
}

_OWNER_PROMPTS = {
    "source_freshness": "Review the source registry update candidate and decide whether cited metadata can be promoted without live crawl output.",
    "guardrail_staleness": "Resolve stale guardrail predicates against cited fixture evidence before any release approval.",
    "regression_coverage": "Review fixture-only regression coverage and identify the missing release evidence needed for agent responses.",
    "attended_pilot_evidence_readiness": "Prepare attended pilot evidence from the template without creating DevHub session artifacts or official actions.",
    "owner_prompt": "Assign an owner prompt for the unresolved release blocker.",
    "prerequisite_packet_id": "Link the blocker to its prerequisite packet before release review.",
}

_ACTION_REQUIRED = {
    "source_freshness": "source_registry_candidate_review",
    "guardrail_staleness": "stale_guardrail_review",
    "regression_coverage": "regression_gap_review",
    "attended_pilot_evidence_readiness": "attended_pilot_template_review",
    "owner_prompt": "owner_prompt_assignment",
    "prerequisite_packet_id": "prerequisite_packet_link_review",
}

_STATUS_FIELDS = {
    "source_freshness": "source_freshness_status",
    "guardrail_staleness": "guardrail_staleness_status",
    "regression_coverage": "regression_coverage_status",
    "attended_pilot_evidence_readiness": "attended_pilot_evidence_status",
    "owner_prompt": "owner_prompt_status",
    "prerequisite_packet_id": "prerequisite_packet_status",
}

_STATUS_VALUES = {
    "source_freshness": "candidate_not_promoted",
    "guardrail_staleness": "stale_requires_review",
    "regression_coverage": "fixture_only_not_release_approval",
    "attended_pilot_evidence_readiness": "template_only_no_live_pilot_record",
    "owner_prompt": "owner_prompt_required",
    "prerequisite_packet_id": "prerequisite_packet_required",
}

_FORBIDDEN_KEY_MARKERS = (
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "devhub_session",
    "har_path",
    "raw_body",
    "raw_crawl",
    "raw_html",
    "screenshot",
    "session_storage",
    "storage_state",
    "trace_path",
    "warc_path",
)

_READY_LABELS = {"production_ready", "ready_for_production", "ready_for_release", "release_ready", "ready"}


def load_burndown_queue_fixture(path: Path) -> dict[str, Any]:
    """Load a committed burn-down queue fixture."""
    with path.open("r", encoding="utf-8") as handle:
        queue = json.load(handle)
    if not isinstance(queue, dict):
        raise ValueError("burn-down queue fixture must be a JSON object")
    return queue


def build_burndown_queue(reconciliation_packet: Mapping[str, Any]) -> dict[str, Any]:
    """Build an ordered release-blocker burn-down queue from reconciliation data."""
    reconciliation_errors = validate_packet(reconciliation_packet)
    if reconciliation_errors:
        raise ValueError("invalid reconciliation packet: " + "; ".join(reconciliation_errors))

    blockers = _unresolved_release_blockers(reconciliation_packet)
    linked_artifacts = reconciliation_packet.get("linked_artifacts")
    if not isinstance(linked_artifacts, Mapping):
        linked_artifacts = {}

    ordered_items = []
    for blocker in blockers:
        dimension = _priority_dimension(blocker)
        prerequisite_key = _PREREQUISITE_BY_DIMENSION.get(dimension)
        prerequisite = linked_artifacts.get(prerequisite_key) if prerequisite_key else None
        if not isinstance(prerequisite, Mapping):
            prerequisite = {}
        ordered_items.append(_queue_item(blocker, dimension, prerequisite_key or "", prerequisite))

    ordered_items.sort(
        key=lambda item: (
            _DIMENSION_ORDER.get(str(item["priority_dimension"]), 99),
            str(item["owner_prompt"]),
            str(item["prerequisite_packet_id"]),
            str(item["blocker_id"]),
        )
    )
    for index, item in enumerate(ordered_items, start=1):
        item["rank"] = index

    return {
        "queue_id": "release-blocker-burndown-" + str(reconciliation_packet.get("packet_id", "unknown")),
        "queue_type": "ppd.release_blocker_burndown_queue.v1",
        "mode": "fixture_first",
        "reconciliation_packet": {
            "packet_id": str(reconciliation_packet.get("packet_id", "")),
            "packet_version": str(reconciliation_packet.get("packet_version", "")),
            "fixture": "ppd/tests/fixtures/readiness/reconciliation_packet.json",
        },
        "ordering_policy": [
            "source_freshness",
            "guardrail_staleness",
            "regression_coverage",
            "attended_pilot_evidence_readiness",
            "owner_prompt",
            "prerequisite_packet_id",
        ],
        "ordered_blockers": ordered_items,
        "open_blocker_count": len(ordered_items),
        "release_status": "blocked_by_open_release_blockers",
        "production_ready": False,
        "live_crawl_enabled": False,
        "devhub_automation_enabled": False,
        "disabled_capabilities": sorted(REQUIRED_DISABLED_CAPABILITIES),
    }


def validate_burndown_queue(queue: Mapping[str, Any]) -> list[str]:
    """Return narrow structural errors for a generated burn-down queue."""
    errors: list[str] = []
    if queue.get("queue_type") != "ppd.release_blocker_burndown_queue.v1":
        errors.append("queue_type must be ppd.release_blocker_burndown_queue.v1")
    if queue.get("mode") != "fixture_first":
        errors.append("mode must be fixture_first")
    if queue.get("production_ready") is not False:
        errors.append("production_ready must be false")
    if queue.get("live_crawl_enabled") is not False:
        errors.append("live_crawl_enabled must be false")
    if queue.get("devhub_automation_enabled") is not False:
        errors.append("devhub_automation_enabled must be false")

    disabled = queue.get("disabled_capabilities")
    disabled_set = {item for item in disabled if isinstance(item, str)} if isinstance(disabled, list) else set()
    missing = sorted(REQUIRED_DISABLED_CAPABILITIES.difference(disabled_set))
    if missing:
        errors.append("missing disabled capabilities: " + ", ".join(missing))

    reconciliation = queue.get("reconciliation_packet")
    if not isinstance(reconciliation, Mapping):
        errors.append("reconciliation_packet must be an object")
    else:
        for field in ("packet_id", "packet_version", "fixture"):
            if not _nonempty_text(reconciliation.get(field)):
                errors.append(f"reconciliation_packet.{field} is required")

    ordered = queue.get("ordered_blockers")
    if not isinstance(ordered, list) or not ordered:
        errors.append("ordered_blockers must be a non-empty list")
    else:
        expected_ranks = list(range(1, len(ordered) + 1))
        actual_ranks = [item.get("rank") for item in ordered if isinstance(item, Mapping)]
        if actual_ranks != expected_ranks:
            errors.append("ordered_blockers ranks must be contiguous and one-based")
        dimensions = [str(item.get("priority_dimension")) for item in ordered if isinstance(item, Mapping)]
        expected_dimensions = sorted(dimensions, key=lambda value: _DIMENSION_ORDER.get(value, 99))
        if dimensions != expected_dimensions:
            errors.append("ordered_blockers must follow the burn-down ordering policy")
        for index, item in enumerate(ordered):
            _validate_queue_item(item, index, errors)

    if queue.get("open_blocker_count") != len(ordered) if isinstance(ordered, list) else True:
        errors.append("open_blocker_count must match ordered_blockers length")

    _scan_for_forbidden_artifacts(queue, "queue", errors)
    _scan_for_ready_labels(queue, "queue", errors)
    return errors


def _unresolved_release_blockers(packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    unresolved_ids = packet.get("unresolved_blockers")
    unresolved = {str(item) for item in unresolved_ids} if isinstance(unresolved_ids, list) else set()
    blockers = packet.get("release_blockers")
    if not isinstance(blockers, list):
        return []
    results = []
    for blocker in blockers:
        if not isinstance(blocker, Mapping):
            continue
        blocker_id = blocker.get("id")
        if blocker.get("status") == "blocking" and (not unresolved or blocker_id in unresolved):
            results.append(blocker)
    return results


def _priority_dimension(blocker: Mapping[str, Any]) -> str:
    evidence_ids = blocker.get("source_evidence_ids")
    if isinstance(evidence_ids, list):
        for evidence_id in evidence_ids:
            dimension = _DIMENSION_BY_EVIDENCE.get(str(evidence_id))
            if dimension:
                return dimension
    blocker_id = str(blocker.get("id", ""))
    if "guardrail" in blocker_id:
        return "guardrail_staleness"
    if "regression" in blocker_id:
        return "regression_coverage"
    if "pilot" in blocker_id:
        return "attended_pilot_evidence_readiness"
    if "registry" in blocker_id or "source" in blocker_id:
        return "source_freshness"
    return "owner_prompt"


def _queue_item(
    blocker: Mapping[str, Any],
    dimension: str,
    prerequisite_key: str,
    prerequisite: Mapping[str, Any],
) -> dict[str, Any]:
    item = {
        "rank": 0,
        "blocker_id": str(blocker.get("id", "")),
        "status": "open",
        "priority_dimension": dimension,
        "summary": str(blocker.get("summary", "")),
        "source_evidence_ids": list(blocker.get("source_evidence_ids", [])),
        "owner_prompt": _OWNER_PROMPTS.get(dimension, _OWNER_PROMPTS["owner_prompt"]),
        "action_required": _ACTION_REQUIRED.get(dimension, _ACTION_REQUIRED["owner_prompt"]),
        "prerequisite_artifact": prerequisite_key,
        "prerequisite_packet_id": str(prerequisite.get("packet_id", "")),
        "prerequisite_packet_version": str(prerequisite.get("packet_version", "")),
        "automation_boundary": "fixture_only_no_live_crawl_no_devhub_automation",
    }
    for status_dimension, field in _STATUS_FIELDS.items():
        item[field] = _STATUS_VALUES[status_dimension] if status_dimension == dimension else "not_primary_ordering_dimension"
    return item


def _validate_queue_item(item: Any, index: int, errors: list[str]) -> None:
    if not isinstance(item, Mapping):
        errors.append(f"ordered_blockers[{index}] must be an object")
        return
    for field in (
        "blocker_id",
        "status",
        "priority_dimension",
        "summary",
        "owner_prompt",
        "action_required",
        "prerequisite_artifact",
        "prerequisite_packet_id",
        "prerequisite_packet_version",
        "automation_boundary",
    ):
        if not _nonempty_text(item.get(field)):
            errors.append(f"ordered_blockers[{index}].{field} is required")
    if item.get("status") != "open":
        errors.append(f"ordered_blockers[{index}].status must be open")
    if item.get("priority_dimension") not in _DIMENSION_ORDER:
        errors.append(f"ordered_blockers[{index}].priority_dimension is unknown")
    if not _text_list(item.get("source_evidence_ids")):
        errors.append(f"ordered_blockers[{index}].source_evidence_ids must be a non-empty list")
    if item.get("automation_boundary") != "fixture_only_no_live_crawl_no_devhub_automation":
        errors.append(f"ordered_blockers[{index}].automation_boundary must keep live systems disabled")


def _scan_for_forbidden_artifacts(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            key_normalized = _normalized(str(key))
            if any(marker in key_normalized for marker in _FORBIDDEN_KEY_MARKERS):
                errors.append(f"{child_path} forbidden private/session/raw artifact field is not allowed")
            _scan_for_forbidden_artifacts(child, child_path, errors)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_artifacts(child, f"{path}[{index}]", errors)


def _scan_for_ready_labels(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if str(key) != "production_ready":
                _scan_for_ready_labels(child, child_path, errors)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_ready_labels(child, f"{path}[{index}]", errors)
        return
    if isinstance(value, str) and _normalized(value) in _READY_LABELS:
        errors.append(f"{path} cannot mark the queue release-ready while blockers remain")


def _text_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_nonempty_text(item) for item in value)


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _normalized(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")
