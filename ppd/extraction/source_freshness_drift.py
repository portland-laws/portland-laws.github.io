"""Validation for PP&D source freshness drift digests.

The validator is intentionally side-effect free: it only inspects already-normalized
metadata and never fetches, opens, or persists source bodies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


PRIVATE_OR_AUTHENTICATED_SOURCE_TYPES = {
    "devhub_authenticated",
    "authenticated",
    "private",
    "private_devhub",
    "user_account",
}

PRIVATE_OR_AUTHENTICATED_SCHEMES = {
    "file",
    "private",
    "auth",
    "session",
    "credential",
}

RAW_OR_DOWNLOADED_REFERENCE_KEYS = {
    "raw_body",
    "raw_body_ref",
    "raw_body_path",
    "raw_html",
    "raw_html_path",
    "body_path",
    "downloaded_document_ref",
    "downloaded_document_path",
    "download_path",
    "downloaded_pdf_path",
    "local_path",
    "warc_path",
    "har_path",
    "trace_path",
    "screenshot_path",
}

RAW_OR_DOWNLOADED_REFERENCE_TYPES = {
    "raw_body",
    "raw_html",
    "downloaded_document",
    "downloaded_pdf",
    "warc",
    "har",
    "trace",
    "screenshot",
}

LIVE_NETWORK_FLAG_KEYS = {
    "allow_live_network",
    "live_network",
    "live_network_run",
    "network_enabled",
    "ran_live_network",
    "used_live_network",
}

CURRENT_STATUSES = {"current", "fresh", "up_to_date"}
STALE_STATUSES = {"stale", "expired", "outdated", "needs_recrawl"}


@dataclass(frozen=True)
class DriftValidationIssue:
    """A single source freshness drift digest validation issue."""

    code: str
    message: str
    path: str


@dataclass(frozen=True)
class DriftValidationResult:
    """Validation result for a source freshness drift digest."""

    valid: bool
    issues: Sequence[DriftValidationIssue]

    def messages(self) -> List[str]:
        return [issue.message for issue in self.issues]


def validate_source_freshness_drift_digest(digest: Mapping[str, Any]) -> DriftValidationResult:
    """Validate a source freshness drift digest for commit-safe use.

    Required policy checks:
    - changed-source claims must have citation/evidence links;
    - changed-source claims must identify affected requirements and guardrails;
    - source references must not point at private/authenticated material;
    - source references must not point at raw bodies or downloaded documents;
    - digest provenance must not indicate live network execution;
    - stale sources cannot be marked current without reviewer acknowledgement.
    """

    issues: List[DriftValidationIssue] = []

    if not isinstance(digest, Mapping):
        return DriftValidationResult(
            valid=False,
            issues=(
                DriftValidationIssue(
                    code="digest_not_mapping",
                    message="source freshness drift digest must be a mapping",
                    path="$",
                ),
            ),
        )

    _validate_no_live_network_flags(digest, "$", issues)

    source_refs = _as_sequence(digest.get("source_references") or digest.get("sources"))
    for index, source_ref in enumerate(source_refs):
        if isinstance(source_ref, Mapping):
            _validate_source_reference(source_ref, "$.source_references[%d]" % index, issues)

    claims = _as_sequence(digest.get("changed_source_claims") or digest.get("claims") or digest.get("changes"))
    for index, claim in enumerate(claims):
        if not isinstance(claim, Mapping):
            issues.append(
                DriftValidationIssue(
                    code="claim_not_mapping",
                    message="changed-source claim must be a mapping",
                    path="$.changed_source_claims[%d]" % index,
                )
            )
            continue
        _validate_changed_source_claim(claim, "$.changed_source_claims[%d]" % index, issues)

    freshness_entries = _as_sequence(
        digest.get("freshness_entries")
        or digest.get("source_freshness")
        or digest.get("freshness")
    )
    for index, entry in enumerate(freshness_entries):
        if isinstance(entry, Mapping):
            _validate_freshness_entry(entry, "$.freshness_entries[%d]" % index, issues)

    return DriftValidationResult(valid=not issues, issues=tuple(issues))


def assert_valid_source_freshness_drift_digest(digest: Mapping[str, Any]) -> None:
    """Raise ValueError when a source freshness drift digest violates policy."""

    result = validate_source_freshness_drift_digest(digest)
    if not result.valid:
        joined = "; ".join("%s at %s" % (issue.code, issue.path) for issue in result.issues)
        raise ValueError("invalid source freshness drift digest: " + joined)


def _validate_changed_source_claim(
    claim: Mapping[str, Any],
    path: str,
    issues: List[DriftValidationIssue],
) -> None:
    if _truthy(claim.get("changed"), default=True):
        citations = _as_sequence(
            claim.get("citation_ids")
            or claim.get("citations")
            or claim.get("source_evidence_ids")
            or claim.get("evidence_ids")
        )
        if not _has_non_empty_string(citations):
            issues.append(
                DriftValidationIssue(
                    code="uncited_changed_source_claim",
                    message="changed-source claim must include at least one citation or source evidence id",
                    path=path,
                )
            )

        affected_requirements = _as_sequence(
            claim.get("affected_requirement_ids")
            or claim.get("affected_requirements")
            or claim.get("requirement_ids")
        )
        if not _has_non_empty_string(affected_requirements):
            issues.append(
                DriftValidationIssue(
                    code="missing_affected_requirement_link",
                    message="changed-source claim must link to at least one affected requirement",
                    path=path,
                )
            )

        affected_guardrails = _as_sequence(
            claim.get("affected_guardrail_bundle_ids")
            or claim.get("affected_guardrails")
            or claim.get("guardrail_bundle_ids")
        )
        if not _has_non_empty_string(affected_guardrails):
            issues.append(
                DriftValidationIssue(
                    code="missing_affected_guardrail_link",
                    message="changed-source claim must link to at least one affected guardrail bundle",
                    path=path,
                )
            )

    for key in ("source_reference", "source", "reference"):
        nested_ref = claim.get(key)
        if isinstance(nested_ref, Mapping):
            _validate_source_reference(nested_ref, path + "." + key, issues)

    for index, source_ref in enumerate(_as_sequence(claim.get("source_references") or claim.get("sources"))):
        if isinstance(source_ref, Mapping):
            _validate_source_reference(source_ref, "%s.source_references[%d]" % (path, index), issues)

    _validate_no_live_network_flags(claim, path, issues)


def _validate_source_reference(
    source_ref: Mapping[str, Any],
    path: str,
    issues: List[DriftValidationIssue],
) -> None:
    source_type = _lower_text(source_ref.get("source_type") or source_ref.get("type"))
    if source_type in PRIVATE_OR_AUTHENTICATED_SOURCE_TYPES:
        issues.append(
            DriftValidationIssue(
                code="private_or_authenticated_source_reference",
                message="source reference must not point at private or authenticated material",
                path=path,
            )
        )

    reference_type = _lower_text(source_ref.get("reference_type") or source_ref.get("artifact_type"))
    if reference_type in RAW_OR_DOWNLOADED_REFERENCE_TYPES:
        issues.append(
            DriftValidationIssue(
                code="raw_or_downloaded_document_reference",
                message="source reference must not point at raw bodies or downloaded documents",
                path=path,
            )
        )

    for url_key in ("url", "canonical_url", "requested_url", "artifact_ref", "document_ref"):
        value = source_ref.get(url_key)
        if isinstance(value, str):
            scheme = value.split(":", 1)[0].lower() if ":" in value else ""
            if scheme in PRIVATE_OR_AUTHENTICATED_SCHEMES:
                issues.append(
                    DriftValidationIssue(
                        code="private_or_authenticated_source_reference",
                        message="source reference uses a private, authenticated, or local scheme",
                        path=path + "." + url_key,
                    )
                )

    for key in RAW_OR_DOWNLOADED_REFERENCE_KEYS:
        if _present(source_ref.get(key)):
            issues.append(
                DriftValidationIssue(
                    code="raw_or_downloaded_document_reference",
                    message="source reference must not include raw body or downloaded-document pointers",
                    path=path + "." + key,
                )
            )

    _validate_no_live_network_flags(source_ref, path, issues)


def _validate_freshness_entry(
    entry: Mapping[str, Any],
    path: str,
    issues: List[DriftValidationIssue],
) -> None:
    freshness_status = _lower_text(entry.get("freshness_status") or entry.get("status"))
    observed_status = _lower_text(
        entry.get("observed_freshness_status")
        or entry.get("detected_status")
        or entry.get("prior_freshness_status")
    )
    stale_signal = _truthy(entry.get("stale"), default=False) or observed_status in STALE_STATUSES
    marked_current = freshness_status in CURRENT_STATUSES
    reviewer_acknowledged = _truthy(
        entry.get("reviewer_acknowledged")
        or entry.get("reviewer_acknowledgement")
        or entry.get("human_review_acknowledged"),
        default=False,
    )

    if stale_signal and marked_current and not reviewer_acknowledged:
        issues.append(
            DriftValidationIssue(
                code="stale_source_marked_current_without_reviewer_acknowledgement",
                message="stale source cannot be marked current without reviewer acknowledgement",
                path=path,
            )
        )

    _validate_no_live_network_flags(entry, path, issues)


def _validate_no_live_network_flags(
    value: Mapping[str, Any],
    path: str,
    issues: List[DriftValidationIssue],
) -> None:
    for key in LIVE_NETWORK_FLAG_KEYS:
        if _truthy(value.get(key), default=False):
            issues.append(
                DriftValidationIssue(
                    code="live_network_run_flag",
                    message="source freshness drift digest must not record live network run flags",
                    path=path + "." + key,
                )
            )

    provenance = value.get("provenance")
    if isinstance(provenance, Mapping):
        _validate_no_live_network_flags(provenance, path + ".provenance", issues)


def _as_sequence(value: Any) -> Sequence[Any]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return value
    return (value,)


def _has_non_empty_string(values: Iterable[Any]) -> bool:
    return any(isinstance(value, str) and bool(value.strip()) for value in values)


def _lower_text(value: Any) -> str:
    return value.strip().lower() if isinstance(value, str) else ""


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, dict, set)):
        return bool(value)
    return True


def _truthy(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)
