"""Metadata-only post-recrawl invalidation decision queue for PP&D.

The queue consumes review packets produced after a public recrawl and emits
follow-up decisions ordered by freshness risk. It intentionally carries only
identifiers, hashes, timestamps, and reason codes. Raw page bodies, extracted
full text, active bundle changes, and authenticated values are outside this
module's contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

_RAW_BODY_KEYS = frozenset(
    {
        "body",
        "raw_body",
        "raw_html",
        "html",
        "text",
        "page_text",
        "content",
        "document_body",
        "normalized_text",
        "authenticated_values",
        "screenshot",
        "trace",
        "har",
    }
)

_DECISION_KIND_ORDER = {
    "source": 0,
    "requirement": 1,
    "process_model": 2,
    "guardrail": 3,
    "agent_readiness": 4,
}

_REASON_WEIGHTS = {
    "source_missing_after_recrawl": 100,
    "robots_policy_changed": 94,
    "privacy_policy_changed": 92,
    "content_hash_changed": 88,
    "http_status_changed": 82,
    "canonical_url_changed": 78,
    "metadata_schema_changed": 74,
    "freshness_overdue": 70,
    "last_seen_stale": 66,
    "review_packet_warning": 60,
    "recrawl_skipped": 54,
    "processor_changed": 50,
    "new_source_discovered": 46,
    "source_unchanged": 12,
    "requirement_evidence_stale": 84,
    "requirement_evidence_changed": 80,
    "process_model_source_stale": 76,
    "guardrail_bundle_candidate_stale": 72,
    "agent_readiness_blocked_by_stale_guardrails": 68,
}

_FOLLOW_UP_BY_KIND = {
    "source": "review_source_metadata",
    "requirement": "review_requirement_evidence",
    "process_model": "review_process_model_dependencies",
    "guardrail": "compile_candidate_guardrail_review",
    "agent_readiness": "refresh_agent_readiness_assessment",
}


class PostRecrawlPacketError(ValueError):
    """Raised when a post-recrawl review packet is unsafe or malformed."""


@dataclass(frozen=True)
class InvalidationDecision:
    """A metadata-only follow-up decision emitted after a recrawl."""

    decision_id: str
    decision_kind: str
    target_id: str
    freshness_risk: int
    follow_up: str
    reasons: tuple[str, ...]
    source_ids: tuple[str, ...] = field(default_factory=tuple)
    requirement_ids: tuple[str, ...] = field(default_factory=tuple)
    process_model_ids: tuple[str, ...] = field(default_factory=tuple)
    guardrail_bundle_ids: tuple[str, ...] = field(default_factory=tuple)
    active_bundle_change: bool = False
    raw_body_persisted: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "decision_kind": self.decision_kind,
            "target_id": self.target_id,
            "freshness_risk": self.freshness_risk,
            "follow_up": self.follow_up,
            "reasons": list(self.reasons),
            "source_ids": list(self.source_ids),
            "requirement_ids": list(self.requirement_ids),
            "process_model_ids": list(self.process_model_ids),
            "guardrail_bundle_ids": list(self.guardrail_bundle_ids),
            "active_bundle_change": self.active_bundle_change,
            "raw_body_persisted": self.raw_body_persisted,
        }


def load_post_recrawl_packet(path: str | Path) -> dict[str, Any]:
    """Load and validate a metadata-only post-recrawl review packet."""

    packet_path = Path(path)
    with packet_path.open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise PostRecrawlPacketError("post-recrawl packet must be a JSON object")
    validate_metadata_only_packet(packet)
    return packet


def validate_metadata_only_packet(packet: Mapping[str, Any]) -> None:
    """Reject packets that contain raw bodies or active bundle mutations."""

    raw_paths = list(_find_raw_body_paths(packet))
    if raw_paths:
        joined = ", ".join(raw_paths[:5])
        raise PostRecrawlPacketError(f"post-recrawl packet contains raw body fields: {joined}")

    if bool(packet.get("active_bundle_change")):
        raise PostRecrawlPacketError("post-recrawl decisions must not change active guardrail bundles")

    for source in _list_of_dicts(packet.get("sources")):
        if bool(source.get("raw_body_persisted")):
            source_id = str(source.get("source_id", ""))
            raise PostRecrawlPacketError(f"source {source_id} indicates raw body persistence")


def build_invalidation_queue(packet: Mapping[str, Any]) -> list[InvalidationDecision]:
    """Build a deterministic freshness-risk ordered invalidation queue."""

    validate_metadata_only_packet(packet)
    captured_at = _parse_datetime(str(packet.get("captured_at", "")))
    decisions: list[InvalidationDecision] = []

    for source in _list_of_dicts(packet.get("sources")):
        decisions.extend(_source_decisions(source, captured_at))
        decisions.extend(_requirement_decisions(source))
        decisions.extend(_process_model_decisions(source))
        decisions.extend(_guardrail_decisions(source))
        decisions.extend(_agent_readiness_decisions(source))

    return sorted(
        _deduplicate(decisions),
        key=lambda item: (
            -item.freshness_risk,
            _DECISION_KIND_ORDER.get(item.decision_kind, 99),
            item.target_id,
            item.decision_id,
        ),
    )


def export_invalidation_queue(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Return a serializable decision queue without raw bodies or bundle changes."""

    queue = build_invalidation_queue(packet)
    return {
        "packet_id": str(packet.get("packet_id", "")),
        "captured_at": str(packet.get("captured_at", "")),
        "decision_count": len(queue),
        "decisions": [decision.as_dict() for decision in queue],
        "raw_body_persisted": False,
        "active_bundle_change": False,
    }


