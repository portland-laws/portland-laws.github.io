"""Deterministic PP&D source change monitoring helpers.

The helpers in this module compare committed metadata fixtures only. They do
not crawl live sites and they intentionally reject raw page-body fields so the
same report shape can be used by later archival jobs without committing page
contents.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

_RAW_BODY_KEYS = frozenset(
    {
        "body",
        "html",
        "page_body",
        "raw_body",
        "raw_html",
        "raw_text",
        "text",
    }
)


@dataclass(frozen=True)
class SourceSnapshot:
    """Hash-only source metadata used for change monitoring."""

    source_id: str
    canonical_url: str
    content_hash: str
    requirement_ids: tuple[str, ...]
    process_ids: tuple[str, ...]
    guardrail_bundle_ids: tuple[str, ...]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "SourceSnapshot":
        return cls(
            source_id=_required_string(value, "source_id"),
            canonical_url=_required_string(value, "canonical_url"),
            content_hash=_required_string(value, "content_hash"),
            requirement_ids=_string_tuple(value.get("requirement_ids", ())),
            process_ids=_string_tuple(value.get("process_ids", ())),
            guardrail_bundle_ids=_string_tuple(value.get("guardrail_bundle_ids", ())),
        )


def load_change_fixture(path: Path) -> dict[str, Any]:
    """Load a fixture and fail closed if it contains raw page-body fields."""

    with path.open("r", encoding="utf-8") as fixture_file:
        fixture = json.load(fixture_file)
    reject_raw_body_fields(fixture)
    return fixture


def reject_raw_body_fields(value: Any, path: str = "$") -> None:
    """Reject raw page body keys in committed monitoring fixtures."""

    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in _RAW_BODY_KEYS:
                raise ValueError(f"raw page body field is not allowed at {path}.{key_text}")
            reject_raw_body_fields(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_raw_body_fields(child, f"{path}[{index}]")


def build_change_report(previous: Iterable[Mapping[str, Any]], current: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Compare source snapshots and return a deterministic affected-ID report."""

    previous_by_id = _snapshot_map(previous)
    current_by_id = _snapshot_map(current)

    changed_sources: list[dict[str, Any]] = []
    added_sources: list[dict[str, Any]] = []
    removed_sources: list[dict[str, Any]] = []

    for source_id in sorted(previous_by_id.keys() & current_by_id.keys()):
        old = previous_by_id[source_id]
        new = current_by_id[source_id]
        if old.content_hash == new.content_hash:
            continue
        changed_sources.append(
            {
                "source_id": source_id,
                "canonical_url": new.canonical_url,
                "previous_content_hash": old.content_hash,
                "current_content_hash": new.content_hash,
                "affected_requirement_ids": sorted(set(old.requirement_ids) | set(new.requirement_ids)),
                "affected_process_ids": sorted(set(old.process_ids) | set(new.process_ids)),
                "affected_guardrail_bundle_ids": sorted(
                    set(old.guardrail_bundle_ids) | set(new.guardrail_bundle_ids)
                ),
            }
        )

    for source_id in sorted(current_by_id.keys() - previous_by_id.keys()):
        snapshot = current_by_id[source_id]
        added_sources.append(_source_effect_record(snapshot))

    for source_id in sorted(previous_by_id.keys() - current_by_id.keys()):
        snapshot = previous_by_id[source_id]
        removed_sources.append(_source_effect_record(snapshot))

    affected_requirement_ids = _sorted_union(
        source["affected_requirement_ids"] for source in changed_sources + added_sources + removed_sources
    )
    affected_process_ids = _sorted_union(
        source["affected_process_ids"] for source in changed_sources + added_sources + removed_sources
    )
    affected_guardrail_bundle_ids = _sorted_union(
        source["affected_guardrail_bundle_ids"] for source in changed_sources + added_sources + removed_sources
    )

    return {
        "report_id": "fixture_change_monitor_report",
        "monitoring_mode": "deterministic_fixture",
        "live_crawl_performed": False,
        "raw_page_bodies_stored": False,
        "changed_sources": changed_sources,
        "added_sources": added_sources,
        "removed_sources": removed_sources,
        "affected_requirement_ids": affected_requirement_ids,
        "affected_process_ids": affected_process_ids,
        "affected_guardrail_bundle_ids": affected_guardrail_bundle_ids,
    }


def build_change_report_from_fixture(path: Path) -> dict[str, Any]:
    """Build a source change report from a committed fixture file."""

    fixture = load_change_fixture(path)
    return build_change_report(fixture["previous_sources"], fixture["current_sources"])


def _snapshot_map(values: Iterable[Mapping[str, Any]]) -> dict[str, SourceSnapshot]:
    snapshots: dict[str, SourceSnapshot] = {}
    for value in values:
        snapshot = SourceSnapshot.from_mapping(value)
        if snapshot.source_id in snapshots:
            raise ValueError(f"duplicate source_id: {snapshot.source_id}")
        snapshots[snapshot.source_id] = snapshot
    return snapshots


def _source_effect_record(snapshot: SourceSnapshot) -> dict[str, Any]:
    return {
        "source_id": snapshot.source_id,
        "canonical_url": snapshot.canonical_url,
        "content_hash": snapshot.content_hash,
        "affected_requirement_ids": sorted(snapshot.requirement_ids),
        "affected_process_ids": sorted(snapshot.process_ids),
        "affected_guardrail_bundle_ids": sorted(snapshot.guardrail_bundle_ids),
    }


def _sorted_union(groups: Iterable[Iterable[str]]) -> list[str]:
    values: set[str] = set()
    for group in groups:
        values.update(group)
    return sorted(values)


def _required_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a non-empty string")
    return item


def _string_tuple(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        raise ValueError("expected a list of strings")
    if not all(isinstance(item, str) and item for item in value):
        raise ValueError("expected a list of non-empty strings")
    return tuple(value)
