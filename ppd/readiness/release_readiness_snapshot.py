"""Build fixture-first PP&D release readiness operator snapshots.

The snapshot is a non-production operator artifact. It links the local readiness
packets that precede release review while preserving unresolved blockers and
keeping live crawl, DevHub, payment, upload, submission, scheduling,
cancellation, and certification paths disabled.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

SNAPSHOT_TYPE = "ppd.release_readiness_operator_snapshot.v1"
SNAPSHOT_MODE = "fixture_first"
READINESS_LABEL = "non_production_operator_snapshot"

REQUIRED_PREREQUISITES = (
    "burn_down_queue",
    "citation_normalization_packet",
    "stale_predicate_remediation_candidate",
    "agent_regression_rerun_plan",
    "attended_pilot_dry_run_review",
)

DEFAULT_FIXTURES = {
    "burn_down_queue": "ppd/tests/fixtures/readiness/burndown_queue.json",
    "citation_normalization_packet": "ppd/tests/fixtures/readiness/source_evidence_citation_packet.json",
    "stale_predicate_remediation_candidate": "ppd/tests/fixtures/stale_predicate_remediation_candidate/normalized_citation_evidence_packet.json",
    "agent_regression_rerun_plan": "ppd/tests/fixtures/agent_regression_rerun_plan/stale_predicate_cases.json",
    "attended_pilot_dry_run_review": "ppd/tests/fixtures/devhub/attended_pilot_review_packet.complete.json",
}

REQUIRED_DISABLED_CAPABILITIES = {
    "account_creation",
    "captcha_automation",
    "cancellation",
    "certification",
    "devhub_authenticated_automation",
    "live_crawl",
    "live_llm_execution",
    "mfa_automation",
    "payment",
    "scheduling",
    "submission",
    "upload",
}

LIVE_CAPABILITY_FLAGS = (
    "live_crawl_enabled",
    "devhub_automation_enabled",
    "authenticated_devhub_enabled",
    "llm_execution_enabled",
    "payment_enabled",
    "upload_enabled",
    "submission_enabled",
    "scheduling_enabled",
    "cancellation_enabled",
    "certification_enabled",
)

FORBIDDEN_MARKERS = (
    "/home/",
    "/Users/",
    "C:/Users/",
    "auth_state",
    "browser_state",
    "cookie",
    "credential",
    "devhub_session",
    "downloaded_document",
    "har",
    "password",
    "private_path",
    "private_value",
    "raw_body",
    "raw_crawl_output",
    "raw_html",
    "screenshot",
    "session_storage",
    "storage_state",
    "trace",
    "warc",
)


class ReleaseReadinessSnapshotError(ValueError):
    """Raised when a release readiness snapshot is unsafe or malformed."""


def load_release_readiness_snapshot_fixture(path: Path) -> dict[str, Any]:
    """Load a committed release readiness snapshot fixture."""

    with path.open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise ReleaseReadinessSnapshotError("release readiness snapshot fixture must be a JSON object")
    return packet


def build_release_readiness_snapshot(
    burn_down_queue: Mapping[str, Any],
    citation_normalization_packet: Mapping[str, Any],
    stale_predicate_remediation_candidate: Mapping[str, Any],
    agent_regression_rerun_plan: Mapping[str, Any],
    attended_pilot_dry_run_review: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a deterministic non-production readiness snapshot from prerequisite packets."""

    prerequisites = {
        "burn_down_queue": _packet_ref(
            burn_down_queue,
            packet_id_fields=("queue_id", "packet_id"),
            packet_type_fields=("queue_type", "packet_type"),
        ),
        "citation_normalization_packet": _packet_ref(
            citation_normalization_packet,
            packet_id_fields=("packet_id",),
            packet_type_fields=("packet_type",),
        ),
        "stale_predicate_remediation_candidate": _packet_ref(
            stale_predicate_remediation_candidate,
            packet_id_fields=("candidate_id", "packet_id"),
            packet_type_fields=("packet_type", "candidate_type"),
        ),
        "agent_regression_rerun_plan": _packet_ref(
            agent_regression_rerun_plan,
            packet_id_fields=("plan_id", "packet_id"),
            packet_type_fields=("packet_type", "plan_status"),
        ),
        "attended_pilot_dry_run_review": _packet_ref(
            attended_pilot_dry_run_review,
            packet_id_fields=("packet_id", "review_id"),
            packet_type_fields=("packet_type",),
        ),
    }
    for key, ref in prerequisites.items():
        ref["fixture"] = DEFAULT_FIXTURES[key]

    unresolved_blockers = _unresolved_blockers_from_queue(burn_down_queue)
    if not unresolved_blockers:
        unresolved_blockers = [
            {
                "blocker_id": "release-readiness-human-review-required",
                "source": "operator_snapshot",
                "summary": "Human review remains unresolved for this fixture-first release snapshot.",
                "status": "open",
                "citations": ["burn_down_queue", "citation_normalization_packet"],
            }
        ]

    readiness_claims = [
        {
            "claim_id": "burn-down-linked",
            "status": "blocked_by_open_release_blockers",
            "summary": "The release-blocker burn-down queue is linked and still contains unresolved blockers.",
            "citations": ["burn_down_queue"],
        },
        {
            "claim_id": "citation-normalization-linked",
            "status": "review_only_not_source_registry_promotion",
            "summary": "Citation normalization evidence is linked for review without replacing active source records.",
            "citations": ["citation_normalization_packet", "burn_down_queue"],
        },
        {
            "claim_id": "stale-predicate-remediation-linked",
            "status": "candidate_only_human_review_unresolved",
            "summary": "Stale-predicate remediation remains a cited candidate and does not mutate active guardrail bundles.",
            "citations": ["stale_predicate_remediation_candidate", "citation_normalization_packet"],
        },
        {
            "claim_id": "regression-rerun-plan-linked",
            "status": "fixture_only_no_llm_no_devhub_execution",
            "summary": "Agent regression rerun planning is limited to affected synthetic cases and expected outcomes.",
            "citations": ["agent_regression_rerun_plan", "stale_predicate_remediation_candidate"],
        },
        {
            "claim_id": "attended-pilot-review-linked",
            "status": "dry_run_review_only_no_live_authenticated_evidence",
            "summary": "The attended pilot dry-run review is linked without captured live authenticated session evidence.",
            "citations": ["attended_pilot_dry_run_review"],
        },
    ]

    snapshot = {
        "snapshot_id": "release-readiness-operator-snapshot-v1",
        "snapshot_type": SNAPSHOT_TYPE,
        "mode": SNAPSHOT_MODE,
        "readiness_label": READINESS_LABEL,
        "production_ready": False,
        "operator_scope": "non_production_review_only",
        "prerequisite_packets": prerequisites,
        "readiness_claims": readiness_claims,
        "unresolved_blockers": unresolved_blockers,
        "live_capabilities": {flag: False for flag in LIVE_CAPABILITY_FLAGS},
        "disabled_capabilities": sorted(REQUIRED_DISABLED_CAPABILITIES),
        "operator_next_actions": [
            "Resolve burn-down blockers against cited fixtures before any production readiness claim.",
            "Complete human review for citation normalization and stale-predicate remediation candidates.",
            "Rerun only fixture-backed synthetic agent cases until live capabilities are separately authorized.",
            "Keep attended DevHub pilot work manual, read-only, and dry-run reviewed before future live attendance.",
        ],
        "validation_summary": {
            "status": "blocked_non_production_snapshot",
            "unresolved_blocker_count": len(unresolved_blockers),
            "live_capabilities_disabled": True,
            "fixture_first_only": True,
        },
    }
    errors = validate_release_readiness_snapshot(snapshot)
    if errors:
        raise ReleaseReadinessSnapshotError("invalid generated release readiness snapshot: " + "; ".join(errors))
    return snapshot


