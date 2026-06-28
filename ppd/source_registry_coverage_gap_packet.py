"""Fixture-first public source registry coverage gap packets.

The packet builder consumes committed fixture metadata only: official source
anchors, a validated public-source recrawl dry-run command plan, and source
evidence freshness badges. It reports cited covered anchors, missing anchors,
skipped-source reasons, stale-source notes, and reviewer-owner assignments
without fetching URLs, downloading documents, or mutating the active source
registry.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.parse import urlsplit

from ppd.crawler.public_source_recrawl_dry_run_command_plan import (
    validate_public_source_recrawl_dry_run_command_plan,
)
from ppd.source_anchor_matrix import ORIGINAL_PUBLIC_SOURCE_ANCHORS


PACKET_TYPE = "ppd_public_source_registry_coverage_gap_packet"
SCHEMA_VERSION = 1
SOURCE_MODE = "fixture_first_no_crawl_no_registry_mutation"

_ALLOWED_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}

_ALLOWED_SKIP_REASONS = {
    "outside_allowlist",
    "unsupported_scheme",
    "private_authenticated",
    "disallowed_by_robots_or_policy",
    "raw_download_not_permitted",
    "too_large",
    "unsupported_content_type",
}

_CURRENT_FRESHNESS_STATUSES = {
    "fresh",
    "current",
    "verified_current",
}

_PRIVATE_TARGET_MARKERS = (
    "/account",
    "/admin",
    "/api/private",
    "/dashboard",
    "/login",
    "/my-permits",
    "/permit/",
    "/private",
    "/signin",
    "/sign-in",
    "/user/",
    "auth=",
    "session=",
    "token=",
)

_FORBIDDEN_KEYS = {
    "archive_artifact_ref",
    "archive_path",
    "archive_ref",
    "archive_url",
    "authorization",
    "auth_state",
    "body",
    "cookie",
    "cookies",
    "crawl_output_path",
    "credential",
    "credentials",
    "download_path",
    "download_url",
    "downloaded_document_path",
    "downloaded_file",
    "har_path",
    "html",
    "local_path",
    "password",
    "raw_archive_ref",
    "raw_body",
    "raw_content",
    "raw_crawl_ref",
    "raw_download_ref",
    "raw_html",
    "raw_response",
    "response_body",
    "screenshot_path",
    "secret",
    "session_state",
    "storage_state",
    "token",
    "trace_path",
    "warc_path",
}

_FORBIDDEN_TRUE_KEYS = {
    "active_registry_mutation_enabled",
    "active_registry_write_enabled",
    "activeRegistryMutationEnabled",
    "activeRegistryWriteEnabled",
    "crawlerInvoked",
    "documentsFetchedLive",
    "fetchedLive",
    "live_fetch",
    "liveFetch",
    "liveFetchClaimed",
    "liveFetchUsed",
    "liveNetworkUsed",
    "mutateActiveRegistry",
    "processorInvoked",
    "registryMutationEnabled",
    "sourceRegistryWriteEnabled",
}

_FORBIDDEN_VALUE_MARKERS = (
    "auth_state",
    "bearer ",
    "cookies.json",
    "credential",
    "devhub/session",
    "downloaded_documents",
    "localstorage.json",
    "password",
    "playwright-report",
    "raw_body",
    "raw_html",
    "response_body",
    "session_cookie",
    "storage_state",
    "trace.zip",
    "warc",
)


@dataclass(frozen=True)
class PublicSourceRegistryCoverageGapValidationResult:
    """Validation result for fixture-first source registry gap packets."""

    valid: bool
    errors: tuple[str, ...]


class PublicSourceRegistryCoverageGapPacketError(ValueError):
    """Raised when a source registry coverage gap packet is unsafe."""


def build_public_source_registry_coverage_gap_packet(
    official_source_anchors: Sequence[Any],
    public_source_recrawl_dry_run_command_plan: Mapping[str, Any],
    source_evidence_freshness_badges: Sequence[Mapping[str, Any]] | Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build a deterministic source registry coverage gap packet from fixtures."""

    anchors = _official_anchor_urls(official_source_anchors)
    if set(anchors) != set(ORIGINAL_PUBLIC_SOURCE_ANCHORS):
        raise PublicSourceRegistryCoverageGapPacketError("official_source_anchors must match the PP&D plan anchors")

    dry_run_plan = deepcopy(dict(public_source_recrawl_dry_run_command_plan))
    dry_run_issues = validate_public_source_recrawl_dry_run_command_plan(dry_run_plan)
    if dry_run_issues:
        detail = "; ".join(f"{issue.code}: {issue.message}" for issue in dry_run_issues)
        raise PublicSourceRegistryCoverageGapPacketError("invalid dry-run command plan: " + detail)

    target_urls = set(_target_urls(dry_run_plan))
    skipped_source_reasons = _skipped_source_reasons(dry_run_plan)
    badges = _badge_rows(source_evidence_freshness_badges)
    badges_by_url = {row["canonical_url"]: row for row in badges if row.get("canonical_url")}

    cited_covered_anchors: list[dict[str, Any]] = []
    missing_anchors: list[dict[str, Any]] = []
    stale_source_notes: list[dict[str, Any]] = []
    reviewer_owner_assignments: list[dict[str, Any]] = []

    for anchor_url in anchors:
        badge = badges_by_url.get(anchor_url, {})
        reviewer_owner = _text(badge.get("reviewer_owner"), "ppd-source-reviewer")
        evidence_id = _text(badge.get("evidence_id"))
        freshness_status = _text(badge.get("freshness_status"), "missing_freshness_badge")
        source_id = _text(badge.get("source_id"), _source_id_from_url(anchor_url))

        reviewer_owner_assignments.append(
            {
                "canonical_url": anchor_url,
                "source_id": source_id,
                "reviewer_owner": reviewer_owner,
                "assignment_basis": "source_evidence_freshness_badge" if badge else "missing_freshness_badge_default_owner",
            }
        )

        if anchor_url in target_urls and evidence_id:
            cited_covered_anchors.append(
                {
                    "canonical_url": anchor_url,
                    "source_id": source_id,
                    "dry_run_target_present": True,
                    "source_evidence_ids": [evidence_id],
                    "freshness_badge_id": _text(badge.get("badge_id"), "badge-" + source_id),
                    "freshness_status": freshness_status,
                    "reviewer_owner": reviewer_owner,
                }
            )
        else:
            missing_anchors.append(
                {
                    "canonical_url": anchor_url,
                    "source_id": source_id,
                    "missing_reason": "not_targeted_by_recrawl_dry_run_plan" if anchor_url not in target_urls else "missing_source_evidence_freshness_badge",
                    "source_evidence_ids": [evidence_id] if evidence_id else [],
                    "reviewer_owner": reviewer_owner,
                }
            )

        if freshness_status not in _CURRENT_FRESHNESS_STATUSES:
            stale_source_notes.append(
                {
                    "canonical_url": anchor_url,
                    "source_id": source_id,
                    "freshness_status": freshness_status,
                    "stale_note": _text(
                        badge.get("stale_note"),
                        "Reviewer must refresh or explicitly defer this source before promotion.",
                    ),
                    "source_evidence_ids": [evidence_id] if evidence_id else [],
                    "reviewer_owner": reviewer_owner,
                }
            )

    packet = {
        "schemaVersion": SCHEMA_VERSION,
        "packetType": PACKET_TYPE,
        "sourceMode": SOURCE_MODE,
        "generatedAt": generated_at,
        "fixtureFirst": True,
        "metadataOnly": True,
        "liveCrawlingUsed": False,
        "documentsDownloaded": False,
        "activeSourceRegistryMutated": False,
        "rawBodiesPersisted": False,
        "inputArtifacts": {
            "officialAnchorCount": len(anchors),
            "dryRunTargetCount": len(target_urls),
            "freshnessBadgeCount": len(badges),
            "dryRunMode": _text(dry_run_plan.get("mode"), "public_source_recrawl_dry_run_command_plan"),
        },
        "coverageSummary": {
            "officialAnchorCount": len(anchors),
            "citedCoveredAnchorCount": len(cited_covered_anchors),
            "missingAnchorCount": len(missing_anchors),
            "skippedSourceReasonCount": len(skipped_source_reasons),
            "staleSourceNoteCount": len(stale_source_notes),
            "reviewerOwnerAssignmentCount": len(reviewer_owner_assignments),
        },
        "citedCoveredAnchors": cited_covered_anchors,
        "missingAnchors": missing_anchors,
        "skippedSourceReasons": skipped_source_reasons,
        "staleSourceNotes": stale_source_notes,
        "reviewerOwnerAssignments": reviewer_owner_assignments,
        "sourceRegistryMutation": {
            "activeRegistryMutated": False,
            "registryEditStatus": "not_applied",
            "requiresSeparatePromotionPacket": True,
        },
    }

    require_valid_public_source_registry_coverage_gap_packet(packet)
    return packet


