"""Build fixture-first post-release monitoring plans.

This module is intentionally side-effect free. It consumes committed fixture
packets and produces reviewer-facing monitoring checks and watch items without
fetching sources, opening browsers, running monitors, or changing schedules.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Mapping

DEFAULT_ALERT_THRESHOLDS = {
    "source_age_warning_days": 14,
    "source_age_critical_days": 30,
    "devhub_drift_warning_count": 1,
    "guardrail_regression_warning_count": 1,
    "missing_citation_abort_count": 1,
}

_RISK_TO_OWNER = {
    "high": "ppd_legal_guardrail_reviewer",
    "medium": "ppd_source_reviewer",
    "low": "ppd_release_reviewer",
}


def build_post_release_monitoring_plan(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic monitoring plan from fixture packet data.

    The returned plan is suitable for review and validation only. It records the
    checks that should be monitored after release, but it does not execute those
    checks or schedule future work.
    """

    thresholds = dict(DEFAULT_ALERT_THRESHOLDS)
    thresholds.update(packet.get("alert_thresholds", {}))

    source_evidence = _index_by_id(packet.get("source_evidence", []), "evidence_id")
    release_candidates = _as_list(packet.get("release_notes_candidates", []))
    freshness_badges = _as_list(packet.get("source_freshness_badges", []))
    drift_packets = _as_list(packet.get("devhub_drift_comparison_packets", []))

    abort_notes: list[str] = [
        "Fixture-only plan: do not run monitors, fetch sources, launch browsers, mutate schedules, or create private DevHub artifacts.",
    ]
    reviewer_owners: dict[str, set[str]] = defaultdict(set)

    monitoring_checks = _build_monitoring_checks(
        release_candidates,
        source_evidence,
        thresholds,
        reviewer_owners,
        abort_notes,
    )
    stale_source_watch_items = _build_stale_source_watch_items(
        freshness_badges,
        thresholds,
        reviewer_owners,
        abort_notes,
    )
    devhub_drift_watch_items = _build_devhub_drift_watch_items(
        drift_packets,
        reviewer_owners,
        abort_notes,
    )
    guardrail_regression_watch_items = _build_guardrail_regression_watch_items(
        release_candidates,
        drift_packets,
        source_evidence,
        reviewer_owners,
        abort_notes,
    )

    return {
        "plan_id": _require_text(packet, "plan_id"),
        "mode": "fixture_first_post_release_monitoring",
        "generated_from_fixture_at": _require_text(packet, "generated_from_fixture_at"),
        "does_not_run_monitors": True,
        "does_not_fetch_sources": True,
        "does_not_launch_browsers": True,
        "does_not_mutate_schedules": True,
        "monitoring_checks": monitoring_checks,
        "stale_source_watch_items": stale_source_watch_items,
        "devhub_drift_watch_items": devhub_drift_watch_items,
        "guardrail_regression_watch_items": guardrail_regression_watch_items,
        "reviewer_owners": {key: sorted(value) for key, value in sorted(reviewer_owners.items())},
        "alert_thresholds": thresholds,
        "abort_escalation_notes": sorted(set(abort_notes)),
    }


