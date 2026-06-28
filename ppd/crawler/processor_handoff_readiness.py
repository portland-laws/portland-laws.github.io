"""Validation for PP&D processor handoff readiness packets.

Readiness packets are preflight descriptions. They must prove that a later
processor handoff is safe to plan, without embedding raw crawl output, private
session data, live execution switches, or claims about archive artifacts that do
not exist yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse

DEFAULT_ALLOWED_HOSTS = frozenset(
    {
        "portland.gov",
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

_PRIVATE_PATH_MARKERS = (
    "/account",
    "/admin",
    "/auth",
    "/dashboard",
    "/login",
    "/logout",
    "/my-permits",
    "/oauth",
    "/permit/application",
    "/register",
    "/saml",
    "/session",
    "/sign-in",
    "/signin",
    "/user",
)

_PRIVATE_QUERY_MARKERS = (
    "access_token",
    "auth",
    "code",
    "id_token",
    "password",
    "session",
    "token",
)

_RAW_PATH_MARKERS = (
    "/archive/",
    "/archives/",
    "/crawl/",
    "/download",
    "/downloads/",
    "/raw/",
    ".har",
    ".warc",
    ".warc.gz",
)

_RAW_REFERENCE_KEYS = frozenset(
    {
        "archive_path",
        "crawl_output",
        "download_path",
        "download_ref",
        "har_path",
        "raw_archive_ref",
        "raw_body",
        "raw_body_ref",
        "raw_content",
        "raw_crawl_ref",
        "raw_download_ref",
        "raw_html",
        "raw_path",
        "raw_text",
        "screenshot_path",
        "trace_path",
        "warc_path",
    }
)

_ARCHIVE_CLAIM_KEYS = frozenset(
    {
        "archive_artifact_ref",
        "archive_artifacts",
        "archive_manifest_ref",
        "artifact_manifest",
        "artifacts_produced",
        "produced_archive_artifacts",
        "warc_artifact_ref",
    }
)

_LIVE_EXECUTION_KEYS = frozenset(
    {
        "allow_live_network",
        "execute",
        "execute_processor",
        "invoke_processor",
        "live",
        "live_crawl",
        "live_processor_execution",
        "processor_execute",
        "run_processor",
        "start_processor",
    }
)

_SKIP_REASON_KEYS = ("skipped_reason", "reason", "policy_reason")
_URL_KEYS = ("url", "href", "target_url", "canonical_url", "requested_url")
_TARGET_COLLECTION_KEYS = ("targets", "target_urls", "source_targets")
_PREREQUISITE_COLLECTION_KEYS = ("prerequisite_links", "prerequisites")
_SKIP_COLLECTION_KEYS = ("skipped_targets", "skips", "skipped_urls")


@dataclass(frozen=True)
class ReadinessIssue:
    code: str
    message: str
    location: str


@dataclass(frozen=True)
class ReadinessValidation:
    ok: bool
    issues: tuple[ReadinessIssue, ...]

    def raise_for_issues(self) -> None:
        if self.issues:
            rendered = "; ".join(
                f"{issue.code} at {issue.location}: {issue.message}"
                for issue in self.issues
            )
            raise ValueError(rendered)


def validate_processor_handoff_readiness(
    packet: Mapping[str, Any],
    *,
    allowed_hosts: Iterable[str] = DEFAULT_ALLOWED_HOSTS,
) -> ReadinessValidation:
    """Validate a PP&D processor handoff readiness packet.

    The validator is intentionally schema-tolerant so packet producers can evolve
    field names while policy-critical checks remain centralized and deterministic.
    """

    allowed = frozenset(host.lower() for host in allowed_hosts)
    issues: list[ReadinessIssue] = []

    prerequisite_links = _collect_entries(packet, _PREREQUISITE_COLLECTION_KEYS)
    if not prerequisite_links:
        issues.append(
            ReadinessIssue(
                "MISSING_PREREQUISITE_LINKS",
                "packet must include at least one public prerequisite link",
                "prerequisite_links",
            )
        )

    for index, entry in enumerate(prerequisite_links):
        url = _entry_url(entry)
        if not url:
            issues.append(
                ReadinessIssue(
                    "MISSING_PREREQUISITE_LINK_URL",
                    "prerequisite link is missing a URL",
                    f"prerequisite_links[{index}]",
                )
            )
            continue
        _validate_public_url(
            url,
            f"prerequisite_links[{index}]",
            allowed,
            issues,
        )

    targets = _collect_entries(packet, _TARGET_COLLECTION_KEYS)
    for index, entry in enumerate(targets):
        url = _entry_url(entry)
        if not url:
            issues.append(
                ReadinessIssue(
                    "MISSING_TARGET_URL",
                    "handoff target is missing a URL",
                    f"targets[{index}]",
                )
            )
            continue
        _validate_public_url(url, f"targets[{index}]", allowed, issues)
        if _looks_like_raw_reference_url(url):
            issues.append(
                ReadinessIssue(
                    "RAW_TARGET_REFERENCE",
                    "handoff targets must not point at raw crawl, download, or archive references",
                    f"targets[{index}]",
                )
            )
        if isinstance(entry, Mapping) and (
            entry.get("private") is True or entry.get("authenticated") is True
        ):
            issues.append(
                ReadinessIssue(
                    "PRIVATE_OR_AUTHENTICATED_TARGET",
                    "handoff targets must be public and unauthenticated",
                    f"targets[{index}]",
                )
            )

    _validate_skip_reasons(packet, issues)
    _validate_no_raw_body_attestation(packet, issues)
    _scan_for_forbidden_fields(packet, "$", issues)

    return ReadinessValidation(ok=not issues, issues=tuple(issues))


def require_processor_handoff_readiness(
    packet: Mapping[str, Any],
    *,
    allowed_hosts: Iterable[str] = DEFAULT_ALLOWED_HOSTS,
) -> None:
    """Raise ValueError when a readiness packet fails validation."""

    validate_processor_handoff_readiness(
        packet,
        allowed_hosts=allowed_hosts,
    ).raise_for_issues()


def _collect_entries(
    packet: Mapping[str, Any],
    keys: Sequence[str],
) -> list[Any]:
    entries: list[Any] = []
    for key in keys:
        value = packet.get(key)
        if value is None:
            continue
        if isinstance(value, str):
            entries.append(value)
        elif isinstance(value, Mapping):
            entries.append(value)
        elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
            entries.extend(value)
    return entries


def _entry_url(entry: Any) -> str | None:
    if isinstance(entry, str):
        return entry.strip() or None
    if isinstance(entry, Mapping):
        for key in _URL_KEYS:
            value = entry.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _validate_public_url(
    url: str,
    location: str,
    allowed_hosts: frozenset[str],
    issues: list[ReadinessIssue],
) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        issues.append(
            ReadinessIssue(
                "UNSUPPORTED_URL_SCHEME",
                "URL must use http or https and include a host",
                location,
            )
        )
        return

    host = parsed.hostname.lower() if parsed.hostname else ""
    if host not in allowed_hosts:
        issues.append(
            ReadinessIssue(
                "NON_ALLOWLISTED_TARGET",
                "URL host is not in the PP&D public source allowlist",
                location,
            )
        )

    lowered_path = parsed.path.lower()
    lowered_query = parsed.query.lower()
    if any(marker in lowered_path for marker in _PRIVATE_PATH_MARKERS) or any(
        marker in lowered_query for marker in _PRIVATE_QUERY_MARKERS
    ):
        issues.append(
            ReadinessIssue(
                "PRIVATE_OR_AUTHENTICATED_TARGET",
                "URL appears to require authentication or private account context",
                location,
            )
        )


def _looks_like_raw_reference_url(url: str) -> bool:
    parsed = urlparse(url)
    combined = f"{parsed.path}?{parsed.query}".lower()
    return any(marker in combined for marker in _RAW_PATH_MARKERS)


def _validate_no_raw_body_attestation(
    packet: Mapping[str, Any],
    issues: list[ReadinessIssue],
) -> None:
    attestations = packet.get("attestations")
    attestation_sources = [packet]
    if isinstance(attestations, Mapping):
        attestation_sources.append(attestations)

    for source in attestation_sources:
        if source.get("no_raw_body_persisted") is True:
            return
        if source.get("no_raw_body_attestation") is True:
            return

    issues.append(
        ReadinessIssue(
            "MISSING_NO_RAW_BODY_ATTESTATION",
            "packet must attest that no raw body content was persisted",
            "attestations.no_raw_body_persisted",
        )
    )


def _validate_skip_reasons(
    packet: Mapping[str, Any],
    issues: list[ReadinessIssue],
) -> None:
    skipped_entries = _collect_entries(packet, _SKIP_COLLECTION_KEYS)
    for index, entry in enumerate(skipped_entries):
        if isinstance(entry, str):
            issues.append(
                ReadinessIssue(
                    "MISSING_SKIPPED_TARGET_REASON",
                    "skipped target entries must include a reason",
                    f"skipped_targets[{index}]",
                )
            )
            continue
        if not isinstance(entry, Mapping):
            issues.append(
                ReadinessIssue(
                    "MISSING_SKIPPED_TARGET_REASON",
                    "skipped target entries must be objects with reasons",
                    f"skipped_targets[{index}]",
                )
            )
            continue
        if not any(isinstance(entry.get(key), str) and entry.get(key).strip() for key in _SKIP_REASON_KEYS):
            issues.append(
                ReadinessIssue(
                    "MISSING_SKIPPED_TARGET_REASON",
                    "skipped target is missing a policy reason",
                    f"skipped_targets[{index}]",
                )
            )


def _scan_for_forbidden_fields(
    value: Any,
    location: str,
    issues: list[ReadinessIssue],
) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            lowered_key = key_text.lower()
            child_location = f"{location}.{key_text}"

            if lowered_key in _LIVE_EXECUTION_KEYS and child is True:
                issues.append(
                    ReadinessIssue(
                        "LIVE_PROCESSOR_EXECUTION_FLAG",
                        "readiness packets must not enable live processor execution",
                        child_location,
                    )
                )

            if lowered_key in _RAW_REFERENCE_KEYS and _has_value(child):
                issues.append(
                    ReadinessIssue(
                        "RAW_REFERENCE_PRESENT",
                        "readiness packets must not contain raw crawl, download, archive, trace, or screenshot references",
                        child_location,
                    )
                )

            if lowered_key in _ARCHIVE_CLAIM_KEYS and _has_value(child):
                issues.append(
                    ReadinessIssue(
                        "ARCHIVE_ARTIFACT_CLAIM",
                        "readiness packets must not claim archive artifacts were already produced",
                        child_location,
                    )
                )

            _scan_for_forbidden_fields(child, child_location, issues)
    elif isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        for index, child in enumerate(value):
            _scan_for_forbidden_fields(child, f"{location}[{index}]", issues)


def _has_value(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (Mapping, Sequence)) and not isinstance(value, (bytes, bytearray, str)):
        return bool(value)
    return True
