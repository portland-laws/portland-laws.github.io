"""Validation for PP&D public source recrawl preflight queue v7.

The queue is intentionally metadata-only. It records the deterministic inputs needed
before a public recrawl can be handed to a processor, while rejecting live crawl
claims, private artifacts, official-action language, guarantees, and mutable flags.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


REQUIRED_REFERENCE_FIELDS: tuple[str, ...] = (
    "authorization_packet_ref",
    "allowlist_fixture_ref",
    "robots_policy_fixture_ref",
    "canonical_url_queue_row_ref",
    "redirect_expectation_ref",
    "skip_reason_row_ref",
    "host_policy_decision_ref",
    "rate_limit_reminder_ref",
    "processor_handoff_eligibility_note",
)

REQUIRED_QUEUE_FIELDS: tuple[str, ...] = (
    "queue_id",
    "source_id",
    "requested_url",
    "canonical_url",
    "validation_commands",
)

ARTIFACT_REFERENCE_FIELDS: tuple[str, ...] = (
    "downloaded_artifact_ref",
    "downloaded_artifact_refs",
    "raw_crawl_artifact_ref",
    "raw_crawl_artifact_refs",
    "raw_body_ref",
    "raw_html_ref",
    "raw_pdf_ref",
    "private_session_ref",
    "private_session_refs",
    "session_state_ref",
    "auth_artifact_ref",
    "auth_artifact_refs",
    "credential_ref",
    "cookie_ref",
    "cookies_ref",
    "har_ref",
    "trace_ref",
    "screenshot_ref",
)

MUTATION_FLAG_FIELDS: tuple[str, ...] = (
    "active_mutation",
    "active_mutation_enabled",
    "mutation_enabled",
    "write_enabled",
    "remote_write_enabled",
    "mutates_remote",
    "submit_enabled",
    "upload_enabled",
    "payment_enabled",
    "schedule_enabled",
    "cancellation_enabled",
)

LIVE_CRAWL_PHRASES: tuple[str, ...] = (
    "live crawl executed",
    "live crawl completed",
    "crawl executed",
    "crawl completed",
    "recrawl executed",
    "recrawl completed",
    "downloaded page",
    "downloaded pdf",
    "fetched live",
    "captured live",
    "raw crawl output",
)

OFFICIAL_ACTION_PHRASES: tuple[str, ...] = (
    "official action completed",
    "permit submitted",
    "application submitted",
    "inspection scheduled",
    "fee paid",
    "payment submitted",
    "correction uploaded",
    "certification completed",
    "acknowledgement certified",
    "permit cancelled",
    "permit withdrawn",
)

GUARANTEE_PHRASES: tuple[str, ...] = (
    "guaranteed approval",
    "approval guaranteed",
    "permit guaranteed",
    "legally sufficient",
    "legal advice",
    "will be approved",
    "will pass review",
    "no permitting risk",
)

SAFE_EXECUTION_STATUSES: tuple[str, ...] = (
    "preflight_only",
    "planned",
    "not_executed",
    "dry_run_metadata_only",
)

TEXT_FIELDS_TO_SCAN: tuple[str, ...] = (
    "status",
    "execution_status",
    "claim",
    "claims",
    "notes",
    "summary",
    "description",
    "operator_note",
    "processor_handoff_eligibility_note",
)


@dataclass(frozen=True)
class PreflightValidationIssue:
    """A single validation failure for a queue row."""

    row_index: int
    code: str
    message: str
    field: str | None = None


@dataclass(frozen=True)
class PreflightValidationResult:
    """Validation result for public recrawl preflight queue v7."""

    ok: bool
    issues: tuple[PreflightValidationIssue, ...]

    def raise_for_issues(self) -> None:
        if self.issues:
            formatted = "; ".join(
                f"row {issue.row_index}: {issue.code}: {issue.message}"
                for issue in self.issues
            )
            raise ValueError(formatted)


def validate_public_recrawl_preflight_queue_v7(
    rows: Sequence[Mapping[str, Any]],
) -> PreflightValidationResult:
    """Validate queue rows before any public recrawl processor handoff.

    The validator accepts only metadata rows that have all policy references and
    validation commands present. It rejects rows that contain live crawl claims,
    downloaded/raw/private/auth artifacts, official-action completion claims,
    legal or permitting guarantees, or active mutation flags.
    """

    issues: list[PreflightValidationIssue] = []

    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        issue = PreflightValidationIssue(
            row_index=-1,
            code="queue_not_sequence",
            message="queue must be a sequence of mapping rows",
        )
        return PreflightValidationResult(ok=False, issues=(issue,))

    for row_index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            issues.append(
                PreflightValidationIssue(
                    row_index=row_index,
                    code="row_not_mapping",
                    message="queue row must be a mapping",
                )
            )
            continue

        for field in REQUIRED_QUEUE_FIELDS:
            if _is_blank(row.get(field)):
                issues.append(
                    PreflightValidationIssue(
                        row_index=row_index,
                        code="missing_required_field",
                        message=f"missing required queue field: {field}",
                        field=field,
                    )
                )

        for field in REQUIRED_REFERENCE_FIELDS:
            if _is_blank(row.get(field)):
                issues.append(
                    PreflightValidationIssue(
                        row_index=row_index,
                        code="missing_preflight_reference",
                        message=f"missing required preflight reference: {field}",
                        field=field,
                    )
                )

        validation_commands = row.get("validation_commands")
        if not _has_validation_command(validation_commands):
            issues.append(
                PreflightValidationIssue(
                    row_index=row_index,
                    code="missing_validation_commands",
                    message="validation_commands must include at least one command token list or non-empty command string",
                    field="validation_commands",
                )
            )

        execution_status = row.get("execution_status")
        if isinstance(execution_status, str):
            normalized_status = execution_status.strip().lower()
            if normalized_status and normalized_status not in SAFE_EXECUTION_STATUSES:
                issues.append(
                    PreflightValidationIssue(
                        row_index=row_index,
                        code="live_crawl_execution_claim",
                        message="execution_status must remain a preflight-only status",
                        field="execution_status",
                    )
                )

        for field in ARTIFACT_REFERENCE_FIELDS:
            if not _is_blank(row.get(field)):
                issues.append(
                    PreflightValidationIssue(
                        row_index=row_index,
                        code="forbidden_artifact_reference",
                        message=f"forbidden downloaded, raw, private, session, or auth artifact reference: {field}",
                        field=field,
                    )
                )

        for field in MUTATION_FLAG_FIELDS:
            if row.get(field) is True:
                issues.append(
                    PreflightValidationIssue(
                        row_index=row_index,
                        code="active_mutation_flag",
                        message=f"active mutation flag must be absent or false: {field}",
                        field=field,
                    )
                )

        scanned_text = "\n".join(_iter_text_values(row, TEXT_FIELDS_TO_SCAN)).lower()
        for phrase in LIVE_CRAWL_PHRASES:
            if phrase in scanned_text:
                issues.append(
                    PreflightValidationIssue(
                        row_index=row_index,
                        code="live_crawl_execution_claim",
                        message=f"preflight row contains live crawl execution claim: {phrase}",
                    )
                )

        for phrase in OFFICIAL_ACTION_PHRASES:
            if phrase in scanned_text:
                issues.append(
                    PreflightValidationIssue(
                        row_index=row_index,
                        code="official_action_completion_claim",
                        message=f"preflight row contains official-action completion claim: {phrase}",
                    )
                )

        for phrase in GUARANTEE_PHRASES:
            if phrase in scanned_text:
                issues.append(
                    PreflightValidationIssue(
                        row_index=row_index,
                        code="legal_or_permitting_guarantee",
                        message=f"preflight row contains legal or permitting guarantee: {phrase}",
                    )
                )

    return PreflightValidationResult(ok=not issues, issues=tuple(issues))


def assert_valid_public_recrawl_preflight_queue_v7(
    rows: Sequence[Mapping[str, Any]],
) -> None:
    """Raise ValueError when queue rows fail v7 preflight validation."""

    validate_public_recrawl_preflight_queue_v7(rows).raise_for_issues()


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, frozenset, dict)):
        return len(value) == 0
    return False


def _has_validation_command(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return False
    if not value:
        return False
    for command in value:
        if isinstance(command, str) and command.strip():
            return True
        if isinstance(command, Sequence) and not isinstance(command, (str, bytes, bytearray)):
            if any(isinstance(token, str) and token.strip() for token in command):
                return True
    return False


def _iter_text_values(row: Mapping[str, Any], fields: Iterable[str]) -> Iterable[str]:
    for field in fields:
        value = row.get(field)
        yield from _flatten_text(value)


def _flatten_text(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for nested_value in value.values():
            yield from _flatten_text(nested_value)
    elif isinstance(value, Iterable) and not isinstance(value, (bytes, bytearray)):
        for nested_value in value:
            yield from _flatten_text(nested_value)
