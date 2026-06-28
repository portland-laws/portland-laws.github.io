"""Validation for DevHub read-only surface drift comparison packets.

The validator is intentionally conservative: packets are evidence bundles for reviewer
comparison, not browser automation transcripts or authenticated crawl output.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import re
from typing import Any


PRIVATE_KEY_PARTS = (
    "auth_state",
    "storage_state",
    "cookie",
    "cookies",
    "local_storage",
    "localstorage",
    "session_storage",
    "sessionstorage",
    "session_id",
    "sessionid",
    "trace",
    "har",
    "screenshot",
    "download",
    "raw_html",
    "raw_response",
)

SECRET_KEY_PARTS = (
    "authorization",
    "access_token",
    "refresh_token",
    "id_token",
    "api_key",
    "apikey",
    "secret",
    "password",
    "bearer",
    "csrf",
)

MUTATION_FLAG_KEYS = (
    "registry_mutation_enabled",
    "active_registry_mutation",
    "write_registry",
    "registry_write_enabled",
    "mutate_registry",
    "apply_registry_changes",
)

CONSEQUENTIAL_ACTION_KEYS = (
    "allow_submit",
    "submit_enabled",
    "submission_enabled",
    "payment_enabled",
    "cancel_enabled",
    "certify_enabled",
    "upload_enabled",
    "account_creation_enabled",
    "mfa_enabled",
    "captcha_automation_enabled",
)

LIVE_BROWSER_PATTERNS = (
    re.compile(r"\b(live|headed|headless)\s+browser\b", re.IGNORECASE),
    re.compile(r"\b(playwright|puppeteer|selenium)\s+(ran|executed|opened|clicked|submitted)\b", re.IGNORECASE),
    re.compile(r"\bclicked\b.*\b(devhub|browser|page)\b", re.IGNORECASE),
    re.compile(r"\bsubmitted\b.*\b(form|application|browser|page)\b", re.IGNORECASE),
)

LOCAL_PATH_PATTERNS = (
    re.compile(r"file://", re.IGNORECASE),
    re.compile(r"/(?:home|Users|private|tmp|var/folders)/[^\s]+"),
    re.compile(r"[A-Za-z]:\\\\(?:Users|Temp|Windows|ProgramData)\\\\[^\s]+"),
    re.compile(r"(?:^|/)(?:\.ssh|\.aws|\.config|\.daemon)(?:/|$)"),
)

PUBLIC_CITATION_RE = re.compile(r"^https://", re.IGNORECASE)


@dataclass(frozen=True)
class DriftValidationIssue:
    code: str
    path: str
    message: str


def validate_devhub_readonly_surface_drift_packet(packet: Mapping[str, Any]) -> list[DriftValidationIssue]:
    """Return validation issues for a DevHub read-only drift packet."""

    issues: list[DriftValidationIssue] = []
    _scan_value(packet, "$", issues)
    _validate_drift_claims(packet, issues)
    _validate_reviewer_owner(packet, issues)
    _validate_deferrals(packet, issues)
    return issues


def assert_valid_devhub_readonly_surface_drift_packet(packet: Mapping[str, Any]) -> None:
    """Raise ValueError when a packet is not safe to accept."""

    issues = validate_devhub_readonly_surface_drift_packet(packet)
    if issues:
        rendered = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in issues)
        raise ValueError(rendered)


def _scan_value(value: Any, path: str, issues: list[DriftValidationIssue]) -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            key = str(raw_key)
            child_path = f"{path}.{key}"
            lowered = _normalized_key(key)
            if any(part in lowered for part in PRIVATE_KEY_PARTS):
                issues.append(DriftValidationIssue("private_or_session_artifact", child_path, "packet includes private/session artifact fields"))
            if any(part in lowered for part in SECRET_KEY_PARTS):
                issues.append(DriftValidationIssue("raw_authenticated_value", child_path, "packet includes raw authenticated value fields"))
            if lowered in MUTATION_FLAG_KEYS and child is not False:
                issues.append(DriftValidationIssue("active_registry_mutation_flag", child_path, "registry mutation flags must be absent or false"))
            if lowered in CONSEQUENTIAL_ACTION_KEYS and child is not False:
                issues.append(DriftValidationIssue("consequential_action_enabled", child_path, "consequential actions must be absent or false"))
            _scan_value(child, child_path, issues)
        return

    if isinstance(value, str):
        for pattern in LOCAL_PATH_PATTERNS:
            if pattern.search(value):
                issues.append(DriftValidationIssue("local_private_path", path, "packet references a local private path"))
                break
        for pattern in LIVE_BROWSER_PATTERNS:
            if pattern.search(value):
                issues.append(DriftValidationIssue("live_browser_execution_claim", path, "packet claims live browser execution"))
                break
        if _looks_like_raw_secret(value):
            issues.append(DriftValidationIssue("raw_authenticated_value", path, "packet includes a value that looks like a raw secret"))
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _scan_value(child, f"{path}[{index}]", issues)


def _validate_drift_claims(packet: Mapping[str, Any], issues: list[DriftValidationIssue]) -> None:
    claims = packet.get("drift_claims", packet.get("claims", []))
    if not isinstance(claims, Sequence) or isinstance(claims, (str, bytes, bytearray)):
        issues.append(DriftValidationIssue("uncited_drift_claim", "$.drift_claims", "drift claims must be a list with public citations"))
        return

    for index, claim in enumerate(claims):
        claim_path = f"$.drift_claims[{index}]"
        if not isinstance(claim, Mapping):
            issues.append(DriftValidationIssue("uncited_drift_claim", claim_path, "drift claim must be an object with public citations"))
            continue
        citations = claim.get("citations", claim.get("source_citations", claim.get("evidence", [])))
        if not _has_public_citation(citations):
            issues.append(DriftValidationIssue("uncited_drift_claim", claim_path, "drift claim lacks at least one public HTTPS citation"))


def _validate_reviewer_owner(packet: Mapping[str, Any], issues: list[DriftValidationIssue]) -> None:
    owner = packet.get("reviewer_owner", packet.get("reviewer", {}).get("owner") if isinstance(packet.get("reviewer"), Mapping) else None)
    if not isinstance(owner, str) or not owner.strip():
        issues.append(DriftValidationIssue("missing_reviewer_owner", "$.reviewer_owner", "packet must name a reviewer owner"))


def _validate_deferrals(packet: Mapping[str, Any], issues: list[DriftValidationIssue]) -> None:
    deferrals = packet.get("deferrals", [])
    if not isinstance(deferrals, Sequence) or isinstance(deferrals, (str, bytes, bytearray)):
        issues.append(DriftValidationIssue("missing_deferral_reason", "$.deferrals", "deferrals must be a list with reasons"))
        return

    for index, deferral in enumerate(deferrals):
        path = f"$.deferrals[{index}]"
        if not isinstance(deferral, Mapping):
            issues.append(DriftValidationIssue("missing_deferral_reason", path, "deferral must include a reason"))
            continue
        reason = deferral.get("reason", deferral.get("deferral_reason"))
        if not isinstance(reason, str) or not reason.strip():
            issues.append(DriftValidationIssue("missing_deferral_reason", path, "deferral lacks a reason"))


def _has_public_citation(citations: Any) -> bool:
    if isinstance(citations, str):
        return bool(PUBLIC_CITATION_RE.match(citations.strip()))
    if isinstance(citations, Mapping):
        url = citations.get("url", citations.get("href"))
        return isinstance(url, str) and bool(PUBLIC_CITATION_RE.match(url.strip()))
    if isinstance(citations, Sequence) and not isinstance(citations, (str, bytes, bytearray)):
        return any(_has_public_citation(citation) for citation in citations)
    return False


def _normalized_key(key: str) -> str:
    return key.replace("-", "_").replace(" ", "_").lower()


def _looks_like_raw_secret(value: str) -> bool:
    lowered = value.lower()
    if "bearer " in lowered or "basic " in lowered:
        return True
    return bool(re.search(r"(?:access|refresh|id|api)[_-]?token\s*[:=]\s*[A-Za-z0-9._~+/=-]{12,}", value, re.IGNORECASE))