def validate_public_source_registry_coverage_gap_packet(
    packet: Mapping[str, Any],
) -> PublicSourceRegistryCoverageGapValidationResult:
    """Validate a fixture-first source registry coverage gap packet."""

    errors: list[str] = []
    _collect_forbidden_content(packet, "$", errors)

    if packet.get("schemaVersion") != SCHEMA_VERSION:
        errors.append("schemaVersion must be 1")
    if packet.get("packetType") != PACKET_TYPE:
        errors.append("packetType must be " + PACKET_TYPE)
    if packet.get("sourceMode") != SOURCE_MODE:
        errors.append("sourceMode must be " + SOURCE_MODE)
    if not str(packet.get("generatedAt", "")).endswith("Z"):
        errors.append("generatedAt must be an ISO UTC timestamp ending in Z")

    for key in ("fixtureFirst", "metadataOnly"):
        if packet.get(key) is not True:
            errors.append(f"{key} must be true")
    for key in ("liveCrawlingUsed", "documentsDownloaded", "activeSourceRegistryMutated", "rawBodiesPersisted"):
        if packet.get(key) is not False:
            errors.append(f"{key} must be false")

    covered = _require_list(packet.get("citedCoveredAnchors"), "citedCoveredAnchors", errors)
    missing = _require_list(packet.get("missingAnchors"), "missingAnchors", errors)
    skipped = _require_list(packet.get("skippedSourceReasons"), "skippedSourceReasons", errors)
    stale = _require_list(packet.get("staleSourceNotes"), "staleSourceNotes", errors)
    owners = _require_list(packet.get("reviewerOwnerAssignments"), "reviewerOwnerAssignments", errors)

    official_urls = set(ORIGINAL_PUBLIC_SOURCE_ANCHORS)
    covered_urls = _validate_anchor_rows(covered, "citedCoveredAnchors", official_urls, True, errors)
    missing_urls = _validate_anchor_rows(missing, "missingAnchors", official_urls, True, errors)
    owner_urls = _validate_owner_rows(owners, official_urls, errors)
    _validate_skipped_rows(skipped, errors)
    _validate_stale_rows(stale, official_urls, errors)

    if not covered_urls:
        errors.append("citedCoveredAnchors must include at least one covered official anchor")
    if not skipped:
        errors.append("skippedSourceReasons must include cited skip decisions for non-covered discovered sources")
    if covered_urls & missing_urls:
        errors.append("citedCoveredAnchors and missingAnchors must not overlap")
    if covered_urls | missing_urls != official_urls:
        errors.append("covered plus missing anchors must equal all official source anchors")
    if owner_urls != official_urls:
        errors.append("reviewerOwnerAssignments must cover every official source anchor")

    mutation = packet.get("sourceRegistryMutation")
    if not isinstance(mutation, Mapping):
        errors.append("sourceRegistryMutation must be an object")
    else:
        if mutation.get("activeRegistryMutated") is not False:
            errors.append("sourceRegistryMutation.activeRegistryMutated must be false")
        if mutation.get("registryEditStatus") != "not_applied":
            errors.append("sourceRegistryMutation.registryEditStatus must be not_applied")
        if mutation.get("requiresSeparatePromotionPacket") is not True:
            errors.append("sourceRegistryMutation.requiresSeparatePromotionPacket must be true")

    summary = packet.get("coverageSummary")
    if not isinstance(summary, Mapping):
        errors.append("coverageSummary must be an object")
    else:
        expected_counts = {
            "officialAnchorCount": len(official_urls),
            "citedCoveredAnchorCount": len(covered),
            "missingAnchorCount": len(missing),
            "skippedSourceReasonCount": len(skipped),
            "staleSourceNoteCount": len(stale),
            "reviewerOwnerAssignmentCount": len(owners),
        }
        for key, expected in expected_counts.items():
            if summary.get(key) != expected:
                errors.append(f"coverageSummary.{key} must be {expected}")

    return PublicSourceRegistryCoverageGapValidationResult(valid=not errors, errors=tuple(errors))


