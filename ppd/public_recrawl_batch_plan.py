"""Fixture-first public recrawl batch planning for PP&D sources.

The planner is intentionally metadata-only: it validates reviewed public registry
fixtures and groups entries into dry-run batches without performing network I/O.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


_GROUP_FIELDS = (
    "cadence",
    "host",
    "rate_limit_bucket",
    "robots_policy_evidence",
    "processor_contract",
    "metadata_output_location",
    "dry_run_execution_window",
)


@dataclass(frozen=True)
class PublicRecrawlGroup:
    """A deterministic metadata-only dry-run recrawl group."""

    cadence: str
    host: str
    rate_limit_bucket: str
    robots_policy_evidence: str
    processor_contract: str
    metadata_output_location: str
    dry_run_execution_window: str
    source_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "cadence": self.cadence,
            "host": self.host,
            "rate_limit_bucket": self.rate_limit_bucket,
            "robots_policy_evidence": self.robots_policy_evidence,
            "processor_contract": self.processor_contract,
            "metadata_output_location": self.metadata_output_location,
            "dry_run_execution_window": self.dry_run_execution_window,
            "source_ids": list(self.source_ids),
            "network_requests_allowed": False,
            "output_mode": "metadata_only",
        }


def load_reviewed_public_registry(path: str | Path) -> list[dict[str, Any]]:
    """Load a reviewed public source registry fixture from JSON."""

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("public recrawl registry fixture must be a JSON list")
    return data


def build_public_recrawl_batch_plan(entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a deterministic dry-run batch plan from reviewed public entries."""

    groups: dict[tuple[str, ...], list[str]] = defaultdict(list)

    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("registry entries must be JSON objects")
        if entry.get("reviewed") is not True or entry.get("public_source") is not True:
            continue

        source_id = _required_text(entry, "source_id")
        url = _required_text(entry, "url")
        host = _host(url)
        group_key = (
            _required_text(entry, "cadence"),
            host,
            _required_text(entry, "rate_limit_bucket"),
            _required_text(entry, "robots_policy_evidence"),
            _required_text(entry, "processor_contract"),
            _required_text(entry, "metadata_output_location"),
            _required_text(entry, "dry_run_execution_window"),
        )
        groups[group_key].append(source_id)

    batch_groups = []
    for group_key in sorted(groups):
        values = dict(zip(_GROUP_FIELDS, group_key, strict=True))
        group = PublicRecrawlGroup(
            cadence=values["cadence"],
            host=values["host"],
            rate_limit_bucket=values["rate_limit_bucket"],
            robots_policy_evidence=values["robots_policy_evidence"],
            processor_contract=values["processor_contract"],
            metadata_output_location=values["metadata_output_location"],
            dry_run_execution_window=values["dry_run_execution_window"],
            source_ids=tuple(sorted(groups[group_key])),
        )
        batch_groups.append(group.as_dict())

    return {
        "plan_name": "ppd-public-recrawl-dry-run",
        "network_requests_allowed": False,
        "output_mode": "metadata_only",
        "groups": batch_groups,
    }


def write_metadata_only_plan(entries: list[dict[str, Any]], path: str | Path) -> dict[str, Any]:
    """Write the computed dry-run plan JSON without crawling sources."""

    plan = build_public_recrawl_batch_plan(entries)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return plan


def _required_text(entry: dict[str, Any], field: str) -> str:
    value = entry.get(field)
    if not isinstance(value, str) or not value.strip():
        source_id = entry.get("source_id", "")
        raise ValueError(f"registry entry {source_id!r} is missing required text field {field!r}")
    return value.strip()


def _host(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"public recrawl URL must include http(s) host: {url!r}")
    return parsed.hostname.lower()
