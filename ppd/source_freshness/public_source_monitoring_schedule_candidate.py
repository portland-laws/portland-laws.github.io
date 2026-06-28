"""Fixture-first public source monitoring schedule candidates.

This module converts already-validated PP&D public-source review fixtures into a
metadata-only monitoring schedule candidate. It never fetches URLs, invokes a
crawler, writes live schedule state, or persists raw crawl output.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Iterable, Mapping
from urllib.parse import urlparse

from ppd.crawler.public_crawl_metadata_intake import validate_public_crawl_metadata_dry_run_intake
from ppd.extraction.source_freshness_drift import validate_source_freshness_drift_digest

PACKET_TYPE = "ppd.public_source_monitoring_schedule_candidate.v1"
MODE = "fixture_first_metadata_only_schedule_candidate"
ALLOWED_CADENCES = {"daily", "weekly", "monthly", "manual_review_before_recrawl"}
RAW_OR_PRIVATE_KEYS = {
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
    "crawl_completed",
    "download_completed",
    "executed_live_network",
    "live_crawl",
    "live_network",
    "live_schedule_mutated",
    "network_executed",
    "raw_body_persisted",
    "schedule_mutation_allowed",
}
PRIVATE_PATH_MARKERS = ("/account", "/admin", "/auth", "/dashboard", "/login", "/payment", "/session", "/upload")
PRIVATE_QUERY_MARKERS = ("access_token=", "auth=", "password=", "session=", "token=")


@dataclass(frozen=True)
class ScheduleCandidateValidationResult:
    """Deterministic validation result for schedule candidate packets."""

    valid: bool
    errors: tuple[str, ...]


def build_public_source_monitoring_schedule_candidate(
    source_freshness_drift_digest: Mapping[str, Any],
    public_crawl_metadata_dry_run_intake: Mapping[str, Any],
    safe_next_action_release_notes: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build a metadata-only monitoring schedule candidate from fixtures."""

    drift = deepcopy(dict(source_freshness_drift_digest))
    intake = deepcopy(dict(public_crawl_metadata_dry_run_intake))
    release_notes = deepcopy(dict(safe_next_action_release_notes))

    drift_result = validate_source_freshness_drift_digest(drift)
    if not drift_result.valid:
        raise ValueError("invalid source freshness drift digest: " + "; ".join(drift_result.messages()))

    intake_errors = validate_public_crawl_metadata_dry_run_intake(intake)
    if intake_errors:
        raise ValueError("invalid public crawl metadata dry-run intake: " + "; ".join(error.code for error in intake_errors))

    allowlisted_sources = _allowlisted_sources(intake)
    prerequisite_ids = _prerequisite_ids(intake)
    reviewer_owners = _reviewer_owners(release_notes)
    abort_conditions = _abort_conditions(intake, release_notes)

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
            "source_freshness_drift_digest_id": _text(drift.get("digest_id"), "source-freshness-drift-digest"),
            "public_crawl_metadata_dry_run_intake_id": _text(intake.get("packet_id"), "public-crawl-metadata-intake"),
            "safe_next_action_release_notes_id": _text(release_notes.get("packet_id"), "safe-next-action-release-notes"),
        },
        "allowlisted_source_ids": sorted(allowlisted_sources),
        "robots_policy_prerequisite_ids": sorted(prerequisite_ids),
        "cadence_recommendations": _cadence_recommendations(drift, allowlisted_sources, prerequisite_ids, reviewer_owners, abort_conditions),
        "reviewer_owners": reviewer_owners,
        "abort_conditions": abort_conditions,
        "candidate_output": {
            "writes_live_schedule": False,
            "requires_separate_reviewer_approval": True,
            "allowed_next_step": "review_metadata_only_schedule_candidate",
        },
    }
    result = validate_public_source_monitoring_schedule_candidate(packet)
    if not result.valid:
        raise ValueError("invalid public source monitoring schedule candidate: " + "; ".join(result.errors))
    return packet


