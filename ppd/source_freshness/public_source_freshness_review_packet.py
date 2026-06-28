"""Reviewer-owned public source freshness review packets.

This module consumes already-built fixture packets: a public source monitoring
schedule candidate and a post-release audit findings packet. It produces a
review-only decision packet. It never fetches URLs, downloads documents, mutates
live schedules, or persists raw crawl output.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import re
from typing import Any, Mapping
from urllib.parse import urlparse

from ppd.agent_readiness.post_release_audit_validation import require_post_release_audit_findings_packet
from ppd.source_freshness.public_source_monitoring_schedule_candidate import (
    ALLOWED_CADENCES,
    validate_public_source_monitoring_schedule_candidate,
)

PACKET_TYPE = "ppd.public_source_freshness_review_packet.v1"
MODE = "fixture_first_public_source_freshness_review"

FORBIDDEN_KEYS = {
    "archive_path",
    "auth_state",
    "body",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "download_path",
    "downloaded_document_path",
    "har_path",
    "html",
    "local_path",
    "password",
    "raw_body",
    "raw_content",
    "raw_html",
    "screenshot_path",
    "session_state",
    "storage_state",
    "trace_path",
    "warc_path",
}
LIVE_TRUE_KEYS = {
    "allow_live_network",
    "download_documents",
    "fetch_urls",
    "live_schedule_mutated",
    "network_allowed",
    "network_invoked",
    "persist_raw_body",
    "schedule_mutation_allowed",
    "writes_live_schedule",
}
PRIVATE_PATH_MARKERS = ("/account", "/admin", "/auth", "/dashboard", "/login", "/payment", "/session", "/upload")
PRIVATE_QUERY_MARKERS = ("access_token=", "auth=", "password=", "session=", "token=")


@dataclass(frozen=True)
class PublicSourceFreshnessReviewValidationResult:
    """Deterministic validation result for freshness review packets."""

    valid: bool
    errors: tuple[str, ...]


def build_public_source_freshness_review_packet(
    public_source_monitoring_schedule_candidate: Mapping[str, Any],
    post_release_audit_findings_packet: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build a reviewer-owned source freshness review packet from fixtures."""

    schedule_candidate = deepcopy(dict(public_source_monitoring_schedule_candidate))
    audit_findings = deepcopy(dict(post_release_audit_findings_packet))

    schedule_result = validate_public_source_monitoring_schedule_candidate(schedule_candidate)
    if not schedule_result.valid:
        raise ValueError("invalid public source monitoring schedule candidate: " + "; ".join(schedule_result.errors))
    require_post_release_audit_findings_packet(audit_findings)

    audit_finding_ids = _audit_finding_ids(audit_findings)
    audit_defer_reasons = _audit_defer_reasons(audit_findings)
    decisions = [
        _decision_from_recommendation(recommendation, audit_finding_ids, audit_defer_reasons)
        for recommendation in _recommendations(schedule_candidate)
    ]

    packet = {
        "packet_type": PACKET_TYPE,
        "mode": MODE,
        "generated_at": generated_at,
        "fixture_first": True,
        "metadata_only": True,
        "execution_policy": {
            "network_allowed": False,
            "network_invoked": False,
            "fetch_urls": False,
            "download_documents": False,
            "persist_raw_body": False,
            "schedule_mutation_allowed": False,
            "live_schedule_mutated": False,
        },
        "input_artifacts": {
            "schedule_candidate_packet_type": _text(schedule_candidate.get("packet_type")),
            "schedule_candidate_mode": _text(schedule_candidate.get("mode")),
            "post_release_audit_packet_type": _text(audit_findings.get("packet_type")),
            "post_release_audit_release_status": _text(audit_findings.get("release_status")),
        },
        "source_ids": sorted(_text(decision.get("source_id")) for decision in decisions),
        "reviewer_owned_source_freshness_decisions": decisions,
        "packet_level_prerequisite_evidence_ids": sorted(
            set(_string_list(schedule_candidate.get("robots_policy_prerequisite_ids")))
        ),
        "post_release_audit_finding_ids": audit_finding_ids,
        "defer_reason_catalog": audit_defer_reasons,
        "schedule_mutation_outcome": {
            "writes_live_schedule": False,
            "live_schedule_mutated": False,
            "requires_separate_reviewer_approval": True,
            "allowed_next_step": "review_source_freshness_decisions_without_fetching_urls",
        },
    }
    result = validate_public_source_freshness_review_packet(packet)
    if not result.valid:
        raise ValueError("invalid public source freshness review packet: " + "; ".join(result.errors))
    return packet


