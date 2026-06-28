"""Validation for PP&D source refresh runbook candidates.

The validator is intentionally side-effect free. It accepts a plain mapping so
fixtures, daemon proposals, and future typed contracts can all be checked before
any live crawl, processor invocation, schedule activation, or registry write.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse


ALLOWLISTED_HOSTS = frozenset(
    {
        "www.portland.gov",
        "portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "portlandoregon.gov",
        "www.portlandmaps.com",
        "portlandmaps.com",
    }
)

PRIVATE_PATH_MARKERS = (
    "/login",
    "/sign-in",
    "/signin",
    "/register",
    "/account",
    "/accounts",
    "/my-permits",
    "/mypermits",
    "/dashboard",
    "/profile",
    "/payment",
    "/payments",
    "/checkout",
    "/upload",
    "/submit",
    "/schedule",
)

PRIVATE_QUERY_MARKERS = (
    "token=",
    "session=",
    "auth=",
    "code=",
    "password=",
    "receipt=",
)

RAW_REFERENCE_MARKERS = (
    "raw_body",
    "raw body",
    "response_body",
    "html_body",
    "body_text",
    "download",
    "download_url",
    "downloaded_document",
    "archive_artifact_ref",
    "warc",
    "har",
    "trace",
    "screenshot",
)

LIVE_EXECUTION_MARKERS = (
    "live fetch",
    "live_fetch",
    "fetch now",
    "run processor",
    "processor execution",
    "execute processor",
    "invoke processor",
    "crawl now",
    "download now",
)


@dataclass(frozen=True)
class SourceRefreshRunbookFinding:
    """A deterministic validation finding for a proposed refresh runbook."""

    code: str
    message: str
    field: str


def validate_source_refresh_runbook_candidate(
    candidate: Mapping[str, Any],
) -> list[SourceRefreshRunbookFinding]:
    """Return blocking findings for an unsafe source refresh runbook candidate."""

    findings: list[SourceRefreshRunbookFinding] = []
    target_urls = _collect_urls(candidate)

    if not target_urls:
        findings.append(
            SourceRefreshRunbookFinding(
                code="missing_targets",
                field="targets",
                message="Refresh runbook candidates must name at least one public target URL.",
            )
        )

    for field, url in target_urls:
        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        query = parsed.query.lower()
        if parsed.scheme not in {"http", "https"}:
            findings.append(
                SourceRefreshRunbookFinding(
                    code="unsupported_scheme",
                    field=field,
                    message=f"Target {url!r} uses a non-HTTP(S) scheme.",
                )
            )
            continue
        if host not in ALLOWLISTED_HOSTS:
            findings.append(
                SourceRefreshRunbookFinding(
                    code="outside_allowlist",
                    field=field,
                    message=f"Target {url!r} is outside the PP&D public source allowlist.",
                )
            )
        if any(marker in path for marker in PRIVATE_PATH_MARKERS) or any(
            marker in query for marker in PRIVATE_QUERY_MARKERS
        ):
            findings.append(
                SourceRefreshRunbookFinding(
                    code="private_or_authenticated_target",
                    field=field,
                    message=f"Target {url!r} appears to require private or authenticated access.",
                )
            )
        if any(marker in path or marker in query for marker in RAW_REFERENCE_MARKERS):
            findings.append(
                SourceRefreshRunbookFinding(
                    code="raw_download_or_archive_reference",
                    field=field,
                    message=f"Target {url!r} references raw body, download, or archive material.",
                )
            )

    if not _has_policy_evidence(candidate, "robots"):
        findings.append(
            SourceRefreshRunbookFinding(
                code="missing_robots_evidence",
                field="robots_evidence",
                message="Refresh runbook candidates must include robots evidence for every target set.",
            )
        )

    if not _has_policy_evidence(candidate, "policy"):
        findings.append(
            SourceRefreshRunbookFinding(
                code="missing_policy_evidence",
                field="policy_evidence",
                message="Refresh runbook candidates must include allowlist or source policy evidence.",
            )
        )

    flattened = _flatten_strings(candidate)
    lowered = "\n".join(flattened).lower()
    for marker in RAW_REFERENCE_MARKERS:
        if marker in lowered:
            findings.append(
                SourceRefreshRunbookFinding(
                    code="raw_download_or_archive_reference",
                    field="candidate",
                    message="Refresh runbook candidates must not reference raw bodies, downloads, archives, HARs, traces, or screenshots.",
                )
            )
            break

    for marker in LIVE_EXECUTION_MARKERS:
        if marker in lowered:
            findings.append(
                SourceRefreshRunbookFinding(
                    code="live_fetch_or_processor_execution_claim",
                    field="candidate",
                    message="Refresh runbook candidates must remain preflight-only and must not claim live fetches or processor execution.",
                )
            )
            break

    if _truthy(candidate.get("live_fetch_enabled")) or _truthy(candidate.get("perform_live_fetch")):
        findings.append(
            SourceRefreshRunbookFinding(
                code="live_fetch_or_processor_execution_claim",
                field="live_fetch_enabled",
                message="Live fetch flags are not allowed in source refresh runbook candidates.",
            )
        )

    if _truthy(candidate.get("processor_execution_enabled")) or _truthy(
        candidate.get("execute_processor")
    ):
        findings.append(
            SourceRefreshRunbookFinding(
                code="live_fetch_or_processor_execution_claim",
                field="processor_execution_enabled",
                message="Processor execution flags are not allowed in source refresh runbook candidates.",
            )
        )

    if not _has_rate_limit_window(candidate):
        findings.append(
            SourceRefreshRunbookFinding(
                code="missing_rate_limit_window",
                field="rate_limit",
                message="Refresh runbook candidates must define a deterministic rate-limit window.",
            )
        )

    if not _has_reviewer_checkpoints(candidate):
        findings.append(
            SourceRefreshRunbookFinding(
                code="missing_reviewer_checkpoints",
                field="reviewer_checkpoints",
                message="Refresh runbook candidates must include reviewer checkpoints before refresh execution.",
            )
        )

    if not _has_abort_and_escalation(candidate):
        findings.append(
            SourceRefreshRunbookFinding(
                code="missing_abort_escalation_notes",
                field="abort_escalation",
                message="Refresh runbook candidates must include abort and escalation notes.",
            )
        )

    if _truthy(candidate.get("active_schedule")) or _truthy(candidate.get("schedule_enabled")):
        findings.append(
            SourceRefreshRunbookFinding(
                code="active_schedule_flag",
                field="active_schedule",
                message="Refresh runbook candidates must not enable active scheduling.",
            )
        )

    if _truthy(candidate.get("registry_mutation")) or _truthy(candidate.get("mutates_registry")):
        findings.append(
            SourceRefreshRunbookFinding(
                code="registry_mutation_flag",
                field="registry_mutation",
                message="Refresh runbook candidates must not mutate the source registry.",
            )
        )

    return findings


def is_source_refresh_runbook_candidate_valid(candidate: Mapping[str, Any]) -> bool:
    """Return True when the candidate has no blocking validation findings."""

    return not validate_source_refresh_runbook_candidate(candidate)


def findings_as_dicts(
    findings: Sequence[SourceRefreshRunbookFinding],
) -> list[dict[str, str]]:
    """Serialize findings without exposing implementation details."""

    return [
        {"code": finding.code, "field": finding.field, "message": finding.message}
        for finding in findings
    ]


def _collect_urls(candidate: Mapping[str, Any]) -> list[tuple[str, str]]:
    urls: list[tuple[str, str]] = []
    for key in ("target_url", "canonical_url", "url"):
        value = candidate.get(key)
        if isinstance(value, str) and value.strip():
            urls.append((key, value.strip()))
    for key in ("targets", "target_urls", "seed_urls", "candidate_targets"):
        value = candidate.get(key)
        if isinstance(value, str) and value.strip():
            urls.append((key, value.strip()))
        elif isinstance(value, Iterable) and not isinstance(value, (str, bytes, Mapping)):
            for index, item in enumerate(value):
                if isinstance(item, str) and item.strip():
                    urls.append((f"{key}[{index}]", item.strip()))
                elif isinstance(item, Mapping):
                    nested_url = item.get("url") or item.get("canonical_url") or item.get("target_url")
                    if isinstance(nested_url, str) and nested_url.strip():
                        urls.append((f"{key}[{index}]", nested_url.strip()))
    return urls


def _flatten_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        strings: list[str] = []
        for key, nested in value.items():
            strings.extend(_flatten_strings(key))
            strings.extend(_flatten_strings(nested))
        return strings
    if isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        strings = []
        for nested in value:
            strings.extend(_flatten_strings(nested))
        return strings
    return []


def _has_policy_evidence(candidate: Mapping[str, Any], policy_name: str) -> bool:
    direct_keys = (
        f"{policy_name}_evidence",
        f"{policy_name}_policy_evidence",
        f"{policy_name}_checked_at",
    )
    if any(_present(candidate.get(key)) for key in direct_keys):
        return True
    evidence = candidate.get("policy_evidence")
    if isinstance(evidence, Mapping):
        return _present(evidence.get(policy_name)) or _present(evidence.get(f"{policy_name}_policy"))
    return False


def _has_rate_limit_window(candidate: Mapping[str, Any]) -> bool:
    value = candidate.get("rate_limit") or candidate.get("rate_limit_window")
    if isinstance(value, Mapping):
        return _present(value.get("window")) or (
            _present(value.get("requests")) and _present(value.get("per_seconds"))
        )
    return _present(value)


def _has_reviewer_checkpoints(candidate: Mapping[str, Any]) -> bool:
    value = candidate.get("reviewer_checkpoints") or candidate.get("review_checkpoints")
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_present(item) for item in value)
    return _present(value)


def _has_abort_and_escalation(candidate: Mapping[str, Any]) -> bool:
    combined = candidate.get("abort_escalation")
    if isinstance(combined, Mapping):
        return _present(combined.get("abort")) and _present(combined.get("escalation"))
    return _present(candidate.get("abort_notes")) and _present(candidate.get("escalation_notes"))


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (Sequence, Mapping)):
        return bool(value)
    return True


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled", "active"}
    return bool(value)