def validate_public_source_monitoring_schedule_candidate(packet: Mapping[str, Any]) -> ScheduleCandidateValidationResult:
    """Validate a candidate packet without performing side effects."""

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
    expected_policy = {
        "network_allowed": False,
        "network_invoked": False,
        "fetch_urls": False,
        "download_documents": False,
        "persist_raw_body": False,
        "schedule_mutation_allowed": False,
        "live_schedule_mutated": False,
    }
    for key, expected in expected_policy.items():
        if policy.get(key) is not expected:
            errors.append(f"execution_policy.{key} must be {str(expected).lower()}")

    allowlisted = set(_string_list(packet.get("allowlisted_source_ids")))
    prerequisites = set(_string_list(packet.get("robots_policy_prerequisite_ids")))
    if not allowlisted:
        errors.append("allowlisted_source_ids must be non-empty")
    if not prerequisites:
        errors.append("robots_policy_prerequisite_ids must be non-empty")

    recommendations = packet.get("cadence_recommendations")
    if not isinstance(recommendations, list) or not recommendations:
        errors.append("cadence_recommendations must be a non-empty list")
    else:
        for index, recommendation in enumerate(recommendations):
            prefix = f"cadence_recommendations[{index}]"
            if not isinstance(recommendation, Mapping):
                errors.append(prefix + " must be an object")
                continue
            source_id = _text(recommendation.get("source_id"))
            if source_id not in allowlisted:
                errors.append(prefix + ".source_id must be allowlisted")
            if recommendation.get("metadata_only") is not True:
                errors.append(prefix + ".metadata_only must be true")
            if recommendation.get("recommended_cadence") not in ALLOWED_CADENCES:
                errors.append(prefix + ".recommended_cadence is invalid")
            if not _text(recommendation.get("reviewer_owner")):
                errors.append(prefix + ".reviewer_owner is required")
            recommendation_prereqs = set(_string_list(recommendation.get("robots_policy_prerequisite_ids")))
            if not recommendation_prereqs:
                errors.append(prefix + ".robots_policy_prerequisite_ids must be non-empty")
            elif not recommendation_prereqs.issubset(prerequisites):
                errors.append(prefix + ".robots_policy_prerequisite_ids must be declared at packet level")
            if not _string_list(recommendation.get("abort_condition_ids")):
                errors.append(prefix + ".abort_condition_ids must be non-empty")
            if not _text(recommendation.get("rationale")):
                errors.append(prefix + ".rationale is required")

    if not isinstance(packet.get("reviewer_owners"), Mapping) or not packet.get("reviewer_owners"):
        errors.append("reviewer_owners must be a non-empty object")
    if not isinstance(packet.get("abort_conditions"), list) or not packet.get("abort_conditions"):
        errors.append("abort_conditions must be a non-empty list")

    output = _mapping(packet.get("candidate_output"))
    if output.get("writes_live_schedule") is not False:
        errors.append("candidate_output.writes_live_schedule must be false")
    if output.get("requires_separate_reviewer_approval") is not True:
        errors.append("candidate_output.requires_separate_reviewer_approval must be true")

    _validate_no_forbidden_fields(packet, "$", errors)
    return ScheduleCandidateValidationResult(valid=not errors, errors=tuple(errors))


def _allowlisted_sources(intake: Mapping[str, Any]) -> set[str]:
    source_ids: set[str] = set()
    for item in _iter_mappings(intake.get("selected_allowlisted_targets")):
        source_id = _text(item.get("source_id")) or _text(item.get("target_id"))
        if source_id:
            source_ids.add(source_id)
    for item in _iter_mappings(intake.get("targets")):
        if item.get("selected_for_metadata_intake") is True:
            source_id = _text(item.get("source_id")) or _text(item.get("target_id"))
            if source_id:
                source_ids.add(source_id)
    return source_ids


def _prerequisite_ids(intake: Mapping[str, Any]) -> set[str]:
    values: set[str] = set()
    for key in ("robots_evidence", "policy_evidence", "prerequisite_evidence_ids"):
        value = intake.get(key)
        if isinstance(value, str) and value.strip():
            values.add(value.strip())
        elif isinstance(value, list):
            values.update(item.strip() for item in value if isinstance(item, str) and item.strip())
        elif isinstance(value, Mapping):
            values.update(str(item).strip() for item in value.values() if str(item).strip())
    for item in _iter_mappings(intake.get("selected_allowlisted_targets")):
        values.update(_string_list(item.get("robots_policy_prerequisite_ids")))
    return values


