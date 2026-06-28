"""Validation for post-recrawl metadata review packets.

The validator is intentionally metadata-only. Review packets may describe public
source changes, skipped sources, and downstream invalidation needs, but they must
not carry raw page/PDF bodies, authenticated evidence, local downloaded paths, or
claims that promote process/guardrail state directly.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import urlparse

_ALLOWED_SKIP_CODES = {
    "outside_allowlist",
    "unsupported_scheme",
    "private_authenticated",
    "disallowed_by_robots_or_policy",
    "raw_download_not_permitted",
    "too_large",
    "unsupported_content_type",
    "not_modified",
    "network_error",
    "processor_error",
}

_HASH_RE = re.compile(r"^[a-fA-F0-9]{32,128}$")
_HTML_RE = re.compile(
    r"]|]|]|]|]",
    re.IGNORECASE,
)
_PDF_RE = re.compile(r"%PDF-|\bstartxref\b|\bxref\b|/Type\s*/Page\b|\bendobj\b")
_LOCAL_PATH_RE = re.compile(
    r"^(file://|~[/\\]|/[^/]|[A-Za-z]:[\\/]|\.\.?[/\\]).*|.*[/\\](Downloads|Temp|tmp|cache|artifacts|raw|crawl-output)[/\\].*",
    re.IGNORECASE,
)
_PRIVATE_URL_HINT_RE = re.compile(
    r"/(account|accounts|login|signin|sign-in|dashboard|my-permits|cart|checkout|payment|upload|corrections)(/|$)",
    re.IGNORECASE,
)
_PROMOTION_RE = re.compile(
    r"\b(promote|publish|activate|mark\s+valid|mark\s+complete|approve|certify)\b.*\b(guardrail|bundle|process|model|requirement)\b|\b(guardrail|bundle|process|model|requirement)\b.*\b(promote|publish|activate|approved|certified)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ReviewValidationIssue:
    """A single validation failure for a post-recrawl review packet."""

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ReviewValidationReport:
    """Validation result for a post-recrawl review packet."""

    ok: bool
    issues: tuple[ReviewValidationIssue, ...]

    def raise_for_issues(self) -> None:
        if self.issues:
            details = "; ".join(f"{issue.path}: {issue.code}" for issue in self.issues)
            raise ValueError(f"post-recrawl review packet failed validation: {details}")


def validate_post_recrawl_review_packet(packet: Mapping[str, Any]) -> ReviewValidationReport:
    """Validate a metadata-only post-recrawl review packet.

    The accepted shape is deliberately flexible because different recrawl tools
    may emit different metadata envelopes. The validator walks the whole mapping
    for prohibited raw/private artifacts, then applies field-specific checks to
    common sections such as changed_sources, skipped_sources, invalidations, and
    review_decisions.
    """

    issues: list[ReviewValidationIssue] = []
    _walk_for_forbidden_artifacts(packet, "$", issues)
    _validate_changed_sources(packet, issues)
    _validate_skipped_sources(packet, issues)
    _validate_downstream_invalidations(packet, issues)
    _validate_review_decisions(packet, issues)
    return ReviewValidationReport(ok=not issues, issues=tuple(issues))


def assert_valid_post_recrawl_review_packet(packet: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return packet when valid, otherwise raise ValueError."""

    validate_post_recrawl_review_packet(packet).raise_for_issues()
    return packet


def _walk_for_forbidden_artifacts(value: Any, path: str, issues: list[ReviewValidationIssue]) -> None:
    if isinstance(value, Mapping):
        _check_mapping_artifacts(value, path, issues)
        for key, child in value.items():
            _walk_for_forbidden_artifacts(child, f"{path}.{key}", issues)
        return

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _walk_for_forbidden_artifacts(child, f"{path}[{index}]", issues)
        return

    if isinstance(value, str):
        _check_string_artifacts(value, path, issues)