def validate_public_source_freshness_review_packet(packet: Mapping[str, Any]) -> PublicSourceFreshnessReviewValidationResult:
    """Validate a public source freshness review packet without side effects."""

    errors: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        errors.append("packet_type must be " + PACKET_TYPE)
    if packet.get("mode") != MODE:
        errors.append("mode must be " + MODE)
    if packet.get("fixture_first") is not True:
        errors.append("fixture_first must be true")
    if packet.get("metadata_only") is not True:
        errors.append("metadata_only must be true")

    policy = _mapping(packet.get("execution_policy"))
    for key in (
        "network_allowed",
        "network_invoked",
        "fetch_urls",
        "download_documents",
        "persist_raw_body",
        "schedule_mutation_allowed",
        "live_schedule_mutated",
    ):
        if policy.get(key) is not False:
            errors.append(f"execution_policy.{key} must be false")

    source_ids = set(_string_list(packet.get("source_ids")))
    if not source_ids:
        errors.append("source_ids must be non-empty")

    decisions = packet.get("reviewer_owned_source_freshness_decisions")
    if not isinstance(decisions, list) or not decisions:
        errors.append("reviewer_owned_source_freshness_decisions must be a non-empty list")
    else:
        for index, decision in enumerate(decisions):
            _validate_decision(decision, index, source_ids, errors)

    if not _string_list(packet.get("packet_level_prerequisite_evidence_ids")):
        errors.append("packet_level_prerequisite_evidence_ids must be non-empty")
    if not _string_list(packet.get("post_release_audit_finding_ids")):
        errors.append("post_release_audit_finding_ids must be non-empty")
    if not isinstance(packet.get("defer_reason_catalog"), list) or not packet.get("defer_reason_catalog"):
        errors.append("defer_reason_catalog must be a non-empty list")

    outcome = _mapping(packet.get("schedule_mutation_outcome"))
    if outcome.get("writes_live_schedule") is not False:
        errors.append("schedule_mutation_outcome.writes_live_schedule must be false")
    if outcome.get("live_schedule_mutated") is not False:
        errors.append("schedule_mutation_outcome.live_schedule_mutated must be false")
    if outcome.get("requires_separate_reviewer_approval") is not True:
        errors.append("schedule_mutation_outcome.requires_separate_reviewer_approval must be true")

    _validate_no_forbidden_fields(packet, "$", errors)
    return PublicSourceFreshnessReviewValidationResult(valid=not errors, errors=tuple(errors))


def _decision_from_recommendation(
    recommendation: Mapping[str, Any],
    audit_finding_ids: list[str],
    audit_defer_reasons: list[dict[str, str]],
) -> dict[str, Any]:
    source_id = _text(recommendation.get("source_id"))
    cadence = _text(recommendation.get("recommended_cadence"), "manual_review_before_recrawl")
    prerequisite_ids = sorted(set(_string_list(recommendation.get("robots_policy_prerequisite_ids"))))
    defer_reason_ids = [_text(reason.get("reason_id")) for reason in audit_defer_reasons if _text(reason.get("reason_id"))]
    if _string_list(recommendation.get("abort_condition_ids")):
        defer_reason_ids.append("schedule-candidate-abort-conditions-require-review")

    return {
        "decision_id": "source-freshness-decision-" + _slug(source_id),
        "source_id": source_id,
        "reviewer_owner": _text(recommendation.get("reviewer_owner"), "ppd-source-reviewer"),
        "decision_status": "deferred_pending_reviewer_approval",
        "source_freshness_decision": "defer_live_schedule_mutation",
        "source_ids_confirmed": [source_id],
        "cadence_note": {
            "candidate_cadence": cadence,
            "reviewer_owned": True,
            "note": _text(recommendation.get("rationale"), "Reviewer must decide cadence from fixture metadata only."),
        },
        "prerequisite_robots_policy_evidence_ids": prerequisite_ids,
        "post_release_audit_finding_ids": audit_finding_ids,
        "stale_source_acknowledgement": {
            "acknowledgement_id": "stale-source-ack-" + _slug(source_id),
            "acknowledgement_status": "acknowledged_for_review_only",
            "does_not_refresh_source": True,
            "requires_reviewer_decision_before_use": True,
        },
        "defer_reason_ids": sorted(set(defer_reason_ids)),
    }


