from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "source_freshness"
FREQUENCY_LIMITS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(days=7),
    "monthly": timedelta(days=31),
}


def _load_fixture(name: str) -> dict[str, Any]:
    with (FIXTURE_DIR / name).open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _parse_instant(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _latest_manifest_by_source(manifests: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for manifest in manifests:
        source_id = manifest["source_id"]
        finished_at = _parse_instant(manifest.get("capture_finished_at"))
        previous_finished_at = _parse_instant(latest.get(source_id, {}).get("capture_finished_at"))
        if previous_finished_at is None or (finished_at is not None and finished_at > previous_finished_at):
            latest[source_id] = manifest
    return latest


def _sorted_items(items: list[Any]) -> list[Any]:
    return sorted(items, key=lambda item: item if isinstance(item, str) else item["source_id"])


def build_fixture_source_freshness_report(
    registry: dict[str, Any], archive_manifest: dict[str, Any]
) -> dict[str, Any]:
    as_of_text = registry["as_of"]
    as_of = _parse_instant(as_of_text)
    if as_of is None:
        raise AssertionError("registry fixture must include an as_of timestamp")

    latest_by_source = _latest_manifest_by_source(archive_manifest["manifests"])
    report: dict[str, Any] = {
        "as_of": as_of_text,
        "fresh": [],
        "stale": [],
        "missing": [],
        "changed_hash": [],
        "intentionally_deferred": [],
    }

    for source in registry["sources"]:
        source_id = source["source_id"]
        if source.get("freshness_status") == "intentionally_deferred":
            report["intentionally_deferred"].append(
                {
                    "source_id": source_id,
                    "deferred_until": source.get("deferred_until"),
                    "deferred_reason": source.get("deferred_reason"),
                }
            )
            continue

        latest_manifest = latest_by_source.get(source_id)
        if latest_manifest is None:
            report["missing"].append(source_id)
            continue

        expected_hash = source.get("expected_content_hash")
        actual_hash = latest_manifest.get("content_hash")
        if expected_hash is not None and expected_hash != actual_hash:
            report["changed_hash"].append(
                {
                    "source_id": source_id,
                    "expected_content_hash": expected_hash,
                    "actual_content_hash": actual_hash,
                }
            )
            continue

        crawl_frequency = source.get("crawl_frequency")
        freshness_limit = FREQUENCY_LIMITS.get(crawl_frequency)
        last_capture_at = _parse_instant(latest_manifest.get("capture_finished_at"))
        if freshness_limit is not None and last_capture_at is not None and as_of - last_capture_at > freshness_limit:
            report["stale"].append(
                {
                    "source_id": source_id,
                    "last_capture_at": latest_manifest["capture_finished_at"],
                    "crawl_frequency": crawl_frequency,
                }
            )
            continue

        report["fresh"].append(source_id)

    for key in ("fresh", "stale", "missing", "changed_hash", "intentionally_deferred"):
        report[key] = _sorted_items(report[key])
    return report


def test_fixture_source_freshness_report_flags_public_source_states_without_network_access() -> None:
    registry = _load_fixture("source_registry.json")
    archive_manifest = _load_fixture("archive_manifest.json")
    expected_report = _load_fixture("expected_report.json")

    assert build_fixture_source_freshness_report(registry, archive_manifest) == expected_report


def test_fixture_archive_manifest_does_not_persist_raw_public_bodies() -> None:
    archive_manifest = _load_fixture("archive_manifest.json")

    assert archive_manifest["manifests"]
    for manifest in archive_manifest["manifests"]:
        assert manifest["archive_artifact_ref"].startswith("fixture://")
        assert manifest["no_raw_body_persisted"] is True


def test_fixture_paths_are_ppd_local() -> None:
    assert FIXTURE_DIR == Path(__file__).parent / "fixtures" / "source_freshness"