def _check_mapping_artifacts(entry: Mapping[str, Any], path: str, issues: list[ReviewValidationIssue]) -> None:
    lowered = {str(key).lower(): val for key, val in entry.items()}

    evidence_kind = _as_lower(lowered.get("evidence_kind") or lowered.get("kind") or lowered.get("source_type"))
    if evidence_kind in {"raw_html", "html_excerpt", "raw_pdf", "pdf_excerpt", "pdf_text_excerpt"}:
        issues.append(
            ReviewValidationIssue(
                "raw_excerpt_forbidden",
                path,
                "review packets must cite normalized public metadata instead of carrying raw HTML or PDF excerpts",
            )
        )

    content_type = _as_lower(lowered.get("content_type") or lowered.get("mime_type"))
    has_body_like_field = any(
        field in lowered
        for field in (
            "body",
            "html",
            "raw_html",
            "raw_pdf",
            "pdf_bytes",
            "pdf_text",
            "excerpt",
            "raw_excerpt",
            "content",
        )
    )
    if has_body_like_field and ("html" in content_type or "pdf" in content_type):
        issues.append(
            ReviewValidationIssue(
                "raw_excerpt_forbidden",
                path,
                "HTML/PDF content-bearing fields are not allowed in post-recrawl review metadata",
            )
        )

    privacy = _as_lower(lowered.get("privacy_classification") or lowered.get("privacy"))
    source_type = _as_lower(lowered.get("source_type"))
    auth_scope = _as_lower(lowered.get("auth_scope") or lowered.get("authentication"))
    if privacy and privacy not in {"public", "public_metadata"}:
        issues.append(
            ReviewValidationIssue(
                "private_evidence_forbidden",
                path,
                "review packet evidence must be public metadata only",
            )
        )
    if source_type == "devhub_authenticated" or auth_scope in {"authenticated", "private", "account", "user"}:
        issues.append(
            ReviewValidationIssue(
                "authenticated_evidence_forbidden",
                path,
                "authenticated DevHub evidence cannot be committed in post-recrawl review packets",
            )
        )

    for key, val in lowered.items():
        if not isinstance(val, str):
            continue
        if key in {"local_path", "downloaded_path", "file_path", "raw_path", "document_path", "screenshot_path", "trace_path", "har_path"}:
            if _looks_like_local_path(val):
                issues.append(
                    ReviewValidationIssue(
                        "downloaded_path_forbidden",
                        f"{path}.{key}",
                        "downloaded document and local artifact paths must not be stored in review packets",
                    )
                )
        if key in {"url", "canonical_url", "requested_url", "source_url"} and _looks_private_url(val):
            issues.append(
                ReviewValidationIssue(
                    "private_evidence_forbidden",
                    f"{path}.{key}",
                    "private, account-scoped, or authenticated URLs are not valid public recrawl evidence",
                )
            )


def _check_string_artifacts(value: str, path: str, issues: list[ReviewValidationIssue]) -> None:
    stripped = value.strip()
    if not stripped:
        return

    if _HTML_RE.search(stripped) or _PDF_RE.search(stripped):
        issues.append(
            ReviewValidationIssue(
                "raw_excerpt_forbidden",
                path,
                "raw HTML and PDF excerpts are forbidden in metadata review packets",
            )
        )
        return

    if _looks_like_local_path(stripped):
        issues.append(
            ReviewValidationIssue(
                "downloaded_path_forbidden",
                path,
                "local downloaded document paths are forbidden in metadata review packets",
            )
        )


def _validate_changed_sources(packet: Mapping[str, Any], issues: list[ReviewValidationIssue]) -> None:
    for path, entry in _section_entries(packet, ("changed_sources", "hash_changes", "change_reports", "source_changes")):
        if not isinstance(entry, Mapping):
            continue
        claims_changed_hash = any(
            key in entry
            for key in (
                "changed_hash",
                "new_hash",
                "old_hash",
                "previous_hash",
                "content_hash_changed",
                "hash_changed",
            )
        )
        if not claims_changed_hash:
            continue
        has_citation = bool(
            entry.get("source_id")
            or entry.get("canonical_url")
            or entry.get("citation_url")
            or entry.get("manifest_id")
            or entry.get("archive_manifest_id")
        )
        new_hash = entry.get("new_hash") or entry.get("changed_hash") or entry.get("content_hash")
        old_hash = entry.get("old_hash") or entry.get("previous_hash")
        has_hash_value = _is_hash_value(new_hash) or _is_hash_value(old_hash) or isinstance(entry.get("content_hash_changed"), bool)
        if not has_citation or not has_hash_value:
            issues.append(
                ReviewValidationIssue(
                    "uncited_changed_hash_claim",
                    path,
                    "changed-hash claims require a source citation and a concrete hash value or boolean manifest-derived change flag",
                )
            )