def validate_release_readiness_snapshot(snapshot: Mapping[str, Any]) -> list[str]:
    """Return deterministic validation errors for a fixture-first release readiness snapshot."""

    errors: list[str] = []
    if snapshot.get("snapshot_type") != SNAPSHOT_TYPE:
        errors.append(f"snapshot_type must be {SNAPSHOT_TYPE}")
    if snapshot.get("mode") != SNAPSHOT_MODE:
        errors.append("mode must be fixture_first")
    if snapshot.get("readiness_label") != READINESS_LABEL:
        errors.append("readiness_label must be non_production_operator_snapshot")
    if snapshot.get("production_ready") is not False:
        errors.append("production_ready must be false")
    if snapshot.get("operator_scope") != "non_production_review_only":
        errors.append("operator_scope must be non_production_review_only")

    prerequisites = snapshot.get("prerequisite_packets")
    if not isinstance(prerequisites, Mapping):
        errors.append("prerequisite_packets must be an object")
        prerequisites = {}
    for key in REQUIRED_PREREQUISITES:
        ref = prerequisites.get(key) if isinstance(prerequisites, Mapping) else None
        if not isinstance(ref, Mapping):
            errors.append(f"prerequisite_packets.{key} is required")
            continue
        for field in ("packet_id", "packet_type", "fixture", "status"):
            if not _has_text(ref.get(field)):
                errors.append(f"prerequisite_packets.{key}.{field} is required")
        if ref.get("fixture") != DEFAULT_FIXTURES[key]:
            errors.append(f"prerequisite_packets.{key}.fixture must point at the committed PP&D fixture")

    claims = snapshot.get("readiness_claims")
    if not isinstance(claims, list) or not claims:
        errors.append("readiness_claims must be a non-empty list")
    else:
        known_keys = set(REQUIRED_PREREQUISITES)
        cited_keys: set[str] = set()
        for index, claim in enumerate(claims):
            if not isinstance(claim, Mapping):
                errors.append(f"readiness_claims[{index}] must be an object")
                continue
            for field in ("claim_id", "status", "summary"):
                if not _has_text(claim.get(field)):
                    errors.append(f"readiness_claims[{index}].{field} is required")
            citations = claim.get("citations")
            if not isinstance(citations, list) or not citations:
                errors.append(f"readiness_claims[{index}].citations must be a non-empty list")
                continue
            for citation in citations:
                if citation not in known_keys:
                    errors.append(f"readiness_claims[{index}].citations must reference prerequisite packet keys")
                elif isinstance(citation, str):
                    cited_keys.add(citation)
        missing_claim_citations = sorted(set(REQUIRED_PREREQUISITES) - cited_keys)
        if missing_claim_citations:
            errors.append("readiness_claims must cite every prerequisite packet: " + ", ".join(missing_claim_citations))

    blockers = snapshot.get("unresolved_blockers")
    if not isinstance(blockers, list) or not blockers:
        errors.append("unresolved_blockers must be a non-empty list")
    else:
        for index, blocker in enumerate(blockers):
            if not isinstance(blocker, Mapping):
                errors.append(f"unresolved_blockers[{index}] must be an object")
                continue
            for field in ("blocker_id", "summary", "status", "citations"):
                if field == "citations":
                    citations = blocker.get(field)
                    if not isinstance(citations, list) or not citations:
                        errors.append(f"unresolved_blockers[{index}].citations must be a non-empty list")
                elif not _has_text(blocker.get(field)):
                    errors.append(f"unresolved_blockers[{index}].{field} is required")
            if blocker.get("status") not in {"open", "unresolved", "blocking"}:
                errors.append(f"unresolved_blockers[{index}].status must remain unresolved")

    live_capabilities = snapshot.get("live_capabilities")
    if not isinstance(live_capabilities, Mapping):
        errors.append("live_capabilities must be an object")
    else:
        for flag in LIVE_CAPABILITY_FLAGS:
            if live_capabilities.get(flag) is not False:
                errors.append(f"live_capabilities.{flag} must be false")

    disabled = snapshot.get("disabled_capabilities")
    disabled_set = {item for item in disabled if isinstance(item, str)} if isinstance(disabled, list) else set()
    missing_disabled = sorted(REQUIRED_DISABLED_CAPABILITIES - disabled_set)
    if missing_disabled:
        errors.append("missing disabled capabilities: " + ", ".join(missing_disabled))

    summary = snapshot.get("validation_summary")
    if not isinstance(summary, Mapping):
        errors.append("validation_summary must be an object")
    else:
        if summary.get("status") != "blocked_non_production_snapshot":
            errors.append("validation_summary.status must be blocked_non_production_snapshot")
        if summary.get("live_capabilities_disabled") is not True:
            errors.append("validation_summary.live_capabilities_disabled must be true")
        if summary.get("fixture_first_only") is not True:
            errors.append("validation_summary.fixture_first_only must be true")
        if isinstance(blockers, list) and summary.get("unresolved_blocker_count") != len(blockers):
            errors.append("validation_summary.unresolved_blocker_count must match unresolved_blockers length")

    _scan_for_forbidden_markers(snapshot, "snapshot", errors)
    return errors


