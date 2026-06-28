"""Build fixture-first source-evidence citation normalization packets.

The packet is a review-only bridge from the release-blocker burn-down queue to
source-evidence cleanup work. It validates synthetic source ids, citation span
anchors, fixture document hashes, normalized-record citation coverage, source id
freshness, and downstream requirement links without crawling, downloading, or
replacing active source records.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .burndown_queue import validate_burndown_queue

_PACKET_TYPE = "ppd.source_evidence_citation_normalization_packet.v1"
_FIXTURE_MODE = "fixture_first"
_BURNDOWN_FIXTURE = "ppd/tests/fixtures/readiness/burndown_queue.json"
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_REVIEW_SOURCE_ACTION = "review_only_no_active_source_record_replacement"
_ALLOWED_RECORD_PROMOTION_ACTION = "review_only_no_source_registry_promotion"
_ALLOWED_BODY_STORAGE = "metadata_only_no_raw_body"
_ALLOWED_SOURCE_ID_STATUS = "synthetic_unverified_review_only"
_ALLOWED_SOURCE_FRESHNESS = "current_fixture_only_not_live_verified"

_FORBIDDEN_MARKERS = (
    "auth_state",
    "authenticated_url",
    "browser_state",
    "cookie",
    "credential",
    "devhub_session",
    "download_path",
    "downloaded_document",
    "downloaded_documents",
    "file_path",
    "har_path",
    "html_body",
    "live_crawl",
    "local_document_path",
    "private_url",
    "raw_body",
    "raw_crawl",
    "raw_html",
    "raw_pdf",
    "replace_active_source_record",
    "screenshot",
    "session_storage",
    "source_registry_promotion",
    "storage_state",
    "trace_path",
    "warc_path",
)

_ALLOWED_FORBIDDEN_LITERAL_VALUES = {
    _ALLOWED_REVIEW_SOURCE_ACTION,
    _ALLOWED_RECORD_PROMOTION_ACTION,
    _ALLOWED_BODY_STORAGE,
}


class SourceEvidenceCitationPacketError(ValueError):
    """Raised when a source-evidence citation packet is unsafe or invalid."""


def load_source_evidence_citation_packet_fixture(path: Path) -> dict[str, Any]:
    """Load a committed source-evidence citation normalization fixture."""

    with path.open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise SourceEvidenceCitationPacketError("source-evidence citation packet fixture must be a JSON object")
    return packet


def build_source_evidence_citation_packet(queue: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic review packet from a release-blocker burn-down queue."""

    queue_errors = validate_burndown_queue(queue)
    if queue_errors:
        raise SourceEvidenceCitationPacketError("invalid burn-down queue: " + "; ".join(queue_errors))

    ordered_blockers = queue.get("ordered_blockers")
    if not isinstance(ordered_blockers, list):
        raise SourceEvidenceCitationPacketError("ordered_blockers must be a list")

    reviews: list[dict[str, Any]] = []
    normalized_records: list[dict[str, Any]] = []
    source_ids: list[str] = []
    for blocker_index, blocker in enumerate(ordered_blockers):
        if not isinstance(blocker, Mapping):
            continue
        evidence_ids = blocker.get("source_evidence_ids")
        if not isinstance(evidence_ids, list):
            continue
        for evidence_index, evidence_id_value in enumerate(evidence_ids):
            evidence_id = str(evidence_id_value)
            slug = _slug(evidence_id)
            source_id = "synthetic-" + slug
            record_id = "normalized-" + slug
            anchor = f"{_BURNDOWN_FIXTURE}#/ordered_blockers/{blocker_index}/source_evidence_ids/{evidence_index}"
            source_ids.append(source_id)
            reviews.append(
                {
                    "review_id": "citation-normalization-" + slug,
                    "source_evidence_id": evidence_id,
                    "synthetic_source_id": source_id,
                    "source_id_status": _ALLOWED_SOURCE_ID_STATUS,
                    "source_id_freshness_status": _ALLOWED_SOURCE_FRESHNESS,
                    "citation_span_anchor": anchor,
                    "citation_anchor_status": "fixture_anchor_present",
                    "normalized_record_ids": [record_id],
                    "document_hash": _document_hash(evidence_id, source_id, blocker),
                    "document_hash_status": "fixture_hash_present_not_live_verified",
                    "visible_update_date": "fixture_only_not_live_verified",
                    "visible_update_date_status": "review_required_before_freshness_promotion",
                    "downstream_requirement_links": [
                        {
                            "requirement_link_id": "burn-down-" + _slug(str(blocker.get("blocker_id", evidence_id))),
                            "blocker_id": str(blocker.get("blocker_id", "")),
                            "action_required": str(blocker.get("action_required", "")),
                            "prerequisite_packet_id": str(blocker.get("prerequisite_packet_id", "")),
                            "source_evidence_ids": [evidence_id],
                        }
                    ],
                    "source_record_action": _ALLOWED_REVIEW_SOURCE_ACTION,
                }
            )
            normalized_records.append(
                {
                    "record_id": record_id,
                    "source_id": source_id,
                    "source_id_freshness_status": _ALLOWED_SOURCE_FRESHNESS,
                    "source_evidence_ids": [evidence_id],
                    "citation_span_anchors": [anchor],
                    "body_storage": _ALLOWED_BODY_STORAGE,
                    "document_ref": "fixture_metadata_only:" + record_id,
                    "promotion_action": _ALLOWED_RECORD_PROMOTION_ACTION,
                }
            )

    packet = {
        "packet_id": "source-evidence-citation-normalization-" + str(queue.get("queue_id", "unknown")),
        "packet_type": _PACKET_TYPE,
        "mode": _FIXTURE_MODE,
        "burn_down_queue": {
            "queue_id": str(queue.get("queue_id", "")),
            "queue_type": str(queue.get("queue_type", "")),
            "fixture": _BURNDOWN_FIXTURE,
        },
        "crawl_enabled": False,
        "download_enabled": False,
        "active_source_record_replacement_enabled": False,
        "source_registry_promotion_enabled": False,
        "source_registry_snapshot": {
            "registered_source_ids": source_ids,
            "stale_source_ids": [],
            "missing_source_id_policy": "reject_packet",
            "promotion_action": "none_review_only",
        },
        "reviews": reviews,
        "normalized_records": normalized_records,
        "review_summary": {
            "review_count": len(reviews),
            "normalized_record_count": len(normalized_records),
            "synthetic_source_id_count": len(set(source_ids)),
            "citation_anchor_count": len({review["citation_span_anchor"] for review in reviews}),
            "downstream_requirement_link_count": sum(len(review["downstream_requirement_links"]) for review in reviews),
            "status": "review_only_fixture_packet_not_production_registry_update",
        },
    }
    errors = validate_source_evidence_citation_packet(packet)
    if errors:
        raise SourceEvidenceCitationPacketError("invalid generated packet: " + "; ".join(errors))
    return packet