def require_valid_public_source_registry_coverage_gap_packet(packet: Mapping[str, Any]) -> None:
    """Raise when a source registry coverage gap packet is unsafe or incomplete."""

    result = validate_public_source_registry_coverage_gap_packet(packet)
    if not result.valid:
        raise PublicSourceRegistryCoverageGapPacketError("; ".join(result.errors))


def _official_anchor_urls(rows: Sequence[Any]) -> list[str]:
    urls: list[str] = []
    for row in rows:
        if isinstance(row, str):
            url = row.strip()
        elif isinstance(row, Mapping):
            url = _text(row.get("canonical_url") or row.get("url"))
        else:
            url = ""
        if url:
            urls.append(url)
    return urls


def _target_urls(plan: Mapping[str, Any]) -> list[str]:
    values = plan.get("targets") or plan.get("sources") or []
    if isinstance(values, Mapping):
        values = [values]
    urls: list[str] = []
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
        for item in values:
            if isinstance(item, str):
                url = item.strip()
            elif isinstance(item, Mapping):
                url = _text(item.get("url") or item.get("target"))
            else:
                url = ""
            if url:
                urls.append(url)
    return urls


def _skipped_source_reasons(plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    values = plan.get("skipped_source_reasons") or plan.get("skippedSources") or plan.get("skipped_urls") or plan.get("skippedUrls") or []
    if isinstance(values, Mapping):
        values = [values]
    rows: list[dict[str, Any]] = []
    if isinstance(values, Sequence) and not isinstance(values, (str, bytes)):
        for index, item in enumerate(values):
            if not isinstance(item, Mapping):
                continue
            rows.append(
                {
                    "skip_id": _text(item.get("skip_id"), f"skip-{index + 1}"),
                    "url": _text(item.get("url")),
                    "reason": _text(item.get("reason")),
                    "cited_policy_evidence_id": _text(item.get("cited_policy_evidence_id"), "policy-public-crawl-preflight"),
                    "raw_body_stored": False,
                }
            )
    return rows


def _badge_rows(value: Sequence[Mapping[str, Any]] | Mapping[str, Any]) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        raw_rows = value.get("badges") or value.get("source_evidence_freshness_badges") or []
    else:
        raw_rows = value
    rows: list[dict[str, Any]] = []
    if isinstance(raw_rows, Sequence) and not isinstance(raw_rows, (str, bytes)):
        for item in raw_rows:
            if not isinstance(item, Mapping):
                continue
            rows.append(
                {
                    "badge_id": _text(item.get("badge_id") or item.get("id")),
                    "canonical_url": _text(item.get("canonical_url") or item.get("url")),
                    "source_id": _text(item.get("source_id")),
                    "evidence_id": _text(item.get("evidence_id")),
                    "freshness_status": _text(item.get("freshness_status"), "unknown"),
                    "stale_note": _text(item.get("stale_note")),
                    "reviewer_owner": _text(item.get("reviewer_owner"), "ppd-source-reviewer"),
                }
            )
    return rows


def _validate_anchor_rows(
    rows: list[Any],
    field: str,
    official_urls: set[str],
    require_evidence: bool,
    errors: list[str],
) -> set[str]:
    urls: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"{field}[{index}] must be an object")
            continue
        prefix = f"{field}[{index}]"
        url = _text(row.get("canonical_url"))
        if _is_private_or_authenticated_target(url):
            errors.append(f"{prefix}.canonical_url must not be a private or authenticated target")
        if not _is_public_allowlisted_url(url):
            errors.append(f"{prefix}.canonical_url must be an HTTPS allowlisted public URL")
        if url not in official_urls:
            errors.append(f"{prefix}.canonical_url must be an official source anchor")
        else:
            urls.add(url)
        if not _text(row.get("source_id")):
            errors.append(f"{prefix}.source_id is required")
        if not _text(row.get("reviewer_owner")):
            errors.append(f"{prefix}.reviewer_owner is required")
        evidence_ids = row.get("source_evidence_ids")
        if require_evidence and (not isinstance(evidence_ids, list) or not all(_text(item) for item in evidence_ids)):
            errors.append(f"{prefix}.source_evidence_ids must cite at least one evidence id")
        if field == "citedCoveredAnchors" and row.get("dry_run_target_present") is not True:
            errors.append(f"{prefix}.dry_run_target_present must be true")
        if field == "missingAnchors" and not _text(row.get("missing_reason")):
            errors.append(f"{prefix}.missing_reason is required")
    return urls