def _packet_ref(
    packet: Mapping[str, Any],
    packet_id_fields: Sequence[str],
    packet_type_fields: Sequence[str],
) -> dict[str, Any]:
    packet_id = _first_text(packet, packet_id_fields) or "unidentified-fixture-packet"
    packet_type = _first_text(packet, packet_type_fields) or "fixture_packet"
    return {
        "packet_id": packet_id,
        "packet_type": packet_type,
        "status": "linked_fixture_review_only",
    }


def _unresolved_blockers_from_queue(queue: Mapping[str, Any]) -> list[dict[str, Any]]:
    blockers = queue.get("ordered_blockers")
    if not isinstance(blockers, list):
        return []
    results: list[dict[str, Any]] = []
    for blocker in blockers:
        if not isinstance(blocker, Mapping):
            continue
        blocker_id = str(blocker.get("blocker_id") or blocker.get("id") or "release-blocker")
        results.append(
            {
                "blocker_id": blocker_id,
                "source": "burn_down_queue",
                "summary": str(blocker.get("summary") or "Release blocker remains unresolved."),
                "status": "open",
                "priority_dimension": str(blocker.get("priority_dimension") or "release_readiness"),
                "citations": ["burn_down_queue"],
            }
        )
    return results


def _first_text(packet: Mapping[str, Any], fields: Sequence[str]) -> str:
    for field in fields:
        value = packet.get(field)
        if _has_text(value):
            return str(value)
    return ""


def _has_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _scan_for_forbidden_markers(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            for marker in FORBIDDEN_MARKERS:
                if marker.lower() in key_text:
                    errors.append(f"{path}.{key} uses forbidden private/session/raw artifact field naming")
                    break
            _scan_for_forbidden_markers(child, f"{path}.{key}", errors)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_markers(child, f"{path}[{index}]", errors)
        return
    if isinstance(value, str):
        text = value.lower()
        for marker in FORBIDDEN_MARKERS:
            if marker.lower() in text:
                errors.append(f"{path} includes forbidden private/session/raw artifact marker: {marker}")
                return