def validate_source_evidence_citation_packet(packet: Mapping[str, Any]) -> list[str]:
    """Return deterministic validation errors for a citation normalization packet."""

    errors: list[str] = []
    if packet.get("packet_type") != _PACKET_TYPE:
        errors.append(f"packet_type must be {_PACKET_TYPE}")
    if packet.get("mode") != _FIXTURE_MODE:
        errors.append("mode must be fixture_first")
    if packet.get("crawl_enabled") is not False:
        errors.append("crawl_enabled must be false")
    if packet.get("download_enabled") is not False:
        errors.append("download_enabled must be false")
    if packet.get("active_source_record_replacement_enabled") is not False:
        errors.append("active_source_record_replacement_enabled must be false")
    if packet.get("source_registry_promotion_enabled") is not False:
        errors.append("source_registry_promotion_enabled must be false")

    burn_down_queue = packet.get("burn_down_queue")
    if not isinstance(burn_down_queue, Mapping):
        errors.append("burn_down_queue must be an object")
    else:
        for field in ("queue_id", "queue_type", "fixture"):
            if not _nonempty_text(burn_down_queue.get(field)):
                errors.append(f"burn_down_queue.{field} is required")
        if burn_down_queue.get("fixture") != _BURNDOWN_FIXTURE:
            errors.append("burn_down_queue.fixture must point at the committed PP&D readiness fixture")

    reviews = packet.get("reviews")
    seen_evidence: set[str] = set()
    seen_sources: set[str] = set()
    review_record_ids: set[str] = set()
    review_anchors: set[str] = set()
    if not isinstance(reviews, list) or not reviews:
        errors.append("reviews must be a non-empty list")
    else:
        for index, review in enumerate(reviews):
            _validate_review(review, index, seen_evidence, seen_sources, review_record_ids, review_anchors, errors)

    registry_source_ids = _validate_source_registry_snapshot(packet.get("source_registry_snapshot"), seen_sources, errors)
    _validate_normalized_records(packet.get("normalized_records"), seen_evidence, review_record_ids, review_anchors, registry_source_ids, errors)

    summary = packet.get("review_summary")
    if not isinstance(summary, Mapping):
        errors.append("review_summary must be an object")
    elif isinstance(reviews, list):
        normalized_records = packet.get("normalized_records")
        if summary.get("review_count") != len(reviews):
            errors.append("review_summary.review_count must match reviews length")
        if isinstance(normalized_records, list) and summary.get("normalized_record_count") != len(normalized_records):
            errors.append("review_summary.normalized_record_count must match normalized_records length")
        if summary.get("status") != "review_only_fixture_packet_not_production_registry_update":
            errors.append("review_summary.status must remain review-only")

    _scan_for_forbidden_markers(packet, "packet", errors)
    return errors


