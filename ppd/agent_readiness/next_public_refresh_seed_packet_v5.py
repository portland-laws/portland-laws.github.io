"""Fixture-first next public refresh seed packet v5.

This module intentionally consumes committed fixtures only. It does not crawl live
sites, download documents, open DevHub, persist raw bodies, or make legal or
permitting guarantees.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PACKET_VERSION = "next-public-refresh-seed-packet-v5"
REHEARSAL_VERSION = "post-activation-monitoring-rehearsal-v4"

OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/next_public_refresh_seed_packet_v5.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_next_public_refresh_seed_packet_v5.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

SOURCE_TYPE_WEIGHT = {
    "public_html": 9,
    "public_pdf": 8,
    "public_form": 7,
    "devhub_public": 6,
    "external_reference": 3,
}

FREQUENCY_WEIGHT = {
    "daily": 9,
    "every_few_days": 8,
    "weekly": 6,
    "monthly": 3,
    "quarterly": 1,
}

SKIPPED_REASON_WEIGHT = {
    "stale_source_hold": 14,
    "changed_requirement_risk": 12,
    "robots_or_policy_review": 10,
    "raw_download_not_permitted": 8,
    "private_or_authenticated": 7,
    "unsupported_content_type": 4,
    "outside_allowlist": 3,
}

REVIEWER_BY_SOURCE_TYPE = {
    "public_html": "public-content-reviewer",
    "public_pdf": "forms-and-pdf-reviewer",
    "public_form": "forms-and-pdf-reviewer",
    "devhub_public": "devhub-public-guidance-reviewer",
    "external_reference": "source-registry-reviewer",
}


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON object fixture from disk."""
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"fixture must contain a JSON object: {path}")
    return data


def build_seed_packet(registry: dict[str, Any], rehearsal: dict[str, Any]) -> dict[str, Any]:
    """Build the v5 seed packet from registry and rehearsal fixtures only."""
    _validate_registry_shape(registry)
    _validate_rehearsal_shape(rehearsal)

    observations = {
        item["source_id"]: item
        for item in rehearsal.get("source_observations", [])
        if isinstance(item, dict) and isinstance(item.get("source_id"), str)
    }

    candidates = []
    for source in registry.get("sources", []):
        source_id = source["source_id"]
        observation = observations.get(source_id, {})
        candidate = _candidate_from_source(source, observation)
        candidates.append(candidate)

    candidates.sort(key=lambda item: (-item["ranking_score"], item["source_id"]))
    for index, candidate in enumerate(candidates, start=1):
        candidate["rank"] = index

    packet = {
        "packet_version": PACKET_VERSION,
        "fixture_first": True,
        "consumed_fixture_versions": [REHEARSAL_VERSION, registry.get("registry_version")],
        "source_boundaries": {
            "live_crawl": False,
            "document_download": False,
            "raw_body_storage": False,
            "devhub_opened": False,
            "legal_or_permitting_guarantee": False,
        },
        "candidate_count": len(candidates),
        "ranking_inputs": [
            "stale-source holds",
            "changed requirement risk",
            "crawl frequency",
            "source type",
            "skipped-source reasons",
            "reviewer routing",
            "rollback notes",
            "offline validation commands",
        ],
        "candidates": candidates,
        "offline_validation_commands": OFFLINE_VALIDATION_COMMANDS,
    }
    validate_seed_packet(packet)
    return packet


def build_seed_packet_from_files(registry_path: str | Path, rehearsal_path: str | Path) -> dict[str, Any]:
    """Load fixtures and build a validated seed packet."""
    return build_seed_packet(load_json(registry_path), load_json(rehearsal_path))


def validate_seed_packet(packet: dict[str, Any]) -> None:
    """Validate the public refresh seed packet contract."""
    if packet.get("packet_version") != PACKET_VERSION:
        raise ValueError("unexpected packet_version")
    if packet.get("fixture_first") is not True:
        raise ValueError("packet must be fixture_first")

    boundaries = packet.get("source_boundaries")
    if not isinstance(boundaries, dict):
        raise ValueError("source_boundaries must be an object")
    for key in (
        "live_crawl",
        "document_download",
        "raw_body_storage",
        "devhub_opened",
        "legal_or_permitting_guarantee",
    ):
        if boundaries.get(key) is not False:
            raise ValueError(f"boundary must remain false: {key}")

    commands = packet.get("offline_validation_commands")
    if commands != OFFLINE_VALIDATION_COMMANDS:
        raise ValueError("offline validation commands must match the exact v5 command set")

    candidates = packet.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("candidates must be a non-empty list")

    previous_score: int | None = None
    for expected_rank, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            raise ValueError("candidate must be an object")
        rank = candidate.get("rank")
        score = candidate.get("ranking_score")
        if rank != expected_rank:
            raise ValueError("candidate ranks must be contiguous and sorted")
        if not isinstance(score, int) or isinstance(score, bool):
            raise ValueError("ranking_score must be an integer")
        if previous_score is not None and score > previous_score:
            raise ValueError("candidates must be sorted by descending ranking_score")
        previous_score = score
        _validate_candidate(candidate)


