"""Validation for PP&D public crawl frontier checkpoint fixtures.

Checkpoint fixtures are deterministic planning records for the public crawler.
They may describe public URLs, skip decisions, and processor handoffs, but they
must not include external crawl targets, authenticated DevHub URLs, raw response
bodies, or processor handoffs without source provenance.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse


ALLOWED_PUBLIC_HOSTS = {
    "www.portland.gov",
    "devhub.portlandoregon.gov",
    "www.portlandoregon.gov",
    "www.portlandmaps.com",
}

SKIPPED_STATUSES = {"skipped", "blocked", "deferred"}
HANDOFF_STATUSES = {"processor_handoff", "handoff"}

AUTHENTICATED_PATH_MARKERS = (
    "/account",
    "/accounts",
    "/dashboard",
    "/login",
    "/logout",
    "/my-permits",
    "/mypermits",
    "/oauth",
    "/permitcart",
    "/permits/my",
    "/profile",
    "/signin",
    "/sign-in",
    "/user",
)

AUTHENTICATED_QUERY_KEYS = {
    "access_token",
    "auth",
    "code",
    "id_token",
    "refresh_token",
    "session",
    "state",
    "token",
}

RAW_BODY_KEYS = {
    "body",
    "content",
    "html",
    "raw_body",
    "raw_content",
    "raw_html",
    "raw_text",
    "response_body",
    "text",
}

PROVENANCE_KEYS = {
    "source_url",
    "canonical_url",
    "captured_at",
    "content_hash",
    "policy_decision",
    "processor_name",
}


@dataclass(frozen=True)
class FrontierCheckpointFinding:
    path: str
    reason: str


def validate_frontier_checkpoint_fixture(fixture: Mapping[str, Any]) -> list[FrontierCheckpointFinding]:
    """Validate a public crawl frontier checkpoint fixture."""

    findings: list[FrontierCheckpointFinding] = []

    if int(fixture.get("schema_version", 0)) != 1:
        findings.append(FrontierCheckpointFinding("schema_version", "schema_version must be 1"))

    checkpoint_id = str(fixture.get("checkpoint_id", "")).strip()
    if not checkpoint_id:
        findings.append(FrontierCheckpointFinding("checkpoint_id", "checkpoint_id is required"))

    generated_at = str(fixture.get("generated_at", ""))
    if not generated_at.endswith("Z"):
        findings.append(FrontierCheckpointFinding("generated_at", "generated_at must be an ISO UTC timestamp ending in Z"))

    entries = fixture.get("frontier", fixture.get("entries"))
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
        findings.append(FrontierCheckpointFinding("frontier", "frontier must be a list of checkpoint entries"))
        return findings

    if not entries:
        findings.append(FrontierCheckpointFinding("frontier", "frontier must contain at least one checkpoint entry"))

    seen_ids: set[str] = set()
    for index, entry in enumerate(entries):
        entry_path = f"frontier[{index}]"
        if not isinstance(entry, Mapping):
            findings.append(FrontierCheckpointFinding(entry_path, "frontier entry must be an object"))
            continue
        findings.extend(_validate_entry(entry, entry_path, seen_ids))

    findings.extend(_validate_no_raw_body_fields(fixture))
    return findings


def assert_valid_frontier_checkpoint_fixture(fixture: Mapping[str, Any]) -> None:
    findings = validate_frontier_checkpoint_fixture(fixture)
    if findings:
        details = "; ".join(f"{finding.path}: {finding.reason}" for finding in findings)
        raise AssertionError(details)


def _validate_entry(entry: Mapping[str, Any], path: str, seen_ids: set[str]) -> list[FrontierCheckpointFinding]:
    findings: list[FrontierCheckpointFinding] = []

    entry_id = str(entry.get("id", "")).strip()
    if not entry_id:
        findings.append(FrontierCheckpointFinding(f"{path}.id", "frontier entry id is required"))
    elif entry_id in seen_ids:
        findings.append(FrontierCheckpointFinding(f"{path}.id", f"duplicate frontier entry id {entry_id}"))
    seen_ids.add(entry_id)

    url = str(entry.get("url", "")).strip()
    findings.extend(_validate_public_url(url, f"{path}.url"))

    status = str(entry.get("status", "")).strip()
    if not status:
        findings.append(FrontierCheckpointFinding(f"{path}.status", "frontier entry status is required"))

    skip_reason = str(entry.get("skip_reason", "")).strip()
    if status in SKIPPED_STATUSES and not skip_reason:
        findings.append(FrontierCheckpointFinding(f"{path}.skip_reason", "skipped frontier entries require skip_reason"))

    if status in HANDOFF_STATUSES:
        handoff = entry.get("processor_handoff")
        if not isinstance(handoff, Mapping):
            findings.append(FrontierCheckpointFinding(f"{path}.processor_handoff", "processor handoff entries require processor_handoff"))
        else:
            findings.extend(_validate_processor_handoff(handoff, f"{path}.processor_handoff"))

    return findings


def _validate_public_url(url: str, path: str) -> list[FrontierCheckpointFinding]:
    findings: list[FrontierCheckpointFinding] = []
    parsed = urlparse(url)

    if parsed.scheme != "https":
        findings.append(FrontierCheckpointFinding(path, "frontier URL must use https"))
    if parsed.hostname not in ALLOWED_PUBLIC_HOSTS:
        findings.append(FrontierCheckpointFinding(path, "frontier URL host must be PP&D allowlisted"))

    lowered_path = parsed.path.lower()
    if parsed.hostname == "devhub.portlandoregon.gov":
        for marker in AUTHENTICATED_PATH_MARKERS:
            if lowered_path.startswith(marker):
                findings.append(FrontierCheckpointFinding(path, "live authenticated DevHub URLs are not allowed in public checkpoint fixtures"))
                break

    query_keys = {part.split("=", 1)[0].lower() for part in parsed.query.split("&") if part}
    if query_keys.intersection(AUTHENTICATED_QUERY_KEYS):
        findings.append(FrontierCheckpointFinding(path, "authenticated query parameters are not allowed in public checkpoint fixtures"))

    return findings


def _validate_processor_handoff(handoff: Mapping[str, Any], path: str) -> list[FrontierCheckpointFinding]:
    findings: list[FrontierCheckpointFinding] = []
    provenance = handoff.get("provenance")
    if not isinstance(provenance, Mapping):
        return [FrontierCheckpointFinding(f"{path}.provenance", "processor handoff requires provenance")]

    missing = sorted(key for key in PROVENANCE_KEYS if not str(provenance.get(key, "")).strip())
    if missing:
        findings.append(FrontierCheckpointFinding(f"{path}.provenance", f"processor handoff provenance missing required keys: {', '.join(missing)}"))

    source_url = str(provenance.get("source_url", ""))
    if source_url:
        findings.extend(_validate_public_url(source_url, f"{path}.provenance.source_url"))

    content_hash = str(provenance.get("content_hash", ""))
    if content_hash and not content_hash.startswith("sha256:"):
        findings.append(FrontierCheckpointFinding(f"{path}.provenance.content_hash", "content_hash must use sha256: prefix"))

    return findings


def _validate_no_raw_body_fields(value: Any, path: str = "fixture") -> list[FrontierCheckpointFinding]:
    findings: list[FrontierCheckpointFinding] = []

    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = key_text.replace("-", "_").lower()
            child_path = f"{path}.{key_text}"
            if normalized in RAW_BODY_KEYS:
                findings.append(FrontierCheckpointFinding(child_path, "raw crawl bodies are not allowed in checkpoint fixtures"))
            findings.extend(_validate_no_raw_body_fields(child, child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            findings.extend(_validate_no_raw_body_fields(child, f"{path}[{index}]"))

    return findings