def _validate_review(
    review: Any,
    index: int,
    seen_evidence: set[str],
    seen_sources: set[str],
    review_record_ids: set[str],
    review_anchors: set[str],
    errors: list[str],
) -> None:
    if not isinstance(review, Mapping):
        errors.append(f"reviews[{index}] must be an object")
        return

    evidence_id = review.get("source_evidence_id")
    source_id = review.get("synthetic_source_id")
    anchor = review.get("citation_span_anchor")
    document_hash = review.get("document_hash")

    if not _nonempty_text(evidence_id):
        errors.append(f"reviews[{index}].source_evidence_id is required")
    elif str(evidence_id) in seen_evidence:
        errors.append(f"reviews[{index}].source_evidence_id must be unique")
    else:
        seen_evidence.add(str(evidence_id))

    if not _nonempty_text(source_id):
        errors.append(f"reviews[{index}].synthetic_source_id is required")
    elif not str(source_id).startswith("synthetic-"):
        errors.append(f"reviews[{index}].synthetic_source_id must be synthetic")
    elif str(source_id) in seen_sources:
        errors.append(f"reviews[{index}].synthetic_source_id must be unique")
    else:
        seen_sources.add(str(source_id))

    if review.get("source_id_status") != _ALLOWED_SOURCE_ID_STATUS:
        errors.append(f"reviews[{index}].source_id_status must be {_ALLOWED_SOURCE_ID_STATUS}")
    if review.get("source_id_freshness_status") != _ALLOWED_SOURCE_FRESHNESS:
        errors.append(f"reviews[{index}].source_id_freshness_status must be {_ALLOWED_SOURCE_FRESHNESS}")
    if not _nonempty_text(anchor) or not str(anchor).startswith(_BURNDOWN_FIXTURE + "#"):
        errors.append(f"reviews[{index}].citation_span_anchor must point into the burn-down fixture")
    else:
        review_anchors.add(str(anchor))
    if review.get("citation_anchor_status") != "fixture_anchor_present":
        errors.append(f"reviews[{index}].citation_anchor_status must be fixture_anchor_present")

    normalized_record_ids = review.get("normalized_record_ids")
    if not isinstance(normalized_record_ids, list) or not normalized_record_ids:
        errors.append(f"reviews[{index}].normalized_record_ids must be a non-empty list")
    else:
        for record_id in normalized_record_ids:
            if not _nonempty_text(record_id):
                errors.append(f"reviews[{index}].normalized_record_ids must contain non-empty strings")
            else:
                review_record_ids.add(str(record_id))

    if not isinstance(document_hash, str) or not _HASH_RE.match(document_hash):
        errors.append(f"reviews[{index}].document_hash must be a 64-character lowercase sha256 hex digest")
    if review.get("document_hash_status") != "fixture_hash_present_not_live_verified":
        errors.append(f"reviews[{index}].document_hash_status must be fixture_hash_present_not_live_verified")
    if review.get("visible_update_date") != "fixture_only_not_live_verified":
        errors.append(f"reviews[{index}].visible_update_date must be fixture_only_not_live_verified")
    if review.get("visible_update_date_status") != "review_required_before_freshness_promotion":
        errors.append(f"reviews[{index}].visible_update_date_status must require freshness review")
    if review.get("source_record_action") != _ALLOWED_REVIEW_SOURCE_ACTION:
        errors.append(f"reviews[{index}].source_record_action must not replace active source records")

    links = review.get("downstream_requirement_links")
    if not isinstance(links, list) or not links:
        errors.append(f"reviews[{index}].downstream_requirement_links must be a non-empty list")
    else:
        for link_index, link in enumerate(links):
            _validate_downstream_link(link, index, link_index, str(evidence_id or ""), errors)