def _source_decisions(source: Mapping[str, Any], captured_at: datetime | None) -> list[InvalidationDecision]:
    source_id = _required_id(source, "source_id")
    reasons = _source_reasons(source, captured_at)
    if not reasons:
        return []
    return [
        InvalidationDecision(
            decision_id=_decision_id("source", source_id, reasons),
            decision_kind="source",
            target_id=source_id,
            freshness_risk=_risk_for(reasons),
            follow_up=_FOLLOW_UP_BY_KIND["source"],
            reasons=tuple(reasons),
            source_ids=(source_id,),
        )
    ]


def _requirement_decisions(source: Mapping[str, Any]) -> list[InvalidationDecision]:
    source_id = _required_id(source, "source_id")
    reasons = _dependency_reasons(source, "requirement")
    decisions = []
    for requirement_id in _strings(source.get("affected_requirement_ids")):
        decisions.append(
            InvalidationDecision(
                decision_id=_decision_id("requirement", requirement_id, reasons),
                decision_kind="requirement",
                target_id=requirement_id,
                freshness_risk=_risk_for(reasons),
                follow_up=_FOLLOW_UP_BY_KIND["requirement"],
                reasons=tuple(reasons),
                source_ids=(source_id,),
                requirement_ids=(requirement_id,),
            )
        )
    return decisions


def _process_model_decisions(source: Mapping[str, Any]) -> list[InvalidationDecision]:
    source_id = _required_id(source, "source_id")
    reasons = _dependency_reasons(source, "process_model")
    decisions = []
    for process_id in _strings(source.get("affected_process_model_ids")):
        decisions.append(
            InvalidationDecision(
                decision_id=_decision_id("process_model", process_id, reasons),
                decision_kind="process_model",
                target_id=process_id,
                freshness_risk=_risk_for(reasons),
                follow_up=_FOLLOW_UP_BY_KIND["process_model"],
                reasons=tuple(reasons),
                source_ids=(source_id,),
                process_model_ids=(process_id,),
            )
        )
    return decisions


def _guardrail_decisions(source: Mapping[str, Any]) -> list[InvalidationDecision]:
    source_id = _required_id(source, "source_id")
    reasons = _dependency_reasons(source, "guardrail")
    decisions = []
    for bundle_id in _strings(source.get("affected_guardrail_bundle_ids")):
        decisions.append(
            InvalidationDecision(
                decision_id=_decision_id("guardrail", bundle_id, reasons),
                decision_kind="guardrail",
                target_id=bundle_id,
                freshness_risk=_risk_for(reasons),
                follow_up=_FOLLOW_UP_BY_KIND["guardrail"],
                reasons=tuple(reasons),
                source_ids=(source_id,),
                guardrail_bundle_ids=(bundle_id,),
                active_bundle_change=False,
            )
        )
    return decisions


def _agent_readiness_decisions(source: Mapping[str, Any]) -> list[InvalidationDecision]:
    source_id = _required_id(source, "source_id")
    guardrail_ids = tuple(_strings(source.get("affected_guardrail_bundle_ids")))
    if not guardrail_ids:
        return []
    reasons = tuple(sorted(set(_dependency_reasons(source, "agent_readiness"))))
    if not reasons:
        return []
    target_id = "agent-readiness:" + source_id
    return [
        InvalidationDecision(
            decision_id=_decision_id("agent_readiness", target_id, reasons),
            decision_kind="agent_readiness",
            target_id=target_id,
            freshness_risk=_risk_for(reasons),
            follow_up=_FOLLOW_UP_BY_KIND["agent_readiness"],
            reasons=reasons,
            source_ids=(source_id,),
            guardrail_bundle_ids=guardrail_ids,
        )
    ]