def _validate_skipped_sources(packet: Mapping[str, Any], issues: list[ReviewValidationIssue]) -> None:
    for path, entry in _section_entries(packet, ("skipped_sources", "skipped", "skip_reports")):
        if not isinstance(entry, Mapping):
            continue
        reason = entry.get("skipped_reason") or entry.get("skip_reason") or entry.get("reason_code")
        if not isinstance(reason, str) or reason not in _ALLOWED_SKIP_CODES:
            issues.append(
                ReviewValidationIssue(
                    "missing_skipped_reason_code",
                    path,
                    "skipped sources require a stable skipped-reason code",
                )
            )


def _validate_downstream_invalidations(packet: Mapping[str, Any], issues: list[ReviewValidationIssue]) -> None:
    changed_entries = list(_section_entries(packet, ("changed_sources", "hash_changes", "change_reports", "source_changes")))
    if not changed_entries:
        return

    invalidation_entries = list(_section_entries(packet, ("downstream_invalidations", "invalidations", "affected_artifacts")))
    if not invalidation_entries:
        issues.append(
            ReviewValidationIssue(
                "missing_downstream_invalidation_links",
                "$.downstream_invalidations",
                "changed sources must link affected requirement, process, or guardrail artifacts for review invalidation",
            )
        )
        return

    for path, entry in invalidation_entries:
        if not isinstance(entry, Mapping):
            issues.append(
                ReviewValidationIssue(
                    "missing_downstream_invalidation_links",
                    path,
                    "downstream invalidation entries must be objects with source and affected artifact references",
                )
            )
            continue
        source_ref = entry.get("source_id") or entry.get("manifest_id") or entry.get("changed_source_id")
        affected = (
            entry.get("affected_requirement_ids")
            or entry.get("affected_guardrail_bundle_ids")
            or entry.get("affected_process_ids")
            or entry.get("affected_artifact_ids")
        )
        if not source_ref or not _has_non_empty_reference(affected):
            issues.append(
                ReviewValidationIssue(
                    "missing_downstream_invalidation_links",
                    path,
                    "each invalidation must identify the changed source and at least one affected downstream artifact",
                )
            )


def _validate_review_decisions(packet: Mapping[str, Any], issues: list[ReviewValidationIssue]) -> None:
    for path, entry in _section_entries(packet, ("review_decisions", "decisions", "recommendations", "actions")):
        if isinstance(entry, Mapping):
            action = " ".join(
                str(entry.get(key, ""))
                for key in ("action", "decision", "status", "recommendation", "notes")
            )
        else:
            action = str(entry)
        if _PROMOTION_RE.search(action):
            issues.append(
                ReviewValidationIssue(
                    "direct_promotion_forbidden",
                    path,
                    "post-recrawl review may request invalidation or human review but cannot directly promote guardrails, requirements, or process models",
                )
            )


def _section_entries(packet: Mapping[str, Any], names: Iterable[str]) -> Iterable[tuple[str, Any]]:
    for name in names:
        section = packet.get(name)
        if section is None:
            continue
        if isinstance(section, Mapping):
            for key, value in section.items():
                yield f"$.{name}.{key}", value
        elif isinstance(section, Sequence) and not isinstance(section, (str, bytes, bytearray)):
            for index, value in enumerate(section):
                yield f"$.{name}[{index}]", value
        else:
            yield f"$.{name}", section


def _as_lower(value: Any) -> str:
    return str(value).strip().lower() if value is not None else ""


def _is_hash_value(value: Any) -> bool:
    return isinstance(value, str) and bool(_HASH_RE.fullmatch(value.strip()))


def _has_non_empty_reference(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(bool(str(item).strip()) for item in value)
    return value is not None


def _looks_like_local_path(value: str) -> bool:
    return bool(_LOCAL_PATH_RE.match(value.strip()))


def _looks_private_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    if parsed.scheme not in {"http", "https"}:
        return False
    return bool(_PRIVATE_URL_HINT_RE.search(parsed.path))
