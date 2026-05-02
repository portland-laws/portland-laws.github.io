"""Preflight boundary for PP&D archive processor handoff.

The PP&D archive adapter must fail closed before invoking the archival
processor backend. This module accepts manifest-like adapter records, checks
public-source and no-private-artifact policy, and only then calls the injected
processor backend.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from urllib.parse import urlparse

from ppd.contracts.archive_adapter import (
    ArchivePolicyDecision,
    PpdArchiveAdapterRecord,
    archive_adapter_record_from_dict,
)
from ppd.contracts.crawl_manifest_privacy import validate_crawl_manifest_privacy


ALLOWED_ARCHIVE_HOSTS = frozenset(
    {
        "www.portland.gov",
        "devhub.portlandoregon.gov",
        "www.portlandoregon.gov",
        "www.portlandmaps.com",
    }
)

PRIVATE_DEVHUB_PATH_PREFIXES = (
    "/account",
    "/accounts",
    "/application",
    "/applications",
    "/cart",
    "/dashboard",
    "/document",
    "/documents",
    "/inspection",
    "/inspections",
    "/my",
    "/payment",
    "/payments",
    "/permit",
    "/permits",
    "/secure",
    "/session",
    "/sessions",
    "/upload",
    "/uploads",
)


class ArchiveProcessorBackend(Protocol):
    """Injected archival backend interface used by fixture tests."""

    def archive(self, record: PpdArchiveAdapterRecord) -> Mapping[str, Any]:
        """Archive a validated public PP&D record."""


@dataclass(frozen=True)
class ArchiveProcessorInvocationResult:
    record_id: str
    status: str
    invoked_processor: bool
    errors: tuple[str, ...]
    processor_response: Mapping[str, Any] | None = None


def invoke_archive_processor_from_dict(
    record_data: Mapping[str, Any],
    backend: ArchiveProcessorBackend,
) -> ArchiveProcessorInvocationResult:
    """Validate a record-like payload and invoke the backend only when allowed."""

    record_id = str(record_data.get("id", ""))
    preflight_errors = validate_archive_adapter_preflight_payload(record_data)
    if preflight_errors:
        return ArchiveProcessorInvocationResult(
            record_id=record_id,
            status="refused",
            invoked_processor=False,
            errors=tuple(preflight_errors),
        )

    try:
        record = archive_adapter_record_from_dict(record_data)
    except ValueError as exc:
        return ArchiveProcessorInvocationResult(
            record_id=record_id,
            status="refused",
            invoked_processor=False,
            errors=(f"archive adapter record could not be parsed: {exc}",),
        )

    validation_errors = record.validate()
    if validation_errors:
        return ArchiveProcessorInvocationResult(
            record_id=record.id,
            status="refused",
            invoked_processor=False,
            errors=tuple(validation_errors),
        )

    if record.policy_decision.decision != ArchivePolicyDecision.ALLOW:
        reasons = ", ".join(reason.value for reason in record.policy_decision.reasons)
        return ArchiveProcessorInvocationResult(
            record_id=record.id,
            status="refused",
            invoked_processor=False,
            errors=(f"policy decision refuses processor archival invocation: {reasons}",),
        )

    response = backend.archive(record)
    return ArchiveProcessorInvocationResult(
        record_id=record.id,
        status="invoked",
        invoked_processor=True,
        errors=(),
        processor_response=response,
    )


def validate_archive_adapter_preflight_payload(record_data: Mapping[str, Any]) -> list[str]:
    """Return pre-parser policy errors for an archive adapter payload."""

    errors: list[str] = []

    for finding in validate_crawl_manifest_privacy(record_data):
        errors.append(f"{finding.path}: {finding.reason}")

    for field in ("sourceUrl", "source_url", "canonicalUrl", "canonical_url"):
        value = record_data.get(field)
        if isinstance(value, str) and value.strip():
            errors.extend(_validate_public_archive_url(value, field))

    return errors


def _validate_public_archive_url(value: str, field: str) -> list[str]:
    errors: list[str] = []
    parsed = urlparse(value)
    host = parsed.hostname or ""
    if host not in ALLOWED_ARCHIVE_HOSTS:
        errors.append(f"{field} host is not PP&D archive allowlisted: {host or ''}")
    if host == "devhub.portlandoregon.gov" and _is_private_devhub_path(parsed.path):
        errors.append(f"{field} is a private DevHub path and cannot be archived: {parsed.path}")
    return errors


def _is_private_devhub_path(path: str) -> bool:
    normalized = "/" + path.strip("/").lower()
    return any(
        normalized == prefix or normalized.startswith(f"{prefix}/")
        for prefix in PRIVATE_DEVHUB_PATH_PREFIXES
    )