def _reviewer_owners(release_notes: Mapping[str, Any]) -> dict[str, str]:
    owners = release_notes.get("reviewer_owners")
    if isinstance(owners, Mapping):
        clean = {str(key): str(value) for key, value in owners.items() if str(key).strip() and str(value).strip()}
        if clean:
            return clean
    return {"source_freshness": "ppd-source-reviewer", "release_notes": "ppd-release-reviewer"}


def _abort_conditions(intake: Mapping[str, Any], release_notes: Mapping[str, Any]) -> list[dict[str, str]]:
    conditions: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in _iter_mappings(intake.get("operator_abort_conditions")):
        condition_id = _text(item.get("condition_id")) or _text(item.get("id"))
        description = _text(item.get("description")) or _text(item.get("reason"))
        if condition_id and description and condition_id not in seen:
            conditions.append({"condition_id": condition_id, "description": description})
            seen.add(condition_id)
    for item in _string_list(release_notes.get("remaining_blockers")):
        condition_id = "release-note-blocker-" + str(len(conditions) + 1)
        conditions.append({"condition_id": condition_id, "description": item})
    if not conditions:
        conditions.append({"condition_id": "abort-if-live-fetch-required", "description": "Abort if reviewer cannot complete the schedule decision from metadata-only fixtures."})
    return conditions


def _cadence_recommendations(
    drift: Mapping[str, Any],
    allowlisted_sources: set[str],
    prerequisite_ids: set[str],
    reviewer_owners: Mapping[str, str],
    abort_conditions: list[Mapping[str, str]],
) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    abort_ids = [_text(item.get("condition_id")) for item in abort_conditions if isinstance(item, Mapping)]
    for claim in _iter_mappings(drift.get("changed_source_claims") or drift.get("claims") or drift.get("changes")):
        source_id = _text(claim.get("source_id"))
        if not source_id or source_id not in allowlisted_sources:
            continue
        recommendations.append(
            {
                "source_id": source_id,
                "recommended_cadence": _recommended_cadence(claim),
                "metadata_only": True,
                "rationale": _text(claim.get("summary"), "changed source requires metadata-only cadence review"),
                "robots_policy_prerequisite_ids": sorted(prerequisite_ids),
                "reviewer_owner": _owner_for_source(source_id, reviewer_owners),
                "abort_condition_ids": [item for item in abort_ids if item],
            }
        )
    if not recommendations:
        for source_id in sorted(allowlisted_sources):
            recommendations.append(
                {
                    "source_id": source_id,
                    "recommended_cadence": "manual_review_before_recrawl",
                    "metadata_only": True,
                    "rationale": "No changed-source claim was linked; reviewer must keep schedule unchanged or document a separate promotion decision.",
                    "robots_policy_prerequisite_ids": sorted(prerequisite_ids),
                    "reviewer_owner": _owner_for_source(source_id, reviewer_owners),
                    "abort_condition_ids": [item for item in abort_ids if item],
                }
            )
    return recommendations


def _recommended_cadence(claim: Mapping[str, Any]) -> str:
    explicit = _text(claim.get("recommended_cadence") or claim.get("cadence"))
    if explicit in ALLOWED_CADENCES:
        return explicit
    severity = _text(claim.get("severity") or claim.get("freshness_status") or claim.get("change_type")).lower()
    if severity in {"high", "critical", "stale", "needs_recrawl"}:
        return "daily"
    if severity in {"low", "unchanged"}:
        return "monthly"
    return "weekly"


def _owner_for_source(source_id: str, reviewer_owners: Mapping[str, str]) -> str:
    return _text(reviewer_owners.get(source_id) or reviewer_owners.get("source_freshness"), "ppd-source-reviewer")


def _iter_mappings(value: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(value, list):
        for item in value:
            if isinstance(item, Mapping):
                yield item


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, list):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any, default: str = "") -> str:
    return value.strip() if isinstance(value, str) and value.strip() else default


def _validate_no_forbidden_fields(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            lowered = key_text.lower()
            child_path = f"{path}.{key_text}"
            if lowered in RAW_OR_PRIVATE_KEYS:
                errors.append(child_path + " is forbidden in schedule candidates")
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