def _validate_downstream_link(link: Any, review_index: int, link_index: int, evidence_id: str, errors: list[str]) -> None:
    if not isinstance(link, Mapping):
        errors.append(f"reviews[{review_index}].downstream_requirement_links[{link_index}] must be an object")
        return
    for field in ("requirement_link_id", "blocker_id", "action_required", "prerequisite_packet_id"):
        if not _nonempty_text(link.get(field)):
            errors.append(f"reviews[{review_index}].downstream_requirement_links[{link_index}].{field} is required")
    source_evidence_ids = link.get("source_evidence_ids")
    if source_evidence_ids != [evidence_id]:
        errors.append(f"reviews[{review_index}].downstream_requirement_links[{link_index}].source_evidence_ids must cite the reviewed evidence id")


def _validate_source_registry_snapshot(snapshot: Any, review_source_ids: set[str], errors: list[str]) -> set[str]:
    registry_source_ids: set[str] = set()
    if not isinstance(snapshot, Mapping):
        errors.append("source_registry_snapshot must be an object")
        return registry_source_ids

    registered_source_ids = snapshot.get("registered_source_ids")
    if not isinstance(registered_source_ids, list) or not registered_source_ids:
        errors.append("source_registry_snapshot.registered_source_ids must be a non-empty list")
    else:
        for source_id in registered_source_ids:
            if not _nonempty_text(source_id):
                errors.append("source_registry_snapshot.registered_source_ids must contain non-empty strings")
            elif not str(source_id).startswith("synthetic-"):
                errors.append("source_registry_snapshot.registered_source_ids must be synthetic review ids")
            else:
                registry_source_ids.add(str(source_id))

    if snapshot.get("stale_source_ids") != []:
        errors.append("source_registry_snapshot.stale_source_ids must be empty")
    if snapshot.get("missing_source_id_policy") != "reject_packet":
        errors.append("source_registry_snapshot.missing_source_id_policy must be reject_packet")
    if snapshot.get("promotion_action") != "none_review_only":
        errors.append("source_registry_snapshot.promotion_action must be none_review_only")

    missing_from_registry = sorted(review_source_ids - registry_source_ids)
    if missing_from_registry:
        errors.append("source_registry_snapshot.registered_source_ids missing reviewed source ids: " + ", ".join(missing_from_registry))
    return registry_source_ids


