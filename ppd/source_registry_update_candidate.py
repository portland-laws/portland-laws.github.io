"""Build fixture-first source registry update candidate packets.

This module intentionally performs no network access and does not mutate an active
SourceRegistry. It converts public coverage-gap and recrawl-review packets into a
metadata-only candidate packet for human review.
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse
import json
import re

from ppd.source_freshness.invalidation_packet import (
    PUBLIC_SOURCE_HOSTS,
    _looks_private_or_authenticated_url,
)

DEFAULT_REVIEWER_OWNER = "ppd-source-registry-reviewer"
DEFAULT_GENERATOR = "ppd.source_registry_update_candidate"

ACTIVE_MUTATION_KEYS = frozenset(
    {
        "active_registry_mutation",
        "active_registry_mutation_enabled",
        "apply_to_live_registry",
        "applied_to_live_registry",
        "edit_live_registry",
        "live_registry_edit",
        "live_registry_edited",
        "live_registry_updated",
        "mutates_active_registry",
        "promote_to_registry",
        "promotes_registry_changes",
        "registry_mutated",
        "write_to_registry",
    }
)
LIVE_FETCH_KEYS = frozenset(
    {
        "crawl_performed",
        "fetch_performed",
        "fetched_at",
        "live_fetch",
        "live_fetch_claim",
        "live_network_evidence",
        "network_requests_made",
        "performs_source_fetch",
        "source_fetched",
    }
)
RAW_REFERENCE_KEYS = frozenset(
    {
        "archive_artifact_ref",
        "archive_path",
        "archive_url",
        "download_path",
        "download_url",
        "downloaded_document",
        "downloaded_document_path",
        "har",
        "raw_archive",
        "raw_archive_path",
        "raw_crawl_output",
        "raw_download",
        "raw_download_path",
        "raw_page_body",
        "raw_response_path",
        "raw_warc_path",
        "screenshot",
        "trace",
        "warc",
        "warc_path",
    }
)
RAW_REFERENCE_PATTERN = re.compile(
    r"(^file://|(^|/)(raw[-_ ]?crawl|raw[-_ ]?archive|downloaded[-_ ]?documents?|warc|har|trace)(/|$)|"
    r"\.(warc|warc\.gz|har|zip|tar|tar\.gz)$|/tmp/|/var/tmp/)",
    re.IGNORECASE,
)
URL_FIELD_NAMES = frozenset({"canonical_url", "requested_url", "source_url", "url"})


def load_json_packet(path: str | Path) -> dict[str, Any]:
    """Load a JSON packet from disk for fixture-first candidate generation."""

    with Path(path).open("r", encoding="utf-8") as packet_file:
        packet = json.load(packet_file)
    if not isinstance(packet, dict):
        raise ValueError(f"packet must be a JSON object: {path}")
    return packet


def build_candidate_packet(
    coverage_gap_packet: Mapping[str, Any],
    recrawl_review_packet: Mapping[str, Any],
    *,
    generated_by: str = DEFAULT_GENERATOR,
) -> dict[str, Any]:
    """Return a deterministic metadata-only source registry candidate packet."""

    coverage_gaps = _as_list(coverage_gap_packet.get("coverage_gaps") or coverage_gap_packet.get("gaps"))
    recrawl_reviews = _as_list(
        recrawl_review_packet.get("reviewed_sources")
        or recrawl_review_packet.get("source_reviews")
        or recrawl_review_packet.get("reviews")
    )

    review_by_key = {_source_key(item): item for item in recrawl_reviews if _source_key(item)}
    gap_by_key = {_source_key(item): item for item in coverage_gaps if _source_key(item)}
    ordered_keys = sorted(set(review_by_key) | set(gap_by_key))
    source_packet_ids = _packet_reference(coverage_gap_packet, recrawl_review_packet)

    proposed_registry_row_diffs: list[dict[str, Any]] = []
    skip_reason_updates: list[dict[str, Any]] = []
    freshness_status_candidates: list[dict[str, Any]] = []
    rollback_notes: list[dict[str, Any]] = []
    reviewer_owners: list[dict[str, Any]] = []

    for key in ordered_keys:
        gap = gap_by_key.get(key, {})
        review = review_by_key.get(key, {})
        combined = _merge_source_metadata(gap, review)
        source_id = combined["source_id"]
        canonical_url = combined["canonical_url"]
        owner = _first_text(review.get("reviewer_owner"), review.get("owner"), gap.get("reviewer_owner"), gap.get("owner"))
        if not owner:
            owner = DEFAULT_REVIEWER_OWNER

        if _requires_registry_row_diff(gap, review):
            proposed_registry_row_diffs.append(
                {
                    "source_id": source_id,
                    "canonical_url": canonical_url,
                    "operation": _row_operation(gap, review),
                    "metadata_only": True,
                    "before": _registry_before(review),
                    "after": _registry_after(combined),
                    "candidate_reason": _first_text(
                        gap.get("candidate_reason"),
                        gap.get("gap_reason"),
                        gap.get("reason"),
                        review.get("candidate_reason"),
                        "coverage gap or recrawl review requires metadata review",
                    ),
                    "citation_ids": source_packet_ids,
                    "source_packet_ids": source_packet_ids,
                }
            )

        skip_reason = _first_text(
            review.get("proposed_skip_reason"),
            review.get("skip_reason"),
            gap.get("proposed_skip_reason"),
            gap.get("skip_reason"),
        )
        if skip_reason:
            skip_reason_updates.append(
                {
                    "source_id": source_id,
                    "canonical_url": canonical_url,
                    "proposed_skip_reason": skip_reason,
                    "metadata_only": True,
                    "source_packet": source_packet_ids,
                }
            )

        freshness_status = _first_text(
            review.get("proposed_freshness_status"),
            review.get("freshness_status"),
            gap.get("proposed_freshness_status"),
            gap.get("freshness_status"),
        )
        if freshness_status:
            freshness_status_candidates.append(
                {
                    "source_id": source_id,
                    "canonical_url": canonical_url,
                    "proposed_freshness_status": freshness_status,
                    "evidence_status": _first_text(review.get("review_status"), gap.get("coverage_status"), "fixture_reviewed"),
                    "metadata_only": True,
                }
            )

        rollback_notes.append(
            {
                "source_id": source_id,
                "canonical_url": canonical_url,
                "rollback_action": "discard_candidate_packet_only",
                "active_registry_impact": "none",
                "notes": "Candidate is metadata-only and can be abandoned without registry rollback.",
            }
        )
        reviewer_owners.append(
            {
                "source_id": source_id,
                "canonical_url": canonical_url,
                "reviewer_owner": owner,
                "review_scope": "source registry metadata candidate review",
            }
        )

    candidate = {
        "packet_type": "source_registry_update_candidate",
        "schema_version": "1.0",
        "generated_by": generated_by,
        "source_packet_ids": source_packet_ids,
        "fixture_first": True,
        "metadata_only": True,
        "promotes_registry_changes": False,
        "performs_source_fetch": False,
        "proposed_registry_row_diffs": proposed_registry_row_diffs,
        "skip_reason_updates": skip_reason_updates,
        "freshness_status_candidates": freshness_status_candidates,
        "rollback_notes": rollback_notes,
        "reviewer_owners": reviewer_owners,
        "no_active_registry_mutation_attestations": [
            {
                "attestation": "no_network_fetch_performed",
                "status": "true",
                "basis": "candidate built only from supplied packets",
            },
            {
                "attestation": "no_active_registry_mutation_performed",
                "status": "true",
                "basis": "output contains proposed diffs only",
            },
            {
                "attestation": "no_registry_promotion_performed",
                "status": "true",
                "basis": "promotes_registry_changes is false",
            },
        ],
    }
    validate_candidate_packet(candidate)
    return candidate


def validate_candidate_packet(candidate_packet: Mapping[str, Any]) -> None:
    """Validate safety invariants for a source registry update candidate packet."""

    if candidate_packet.get("metadata_only") is not True:
        raise ValueError("candidate packet must be metadata_only")
    if candidate_packet.get("promotes_registry_changes") is not False:
        raise ValueError("candidate packet must not promote registry changes")
    if candidate_packet.get("performs_source_fetch") is not False:
        raise ValueError("candidate packet must not perform source fetches")
    if not candidate_packet.get("no_active_registry_mutation_attestations"):
        raise ValueError("candidate packet must include no-mutation attestations")

    for section_name in (
        "proposed_registry_row_diffs",
        "skip_reason_updates",
        "freshness_status_candidates",
        "rollback_notes",
        "reviewer_owners",
    ):
        section = candidate_packet.get(section_name)
        if not isinstance(section, list):
            raise ValueError(f"{section_name} must be a list")

    _assert_no_forbidden_claims(candidate_packet)
    _assert_candidate_sections_are_review_owned(candidate_packet)

    for index, diff in enumerate(candidate_packet.get("proposed_registry_row_diffs", [])):
        if not isinstance(diff, Mapping):
            raise ValueError("registry row diffs must be objects")
        if diff.get("metadata_only") is not True:
            raise ValueError("registry row diffs must be metadata-only")
        operation = diff.get("operation")
        if operation not in {"add_metadata_only_row", "update_metadata_only_row"}:
            raise ValueError(f"unsupported registry row diff operation: {operation}")
        if not _string_list(diff.get("citation_ids")) and not _string_list(diff.get("source_packet_ids")):
            raise ValueError(f"proposed_registry_row_diffs[{index}] must include citation_ids or source_packet_ids")
        _assert_official_public_url(_first_text(diff.get("canonical_url")), f"proposed_registry_row_diffs[{index}].canonical_url")
        after = diff.get("after")
        if isinstance(after, Mapping):
            _assert_official_public_url(_first_text(after.get("canonical_url")), f"proposed_registry_row_diffs[{index}].after.canonical_url")


def _as_list(value: Any) -> list[Mapping[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("packet list section must be a list")
    result: list[Mapping[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise ValueError("packet list items must be objects")
        result.append(item)
    return result


def _source_key(item: Mapping[str, Any]) -> str:
    source_id = _first_text(item.get("source_id"))
    canonical_url = _first_text(item.get("canonical_url"), item.get("url"))
    return source_id or canonical_url


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _packet_reference(*packets: Mapping[str, Any]) -> list[str]:
    packet_ids: list[str] = []
    for packet in packets:
        packet_id = _first_text(packet.get("packet_id"), packet.get("id"))
        if packet_id and packet_id not in packet_ids:
            packet_ids.append(packet_id)
    return packet_ids


def _merge_source_metadata(gap: Mapping[str, Any], review: Mapping[str, Any]) -> dict[str, Any]:
    merged = deepcopy(dict(gap))
    merged.update({key: value for key, value in review.items() if value not in (None, "")})
    source_id = _first_text(merged.get("source_id"), merged.get("canonical_url"), merged.get("url"))
    canonical_url = _first_text(merged.get("canonical_url"), merged.get("url"), source_id)
    merged["source_id"] = source_id
    merged["canonical_url"] = canonical_url
    return merged


def _requires_registry_row_diff(gap: Mapping[str, Any], review: Mapping[str, Any]) -> bool:
    if _first_text(gap.get("gap_type")) in {"missing_registry_row", "absent_from_registry"}:
        return True
    if _first_text(review.get("review_disposition")) in {"metadata_update_candidate", "add_metadata_candidate"}:
        return True
    if review.get("registry_before") and review.get("registry_after"):
        return True
    return bool(gap) and not _first_text(gap.get("skip_reason"), review.get("skip_reason"))


def _row_operation(gap: Mapping[str, Any], review: Mapping[str, Any]) -> str:
    if _first_text(gap.get("gap_type")) in {"missing_registry_row", "absent_from_registry"}:
        return "add_metadata_only_row"
    if _first_text(review.get("review_disposition")) == "add_metadata_candidate":
        return "add_metadata_only_row"
    return "update_metadata_only_row"


def _registry_before(review: Mapping[str, Any]) -> dict[str, Any] | None:
    before = review.get("registry_before")
    if before is None:
        return None
    if not isinstance(before, Mapping):
        raise ValueError("registry_before must be an object when present")
    return dict(before)


def _registry_after(combined: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_id": combined["source_id"],
        "canonical_url": combined["canonical_url"],
        "source_type": _first_text(combined.get("source_type"), "public_html"),
        "owning_surface": _first_text(combined.get("owning_surface"), "ppd_public"),
        "allowlist_policy": _first_text(combined.get("allowlist_policy"), "official_public_allowlist"),
        "robots_policy": _first_text(combined.get("robots_policy"), "respect_robots_txt"),
        "crawl_frequency": _first_text(combined.get("crawl_frequency"), "review_required"),
        "processor_policy": _first_text(combined.get("processor_policy"), "metadata_only_candidate_no_fetch"),
        "privacy_classification": _first_text(combined.get("privacy_classification"), "public"),
        "last_seen_at": _first_text(combined.get("last_seen_at"), "not_captured_by_candidate"),
        "freshness_status": _first_text(combined.get("proposed_freshness_status"), combined.get("freshness_status"), "review_required"),
    }


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _is_falsey_claim(value: Any) -> bool:
    return value is False or value is None or value in {"false", "none", "not_applied", "proposed_only"}


def _assert_no_forbidden_claims(value: Any, path: str = "candidate_packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            if key_lower in ACTIVE_MUTATION_KEYS and not _is_falsey_claim(child):
                raise ValueError(f"active registry mutation flag is not allowed: {path}.{key_text}")
            if key_lower in LIVE_FETCH_KEYS and not _is_falsey_claim(child):
                raise ValueError(f"live fetch claim is not allowed: {path}.{key_text}")
            if key_lower in RAW_REFERENCE_KEYS and not _is_falsey_claim(child):
                raise ValueError(f"raw crawl, download, or archive reference is not allowed: {path}.{key_text}")
            if key_lower in URL_FIELD_NAMES and isinstance(child, str):
                _assert_official_public_url(child, f"{path}.{key_text}")
            _assert_no_forbidden_claims(child, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_forbidden_claims(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if RAW_REFERENCE_PATTERN.search(value):
            raise ValueError(f"raw crawl, download, or archive reference is not allowed: {path}")
        if value.startswith("http://") or value.startswith("https://"):
            _assert_official_public_url(value, path)


def _assert_candidate_sections_are_review_owned(candidate_packet: Mapping[str, Any]) -> None:
    candidate_source_ids = _source_ids_from_sections(
        candidate_packet,
        "proposed_registry_row_diffs",
        "skip_reason_updates",
        "freshness_status_candidates",
    )
    rollback_source_ids = _source_ids_from_sections(candidate_packet, "rollback_notes")
    reviewer_source_ids = _source_ids_from_sections(candidate_packet, "reviewer_owners")
    missing_rollback = sorted(candidate_source_ids - rollback_source_ids)
    missing_reviewer = sorted(candidate_source_ids - reviewer_source_ids)
    if missing_rollback:
        raise ValueError("candidate packet missing rollback notes for: " + ", ".join(missing_rollback))
    if missing_reviewer:
        raise ValueError("candidate packet missing reviewer owners for: " + ", ".join(missing_reviewer))
    for index, note in enumerate(candidate_packet.get("rollback_notes", [])):
        if not isinstance(note, Mapping) or not _first_text(note.get("rollback_action"), note.get("notes")):
            raise ValueError(f"rollback_notes[{index}] must include rollback_action or notes")
    for index, owner in enumerate(candidate_packet.get("reviewer_owners", [])):
        if not isinstance(owner, Mapping) or not _first_text(owner.get("reviewer_owner")):
            raise ValueError(f"reviewer_owners[{index}] must include reviewer_owner")


def _source_ids_from_sections(candidate_packet: Mapping[str, Any], *section_names: str) -> set[str]:
    source_ids: set[str] = set()
    for section_name in section_names:
        for item in candidate_packet.get(section_name, []):
            if isinstance(item, Mapping):
                source_id = _first_text(item.get("source_id"))
                if source_id:
                    source_ids.add(source_id)
    return source_ids


def _assert_official_public_url(url: str, label: str) -> None:
    if not url:
        raise ValueError(f"{label} is required")
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    if parsed.scheme not in {"http", "https"} or not hostname:
        raise ValueError(f"{label} must be an http(s) URL")
    if hostname not in PUBLIC_SOURCE_HOSTS:
        raise ValueError(f"{label} is outside the PP&D official public allowlist")
    if _looks_private_or_authenticated_url(url):
        raise ValueError(f"{label} is a private or authenticated target")
