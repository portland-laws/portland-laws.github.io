"""Deterministic source freshness reporting helpers for PP&D fixtures.

The helper intentionally accepts plain dictionaries so callers can use it with
fixture data, crawl summaries, or daemon-produced JSON without extending shared
contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable


_DATETIME_FORMATS = (
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%d",
)


@dataclass(frozen=True)
class SourceFreshnessPolicy:
    """Policy for classifying a source observation as fresh or stale."""

    stale_after_days: int = 30
    missing_status: str = "missing"
    fresh_status: str = "fresh"
    stale_status: str = "stale"


def load_source_observations(path: Path | str) -> list[dict[str, Any]]:
    """Load source observations from a JSON file.

    The JSON may be either a list of observations or an object with a top-level
    ``sources`` list. This keeps fixture files compact while leaving room for
    metadata in future daemon outputs.
    """

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [_require_mapping(item) for item in data]
    if isinstance(data, dict) and isinstance(data.get("sources"), list):
        return [_require_mapping(item) for item in data["sources"]]
    raise ValueError("source observations JSON must be a list or an object with a sources list")


def build_source_freshness_report(
    observations: Iterable[dict[str, Any]],
    *,
    as_of: str | datetime,
    policy: SourceFreshnessPolicy | None = None,
) -> dict[str, Any]:
    """Build a deterministic freshness report from source observations."""

    active_policy = policy or SourceFreshnessPolicy()
    as_of_dt = _parse_datetime(as_of)
    source_rows = [
        _build_source_row(observation, as_of_dt=as_of_dt, policy=active_policy)
        for observation in observations
    ]
    source_rows.sort(key=lambda row: (row["source_id"], row["citation_id"]))

    status_counts: dict[str, int] = {}
    affected_bundle_ids: set[str] = set()
    for row in source_rows:
        status = row["freshness_status"]
        status_counts[status] = status_counts.get(status, 0) + 1
        if status != active_policy.fresh_status:
            affected_bundle_ids.update(row["guardrail_bundle_ids"])

    return {
        "as_of": _format_datetime(as_of_dt),
        "stale_after_days": active_policy.stale_after_days,
        "source_count": len(source_rows),
        "status_counts": dict(sorted(status_counts.items())),
        "affected_guardrail_bundle_ids": sorted(affected_bundle_ids),
        "sources": source_rows,
    }


def write_source_freshness_report(
    observations: Iterable[dict[str, Any]],
    output_path: Path | str,
    *,
    as_of: str | datetime,
    policy: SourceFreshnessPolicy | None = None,
) -> dict[str, Any]:
    """Build and write a deterministic source freshness report as JSON."""

    report = build_source_freshness_report(observations, as_of=as_of, policy=policy)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _build_source_row(
    observation: dict[str, Any],
    *,
    as_of_dt: datetime,
    policy: SourceFreshnessPolicy,
) -> dict[str, Any]:
    source_id = _require_text(observation, "source_id")
    citation_id = _require_text(observation, "citation_id")
    guardrail_bundle_ids = _string_list(observation.get("guardrail_bundle_ids", []), "guardrail_bundle_ids")
    last_seen_value = observation.get("last_seen_at")

    if last_seen_value in (None, ""):
        age_days = None
        freshness_status = policy.missing_status
        last_seen_at = None
    else:
        last_seen_dt = _parse_datetime(last_seen_value)
        age_days = max(0, (as_of_dt.date() - last_seen_dt.date()).days)
        freshness_status = policy.stale_status if age_days > policy.stale_after_days else policy.fresh_status
        last_seen_at = _format_datetime(last_seen_dt)

    return {
        "source_id": source_id,
        "citation_id": citation_id,
        "last_seen_at": last_seen_at,
        "freshness_status": freshness_status,
        "age_days": age_days,
        "guardrail_bundle_ids": sorted(set(guardrail_bundle_ids)),
    }


def _require_mapping(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("source observation entries must be objects")
    return value


def _require_text(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"source observation is missing required text field {key!r}")
    return value


def _string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError(f"{field_name} entries must be non-empty strings")
        result.append(item)
    return result


def _parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = _parse_datetime_text(value)
    else:
        raise ValueError("datetime value must be a string or datetime")

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_datetime_text(value: str) -> datetime:
    normalized = value.strip()
    for datetime_format in _DATETIME_FORMATS:
        try:
            return datetime.strptime(normalized, datetime_format)
        except ValueError:
            continue
    raise ValueError(f"unsupported datetime format: {value!r}")


def _format_datetime(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
