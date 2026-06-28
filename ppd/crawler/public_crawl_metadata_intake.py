"""Validation for PP&D public crawl metadata dry-run intake packets.

The intake validator is intentionally conservative. Public crawl dry-runs may
record metadata needed for review, but they must not claim live execution,
completed crawls/downloads, private/authenticated access, or raw artifact
persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable
from urllib.parse import urlparse

ALLOWED_PUBLIC_HOSTS = frozenset(
    {
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

PRIVATE_OR_AUTH_PATH_MARKERS = frozenset(
    {
        "account",
        "admin",
        "auth",
        "dashboard",
        "login",
        "logout",
        "mfa",
        "my-account",
        "my-permits",
        "oauth",
        "password",
        "payment",
        "payments",
        "profile",
        "register",
        "session",
        "signin",
        "sign-in",
        "signup",
        "sign-up",
        "sso",
        "token",
        "upload",
        "uploads",
        "user",
    }
)

PRIVATE_OR_AUTH_QUERY_MARKERS = frozenset(
    {
        "access_token",
        "auth",
        "authorization",
        "code",
        "id_token",
        "jwt",
        "login",
        "password",
        "session",
        "sso",
        "token",
    }
)

RAW_ARTIFACT_KEY_MARKERS = frozenset(
    {
        "archive_path",
        "archive_paths",
        "archive_ref",
        "archive_refs",
        "body",
        "body_path",
        "download_path",
        "download_paths",
        "downloaded_file",
        "downloaded_files",
        "har_path",
        "html_body",
        "local_archive",
        "local_path",
        "raw",
        "raw_archive",
        "raw_body",
        "raw_body_path",
        "raw_content",
        "raw_download",
        "raw_html",
        "trace_path",
        "warc_path",
        "warc_paths",
    }
)

RAW_ARTIFACT_VALUE_MARKERS = frozenset(
    {
        ".har",
        ".trace",
        ".warc",
        ".warc.gz",
        "/archive/",
        "/archives/",
        "/downloads/",
        "/raw/",
        "archive_path",
        "download_path",
        "raw_body",
        "raw_content",
        "warc_path",
    }
)

LIVE_EXECUTION_KEYS = frozenset(
    {
        "executed_live_network",
        "live_network_execution",
        "network_executed",
        "performed_live_crawl",
        "real_crawl_completed",
        "crawl_completed",
        "download_completed",
        "completed_download",
        "downloaded",
    }
)

LIVE_EXECUTION_PHRASES = (
    "download completed",
    "downloaded document",
    "downloaded file",
    "executed live network",
    "live network execution",
    "performed live crawl",
    "real crawl completed",
    "real download completed",
)


@dataclass(frozen=True)
class IntakeViolation:
    """A deterministic intake validation failure."""

    code: str
    message: str
    location: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message, "location": self.location}


def validate_public_crawl_metadata_dry_run_intake(
    packet: dict[str, Any],
    *,
    allowed_hosts: Iterable[str] = ALLOWED_PUBLIC_HOSTS,
) -> list[IntakeViolation]:
    """Return all policy violations in a public crawl metadata dry-run packet."""

    allowed_host_set = frozenset(host.lower() for host in allowed_hosts)
    violations: list[IntakeViolation] = []

    if not isinstance(packet, dict):
        return [
            IntakeViolation(
                "packet_not_object",
                "Public crawl metadata dry-run intake packet must be an object.",
                "$",
            )
        ]

    if packet.get("dry_run") is not True:
        violations.append(
            IntakeViolation(
                "dry_run_required",
                "Public crawl metadata intake must be explicitly marked dry_run=true.",
                "$.dry_run",
            )
        )

    _require_link(packet, violations, "promotion_manifest_url", "missing_promotion_manifest")
    _require_evidence(packet, violations, "robots_evidence", "missing_robots_evidence")
    _require_evidence(packet, violations, "policy_evidence", "missing_policy_evidence")
    _require_abort_decision(packet, violations)

    for location, key, value in _walk(packet):
        lowered_key = key.lower() if key else ""

        if _is_url_like(value):
            _validate_url(str(value), location, allowed_host_set, violations)

        if _is_raw_artifact_key(lowered_key):
            violations.append(
                IntakeViolation(
                    "raw_artifact_path_forbidden",
                    "Dry-run intake must not include raw body, download, archive, trace, HAR, or WARC paths.",
                    location,
                )
            )
        elif isinstance(value, str) and _looks_like_raw_artifact_value(value):
            violations.append(
                IntakeViolation(
                    "raw_artifact_path_forbidden",
                    "Dry-run intake must not include raw body, download, archive, trace, HAR, or WARC paths.",
                    location,
                )
            )

        if lowered_key in LIVE_EXECUTION_KEYS and _truthy_claim(value):
            violations.append(
                IntakeViolation(
                    "live_execution_claim_forbidden",
                    "Dry-run intake must not claim live network execution, completed crawls, or completed downloads.",
                    location,
                )
            )
        elif isinstance(value, str) and _contains_live_execution_phrase(value):
            violations.append(
                IntakeViolation(
                    "live_execution_claim_forbidden",
                    "Dry-run intake must not claim live network execution, completed crawls, or completed downloads.",
                    location,
                )
            )

    return _dedupe(violations)


def validate_public_crawl_metadata_dry_run_intake_dict(
    packet: dict[str, Any],
) -> dict[str, Any]:
    """Return a JSON-serializable validation result."""

    violations = validate_public_crawl_metadata_dry_run_intake(packet)
    return {
        "accepted": not violations,
        "violations": [violation.as_dict() for violation in violations],
    }


def _require_link(
    packet: dict[str, Any],
    violations: list[IntakeViolation],
    field_name: str,
    code: str,
) -> None:
    value = packet.get(field_name) or packet.get("promotion_manifest_link")
    if not isinstance(value, str) or not value.strip():
        violations.append(
            IntakeViolation(
                code,
                "Dry-run intake must include a promotion-manifest link before promotion review.",
                f"$.{field_name}",
            )
        )


def _require_evidence(
    packet: dict[str, Any],
    violations: list[IntakeViolation],
    field_name: str,
    code: str,
) -> None:
    value = packet.get(field_name)
    if value in (None, "", [], {}):
        violations.append(
            IntakeViolation(
                code,
                f"Dry-run intake must include {field_name.replace('_', ' ')}.",
                f"$.{field_name}",
            )
        )


def _require_abort_decision(packet: dict[str, Any], violations: list[IntakeViolation]) -> None:
    value = packet.get("abort_decision")
    if not isinstance(value, dict) or value.get("decision") not in {"abort", "continue_dry_run_only", "blocked"}:
        violations.append(
            IntakeViolation(
                "missing_abort_decision",
                "Dry-run intake must include an abort decision proving no real crawl or download was completed.",
                "$.abort_decision",
            )
        )


def _walk(value: Any, location: str = "$", key: str = "") -> Iterable[tuple[str, str, Any]]:
    yield location, key, value
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            yield from _walk(child_value, f"{location}.{child_key_text}", child_key_text)
    elif isinstance(value, list):
        for index, child_value in enumerate(value):
            yield from _walk(child_value, f"{location}[{index}]", key)


def _is_url_like(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _validate_url(
    url: str,
    location: str,
    allowed_hosts: frozenset[str],
    violations: list[IntakeViolation],
) -> None:
    parsed = urlparse(url.strip())
    host = (parsed.hostname or "").lower()

    if parsed.scheme != "https":
        violations.append(
            IntakeViolation(
                "unsupported_url_scheme",
                "Public crawl dry-run URLs must use https.",
                location,
            )
        )

    if host not in allowed_hosts:
        violations.append(
            IntakeViolation(
                "non_allowlisted_host",
                "Public crawl dry-run URL host is not allowlisted for PP&D metadata intake.",
                location,
            )
        )

    path_parts = {part.lower() for part in PurePosixPath(parsed.path).parts if part not in {"/", ""}}
    query = parsed.query.lower()
    if path_parts.intersection(PRIVATE_OR_AUTH_PATH_MARKERS) or any(
        marker in query for marker in PRIVATE_OR_AUTH_QUERY_MARKERS
    ):
        violations.append(
            IntakeViolation(
                "private_or_authenticated_url",
                "Dry-run intake must reject private, authenticated, account, payment, upload, or session URLs.",
                location,
            )
        )


def _is_raw_artifact_key(key: str) -> bool:
    if key in RAW_ARTIFACT_KEY_MARKERS:
        return True
    return any(marker in key for marker in ("raw_body", "raw_content", "warc_path", "har_path", "trace_path"))


def _looks_like_raw_artifact_value(value: str) -> bool:
    lowered = value.strip().lower()
    if not lowered:
        return False
    return any(marker in lowered for marker in RAW_ARTIFACT_VALUE_MARKERS)


def _truthy_claim(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"1", "completed", "done", "executed", "true", "yes"}
    return value not in (None, [], {})


def _contains_live_execution_phrase(value: str) -> bool:
    lowered = value.lower()
    return any(phrase in lowered for phrase in LIVE_EXECUTION_PHRASES)


def _dedupe(violations: list[IntakeViolation]) -> list[IntakeViolation]:
    seen: set[tuple[str, str]] = set()
    deduped: list[IntakeViolation] = []
    for violation in violations:
        key = (violation.code, violation.location)
        if key not in seen:
            seen.add(key)
            deduped.append(violation)
    return deduped
