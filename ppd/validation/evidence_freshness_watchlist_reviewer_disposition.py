"""Validation for evidence freshness watchlist reviewer disposition packets.

The validator is intentionally conservative: reviewer disposition packets are
supposed to document an offline review decision, not execute crawls, mutate
registries, or preserve private/raw artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse


ALLOWLISTED_URL_HOSTS = frozenset(
    {
        "www.portland.gov",
        "portland.gov",
        "efiles.portlandoregon.gov",
        "www.oregon.gov",
        "oregon.gov",
    }
)

AUTHENTICATED_URL_MARKERS = (
    "login",
    "logout",
    "oauth",
    "saml",
    "session",
    "signin",
    "sign-in",
    "account",
    "auth",
    "token",
)

PRIVATE_ARTIFACT_MARKERS = (
    "cookie",
    "cookies",
    "bearer ",
    "authorization",
    "access_token",
    "refresh_token",
    "sessionid",
    "storage_state",
    "localstorage",
    "indexeddb",
    ".har",
    "trace.zip",
    "devhub_session",
    "/tmp/",
    "/var/folders/",
)

RAW_OR_ARCHIVE_MARKERS = (
    "raw_body",
    "body_html",
    "response_body",
    "downloaded_file",
    "download_path",
    "archive_path",
    "warc",
    ".zip",
    ".tar",
    ".gz",
    "/download",
    "/archive",
)

EXECUTION_CLAIM_MARKERS = (
    "live crawl",
    "live-crawl",
    "ran crawl",
    "ran scraper",
    "executed scraper",
    "executed processor",
    "ran processor",
    "processor execution",
    "playwright run",
    "selenium run",
    "browser automation",
)

OUTCOME_GUARANTEE_MARKERS = (
    "guarantee permit",
    "guarantees permit",
    "permit will be approved",
    "approval guaranteed",
    "legal determination",
    "legally sufficient",
    "compliance guaranteed",
    "entitled to approval",
)

MUTATION_FLAG_NAMES = frozenset(
    {
        "active_registry_mutation",
        "active_requirement_mutation",
        "active_guardrail_mutation",
        "active_schedule_mutation",
        "active_release_state_mutation",
        "registry_mutation",
        "requirement_mutation",
        "guardrail_mutation",
        "schedule_mutation",
        "release_state_mutation",
        "mutates_registry",
        "mutates_requirements",
        "mutates_guardrails",
        "mutates_schedule",
        "mutates_release_state",
    }
)


@dataclass(frozen=True)
class DispositionPacketFinding:
    code: str
    path: str
    message: str


def validate_disposition_packet(packet: dict[str, Any]) -> list[DispositionPacketFinding]:
    """Return validation findings for an evidence freshness reviewer packet."""

    findings: list[DispositionPacketFinding] = []

    if not _has_nonempty_list(packet, ("consumed_packet_refs", "consumed_packet_references")):
        findings.append(
            DispositionPacketFinding(
                "missing_consumed_packet_refs",
                "$",
                "reviewer disposition packets must name consumed packet references",
            )
        )

    if not _has_nonempty_list(packet, ("offline_validation_commands", "validation_commands")):
        findings.append(
            DispositionPacketFinding(
                "missing_offline_validation_commands",
                "$",
                "reviewer disposition packets must include offline validation commands",
            )
        )

    if not _has_reviewer_owner(packet):
        findings.append(
            DispositionPacketFinding(
                "missing_reviewer_owner",
                "$",
                "reviewer disposition packets must identify a reviewer owner",
            )
        )

    decisions = packet.get("decisions")
    if not isinstance(decisions, list) or not decisions:
        findings.append(
            DispositionPacketFinding(
                "missing_decisions",
                "$.decisions",
                "reviewer disposition packets must include at least one decision",
            )
        )
    else:
        for index, decision in enumerate(decisions):
            if not isinstance(decision, dict) or not _decision_has_citation(decision):
                findings.append(
                    DispositionPacketFinding(
                        "uncited_decision",
                        f"$.decisions[{index}]",
                        "each reviewer decision must cite evidence or consumed packet references",
                    )
                )

    for path, value in _walk(packet):
        lowered_path = path.lower()
        lowered_value = str(value).lower() if isinstance(value, str) else ""

        if isinstance(value, str) and _looks_like_url(value):
            findings.extend(_validate_url(path, value))

        if _contains_any(lowered_path, RAW_OR_ARCHIVE_MARKERS) or _contains_any(lowered_value, RAW_OR_ARCHIVE_MARKERS):
            findings.append(
                DispositionPacketFinding(
                    "raw_body_download_or_archive_reference",
                    path,
                    "reviewer packets must not reference raw bodies, downloads, or archives",
                )
            )

        if _contains_any(lowered_path, PRIVATE_ARTIFACT_MARKERS) or _contains_any(lowered_value, PRIVATE_ARTIFACT_MARKERS):
            findings.append(
                DispositionPacketFinding(
                    "private_or_session_artifact",
                    path,
                    "reviewer packets must not contain private session artifacts",
                )
            )

        if _contains_any(lowered_value, EXECUTION_CLAIM_MARKERS):
            findings.append(
                DispositionPacketFinding(
                    "live_crawl_or_processor_execution_claim",
                    path,
                    "reviewer packets must not claim live crawl or processor execution",
                )
            )

        if _contains_any(lowered_value, OUTCOME_GUARANTEE_MARKERS):
            findings.append(
                DispositionPacketFinding(
                    "legal_or_permitting_outcome_guarantee",
                    path,
                    "reviewer packets must not guarantee legal or permitting outcomes",
                )
            )

        if path.rsplit(".", 1)[-1] in MUTATION_FLAG_NAMES and bool(value):
            findings.append(
                DispositionPacketFinding(
                    "active_mutation_flag",
                    path,
                    "reviewer packets must not set active mutation flags",
                )
            )

    return findings


def assert_valid_disposition_packet(packet: dict[str, Any]) -> None:
    findings = validate_disposition_packet(packet)
    if findings:
        details = "; ".join(f"{finding.code} at {finding.path}" for finding in findings)
        raise ValueError(f"invalid evidence freshness reviewer disposition packet: {details}")


def _has_nonempty_list(packet: dict[str, Any], names: tuple[str, ...]) -> bool:
    return any(isinstance(packet.get(name), list) and bool(packet.get(name)) for name in names)


def _has_reviewer_owner(packet: dict[str, Any]) -> bool:
    if isinstance(packet.get("reviewer_owner"), str) and packet["reviewer_owner"].strip():
        return True
    reviewer = packet.get("reviewer")
    return isinstance(reviewer, dict) and isinstance(reviewer.get("owner"), str) and bool(reviewer["owner"].strip())


def _decision_has_citation(decision: dict[str, Any]) -> bool:
    citation_fields = ("citations", "evidence_refs", "consumed_packet_refs", "source_refs")
    return any(isinstance(decision.get(field), list) and bool(decision.get(field)) for field in citation_fields)


def _walk(value: Any, path: str = "$") -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = [(path, value)]
    if isinstance(value, dict):
        for key, child in value.items():
            items.extend(_walk(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            items.extend(_walk(child, f"{path}[{index}]"))
    return items


def _looks_like_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _validate_url(path: str, value: str) -> list[DispositionPacketFinding]:
    parsed = urlparse(value)
    host = parsed.netloc.lower().split(":", 1)[0]
    url_text = value.lower()
    findings: list[DispositionPacketFinding] = []

    if host not in ALLOWLISTED_URL_HOSTS:
        findings.append(
            DispositionPacketFinding(
                "non_allowlisted_url",
                path,
                "reviewer packets may only cite allowlisted public URLs",
            )
        )

    if _contains_any(url_text, AUTHENTICATED_URL_MARKERS) or parsed.query:
        findings.append(
            DispositionPacketFinding(
                "authenticated_or_session_url",
                path,
                "reviewer packets must not cite authenticated or session-bearing URLs",
            )
        )

    return findings


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    return any(marker in value for marker in markers)
