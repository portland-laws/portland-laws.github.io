"""Deterministic change-impact helpers for PP&D source snapshots.

The helpers in this module operate only on caller-supplied metadata. They do
not crawl live pages, fetch URLs, or persist raw source bodies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

_RAW_BODY_KEYS = frozenset(
    {
        "body",
        "raw_body",
        "html",
        "raw_html",
        "text",
        "raw_text",
        "content",
        "raw_content",
        "source_body",
        "document_body",
    }
)


@dataclass(frozen=True, order=True)
class SourceSnapshot:
    """Commit-safe source metadata used for deterministic impact analysis."""

    source_id: str
    canonical_url: str
    content_hash: str
    requirement_ids: tuple[str, ...] = field(default_factory=tuple)
    guardrail_bundle_ids: tuple[str, ...] = field(default_factory=tuple)
    semantic_signatures: tuple[str, ...] = field(default_factory=tuple)
    normalized_document_id: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SourceSnapshot":
        _reject_raw_body_keys(value)
        return cls(
            source_id=_required_string(value, "source_id"),
            canonical_url=_required_string(value, "canonical_url"),
            content_hash=_required_string(value, "content_hash"),
            requirement_ids=_sorted_strings(value.get("requirement_ids", ())),
            guardrail_bundle_ids=_sorted_strings(value.get("guardrail_bundle_ids", ())),
            semantic_signatures=_sorted_strings(value.get("semantic_signatures", ())),
            normalized_document_id=_optional_string(value.get("normalized_document_id")),
        )


@dataclass(frozen=True, order=True)
class SourceChangeImpact:
    """Impact record for one source whose metadata changed."""

    source_id: str
    canonical_url: str
    change_type: str
    previous_content_hash: str | None
    current_content_hash: str | None
    affected_requirement_ids: tuple[str, ...]
    affected_guardrail_bundle_ids: tuple[str, ...]
    changed_semantic_signatures: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "canonical_url": self.canonical_url,
            "change_type": self.change_type,
            "previous_content_hash": self.previous_content_hash,
            "current_content_hash": self.current_content_hash,
            "affected_requirement_ids": list(self.affected_requirement_ids),
            "affected_guardrail_bundle_ids": list(self.affected_guardrail_bundle_ids),
            "changed_semantic_signatures": list(self.changed_semantic_signatures),
        }


def compute_change_impacts(
    previous: Sequence[SourceSnapshot | Mapping[str, Any]],
    current: Sequence[SourceSnapshot | Mapping[str, Any]],
) -> tuple[SourceChangeImpact, ...]:
    """Return deterministic impact records for changed source metadata.

    Inputs may be ``SourceSnapshot`` instances or dictionaries with the same
    fields. Raw page bodies are rejected by key name so fixtures and manifests
    remain commit-safe.
    """

    previous_by_id = _index_snapshots(previous)
    current_by_id = _index_snapshots(current)
    impacts: list[SourceChangeImpact] = []

    for source_id in sorted(previous_by_id.keys() | current_by_id.keys()):
        old = previous_by_id.get(source_id)
        new = current_by_id.get(source_id)
        if old is None and new is not None:
            impacts.append(_impact_for_added(new))
            continue
        if new is None and old is not None:
            impacts.append(_impact_for_removed(old))
            continue
        if old is None or new is None:
            continue
        if _snapshot_signature(old) == _snapshot_signature(new):
            continue
        impacts.append(_impact_for_changed(old, new))

    return tuple(impacts)


def impacted_requirement_ids(impacts: Sequence[SourceChangeImpact]) -> tuple[str, ...]:
    """Return all affected requirement IDs from impact records."""

    values: set[str] = set()
    for impact in impacts:
        values.update(impact.affected_requirement_ids)
    return tuple(sorted(values))


def impacted_guardrail_bundle_ids(impacts: Sequence[SourceChangeImpact]) -> tuple[str, ...]:
    """Return all affected guardrail bundle IDs from impact records."""

    values: set[str] = set()
    for impact in impacts:
        values.update(impact.affected_guardrail_bundle_ids)
    return tuple(sorted(values))


def _index_snapshots(values: Sequence[SourceSnapshot | Mapping[str, Any]]) -> dict[str, SourceSnapshot]:
    indexed: dict[str, SourceSnapshot] = {}
    for value in values:
        snapshot = value if isinstance(value, SourceSnapshot) else SourceSnapshot.from_mapping(value)
        if snapshot.source_id in indexed:
            raise ValueError(f"duplicate source_id: {snapshot.source_id}")
        indexed[snapshot.source_id] = snapshot
    return indexed


def _impact_for_added(snapshot: SourceSnapshot) -> SourceChangeImpact:
    return SourceChangeImpact(
        source_id=snapshot.source_id,
        canonical_url=snapshot.canonical_url,
        change_type="added",
        previous_content_hash=None,
        current_content_hash=snapshot.content_hash,
        affected_requirement_ids=snapshot.requirement_ids,
        affected_guardrail_bundle_ids=snapshot.guardrail_bundle_ids,
        changed_semantic_signatures=snapshot.semantic_signatures,
    )


def _impact_for_removed(snapshot: SourceSnapshot) -> SourceChangeImpact:
    return SourceChangeImpact(
        source_id=snapshot.source_id,
        canonical_url=snapshot.canonical_url,
        change_type="removed",
        previous_content_hash=snapshot.content_hash,
        current_content_hash=None,
        affected_requirement_ids=snapshot.requirement_ids,
        affected_guardrail_bundle_ids=snapshot.guardrail_bundle_ids,
        changed_semantic_signatures=snapshot.semantic_signatures,
    )


def _impact_for_changed(old: SourceSnapshot, new: SourceSnapshot) -> SourceChangeImpact:
    return SourceChangeImpact(
        source_id=new.source_id,
        canonical_url=new.canonical_url,
        change_type="changed",
        previous_content_hash=old.content_hash,
        current_content_hash=new.content_hash,
        affected_requirement_ids=tuple(sorted(set(old.requirement_ids) | set(new.requirement_ids))),
        affected_guardrail_bundle_ids=tuple(sorted(set(old.guardrail_bundle_ids) | set(new.guardrail_bundle_ids))),
        changed_semantic_signatures=tuple(
            sorted(set(old.semantic_signatures) ^ set(new.semantic_signatures))
        ),
    )


def _snapshot_signature(snapshot: SourceSnapshot) -> tuple[Any, ...]:
    return (
        snapshot.canonical_url,
        snapshot.content_hash,
        snapshot.requirement_ids,
        snapshot.guardrail_bundle_ids,
        snapshot.semantic_signatures,
        snapshot.normalized_document_id,
    )


def _reject_raw_body_keys(value: Mapping[str, Any]) -> None:
    forbidden = sorted(_RAW_BODY_KEYS.intersection(value.keys()))
    if forbidden:
        names = ", ".join(forbidden)
        raise ValueError(f"raw source body fields are not allowed: {names}")


def _required_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a non-empty string")
    return item


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value:
        raise ValueError("optional string fields must be non-empty strings when present")
    return value


def _sorted_strings(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError("expected a sequence of strings")
    strings: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError("expected only non-empty strings")
        strings.append(item)
    return tuple(sorted(set(strings)))