def _validate_owner_rows(rows: list[Any], official_urls: set[str], errors: list[str]) -> set[str]:
    urls: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"reviewerOwnerAssignments[{index}] must be an object")
            continue
        prefix = f"reviewerOwnerAssignments[{index}]"
        url = _text(row.get("canonical_url"))
        if _is_private_or_authenticated_target(url):
            errors.append(f"{prefix}.canonical_url must not be a private or authenticated target")
        if not _is_public_allowlisted_url(url):
            errors.append(f"{prefix}.canonical_url must be an HTTPS allowlisted public URL")
        if url not in official_urls:
            errors.append(f"{prefix}.canonical_url must be an official source anchor")
        else:
            urls.add(url)
        if not _text(row.get("source_id")):
            errors.append(f"{prefix}.source_id is required")
        if not _text(row.get("reviewer_owner")):
            errors.append(f"{prefix}.reviewer_owner is required")
        if not _text(row.get("assignment_basis")):
            errors.append(f"{prefix}.assignment_basis is required")
    return urls


def _validate_skipped_rows(rows: list[Any], errors: list[str]) -> None:
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"skippedSourceReasons[{index}] must be an object")
            continue
        prefix = f"skippedSourceReasons[{index}]"
        url = _text(row.get("url"))
        reason = _text(row.get("reason"))
        if not _text(row.get("skip_id")):
            errors.append(f"{prefix}.skip_id is required")
        if not url:
            errors.append(f"{prefix}.url is required")
        if reason not in _ALLOWED_SKIP_REASONS:
            errors.append(f"{prefix}.reason is not an allowed skip reason")
        if not _text(row.get("cited_policy_evidence_id")):
            errors.append(f"{prefix}.cited_policy_evidence_id is required")
        if row.get("raw_body_stored") is not False:
            errors.append(f"{prefix}.raw_body_stored must be false")
        if reason != "unsupported_scheme" and url:
            parsed = urlsplit(url)
            if parsed.scheme != "https":
                errors.append(f"{prefix}.url must be HTTPS unless reason is unsupported_scheme")