def _validate_normalized_records(
    records: Any,
    reviewed_evidence_ids: set[str],
    reviewed_record_ids: set[str],
    reviewed_anchors: set[str],
    registry_source_ids: set[str],
    errors: list[str],
) -> None:
    if not isinstance(records, list) or not records:
        errors.append("normalized_records must be a non-empty list")
        return

    seen_record_ids: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            errors.append(f"normalized_records[{index}] must be an object")
            continue

        record_id = record.get("record_id")
        if not _nonempty_text(record_id):
            errors.append(f"normalized_records[{index}].record_id is required")
        else:
            record_id_text = str(record_id)
            if record_id_text in seen_record_ids:
                errors.append(f"normalized_records[{index}].record_id must be unique")
            seen_record_ids.add(record_id_text)
            if record_id_text not in reviewed_record_ids:
                errors.append(f"normalized_records[{index}].record_id must be cited by a review")

        source_id = record.get("source_id")
        if not _nonempty_text(source_id):
            errors.append(f"normalized_records[{index}].source_id is required")
        elif str(source_id) not in registry_source_ids:
            errors.append(f"normalized_records[{index}].source_id must be present in source_registry_snapshot.registered_source_ids")

        if record.get("source_id_freshness_status") != _ALLOWED_SOURCE_FRESHNESS:
            errors.append(f"normalized_records[{index}].source_id_freshness_status must be {_ALLOWED_SOURCE_FRESHNESS}")
        if record.get("body_storage") != _ALLOWED_BODY_STORAGE:
            errors.append(f"normalized_records[{index}].body_storage must be {_ALLOWED_BODY_STORAGE}")
        if record.get("promotion_action") != _ALLOWED_RECORD_PROMOTION_ACTION:
            errors.append(f"normalized_records[{index}].promotion_action must be review-only")

        document_ref = record.get("document_ref")
        if not _nonempty_text(document_ref):
            errors.append(f"normalized_records[{index}].document_ref is required")
        elif _looks_like_private_url(str(document_ref)) or _looks_like_downloaded_path(str(document_ref)):
            errors.append(f"normalized_records[{index}].document_ref must not be private, authenticated, or downloaded")

        source_evidence_ids = record.get("source_evidence_ids")
        if not isinstance(source_evidence_ids, list) or not source_evidence_ids:
            errors.append(f"normalized_records[{index}].source_evidence_ids must be a non-empty list")
        else:
            for evidence_id in source_evidence_ids:
                if not _nonempty_text(evidence_id) or str(evidence_id) not in reviewed_evidence_ids:
                    errors.append(f"normalized_records[{index}].source_evidence_ids must cite reviewed evidence ids")
                    break

        citation_span_anchors = record.get("citation_span_anchors")
        if not isinstance(citation_span_anchors, list) or not citation_span_anchors:
            errors.append(f"normalized_records[{index}].citation_span_anchors must be a non-empty list")
        else:
            for anchor in citation_span_anchors:
                if not _nonempty_text(anchor) or str(anchor) not in reviewed_anchors:
                    errors.append(f"normalized_records[{index}].citation_span_anchors must cite reviewed fixture anchors")
                    break


def _document_hash(evidence_id: str, source_id: str, blocker: Mapping[str, Any]) -> str:
    seed = "|".join(
        [
            evidence_id,
            source_id,
            str(blocker.get("blocker_id", "")),
            str(blocker.get("summary", "")),
        ]
    )
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _scan_for_forbidden_markers(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = _normalized(str(key))
            if any(marker in key_text for marker in _FORBIDDEN_MARKERS):
                if str(key) not in {
                    "crawl_enabled",
                    "download_enabled",
                    "active_source_record_replacement_enabled",
                    "source_registry_promotion_enabled",
                }:
                    errors.append(f"{path}.{key} uses forbidden live/private/source-replacement field naming")
            _scan_for_forbidden_markers(child, f"{path}.{key}", errors)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_for_forbidden_markers(child, f"{path}[{index}]", errors)
        return
    if isinstance(value, str):
        text = _normalized(value)
        if _looks_like_private_url(value):
            errors.append(f"{path} includes forbidden private/authenticated URL")
            return
        if _looks_like_downloaded_path(value):
            errors.append(f"{path} includes forbidden downloaded document path")
            return
        for marker in _FORBIDDEN_MARKERS:
            if marker in text and value not in _ALLOWED_FORBIDDEN_LITERAL_VALUES:
                errors.append(f"{path} includes forbidden live/private/source-replacement marker: {marker}")
                return


def _looks_like_private_url(value: str) -> bool:
    text = value.strip().lower()
    if text.startswith(("http://", "https://")):
        private_parts = ("/login", "/signin", "/sign-in", "/account", "/session", "token=", "auth=", "access_token=")
        return any(part in text for part in private_parts)
    return False


def _looks_like_downloaded_path(value: str) -> bool:
    text = value.strip().lower()
    path_markers = ("/downloads/", "\\downloads\\", "/downloaded_documents/", "downloaded_documents/", "file://")
    if any(marker in text for marker in path_markers):
        return True
    if text.endswith((".html", ".htm", ".pdf")) and not text.startswith("fixture_metadata_only:"):
        return True
    return False


def _slug(value: str) -> str:
    slug = _normalized(value)
    slug = re.sub(r"[^a-z0-9_]+", "_", slug).strip("_")
    return slug.replace("_", "-") or "unknown"


def _normalized(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