def _validate_decision(value: Any, index: int, source_ids: set[str], errors: list[str]) -> None:
    prefix = f"reviewer_owned_source_freshness_decisions[{index}]"
    if not isinstance(value, Mapping):
        errors.append(prefix + " must be an object")
        return
    source_id = _text(value.get("source_id"))
    if not source_id or source_id not in source_ids:
        errors.append(prefix + ".source_id must be declared in source_ids")
    if value.get("decision_status") != "deferred_pending_reviewer_approval":
        errors.append(prefix + ".decision_status must be deferred_pending_reviewer_approval")
    if value.get("source_freshness_decision") != "defer_live_schedule_mutation":
        errors.append(prefix + ".source_freshness_decision must defer live schedule mutation")
    if not _text(value.get("reviewer_owner")):
        errors.append(prefix + ".reviewer_owner is required")
    if _string_list(value.get("source_ids_confirmed")) != [source_id]:
        errors.append(prefix + ".source_ids_confirmed must contain exactly the decision source_id")

    cadence_note = _mapping(value.get("cadence_note"))
    if cadence_note.get("candidate_cadence") not in ALLOWED_CADENCES:
        errors.append(prefix + ".cadence_note.candidate_cadence is invalid")
    if cadence_note.get("reviewer_owned") is not True:
        errors.append(prefix + ".cadence_note.reviewer_owned must be true")
    if not _text(cadence_note.get("note")):
        errors.append(prefix + ".cadence_note.note is required")

    if not _string_list(value.get("prerequisite_robots_policy_evidence_ids")):
        errors.append(prefix + ".prerequisite_robots_policy_evidence_ids must be non-empty")
    if not _string_list(value.get("post_release_audit_finding_ids")):
        errors.append(prefix + ".post_release_audit_finding_ids must be non-empty")
    if not _string_list(value.get("defer_reason_ids")):
        errors.append(prefix + ".defer_reason_ids must be non-empty")

    acknowledgement = _mapping(value.get("stale_source_acknowledgement"))
    if acknowledgement.get("acknowledgement_status") != "acknowledged_for_review_only":
        errors.append(prefix + ".stale_source_acknowledgement.acknowledgement_status must be acknowledged_for_review_only")
    if acknowledgement.get("does_not_refresh_source") is not True:
        errors.append(prefix + ".stale_source_acknowledgement.does_not_refresh_source must be true")
    if acknowledgement.get("requires_reviewer_decision_before_use") is not True:
        errors.append(prefix + ".stale_source_acknowledgement.requires_reviewer_decision_before_use must be true")


def _audit_finding_ids(packet: Mapping[str, Any]) -> list[str]:
    findings = packet.get("findings")
    ids: list[str] = []
    if isinstance(findings, list):
        for index, finding in enumerate(findings, 1):
            if isinstance(finding, Mapping):
                ids.append(_text(finding.get("finding_id"), f"post-release-audit-finding-{index}"))
    return sorted(set(ids)) or ["post-release-audit-findings-present"]


def _audit_defer_reasons(packet: Mapping[str, Any]) -> list[dict[str, str]]:
    reasons = [
        {
            "reason_id": "post-release-audit-requires-reviewer-source-freshness-decision",
            "description": "Post-release audit findings must be reviewed before source freshness decisions can affect downstream guardrails.",
        }
    ]
    if packet.get("production_ready") is not True:
        reasons.append(
            {
                "reason_id": "post-release-audit-not-production-ready",
                "description": "Audit packet is not production-ready, so source freshness output remains review-only.",
            }
        )
    release_status = _text(packet.get("release_status"))
    if release_status and release_status != "production_ready":
        reasons.append(
            {
                "reason_id": "post-release-audit-" + _slug(release_status),
                "description": "Audit release status requires a reviewer-owned defer decision: " + release_status,
            }
        )
    return reasons


def _recommendations(packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    value = packet.get("cadence_recommendations")
    if isinstance(value, list):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _text(value: Any, default: str = "") -> str:
    return value.strip() if isinstance(value, str) and value.strip() else default


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "unknown-source"


def _validate_no_forbidden_fields(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            child_path = f"{path}.{key_text}"
            if lowered in FORBIDDEN_KEYS:
                errors.append(child_path + " is forbidden in source freshness review packets")
            if lowered in LIVE_TRUE_KEYS and child is True:
                errors.append(child_path + " must not be true")
            _validate_no_forbidden_fields(child, child_path, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_no_forbidden_fields(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        lowered_value = value.lower()
        if any(marker in lowered_value for marker in (".har", ".warc", "trace.zip", "raw_body", "download_path")):
            errors.append(path + " must not reference raw crawl or browser artifacts")
        parsed = urlparse(value)
        if parsed.scheme in {"http", "https"}:
            query = parsed.query.lower()
            path_lower = parsed.path.lower()
            if any(marker in path_lower for marker in PRIVATE_PATH_MARKERS) or any(marker in query for marker in PRIVATE_QUERY_MARKERS):
                errors.append(path + " must not reference private or authenticated URLs")


__all__ = [
    "PACKET_TYPE",
    "PublicSourceFreshnessReviewValidationResult",
    "build_public_source_freshness_review_packet",
    "validate_public_source_freshness_review_packet",
]
