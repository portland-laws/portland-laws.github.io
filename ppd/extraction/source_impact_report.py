from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

BLOCKED_READINESS_PREFIX = "blocked_"
NOT_CURRENT_RECOMMENDATION_STATUS = "not_current"


@dataclass(frozen=True)
class SourceImpact:
    source_id: str
    changed_source_hash: str
    previous_source_hash: str
    change_reason: str
    affected_requirement_ids: tuple[str, ...]
    affected_process_ids: tuple[str, ...]
    affected_guardrail_bundle_ids: tuple[str, ...]
    blocked_readiness_statuses: tuple[str, ...]
    recommendation_status: str

    @property
    def recommendation_is_current(self) -> bool:
        return self.recommendation_status != NOT_CURRENT_RECOMMENDATION_STATUS


def load_source_impacts(report: Mapping[str, Any]) -> tuple[SourceImpact, ...]:
    entries = report.get("source_impacts")
    if not isinstance(entries, list):
        raise ValueError("source impact report must contain a source_impacts list")

    impacts: list[SourceImpact] = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("each source impact entry must be an object")
        impacts.append(
            SourceImpact(
                source_id=_required_str(entry, "source_id"),
                changed_source_hash=_required_str(entry, "changed_source_hash"),
                previous_source_hash=_required_str(entry, "previous_source_hash"),
                change_reason=_required_str(entry, "change_reason"),
                affected_requirement_ids=_required_str_tuple(entry, "affected_requirement_ids"),
                affected_process_ids=_required_str_tuple(entry, "affected_process_ids"),
                affected_guardrail_bundle_ids=_required_str_tuple(entry, "affected_guardrail_bundle_ids"),
                blocked_readiness_statuses=_required_str_tuple(entry, "blocked_readiness_statuses"),
                recommendation_status=_required_str(entry, "recommendation_status"),
            )
        )
    return tuple(impacts)


def changed_hash_impact_index(report: Mapping[str, Any]) -> dict[str, SourceImpact]:
    impacts = load_source_impacts(report)
    index: dict[str, SourceImpact] = {}
    for impact in impacts:
        if impact.changed_source_hash in index:
            raise ValueError(f"duplicate changed source hash: {impact.changed_source_hash}")
        index[impact.changed_source_hash] = impact
    return dict(sorted(index.items()))


def validate_blocked_before_current(report: Mapping[str, Any]) -> None:
    for impact in load_source_impacts(report):
        if impact.changed_source_hash == impact.previous_source_hash:
            raise ValueError(f"unchanged hash cannot produce impact: {impact.source_id}")
        if not impact.affected_requirement_ids:
            raise ValueError(f"missing affected requirements for {impact.source_id}")
        if not impact.affected_process_ids:
            raise ValueError(f"missing affected processes for {impact.source_id}")
        if not impact.affected_guardrail_bundle_ids:
            raise ValueError(f"missing affected guardrail bundles for {impact.source_id}")
        if not impact.blocked_readiness_statuses:
            raise ValueError(f"missing blocked readiness statuses for {impact.source_id}")
        for status in impact.blocked_readiness_statuses:
            if not status.startswith(BLOCKED_READINESS_PREFIX):
                raise ValueError(f"readiness status is not blocked for {impact.source_id}: {status}")
        if impact.recommendation_status != NOT_CURRENT_RECOMMENDATION_STATUS:
            raise ValueError(f"recommendation was marked current too early for {impact.source_id}")


def _required_str(entry: Mapping[str, Any], key: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be a non-empty string")
    return value


def _required_str_tuple(entry: Mapping[str, Any], key: str) -> tuple[str, ...]:
    value = entry.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{key} must be a non-empty list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError(f"{key} must contain only non-empty strings")
        result.append(item)
    return tuple(result)