def _candidate_from_source(source: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    source_type = source.get("source_type", "external_reference")
    crawl_frequency = source.get("crawl_frequency", "monthly")
    skipped_reasons = _as_string_list(observation.get("skipped_source_reasons"))
    stale_source_hold = bool(observation.get("stale_source_hold", source.get("freshness_status") == "stale"))
    changed_requirement_risk = _risk_level(observation.get("changed_requirement_risk", "unknown"))
    ranking_score = _ranking_score(
        stale_source_hold=stale_source_hold,
        changed_requirement_risk=changed_requirement_risk,
        crawl_frequency=str(crawl_frequency),
        source_type=str(source_type),
        skipped_reasons=skipped_reasons,
    )

    reviewer = observation.get("reviewer_routing") or REVIEWER_BY_SOURCE_TYPE.get(
        str(source_type), "source-registry-reviewer"
    )
    rollback_notes = observation.get("rollback_notes") or _default_rollback_notes(source, skipped_reasons)

    return {
        "rank": 0,
        "source_id": source["source_id"],
        "canonical_url": source["canonical_url"],
        "source_type": source_type,
        "crawl_frequency": crawl_frequency,
        "freshness_status": source.get("freshness_status", "unknown"),
        "stale_source_hold": stale_source_hold,
        "changed_requirement_risk": changed_requirement_risk,
        "skipped_source_reasons": skipped_reasons,
        "reviewer_routing": str(reviewer),
        "rollback_notes": str(rollback_notes),
        "ranking_score": ranking_score,
        "candidate_basis": {
            "from_registry_placeholder": True,
            "from_post_activation_monitoring_rehearsal_v4": bool(observation),
            "no_live_fetch_performed": True,
        },
    }


def _ranking_score(
    *,
    stale_source_hold: bool,
    changed_requirement_risk: str,
    crawl_frequency: str,
    source_type: str,
    skipped_reasons: list[str],
) -> int:
    score = 0
    if stale_source_hold:
        score += 30
    if changed_requirement_risk == "high":
        score += 25
    elif changed_requirement_risk == "medium":
        score += 15
    elif changed_requirement_risk == "low":
        score += 5
    else:
        score += 2
    score += FREQUENCY_WEIGHT.get(crawl_frequency, 1)
    score += SOURCE_TYPE_WEIGHT.get(source_type, 1)
    for reason in skipped_reasons:
        score += SKIPPED_REASON_WEIGHT.get(reason, 1)
    return score


def _risk_level(value: Any) -> str:
    if value in {"high", "medium", "low", "unknown"}:
        return str(value)
    return "unknown"


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _default_rollback_notes(source: dict[str, Any], skipped_reasons: list[str]) -> str:
    source_id = source.get("source_id", "unknown-source")
    if skipped_reasons:
        return f"Keep {source_id} on the existing public registry placeholder until skipped-source reasons are reviewed offline."
    return f"Keep {source_id} on the existing public registry placeholder if validation fails."


def _validate_registry_shape(registry: dict[str, Any]) -> None:
    if not isinstance(registry.get("sources"), list) or not registry["sources"]:
        raise ValueError("registry fixture must include non-empty sources")
    for source in registry["sources"]:
        if not isinstance(source, dict):
            raise ValueError("registry source must be an object")
        for key in ("source_id", "canonical_url", "source_type", "crawl_frequency"):
            if not isinstance(source.get(key), str) or not source[key]:
                raise ValueError(f"registry source missing string field: {key}")
        if source.get("raw_body") is not None:
            raise ValueError("registry fixture must not include raw_body")


def _validate_rehearsal_shape(rehearsal: dict[str, Any]) -> None:
    if rehearsal.get("rehearsal_version") != REHEARSAL_VERSION:
        raise ValueError("unexpected rehearsal fixture version")
    observations = rehearsal.get("source_observations")
    if not isinstance(observations, list) or not observations:
        raise ValueError("rehearsal fixture must include source_observations")
    for observation in observations:
        if not isinstance(observation, dict):
            raise ValueError("rehearsal observation must be an object")
        if not isinstance(observation.get("source_id"), str):
            raise ValueError("rehearsal observation missing source_id")
        if observation.get("raw_body") is not None:
            raise ValueError("rehearsal fixture must not include raw_body")


def _validate_candidate(candidate: dict[str, Any]) -> None:
    required_string_fields = (
        "source_id",
        "canonical_url",
        "source_type",
        "crawl_frequency",
        "freshness_status",
        "changed_requirement_risk",
        "reviewer_routing",
        "rollback_notes",
    )
    for field in required_string_fields:
        if not isinstance(candidate.get(field), str) or not candidate[field]:
            raise ValueError(f"candidate missing string field: {field}")
    if not isinstance(candidate.get("stale_source_hold"), bool):
        raise ValueError("stale_source_hold must be a boolean")
    if not isinstance(candidate.get("skipped_source_reasons"), list):
        raise ValueError("skipped_source_reasons must be a list")
    basis = candidate.get("candidate_basis")
    if not isinstance(basis, dict):
        raise ValueError("candidate_basis must be an object")
    if basis.get("no_live_fetch_performed") is not True:
        raise ValueError("candidate must be marked no_live_fetch_performed")
