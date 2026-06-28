"""Fixture-first post-intake review for public recrawl metadata.

This module is intentionally side-effect free. It accepts already-captured public
recrawl intake reconciliation metadata plus source evidence freshness badges and
returns reviewer-facing triage decisions. It does not fetch URLs, invoke archive
processors, or write archive artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence
from urllib.parse import urlparse


REVIEW_DECISIONS = {"changed", "new", "missing", "conflict"}
STALE_BADGE_STATUSES = {"stale", "expired", "conflicting", "unknown"}
ALLOWED_PUBLIC_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}
PRIVATE_SOURCE_TYPES = {"devhub_authenticated", "private", "authenticated"}
ABORT_FLAGS = (
    "live_fetch_attempted",
    "processor_invoked",
    "archive_artifact_written",
    "raw_body_persisted",
    "authenticated_source_detected",
)
RAW_REFERENCE_KEYS = {
    "raw_body",
    "raw_html",
    "raw_text",
    "body_text",
    "downloaded_document_path",
    "downloaded_document_ref",
    "download_path",
    "archive_artifact_ref",
    "archive_path",
    "warc_path",
    "raw_archive_ref",
}
EXECUTION_CLAIM_KEYS = {
    "live_fetch_attempted",
    "live_fetch_executed",
    "fetched_live_url",
    "processor_invoked",
    "processor_executed",
    "processor_execution_claimed",
}
MUTATION_FLAG_KEYS = {
    "active_source_registry_mutation",
    "active_source_registry_mutated",
    "source_registry_mutation_enabled",
    "source_registry_mutated",
    "archive_mutation_enabled",
    "archive_manifest_mutated",
    "archive_artifact_written",
    "writes_archive_artifacts",
}
FORBIDDEN_URL_MARKERS = (
    "/login",
    "/signin",
    "/sign-in",
    "/account",
    "/my-permits",
    "/dashboard",
    "/admin",
)


@dataclass(frozen=True)
class BadgeSummary:
    statuses: List[str]
    badges: List[Mapping[str, Any]]

    @property
    def has_stale_status(self) -> bool:
        return any(status in STALE_BADGE_STATUSES for status in self.statuses)

    @property
    def worst_status(self) -> str:
        for status in ("expired", "conflicting", "stale", "unknown", "fresh"):
            if status in self.statuses:
                return status
        return "unbadged"


@dataclass(frozen=True)
class PostIntakeReviewValidationResult:
    errors: List[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def build_post_intake_review_packet(
    intake_reconciliation_packet: Mapping[str, Any],
    freshness_badges_packet: Mapping[str, Any],
) -> Dict[str, Any]:
    """Build a public recrawl post-intake review packet.

    The returned packet is deterministic for the provided inputs and contains no
    filesystem, network, browser, or processor side effects.
    """

    input_errors: List[str] = []
    _scan_for_forbidden_content(intake_reconciliation_packet, "intake_reconciliation_packet", input_errors)
    _scan_for_forbidden_content(freshness_badges_packet, "freshness_badges_packet", input_errors)
    if input_errors:
        raise ValueError("invalid public recrawl post-intake review inputs: " + "; ".join(input_errors))

    sources = list(_as_sequence(intake_reconciliation_packet.get("sources")))
    badges_by_source = _index_badges_by_source(freshness_badges_packet)
    evidence_catalog = sorted(_collect_input_evidence_ids(sources, freshness_badges_packet))

    decisions: List[Dict[str, Any]] = []
    queues: MutableMapping[str, List[str]] = {
        "urgent_review": [],
        "changed_source_review": [],
        "freshness_monitor": [],
    }
    queue_owners: MutableMapping[str, Dict[str, str]] = {
        "urgent_review": {},
        "changed_source_review": {},
        "freshness_monitor": {},
    }
    notes: List[Dict[str, Any]] = []
    blockers: List[Dict[str, Any]] = []
    aborts: List[Dict[str, Any]] = []

    for source in sources:
        source_id = str(source.get("source_id", ""))
        badge_summary = badges_by_source.get(source_id, BadgeSummary([], []))
        decision = _triage_source(source, badge_summary)
        decisions.append(decision)
        _append_queue_membership(queues, queue_owners, decision)
        notes.extend(_freshness_notes(source, badge_summary))
        blockers.extend(_promotion_blockers(source, decision, badge_summary))
        aborts.extend(_abort_recommendations(source))

    packet = {
        "packet_type": "public_recrawl_post_intake_review",
        "packet_id": _packet_id(intake_reconciliation_packet),
        "generated_at": str(
            intake_reconciliation_packet.get("generated_at")
            or freshness_badges_packet.get("generated_at")
            or "fixture-generated"
        ),
        "input_packet_ids": {
            "intake_reconciliation_packet_id": intake_reconciliation_packet.get("packet_id"),
            "freshness_badges_packet_id": freshness_badges_packet.get("packet_id"),
        },
        "side_effect_policy": {
            "fetch_urls": False,
            "invoke_processors": False,
            "write_archive_artifacts": False,
            "source_registry_mutation": False,
            "archive_manifest_mutation": False,
            "source": "fixture_or_precomputed_metadata_only",
        },
        "known_source_ids": sorted(str(source.get("source_id")) for source in sources if source.get("source_id")),
        "source_evidence_catalog": evidence_catalog,
        "source_level_triage_decisions": decisions,
        "changed_source_reviewer_queues": queues,
        "changed_source_reviewer_queue_owners": queue_owners,
        "freshness_badge_reconciliation_notes": notes,
        "promotion_blockers": blockers,
        "operator_abort_recommendations": aborts,
    }
    require_post_intake_review_packet(packet)
    return packet


def validate_post_intake_review_packet(packet: Mapping[str, Any]) -> PostIntakeReviewValidationResult:
    """Validate a public recrawl post-intake review packet without side effects."""

    errors: List[str] = []
    if packet.get("packet_type") != "public_recrawl_post_intake_review":
        errors.append("packet_type must be public_recrawl_post_intake_review")

    side_effect_policy = packet.get("side_effect_policy")
    if not isinstance(side_effect_policy, Mapping):
        errors.append("side_effect_policy must be an object")
    else:
        for key in ("fetch_urls", "invoke_processors", "write_archive_artifacts", "source_registry_mutation", "archive_manifest_mutation"):
            if side_effect_policy.get(key) is not False:
                errors.append(f"side_effect_policy.{key} must be false")

    known_sources = set(_string_list(packet.get("known_source_ids")))
    known_evidence = set(_string_list(packet.get("source_evidence_catalog")))
    decisions = packet.get("source_level_triage_decisions")
    blockers = packet.get("promotion_blockers")
    notes = packet.get("freshness_badge_reconciliation_notes")

    if not isinstance(decisions, list) or not decisions:
        errors.append("source_level_triage_decisions must be a non-empty list")
    else:
        if not known_sources:
            known_sources = {str(decision.get("source_id")) for decision in decisions if isinstance(decision, Mapping) and decision.get("source_id")}
        for index, decision in enumerate(decisions):
            if isinstance(decision, Mapping):
                _validate_decision(decision, index, known_sources, known_evidence, errors)
            else:
                errors.append(f"source_level_triage_decisions[{index}] must be an object")

    blocker_source_ids: set[str] = set()
    if not isinstance(blockers, list):
        errors.append("promotion_blockers must be a list")
    else:
        for index, blocker in enumerate(blockers):
            if not isinstance(blocker, Mapping):
                errors.append(f"promotion_blockers[{index}] must be an object")
                continue
            source_id = str(blocker.get("source_id", ""))
            if not source_id or source_id not in known_sources:
                errors.append(f"promotion_blockers[{index}].source_id references an unknown source")
            else:
                blocker_source_ids.add(source_id)
            if not _text(blocker.get("blocker_type")):
                errors.append(f"promotion_blockers[{index}].blocker_type is required")
            if not _text(blocker.get("reviewer_owner")):
                errors.append(f"promotion_blockers[{index}].reviewer_owner is required")

    if isinstance(decisions, list):
        for index, decision in enumerate(decisions):
            if isinstance(decision, Mapping) and decision.get("review_required") is True:
                source_id = str(decision.get("source_id", ""))
                if source_id not in blocker_source_ids:
                    errors.append(f"source_level_triage_decisions[{index}] requires at least one promotion blocker")

    if not isinstance(notes, list):
        errors.append("freshness_badge_reconciliation_notes must be a list")
    else:
        for index, note in enumerate(notes):
            if not isinstance(note, Mapping):
                errors.append(f"freshness_badge_reconciliation_notes[{index}] must be an object")
                continue
            source_id = str(note.get("source_id", ""))
            if source_id not in known_sources:
                errors.append(f"freshness_badge_reconciliation_notes[{index}].source_id references an unknown source")
            _validate_evidence_ids(note, f"freshness_badge_reconciliation_notes[{index}]", known_evidence, errors)

    _validate_queue_owners(packet, known_sources, errors)
    _scan_for_forbidden_content(packet, "packet", errors)
    return PostIntakeReviewValidationResult(errors=errors)


def require_post_intake_review_packet(packet: Mapping[str, Any]) -> None:
    result = validate_post_intake_review_packet(packet)
    if not result.ok:
        raise ValueError("invalid public recrawl post-intake review packet: " + "; ".join(result.errors))


def _validate_decision(
    decision: Mapping[str, Any],
    index: int,
    known_sources: set[str],
    known_evidence: set[str],
    errors: List[str],
) -> None:
    prefix = f"source_level_triage_decisions[{index}]"
    source_id = str(decision.get("source_id", ""))
    if not source_id or source_id not in known_sources:
        errors.append(prefix + ".source_id references an unknown source")
    if not _is_allowlisted_public_url(decision.get("canonical_url")):
        errors.append(prefix + ".canonical_url must be an allowlisted public URL")
    if str(decision.get("source_type", "")) in PRIVATE_SOURCE_TYPES:
        errors.append(prefix + ".source_type must not be private or authenticated")
    if not _text(decision.get("reviewer_owner")):
        errors.append(prefix + ".reviewer_owner is required")
    if not _string_list(decision.get("source_evidence_ids")) and not _string_list(decision.get("citation_refs")):
        errors.append(prefix + " must cite source_evidence_ids or citation_refs")
    _validate_evidence_ids(decision, prefix, known_evidence, errors)


def _validate_evidence_ids(value: Mapping[str, Any], prefix: str, known_evidence: set[str], errors: List[str]) -> None:
    for evidence_id in _string_list(value.get("source_evidence_ids")):
        if known_evidence and evidence_id not in known_evidence:
            errors.append(prefix + f".source_evidence_ids references unknown evidence id: {evidence_id}")


def _validate_queue_owners(packet: Mapping[str, Any], known_sources: set[str], errors: List[str]) -> None:
    queues = packet.get("changed_source_reviewer_queues")
    owners = packet.get("changed_source_reviewer_queue_owners")
    if not isinstance(queues, Mapping):
        errors.append("changed_source_reviewer_queues must be an object")
        return
    if not isinstance(owners, Mapping):
        errors.append("changed_source_reviewer_queue_owners must be an object")
        return
    for queue_name, queued_sources in queues.items():
        if not isinstance(queued_sources, list):
            errors.append(f"changed_source_reviewer_queues.{queue_name} must be a list")
            continue
        owner_map = owners.get(queue_name)
        if not isinstance(owner_map, Mapping):
            errors.append(f"changed_source_reviewer_queue_owners.{queue_name} must be an object")
            continue
        for source_id in _string_list(queued_sources):
            if source_id not in known_sources:
                errors.append(f"changed_source_reviewer_queues.{queue_name} references unknown source: {source_id}")
            if not _text(owner_map.get(source_id)):
                errors.append(f"changed_source_reviewer_queue_owners.{queue_name}.{source_id} is required")


def _scan_for_forbidden_content(value: Any, path: str, errors: List[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            normalized = key_text.lower()
            if normalized in RAW_REFERENCE_KEYS:
                errors.append(child_path + " is a raw body, download, or archive reference")
            if normalized in EXECUTION_CLAIM_KEYS and child not in (False, None, "", "false", "False"):
                errors.append(child_path + " claims live fetch or processor execution")
            if normalized in MUTATION_FLAG_KEYS and child not in (False, None, "", "false", "False"):
                errors.append(child_path + " claims active source registry or archive mutation")
            if normalized in {"authenticated_source_detected", "private_source_detected"} and child not in (False, None, "", "false", "False"):
                errors.append(child_path + " claims a private or authenticated source")
            _scan_for_forbidden_content(child, child_path, errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_for_forbidden_content(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        lower = value.lower()
        if lower.startswith(("file://", "/tmp/", "/var/", "/home/")):
            errors.append(path + " contains a local raw/download/archive path")
        if "live fetch completed" in lower or "processor execution completed" in lower:
            errors.append(path + " claims live fetch or processor execution")
        if _looks_like_url(value) and not _is_allowlisted_public_url(value):
            errors.append(path + " contains a private, authenticated, or non-allowlisted URL")


def _is_allowlisted_public_url(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.netloc.lower() not in ALLOWED_PUBLIC_HOSTS:
        return False
    lowered_path = parsed.path.lower()
    if any(marker in lowered_path for marker in FORBIDDEN_URL_MARKERS):
        return False
    lowered_query = parsed.query.lower()
    if any(marker in lowered_query for marker in ("token=", "session=", "auth=", "password=")):
        return False
    return True


def _looks_like_url(value: str) -> bool:
    return value.startswith("http://") or value.startswith("https://")


def _packet_id(packet: Mapping[str, Any]) -> str:
    base_id = str(packet.get("packet_id") or "unknown-intake-packet")
    return f"post-intake-review::{base_id}"


def _as_sequence(value: Any) -> Sequence[Mapping[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _index_badges_by_source(packet: Mapping[str, Any]) -> Dict[str, BadgeSummary]:
    indexed: Dict[str, List[Mapping[str, Any]]] = {}
    for badge in _as_sequence(packet.get("badges")):
        source_id = str(badge.get("source_id", ""))
        if not source_id:
            continue
        indexed.setdefault(source_id, []).append(badge)

    summaries: Dict[str, BadgeSummary] = {}
    for source_id, badges in indexed.items():
        statuses = sorted({str(badge.get("status", "unknown")) for badge in badges})
        summaries[source_id] = BadgeSummary(statuses=statuses, badges=badges)
    return summaries


def _collect_input_evidence_ids(sources: Sequence[Mapping[str, Any]], badges_packet: Mapping[str, Any]) -> set[str]:
    evidence_ids: set[str] = set()
    for source in sources:
        evidence_ids.update(_string_list(source.get("source_evidence_ids")))
    for badge in _as_sequence(badges_packet.get("badges")):
        evidence_ids.update(_string_list(badge.get("source_evidence_ids")))
    return evidence_ids


def _triage_source(source: Mapping[str, Any], badge_summary: BadgeSummary) -> Dict[str, Any]:
    source_id = str(source.get("source_id", ""))
    reconciliation = str(source.get("reconciliation_decision", "unknown"))
    previous_hash = source.get("previous_content_hash")
    current_hash = source.get("current_content_hash")
    hash_changed = bool(previous_hash and current_hash and previous_hash != current_hash)
    evidence_ids = _string_list(source.get("source_evidence_ids"))
    citation_refs = _string_list(source.get("citation_refs"))

    reasons: List[str] = []
    if reconciliation in REVIEW_DECISIONS:
        reasons.append(f"reconciliation:{reconciliation}")
    if hash_changed:
        reasons.append("content_hash_changed")
    if badge_summary.has_stale_status:
        reasons.append(f"freshness_badge:{badge_summary.worst_status}")
    if not evidence_ids and not citation_refs:
        reasons.append("missing_cited_source_evidence")

    if reconciliation == "conflict" or badge_summary.worst_status in {"expired", "conflicting"}:
        triage = "hold_for_senior_review"
    elif reconciliation in {"changed", "new", "missing"} or hash_changed:
        triage = "changed_source_review"
    elif badge_summary.has_stale_status:
        triage = "freshness_monitor"
    else:
        triage = "no_promotion_blocker"

    return {
        "source_id": source_id,
        "canonical_url": source.get("canonical_url"),
        "source_type": source.get("source_type"),
        "reconciliation_decision": reconciliation,
        "freshness_status": badge_summary.worst_status,
        "triage_decision": triage,
        "review_required": triage != "no_promotion_blocker",
        "reviewer_owner": _reviewer_owner_for_triage(triage),
        "source_evidence_ids": evidence_ids,
        "citation_refs": citation_refs,
        "affected_requirement_ids": _string_list(source.get("affected_requirement_ids")),
        "affected_guardrail_bundle_ids": _string_list(source.get("affected_guardrail_bundle_ids")),
        "reasons": reasons,
    }


def _reviewer_owner_for_triage(triage: str) -> str:
    if triage == "hold_for_senior_review":
        return "ppd-senior-source-reviewer"
    if triage == "freshness_monitor":
        return "ppd-source-freshness-reviewer"
    return "ppd-public-recrawl-reviewer"


def _append_queue_membership(
    queues: MutableMapping[str, List[str]],
    queue_owners: MutableMapping[str, Dict[str, str]],
    decision: Mapping[str, Any],
) -> None:
    source_id = str(decision.get("source_id", ""))
    if not source_id:
        return
    triage = decision.get("triage_decision")
    owner = str(decision.get("reviewer_owner", ""))
    if triage == "hold_for_senior_review":
        queues["urgent_review"].append(source_id)
        queue_owners["urgent_review"][source_id] = owner
    elif triage == "changed_source_review":
        queues["changed_source_review"].append(source_id)
        queue_owners["changed_source_review"][source_id] = owner
    elif triage == "freshness_monitor":
        queues["freshness_monitor"].append(source_id)
        queue_owners["freshness_monitor"][source_id] = owner


def _freshness_notes(source: Mapping[str, Any], badge_summary: BadgeSummary) -> List[Dict[str, Any]]:
    source_id = str(source.get("source_id", ""))
    notes: List[Dict[str, Any]] = []
    for badge in badge_summary.badges:
        notes.append(
            {
                "source_id": source_id,
                "badge_id": badge.get("badge_id"),
                "badge_status": badge.get("status", "unknown"),
                "observed_at": badge.get("observed_at"),
                "source_evidence_ids": _string_list(badge.get("source_evidence_ids")),
                "note": _badge_note_text(source, badge),
            }
        )
    if not badge_summary.badges:
        notes.append(
            {
                "source_id": source_id,
                "badge_id": None,
                "badge_status": "unbadged",
                "observed_at": None,
                "source_evidence_ids": _string_list(source.get("source_evidence_ids")),
                "note": "No freshness badge was supplied for this reconciled source; keep it out of automatic promotion until cited evidence is reviewed.",
            }
        )
    return notes


def _badge_note_text(source: Mapping[str, Any], badge: Mapping[str, Any]) -> str:
    status = str(badge.get("status", "unknown"))
    source_id = str(source.get("source_id", ""))
    if status == "fresh":
        return f"Freshness badge for {source_id} is fresh and can support promotion only if reconciliation has no other blocker."
    return f"Freshness badge for {source_id} is {status}; reviewer must reconcile cited source evidence before promotion."


def _promotion_blockers(
    source: Mapping[str, Any],
    decision: Mapping[str, Any],
    badge_summary: BadgeSummary,
) -> List[Dict[str, Any]]:
    blockers: List[Dict[str, Any]] = []
    source_id = str(source.get("source_id", ""))
    reviewer_owner = str(decision.get("reviewer_owner", "ppd-public-recrawl-reviewer"))
    if decision.get("triage_decision") == "hold_for_senior_review":
        blockers.append(
            {
                "source_id": source_id,
                "blocker_type": "senior_review_required",
                "reviewer_owner": reviewer_owner,
                "reason": "Conflicting or expired public source evidence cannot be promoted without human review.",
            }
        )
    elif decision.get("triage_decision") == "changed_source_review":
        blockers.append(
            {
                "source_id": source_id,
                "blocker_type": "changed_source_review_required",
                "reviewer_owner": reviewer_owner,
                "reason": "Changed or new source metadata must be reviewed before promotion.",
            }
        )
    elif decision.get("triage_decision") == "freshness_monitor":
        blockers.append(
            {
                "source_id": source_id,
                "blocker_type": "freshness_monitor_review_required",
                "reviewer_owner": reviewer_owner,
                "reason": "Freshness monitor sources must be reconciled before promotion.",
            }
        )
    if badge_summary.has_stale_status:
        blockers.append(
            {
                "source_id": source_id,
                "blocker_type": "freshness_badge_not_current",
                "reviewer_owner": reviewer_owner,
                "reason": f"Worst freshness badge status is {badge_summary.worst_status}.",
            }
        )
    if not decision.get("source_evidence_ids") and not decision.get("citation_refs"):
        blockers.append(
            {
                "source_id": source_id,
                "blocker_type": "missing_cited_source_evidence",
                "reviewer_owner": reviewer_owner,
                "reason": "Every post-intake promotion decision must identify source evidence or citation references.",
            }
        )
    return blockers


def _abort_recommendations(source: Mapping[str, Any]) -> List[Dict[str, Any]]:
    source_id = str(source.get("source_id", ""))
    recommendations: List[Dict[str, Any]] = []
    for flag in ABORT_FLAGS:
        if bool(source.get(flag)):
            recommendations.append(
                {
                    "source_id": source_id,
                    "abort_type": flag,
                    "reviewer_owner": "ppd-public-recrawl-reviewer",
                    "recommendation": "Abort operator promotion and rerun with fixture or precomputed public metadata only.",
                }
            )
    return recommendations


def _string_list(value: Any) -> List[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [str(item) for item in value if item is not None]


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    return ""


__all__ = [
    "PostIntakeReviewValidationResult",
    "build_post_intake_review_packet",
    "require_post_intake_review_packet",
    "validate_post_intake_review_packet",
]