def _build_monitoring_checks(
    candidates: list[Mapping[str, Any]],
    source_evidence: Mapping[str, Mapping[str, Any]],
    thresholds: Mapping[str, int],
    reviewer_owners: dict[str, set[str]],
    abort_notes: list[str],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for candidate in candidates:
        candidate_id = _require_text(candidate, "candidate_id")
        risk = str(candidate.get("risk_level", "low")).lower()
        owner = str(candidate.get("reviewer_owner") or _RISK_TO_OWNER.get(risk, _RISK_TO_OWNER["low"]))
        citations = _citations_for_ids(candidate.get("source_evidence_ids", []), source_evidence, abort_notes)
        if not citations:
            abort_notes.append(f"Abort release note candidate {candidate_id}: no source citations were supplied.")
        reviewer_owners[owner].add(candidate_id)
        checks.append(
            {
                "check_id": f"post_release_check:{candidate_id}",
                "release_note_candidate_id": candidate_id,
                "title": _require_text(candidate, "title"),
                "owner": owner,
                "risk_level": risk,
                "citations": citations,
                "guardrail_bundle_ids": sorted(str(item) for item in candidate.get("guardrail_bundle_ids", [])),
                "alert_threshold": "missing citation abort" if not citations else _threshold_for_risk(risk, thresholds),
                "review_instruction": "Reviewer verifies the cited fixture evidence still supports the release note before any live monitoring is enabled.",
            }
        )
    return sorted(checks, key=lambda item: item["check_id"])


def _build_stale_source_watch_items(
    badges: list[Mapping[str, Any]],
    thresholds: Mapping[str, int],
    reviewer_owners: dict[str, set[str]],
    abort_notes: list[str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for badge in badges:
        source_id = _require_text(badge, "source_id")
        age_days = int(badge.get("age_days", 0))
        status = str(badge.get("freshness_status", "unknown")).lower()
        alert_level = "none"
        if status in {"stale", "expired"} or age_days >= thresholds["source_age_critical_days"]:
            alert_level = "critical"
        elif status in {"aging", "unknown"} or age_days >= thresholds["source_age_warning_days"]:
            alert_level = "warning"
        if alert_level == "none":
            continue
        citation = _require_text(badge, "citation")
        owner = str(badge.get("reviewer_owner", "ppd_source_reviewer"))
        reviewer_owners[owner].add(source_id)
        if alert_level == "critical":
            abort_notes.append(f"Escalate stale source {source_id}: refresh evidence before relying on affected guardrails.")
        items.append(
            {
                "watch_id": f"stale_source:{source_id}",
                "source_id": source_id,
                "owner": owner,
                "freshness_status": status,
                "age_days": age_days,
                "verified_at": _require_text(badge, "verified_at"),
                "alert_level": alert_level,
                "citation": citation,
                "required_review": "Confirm freshness from committed evidence before any live source check is scheduled.",
            }
        )
    return sorted(items, key=lambda item: item["watch_id"])


def _build_devhub_drift_watch_items(
    packets: list[Mapping[str, Any]],
    reviewer_owners: dict[str, set[str]],
    abort_notes: list[str],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for packet in packets:
        packet_id = _require_text(packet, "packet_id")
        expected_hash = _require_text(packet, "expected_surface_hash")
        observed_hash = _require_text(packet, "observed_surface_hash")
        drift_type = str(packet.get("drift_type", "unchanged")).lower()
        if drift_type == "unchanged" and expected_hash == observed_hash:
            continue
        surface_id = _require_text(packet, "surface_id")
        owner = str(packet.get("reviewer_owner", "ppd_devhub_surface_reviewer"))
        reviewer_owners[owner].add(surface_id)
        read_only = bool(packet.get("read_only_surface", False))
        alert_level = "warning" if read_only else "critical"
        if not read_only:
            abort_notes.append(f"Abort DevHub drift review {packet_id}: packet is not marked read-only.")
        items.append(
            {
                "watch_id": f"devhub_drift:{packet_id}",
                "packet_id": packet_id,
                "surface_id": surface_id,
                "owner": owner,
                "drift_type": drift_type,
                "read_only_surface": read_only,
                "alert_level": alert_level,
                "citation": _require_text(packet, "citation"),
                "expected_surface_hash": expected_hash,
                "observed_surface_hash": observed_hash,
                "required_review": "Compare fixture packet fields only; do not open DevHub or create browser/session artifacts.",
            }
        )
    return sorted(items, key=lambda item: item["watch_id"])


def _build_guardrail_regression_watch_items(
    candidates: list[Mapping[str, Any]],
    drift_packets: list[Mapping[str, Any]],
    source_evidence: Mapping[str, Mapping[str, Any]],
    reviewer_owners: dict[str, set[str]],
    abort_notes: list[str],
) -> list[dict[str, Any]]:
    guardrails: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        citations = _citations_for_ids(candidate.get("source_evidence_ids", []), source_evidence, abort_notes)
        for guardrail_id in candidate.get("guardrail_bundle_ids", []):
            key = str(guardrail_id)
            guardrails.setdefault(key, {"citations": set(), "release_note_candidate_ids": set(), "devhub_packet_ids": set()})
            guardrails[key]["citations"].update(citations)
            guardrails[key]["release_note_candidate_ids"].add(_require_text(candidate, "candidate_id"))
    for packet in drift_packets:
        for guardrail_id in packet.get("affected_guardrail_bundle_ids", []):
            key = str(guardrail_id)
            guardrails.setdefault(key, {"citations": set(), "release_note_candidate_ids": set(), "devhub_packet_ids": set()})
            guardrails[key]["citations"].add(_require_text(packet, "citation"))
            guardrails[key]["devhub_packet_ids"].add(_require_text(packet, "packet_id"))
    items: list[dict[str, Any]] = []
    for guardrail_id, data in guardrails.items():
        owner = "ppd_legal_guardrail_reviewer"
        reviewer_owners[owner].add(guardrail_id)
        citations = sorted(data["citations"])
        if not citations:
            abort_notes.append(f"Abort guardrail regression review {guardrail_id}: no citations were supplied.")
        items.append(
            {
                "watch_id": f"guardrail_regression:{guardrail_id}",
                "guardrail_bundle_id": guardrail_id,
                "owner": owner,
                "release_note_candidate_ids": sorted(data["release_note_candidate_ids"]),
                "devhub_packet_ids": sorted(data["devhub_packet_ids"]),
                "citations": citations,
                "alert_level": "warning" if citations else "critical",
                "required_review": "Run fixture validation and human review before any guardrail bundle is promoted after release.",
            }
        )
    return sorted(items, key=lambda item: item["watch_id"])


def _threshold_for_risk(risk: str, thresholds: Mapping[str, int]) -> str:
    if risk == "high":
        return f"alert on first stale source, DevHub drift, or guardrail regression; abort at {thresholds['missing_citation_abort_count']} missing citation"
    if risk == "medium":
        return f"alert at {thresholds['devhub_drift_warning_count']} DevHub drift or {thresholds['guardrail_regression_warning_count']} guardrail regression"
    return f"alert when source age reaches {thresholds['source_age_warning_days']} days or any cited drift appears"


def _citations_for_ids(ids: Any, evidence: Mapping[str, Mapping[str, Any]], abort_notes: list[str]) -> list[str]:
    citations: list[str] = []
    for evidence_id in _as_list(ids):
        key = str(evidence_id)
        record = evidence.get(key)
        if record is None:
            abort_notes.append(f"Abort cited monitoring check: missing source evidence fixture {key}.")
            continue
        citations.append(_require_text(record, "citation"))
    return sorted(set(citations))


def _index_by_id(records: Any, key: str) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for record in _as_list(records):
        indexed[_require_text(record, key)] = record
    return indexed


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    raise TypeError(f"expected list, got {type(value).__name__}")


def _require_text(record: Mapping[str, Any], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"missing required text field: {key}")
    if key.endswith("_at"):
        _parse_iso_datetime(value)
    return value


def _parse_iso_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