def _source_reasons(source: Mapping[str, Any], captured_at: datetime | None) -> list[str]:
    reasons = list(_strings(source.get("freshness_reasons")))

    if source.get("previous_content_hash") and source.get("content_hash"):
        if source.get("previous_content_hash") != source.get("content_hash"):
            reasons.append("content_hash_changed")

    if source.get("previous_http_status") and source.get("http_status"):
        if str(source.get("previous_http_status")) != str(source.get("http_status")):
            reasons.append("http_status_changed")

    if source.get("previous_canonical_url") and source.get("canonical_url"):
        if source.get("previous_canonical_url") != source.get("canonical_url"):
            reasons.append("canonical_url_changed")

    if source.get("skipped_reason"):
        reasons.append("recrawl_skipped")

    if source.get("freshness_status") in {"missing", "not_seen"}:
        reasons.append("source_missing_after_recrawl")

    if source.get("freshness_status") in {"overdue", "stale"}:
        reasons.append("freshness_overdue")

    if _is_stale_last_seen(source.get("last_seen_at"), captured_at, int(source.get("stale_after_days", 30))):
        reasons.append("last_seen_stale")

    if not reasons and source.get("freshness_status") == "unchanged":
        reasons.append("source_unchanged")

    return sorted(set(reasons), key=lambda reason: (-_REASON_WEIGHTS.get(reason, 1), reason))


def _dependency_reasons(source: Mapping[str, Any], dependency_kind: str) -> tuple[str, ...]:
    source_reasons = _source_reasons(source, None)
    changed = any(reason in source_reasons for reason in ("content_hash_changed", "http_status_changed", "canonical_url_changed"))
    stale = any(reason in source_reasons for reason in ("freshness_overdue", "last_seen_stale", "source_missing_after_recrawl"))
    warnings = "review_packet_warning" in source_reasons

    reasons: list[str] = []
    if dependency_kind == "requirement":
        if changed:
            reasons.append("requirement_evidence_changed")
        if stale or warnings:
            reasons.append("requirement_evidence_stale")
    elif dependency_kind == "process_model":
        if changed or stale or warnings:
            reasons.append("process_model_source_stale")
    elif dependency_kind == "guardrail":
        if changed or stale or warnings:
            reasons.append("guardrail_bundle_candidate_stale")
    elif dependency_kind == "agent_readiness":
        if changed or stale or warnings:
            reasons.append("agent_readiness_blocked_by_stale_guardrails")

    if not reasons and source_reasons:
        reasons.extend(source_reasons)
    return tuple(sorted(set(reasons), key=lambda reason: (-_REASON_WEIGHTS.get(reason, 1), reason)))


def _risk_for(reasons: Sequence[str]) -> int:
    if not reasons:
        return 0
    return min(100, max(_REASON_WEIGHTS.get(reason, 1) for reason in reasons))


def _decision_id(kind: str, target_id: str, reasons: Sequence[str]) -> str:
    reason_token = "+".join(sorted(reasons)) if reasons else "review"
    return f"post-recrawl:{kind}:{target_id}:{reason_token}"


def _deduplicate(decisions: Iterable[InvalidationDecision]) -> list[InvalidationDecision]:
    by_id: dict[str, InvalidationDecision] = {}
    for decision in decisions:
        current = by_id.get(decision.decision_id)
        if current is None or decision.freshness_risk > current.freshness_risk:
            by_id[decision.decision_id] = decision
    return list(by_id.values())


def _find_raw_body_paths(value: Any, path: str = "$") -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text.lower() in _RAW_BODY_KEYS:
                yield child_path
            yield from _find_raw_body_paths(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _find_raw_body_paths(child, f"{path}[{index}]")


def _list_of_dicts(value: Any) -> list[Mapping[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise PostRecrawlPacketError("expected a list of objects")
    result = []
    for item in value:
        if not isinstance(item, Mapping):
            raise PostRecrawlPacketError("expected a list of objects")
        result.append(item)
    return result


def _strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        return []
    return sorted({str(item) for item in value if str(item)})


def _required_id(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not value:
        raise PostRecrawlPacketError(f"missing required id field: {key}")
    return str(value)


def _parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_stale_last_seen(value: Any, captured_at: datetime | None, stale_after_days: int) -> bool:
    if captured_at is None or not value:
        return False
    last_seen = _parse_datetime(str(value))
    if last_seen is None:
        return False
    return (captured_at - last_seen).days >= stale_after_days
