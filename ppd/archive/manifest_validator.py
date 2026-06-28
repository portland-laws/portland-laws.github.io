"""Validation for commit-safe PP&D archive manifests.

The validator is intentionally small and deterministic. It checks the policy
properties that must hold before a public crawl manifest is accepted into the
PP&D workspace, without performing any network access or authenticated browser
work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlparse


@dataclass(frozen=True)
class ManifestValidationIssue:
    """A single archive manifest policy violation."""

    code: str
    message: str
    field: str | None = None


class ManifestValidationError(ValueError):
    """Raised when an archive manifest violates PP&D archival policy."""

    def __init__(self, issues: list[ManifestValidationIssue]) -> None:
        self.issues = issues
        details = "; ".join(issue.code for issue in issues)
        super().__init__(f"Archive manifest failed validation: {details}")


_RAW_BODY_FIELDS = frozenset(
    {
        "body",
        "body_bytes",
        "body_text",
        "content",
        "content_bytes",
        "content_text",
        "html",
        "raw_body",
        "raw_body_bytes",
        "raw_body_path",
        "raw_content",
        "response_body",
        "text",
    }
)

_PRIVATE_DEVHUB_PATH_MARKERS = (
    "/account",
    "/admin",
    "/application",
    "/applications",
    "/dashboard",
    "/fees",
    "/inspection",
    "/inspections",
    "/login",
    "/my",
    "/payment",
    "/payments",
    "/permit",
    "/permits",
    "/portal/account",
    "/request",
    "/requests",
    "/secure",
    "/signin",
    "/sign-in",
    "/user",
)

_PRIVATE_QUERY_KEYS = frozenset(
    {
        "access_token",
        "accountid",
        "auth",
        "authorization",
        "caseid",
        "code",
        "contactid",
        "id_token",
        "permitid",
        "requestid",
        "session",
        "sessionid",
        "sid",
        "state",
        "ticket",
        "token",
    }
)


def validate_archive_manifest(manifest: Mapping[str, Any]) -> list[ManifestValidationIssue]:
    """Return PP&D archive manifest validation issues.

    The function does not mutate ``manifest``. Callers that want fail-fast
    behavior can raise ``ManifestValidationError`` when the returned list is not
    empty.
    """

    issues: list[ManifestValidationIssue] = []

    _check_source_id(manifest, issues)
    _check_processor_metadata(manifest, issues)
    _check_raw_body_policy(manifest, issues)
    _check_devhub_url_policy(manifest, issues)
    _check_skipped_capture_hash_policy(manifest, issues)

    return issues


def require_valid_archive_manifest(manifest: Mapping[str, Any]) -> None:
    """Raise ``ManifestValidationError`` if ``manifest`` is not policy-safe."""

    issues = validate_archive_manifest(manifest)
    if issues:
        raise ManifestValidationError(issues)


def _check_source_id(manifest: Mapping[str, Any], issues: list[ManifestValidationIssue]) -> None:
    if not _present_text(manifest.get("source_id")):
        issues.append(
            ManifestValidationIssue(
                code="missing_source_id",
                field="source_id",
                message="Archive manifests must identify the SourceRegistry entry they came from.",
            )
        )


def _check_processor_metadata(manifest: Mapping[str, Any], issues: list[ManifestValidationIssue]) -> None:
    for field in ("processor_name", "processor_version"):
        if not _present_text(manifest.get(field)):
            issues.append(
                ManifestValidationIssue(
                    code="missing_processor_metadata",
                    field=field,
                    message="Archive manifests must record processor name and version metadata.",
                )
            )


def _check_raw_body_policy(manifest: Mapping[str, Any], issues: list[ManifestValidationIssue]) -> None:
    if manifest.get("no_raw_body_persisted") is not True:
        issues.append(
            ManifestValidationIssue(
                code="raw_body_persistence_not_denied",
                field="no_raw_body_persisted",
                message="Archive manifests must explicitly state that no raw response body was persisted.",
            )
        )

    for field in sorted(_RAW_BODY_FIELDS.intersection(manifest.keys())):
        if manifest.get(field) not in (None, "", [], {}):
            issues.append(
                ManifestValidationIssue(
                    code="raw_body_persisted",
                    field=field,
                    message="Archive manifests must not contain raw response bodies or raw-body file references.",
                )
            )


def _check_devhub_url_policy(manifest: Mapping[str, Any], issues: list[ManifestValidationIssue]) -> None:
    for field in ("canonical_url", "requested_url"):
        value = manifest.get(field)
        if isinstance(value, str) and _is_private_devhub_url(value):
            issues.append(
                ManifestValidationIssue(
                    code="private_devhub_url",
                    field=field,
                    message="Archive manifests must not persist private or authenticated DevHub URLs.",
                )
            )

    redirect_chain = manifest.get("redirect_chain")
    if isinstance(redirect_chain, list):
        for index, value in enumerate(redirect_chain):
            url = value.get("url") if isinstance(value, Mapping) else value
            if isinstance(url, str) and _is_private_devhub_url(url):
                issues.append(
                    ManifestValidationIssue(
                        code="private_devhub_url",
                        field=f"redirect_chain[{index}]",
                        message="Archive manifests must not persist private or authenticated DevHub redirect URLs.",
                    )
                )


def _check_skipped_capture_hash_policy(
    manifest: Mapping[str, Any], issues: list[ManifestValidationIssue]
) -> None:
    skipped_reason = manifest.get("skipped_reason")
    if not _present_text(skipped_reason):
        return

    if _present_text(manifest.get("content_hash")):
        issues.append(
            ManifestValidationIssue(
                code="invented_hash_for_skipped_capture",
                field="content_hash",
                message="Skipped captures must not include a content hash because no content was captured.",
            )
        )


def _is_private_devhub_url(value: str) -> bool:
    parsed = urlparse(value)
    host = parsed.hostname or ""
    if host.lower() != "devhub.portlandoregon.gov":
        return False

    if parsed.username or parsed.password:
        return True

    path = parsed.path.lower().rstrip("/")
    if any(path == marker or path.startswith(f"{marker}/") for marker in _PRIVATE_DEVHUB_PATH_MARKERS):
        return True

    query_keys = {key.lower() for key, _value in parse_qsl(parsed.query, keep_blank_values=True)}
    return bool(query_keys.intersection(_PRIVATE_QUERY_KEYS))


def _present_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
