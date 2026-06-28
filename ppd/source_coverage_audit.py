"""Validation for PP&D source coverage audit packets.

The validator is intentionally side-effect free. It accepts already-materialized
packet dictionaries from tests, daemon handoff code, or future crawl preflight
steps and reports deterministic findings without fetching any URL.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlparse


OFFICIAL_SOURCE_ANCHORS: tuple[str, ...] = (
    "https://www.portland.gov/ppd",
    "https://www.portland.gov/ppd/how-use-online-permitting-tools",
    "https://devhub.portlandoregon.gov",
    "https://www.portland.gov/ppd/devhub-faqs",
    "https://www.portland.gov/ppd/devhub-sign-guide",
    "https://www.portland.gov/ppd/get-permit/apply-permits",
    "https://www.portland.gov/ppd/devhub-guide-submit-permit-application",
    "https://www.portland.gov/ppd/get-permit/submit-plans-online",
    "https://www.portland.gov/ppd/brochures-forms-handouts/permits-and-inspections-applications",
    "https://www.portland.gov/ppd/spp-file-naming-standards-preparing-pdfs",
    "https://www.portland.gov/ppd/documents/how-pay-fees/download",
    "https://www.portlandmaps.com",
)

ALLOWLIST_HOSTS: frozenset[str] = frozenset(
    {
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

SKIPPED_REASON_CODES: frozenset[str] = frozenset(
    {
        "outside_allowlist",
        "unsupported_scheme",
        "private_authenticated",
        "robots_or_policy_disallowed",
        "raw_download_not_permitted",
        "too_large",
        "unsupported_content_type",
    }
)

_URL_COLLECTION_KEYS: frozenset[str] = frozenset(
    {
        "official_anchors",
        "anchors",
        "sources",
        "source_registry",
        "downstream_links",
        "discovered_links",
        "links",
        "skipped_links",
        "skipped_urls",
        "external_references",
    }
)

_DOWNSTREAM_KEYS: frozenset[str] = frozenset(
    {
        "downstream_links",
        "discovered_links",
        "links",
        "external_references",
    }
)

_URL_FIELD_NAMES: tuple[str, ...] = (
    "canonical_url",
    "requested_url",
    "url",
    "href",
    "source_url",
)

_CITATION_FIELD_NAMES: tuple[str, ...] = (
    "cited_by",
    "source_anchor",
    "source_anchors",
    "parent_anchor",
    "parent_url",
    "discovered_from",
    "source_url",
)

_PRIVATE_PATH_MARKERS: tuple[str, ...] = (
    "/login",
    "/signin",
    "/sign-in",
    "/register",
    "/account",
    "/profile",
    "/dashboard",
    "/my-permits",
    "/mypermits",
    "/secure",
    "/authenticated",
    "/oauth",
    "/saml",
)

_PRIVATE_QUERY_MARKERS: tuple[str, ...] = (
    "token=",
    "session=",
    "password=",
    "code=",
    "auth=",
)

_RAW_BODY_KEYS: frozenset[str] = frozenset(
    {
        "raw_body",
        "raw_html",
        "response_body",
        "body_html",
        "html_body",
        "content_bytes",
        "raw_content",
    }
)

_RAW_PATH_KEYS: frozenset[str] = frozenset(
    {
        "download_path",
        "downloaded_path",
        "downloaded_file",
        "raw_body_path",
        "raw_html_path",
        "raw_archive_path",
    }
)

_DOWNLOAD_SUFFIXES: tuple[str, ...] = (
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".zip",
)


@dataclass(frozen=True)
class AuditFinding:
    """A single validation failure in a source coverage audit packet."""

    code: str
    message: str
    path: str
    url: str | None = None


def validate_source_coverage_audit_packet(packet: dict[str, Any]) -> list[AuditFinding]:
    """Return policy findings for a PP&D source coverage audit packet."""

    findings: list[AuditFinding] = []
    official_anchor_set = set(OFFICIAL_SOURCE_ANCHORS)
    declared_official_anchors = _declared_official_anchors(packet)

    for anchor in OFFICIAL_SOURCE_ANCHORS:
        if anchor not in declared_official_anchors:
            findings.append(
                AuditFinding(
                    code="missing_official_anchor",
                    message="Source coverage audit packet is missing a required official source anchor.",
                    path="official_anchors",
                    url=anchor,
                )
            )

    for key_path, value in _walk(packet):
        key_name = key_path.rsplit(".", 1)[-1].split("[", 1)[0]
        if key_name in _RAW_BODY_KEYS and _has_value(value):
            findings.append(
                AuditFinding(
                    code="raw_body_or_download_path",
                    message="Source coverage audit packets must not include raw body content.",
                    path=key_path,
                )
            )
        if key_name in _RAW_PATH_KEYS and _has_value(value):
            findings.append(
                AuditFinding(
                    code="raw_body_or_download_path",
                    message="Source coverage audit packets must not include raw body or downloaded file paths.",
                    path=key_path,
                )
            )

    for entry_path, entry, url in _iter_url_entries(packet):
        skipped_reason = _skipped_reason(entry)
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()

        if parsed.scheme not in {"http", "https"}:
            _require_skip_reason(
                findings,
                entry_path,
                url,
                skipped_reason,
                "unsupported_scheme",
            )
            continue

        if host not in ALLOWLIST_HOSTS:
            _require_skip_reason(
                findings,
                entry_path,
                url,
                skipped_reason,
                "outside_allowlist",
            )

        if _is_private_or_authenticated_url(url):
            _require_skip_reason(
                findings,
                entry_path,
                url,
                skipped_reason,
                "private_authenticated",
            )

        if _is_download_url(url) and _normalize_url(url) not in official_anchor_set:
            _require_skip_reason(
                findings,
                entry_path,
                url,
                skipped_reason,
                "raw_download_not_permitted",
            )

        if _is_skipped_entry(entry) and skipped_reason not in SKIPPED_REASON_CODES:
            findings.append(
                AuditFinding(
                    code="missing_skipped_reason_code",
                    message="Skipped source entries must include a recognized skipped_reason code.",
                    path=f"{entry_path}.skipped_reason",
                    url=url,
                )
            )

        if _is_downstream_entry(entry_path, url, official_anchor_set):
            citations = _citation_values(entry)
            if not any(_normalize_url(citation) in official_anchor_set for citation in citations):
                findings.append(
                    AuditFinding(
                        code="uncited_downstream_link",
                        message="Downstream source links must cite the official anchor that led to discovery.",
                        path=entry_path,
                        url=url,
                    )
                )

    if _claims_complete_without_human_review(packet):
        findings.append(
            AuditFinding(
                code="complete_without_human_review",
                message="Coverage cannot be claimed complete without explicit human review.",
                path="coverage_claim",
            )
        )

    return findings


def require_valid_source_coverage_audit_packet(packet: dict[str, Any]) -> None:
    """Raise ValueError when a source coverage audit packet has findings."""

    findings = validate_source_coverage_audit_packet(packet)
    if findings:
        details = "; ".join(
            f"{finding.code} at {finding.path}"
            + (f" ({finding.url})" if finding.url else "")
            for finding in findings
        )
        raise ValueError(f"invalid source coverage audit packet: {details}")


def finding_codes(findings: Iterable[AuditFinding]) -> set[str]:
    """Return the set of finding codes, useful for focused tests."""

    return {finding.code for finding in findings}


def _declared_official_anchors(packet: dict[str, Any]) -> set[str]:
    anchors: set[str] = set()
    for value in packet.get("official_anchors", []):
        if isinstance(value, str):
            anchors.add(_normalize_url(value))
        elif isinstance(value, dict):
            url = _entry_url(value)
            if url:
                anchors.add(_normalize_url(url))
    for collection_name in ("anchors", "sources", "source_registry"):
        collection = packet.get(collection_name, [])
        if not isinstance(collection, list):
            continue
        for value in collection:
            if not isinstance(value, dict):
                continue
            if value.get("official_anchor") is True or value.get("source_role") == "official_anchor":
                url = _entry_url(value)
                if url:
                    anchors.add(_normalize_url(url))
    return anchors


def _iter_url_entries(packet: dict[str, Any]) -> Iterable[tuple[str, dict[str, Any], str]]:
    for key_path, value in _walk(packet):
        key_name = key_path.rsplit(".", 1)[-1].split("[", 1)[0]
        if key_name not in _URL_COLLECTION_KEYS or not isinstance(value, list):
            continue
        for index, item in enumerate(value):
            item_path = f"{key_path}[{index}]"
            if isinstance(item, str):
                yield item_path, {"url": item}, _normalize_url(item)
            elif isinstance(item, dict):
                url = _entry_url(item)
                if url:
                    yield item_path, item, _normalize_url(url)


def _entry_url(entry: dict[str, Any]) -> str | None:
    for field_name in _URL_FIELD_NAMES:
        value = entry.get(field_name)
        if isinstance(value, str) and value.strip():
            return value
    return None


def _citation_values(entry: dict[str, Any]) -> list[str]:
    citations: list[str] = []
    for field_name in _CITATION_FIELD_NAMES:
        value = entry.get(field_name)
        if isinstance(value, str) and value.strip():
            citations.append(value)
        elif isinstance(value, list):
            citations.extend(item for item in value if isinstance(item, str) and item.strip())
    return citations


def _is_downstream_entry(path: str, url: str, official_anchors: set[str]) -> bool:
    if _normalize_url(url) in official_anchors:
        return False
    return any(f".{key}" in path or path.startswith(key) for key in _DOWNSTREAM_KEYS)


def _skipped_reason(entry: dict[str, Any]) -> str | None:
    value = entry.get("skipped_reason") or entry.get("skip_reason") or entry.get("reason_code")
    return value if isinstance(value, str) else None


def _is_skipped_entry(entry: dict[str, Any]) -> bool:
    status = entry.get("status") or entry.get("decision") or entry.get("coverage_status")
    return (
        entry.get("skipped") is True
        or entry.get("included") is False
        or status in {"skipped", "blocked", "excluded", "rejected"}
        or _skipped_reason(entry) is not None
    )


def _require_skip_reason(
    findings: list[AuditFinding],
    path: str,
    url: str,
    actual_reason: str | None,
    required_reason: str,
) -> None:
    if actual_reason == required_reason:
        return
    code_by_reason = {
        "outside_allowlist": "outside_allowlist_host",
        "private_authenticated": "private_or_authenticated_url",
        "raw_download_not_permitted": "raw_body_or_download_path",
        "unsupported_scheme": "missing_skipped_reason_code",
    }
    findings.append(
        AuditFinding(
            code=code_by_reason[required_reason],
            message=f"URL must be skipped with skipped_reason={required_reason}.",
            path=path,
            url=url,
        )
    )


def _is_private_or_authenticated_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    query = parsed.query.lower()
    return any(marker in path for marker in _PRIVATE_PATH_MARKERS) or any(
        marker in query for marker in _PRIVATE_QUERY_MARKERS
    )


def _is_download_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower().rstrip("/")
    return path.endswith("/download") or any(path.endswith(suffix) for suffix in _DOWNLOAD_SUFFIXES)


def _claims_complete_without_human_review(packet: dict[str, Any]) -> bool:
    claim = packet.get("coverage_claim")
    candidates: list[dict[str, Any]] = [packet]
    if isinstance(claim, dict):
        candidates.append(claim)

    claims_complete = any(
        candidate.get("coverage_complete") is True
        or candidate.get("all_sources_covered") is True
        or candidate.get("status") in {"complete", "completed"}
        or candidate.get("claim") in {"complete", "completed", "full_coverage"}
        for candidate in candidates
    )
    if not claims_complete:
        return False

    return not any(_has_human_review(candidate) for candidate in candidates)


def _has_human_review(candidate: dict[str, Any]) -> bool:
    status = candidate.get("human_review_status")
    return candidate.get("human_reviewed") is True or status in {
        "reviewed",
        "approved",
        "complete",
        "human_reviewed",
    }


def _walk(value: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            yield child_path, child
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, child
            yield from _walk(child, child_path)


def _has_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _normalize_url(url: str) -> str:
    return url.strip().rstrip("/")