def _validate_stale_rows(rows: list[Any], official_urls: set[str], errors: list[str]) -> None:
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(f"staleSourceNotes[{index}] must be an object")
            continue
        prefix = f"staleSourceNotes[{index}]"
        url = _text(row.get("canonical_url"))
        if _is_private_or_authenticated_target(url):
            errors.append(f"{prefix}.canonical_url must not be a private or authenticated target")
        if not _is_public_allowlisted_url(url):
            errors.append(f"{prefix}.canonical_url must be an HTTPS allowlisted public URL")
        if url not in official_urls:
            errors.append(f"{prefix}.canonical_url must be an official source anchor")
        if _text(row.get("freshness_status")) in _CURRENT_FRESHNESS_STATUSES:
            errors.append(f"{prefix}.freshness_status must represent stale or pending evidence")
        if not _text(row.get("stale_note")):
            errors.append(f"{prefix}.stale_note is required")
        evidence_ids = row.get("source_evidence_ids")
        if not isinstance(evidence_ids, list) or not all(_text(item) for item in evidence_ids):
            errors.append(f"{prefix}.source_evidence_ids must cite at least one evidence id")
        if not _text(row.get("reviewer_owner")):
            errors.append(f"{prefix}.reviewer_owner is required")


def _require_list(value: Any, field: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{field} must be a list")
        return []
    return value


def _collect_forbidden_content(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            if key_text in _FORBIDDEN_TRUE_KEYS and child not in (None, "", [], {}, False):
                errors.append(f"{path}.{key_text} must not claim live fetch, processor execution, or active registry mutation")
            if key_text.lower() in _FORBIDDEN_KEYS and child not in (None, "", [], {}, False):
                errors.append(f"{path}.{key_text} must not contain private, raw, download, crawl, archive, or authenticated content")
            _collect_forbidden_content(child, f"{path}.{key_text}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _collect_forbidden_content(child, f"{path}[{index}]", errors)
    elif isinstance(value, str):
        lower_value = value.lower()
        for marker in _FORBIDDEN_VALUE_MARKERS:
            if marker in lower_value:
                errors.append(f"{path} contains forbidden private/raw artifact marker {marker}")


def _is_public_allowlisted_url(url: str) -> bool:
    parsed = urlsplit(url)
    return parsed.scheme == "https" and parsed.netloc.lower() in _ALLOWED_HOSTS


def _is_private_or_authenticated_target(url: str) -> bool:
    parsed = urlsplit(url)
    combined = (parsed.path + "?" + parsed.query).lower()
    return any(marker in combined for marker in _PRIVATE_TARGET_MARKERS)


def _source_id_from_url(url: str) -> str:
    parsed = urlsplit(url)
    slug = (parsed.netloc + parsed.path).strip("/").lower()
    for old, new in (("https://", ""), ("www.", ""), ("/", "-"), ("_", "-"), (".", "-")):
        slug = slug.replace(old, new)
    return "source-" + "-".join(part for part in slug.split("-") if part)


def _text(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else default
    return default


__all__ = [
    "PACKET_TYPE",
    "PublicSourceRegistryCoverageGapPacketError",
    "PublicSourceRegistryCoverageGapValidationResult",
    "build_public_source_registry_coverage_gap_packet",
    "require_valid_public_source_registry_coverage_gap_packet",
    "validate_public_source_registry_coverage_gap_packet",
]
