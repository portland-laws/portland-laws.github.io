"""Validation for requirement re-extraction batch plan v6 artifacts.

The batch plan is fixture-first and offline-only. It may group stale public
citation remediation work for later reviewer attention, but it must not claim
live crawl execution, persist downloaded/raw artifacts, store private session
material, activate guardrails, or imply official PP&D actions or legal outcomes.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


class RequirementReextractionBatchPlanError(ValueError):
    """Raised when a requirement re-extraction batch plan is not acceptable."""


@dataclass(frozen=True)
class BatchPlanViolation:
    """A deterministic validation failure."""

    code: str
    path: str
    message: str


_REQUIRED_GUARDRAILS = {
    "live_site_access",
    "authenticated_devhub_access",
    "private_document_access",
    "raw_body_storage",
    "transactional_actions",
    "legal_or_permitting_guarantees",
}

_PRIVATE_KEY_TOKENS = (
    "auth",
    "bearer",
    "cookie",
    "credential",
    "har",
    "mfa",
    "password",
    "private_upload",
    "session",
    "screenshot",
    "secret",
    "storage_state",
    "token",
    "trace",
)

_RAW_ARTIFACT_KEY_TOKENS = (
    "downloaded_artifact",
    "downloaded_document",
    "download_path",
    "raw_artifact",
    "raw_body",
    "raw_crawl",
    "source_pdf",
    "warc",
)

_LIVE_CRAWL_PHRASES = (
    "live crawl executed",
    "live crawl completed",
    "executed live crawl",
    "ran live crawl",
    "crawled live",
    "downloaded from live site",
)

_OFFICIAL_ACTION_PHRASES = (
    "official action completed",
    "permit submitted",
    "submitted permit",
    "application submitted",
    "paid fees",
    "payment submitted",
    "inspection scheduled",
    "correction uploaded",
    "certification completed",
)

_GUARANTEE_PHRASES = (
    "guarantee approval",
    "guaranteed approval",
    "will be approved",
    "permit will issue",
    "legally sufficient",
    "legal guarantee",
    "permitting guarantee",
    "no legal risk",
)

_ACTIVE_MUTATION_KEYS = (
    "active_mutation",
    "allow_mutation",
    "can_mutate_official_record",
    "guardrails_active",
    "mutation_enabled",
    "official_action_enabled",
    "write_enabled",
)

_FORBIDDEN_TRUE_KEYS = (
    "live_crawl_executed",
    "live_crawl_completed",
    "official_action_completed",
    "payment_completed",
    "permit_submitted",
    "inspection_scheduled",
    "certification_completed",
) + _ACTIVE_MUTATION_KEYS

_ALLOWED_VALIDATION_COMMANDS = (
    ("python3", "-m", "py_compile"),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
    ("python3", "-m", "pytest"),
    ("pytest",),
)


def validate_batch_plan_v6(plan: Mapping[str, Any]) -> list[BatchPlanViolation]:
    """Return deterministic validation failures for a batch plan v6 mapping."""

    violations: list[BatchPlanViolation] = []

    if plan.get("version") != 6:
        violations.append(
            BatchPlanViolation(
                "invalid_version",
                "version",
                "requirement re-extraction batch plans must declare version 6",
            )
        )

    _validate_stale_citation_refs(plan, violations)
    _validate_permit_process_batches(plan, violations)
    _validate_reviewer_acceptance_criteria(plan, violations)
    _validate_guardrails(plan, violations)
    _validate_validation_commands(plan, violations)
    _validate_forbidden_content(plan, violations)

    return violations


def assert_valid_batch_plan_v6(plan: Mapping[str, Any]) -> None:
    """Raise RequirementReextractionBatchPlanError if validation fails."""

    violations = validate_batch_plan_v6(plan)
    if violations:
        rendered = "; ".join(
            f"{violation.code} at {violation.path}: {violation.message}"
            for violation in violations
        )
        raise RequirementReextractionBatchPlanError(rendered)


def _validate_stale_citation_refs(
    plan: Mapping[str, Any], violations: list[BatchPlanViolation]
) -> None:
    refs = plan.get("stale_citation_remediation_refs")
    if not _is_nonempty_sequence(refs):
        violations.append(
            BatchPlanViolation(
                "missing_stale_citation_remediation_refs",
                "stale_citation_remediation_refs",
                "at least one stale-citation remediation queue fixture reference is required",
            )
        )
        return

    for index, ref in enumerate(refs):
        path = f"stale_citation_remediation_refs[{index}]"
        if not isinstance(ref, Mapping):
            violations.append(BatchPlanViolation("invalid_stale_citation_ref", path, "reference must be an object"))
            continue
        _require_text(ref, "queue_id", f"{path}.queue_id", violations)
        fixture_path = _require_text(ref, "fixture_path", f"{path}.fixture_path", violations)
        if fixture_path and not fixture_path.startswith("ppd/tests/fixtures/stale_citation_queue_v6/"):
            violations.append(
                BatchPlanViolation(
                    "invalid_stale_citation_fixture_path",
                    f"{path}.fixture_path",
                    "stale-citation references must point at committed ppd/tests fixtures",
                )
            )


def _validate_permit_process_batches(
    plan: Mapping[str, Any], violations: list[BatchPlanViolation]
) -> None:
    batches = plan.get("permit_process_batches")
    if not _is_nonempty_sequence(batches):
        violations.append(
            BatchPlanViolation(
                "missing_permit_process_grouping",
                "permit_process_batches",
                "at least one permit-process batch is required",
            )
        )
        return

    seen_processes: set[str] = set()
    for index, batch in enumerate(batches):
        path = f"permit_process_batches[{index}]"
        if not isinstance(batch, Mapping):
            violations.append(BatchPlanViolation("invalid_permit_process_batch", path, "batch must be an object"))
            continue

        process = _require_text(batch, "permit_process", f"{path}.permit_process", violations)
        if process:
            if process in seen_processes:
                violations.append(
                    BatchPlanViolation(
                        "duplicate_permit_process_batch",
                        f"{path}.permit_process",
                        "each permit process must appear in only one batch",
                    )
                )
            seen_processes.add(process)

        changed_documents = batch.get("changed_public_documents")
        if not _is_nonempty_sequence(changed_documents):
            violations.append(
                BatchPlanViolation(
                    "missing_changed_public_documents",
                    f"{path}.changed_public_documents",
                    "each permit-process batch must list changed public documents",
                )
            )
        else:
            for document_index, document in enumerate(changed_documents):
                document_path = f"{path}.changed_public_documents[{document_index}]"
                if not isinstance(document, Mapping):
                    violations.append(BatchPlanViolation("invalid_changed_document", document_path, "document row must be an object"))
                    continue
                _require_text(document, "document_key", f"{document_path}.document_key", violations)
                _require_text(
                    document,
                    "stale_citation_queue_fixture_id",
                    f"{document_path}.stale_citation_queue_fixture_id",
                    violations,
                )
                if document.get("change_reason") != "fixture_stale_citation_remediation":
                    violations.append(
                        BatchPlanViolation(
                            "invalid_changed_document_reason",
                            f"{document_path}.change_reason",
                            "changed documents must be derived from stale-citation remediation fixtures",
                        )
                    )

        fixtures = batch.get("cite_extraction_fixtures_to_refresh")
        if not _is_nonempty_sequence(fixtures):
            violations.append(
                BatchPlanViolation(
                    "missing_extraction_fixture_references",
                    f"{path}.cite_extraction_fixtures_to_refresh",
                    "each batch must list cite extraction fixtures to refresh",
                )
            )
        else:
            for fixture_index, fixture in enumerate(fixtures):
                fixture_path = f"{path}.cite_extraction_fixtures_to_refresh[{fixture_index}]"
                if not isinstance(fixture, str) or not fixture.startswith("ppd/tests/fixtures/cite_extraction/") or not fixture.endswith(".json"):
                    violations.append(
                        BatchPlanViolation(
                            "invalid_extraction_fixture_reference",
                            fixture_path,
                            "extraction fixtures must be committed cite_extraction JSON fixtures",
                        )
                    )

        holds = batch.get("human_review_holds")
        if not _is_nonempty_sequence(holds):
            violations.append(
                BatchPlanViolation(
                    "missing_propagated_human_review_holds",
                    f"{path}.human_review_holds",
                    "each batch must carry human-review holds forward",
                )
            )
        else:
            for hold_index, hold in enumerate(holds):
                hold_path = f"{path}.human_review_holds[{hold_index}]"
                if not isinstance(hold, Mapping):
                    violations.append(BatchPlanViolation("invalid_human_review_hold", hold_path, "hold row must be an object"))
                    continue
                _require_text(hold, "hold_id", f"{hold_path}.hold_id", violations)
                _require_text(hold, "reason", f"{hold_path}.reason", violations)
                if hold.get("carried_forward") is not True:
                    violations.append(
                        BatchPlanViolation(
                            "human_review_hold_not_carried_forward",
                            f"{hold_path}.carried_forward",
                            "human-review holds must be propagated as carried_forward=true",
                        )
                    )
                if _lower_text(hold.get("status")) not in {"hold", "pending_human_review", "requires_human_review"}:
                    violations.append(
                        BatchPlanViolation(
                            "invalid_human_review_hold_status",
                            f"{hold_path}.status",
                            "human-review holds must remain on hold",
                        )
                    )


def _validate_reviewer_acceptance_criteria(
    plan: Mapping[str, Any], violations: list[BatchPlanViolation]
) -> None:
    criteria = plan.get("reviewer_acceptance_criteria")
    if not _is_nonempty_sequence(criteria):
        violations.append(
            BatchPlanViolation(
                "missing_reviewer_acceptance_criteria",
                "reviewer_acceptance_criteria",
                "reviewer acceptance criteria are required",
            )
        )
        return
    for index, criterion in enumerate(criteria):
        if not isinstance(criterion, str) or not criterion.strip():
            violations.append(
                BatchPlanViolation(
                    "invalid_reviewer_acceptance_criterion",
                    f"reviewer_acceptance_criteria[{index}]",
                    "criteria must be non-empty strings",
                )
            )


def _validate_guardrails(
    plan: Mapping[str, Any], violations: list[BatchPlanViolation]
) -> None:
    guardrails = plan.get("guardrails")
    if not isinstance(guardrails, Mapping):
        violations.append(
            BatchPlanViolation(
                "missing_inactive_guardrail_preservation",
                "guardrails",
                "guardrail inactive status preservation is required",
            )
        )
        return

    missing = _REQUIRED_GUARDRAILS.difference(str(key) for key in guardrails)
    if missing:
        violations.append(
            BatchPlanViolation(
                "missing_inactive_guardrail_preservation",
                "guardrails",
                "missing inactive guardrails: " + ", ".join(sorted(missing)),
            )
        )

    for key, value in guardrails.items():
        if value != "inactive":
            violations.append(
                BatchPlanViolation(
                    "guardrail_not_inactive",
                    f"guardrails.{key}",
                    "all existing guardrails must remain inactive in this batch plan",
                )
            )


def _validate_validation_commands(
    plan: Mapping[str, Any], violations: list[BatchPlanViolation]
) -> None:
    commands = plan.get("offline_validation_commands") or plan.get("validation_commands")
    if not _is_nonempty_sequence(commands):
        violations.append(
            BatchPlanViolation(
                "missing_validation_commands",
                "offline_validation_commands",
                "at least one offline validation command is required",
            )
        )
        return

    for index, command in enumerate(commands):
        path = f"offline_validation_commands[{index}]"
        if not _is_nonempty_sequence(command) or not all(isinstance(part, str) and part for part in command):
            violations.append(
                BatchPlanViolation(
                    "invalid_validation_command",
                    path,
                    "validation commands must be non-empty arrays of strings",
                )
            )
            continue
        if not _has_allowed_command_prefix(tuple(command)):
            violations.append(
                BatchPlanViolation(
                    "unsupported_validation_command",
                    path,
                    "validation command must use an approved deterministic PP&D test command",
                )
            )


def _validate_forbidden_content(
    plan: Mapping[str, Any], violations: list[BatchPlanViolation]
) -> None:
    for path, key, value in _walk(plan):
        key_text = key.lower()
        value_text = _lower_text(value)

        if key_text in _FORBIDDEN_TRUE_KEYS and value is True:
            violations.append(
                BatchPlanViolation(
                    "active_mutation_or_forbidden_true_flag",
                    path,
                    f"{key} must not be true in a requirement re-extraction batch plan",
                )
            )

        if _contains_token(key_text, _PRIVATE_KEY_TOKENS):
            violations.append(
                BatchPlanViolation(
                    "private_or_session_artifact",
                    path,
                    "private, session, authentication, trace, HAR, or screenshot fields are not allowed",
                )
            )

        if _contains_token(key_text, _RAW_ARTIFACT_KEY_TOKENS):
            violations.append(
                BatchPlanViolation(
                    "downloaded_or_raw_crawl_artifact",
                    path,
                    "downloaded documents, raw crawl bodies, WARC files, and raw artifacts are not allowed",
                )
            )

        if isinstance(value, str):
            lowered = value.lower()
            _reject_phrases(
                violations,
                "live_crawl_execution_claim",
                path,
                lowered,
                _LIVE_CRAWL_PHRASES,
                "batch plan must not claim live crawl execution",
            )
            _reject_phrases(
                violations,
                "official_action_completion_claim",
                path,
                lowered,
                _OFFICIAL_ACTION_PHRASES,
                "batch plan must not claim official action completion",
            )
            _reject_phrases(
                violations,
                "legal_or_permitting_guarantee",
                path,
                lowered,
                _GUARANTEE_PHRASES,
                "batch plan must not make legal or permitting guarantees",
            )
            if _looks_like_private_or_raw_path(value):
                violations.append(
                    BatchPlanViolation(
                        "forbidden_artifact_path",
                        path,
                        "paths to private, session, downloaded, or raw crawl artifacts are not allowed",
                    )
                )

        if value_text in {"active mutation", "mutation enabled", "write enabled", "guardrail active"}:
            violations.append(
                BatchPlanViolation(
                    "active_mutation_flag",
                    path,
                    "active mutation flags are not allowed",
                )
            )


def _require_text(
    row: Mapping[str, Any], key: str, path: str, violations: list[BatchPlanViolation]
) -> str:
    value = row.get(key)
    if not isinstance(value, str) or not value.strip():
        violations.append(BatchPlanViolation(f"missing_{key}", path, f"{key} is required"))
        return ""
    return value.strip()


def _reject_phrases(
    violations: list[BatchPlanViolation],
    code: str,
    path: str,
    lowered_value: str,
    phrases: Iterable[str],
    message: str,
) -> None:
    if any(phrase in lowered_value for phrase in phrases):
        violations.append(BatchPlanViolation(code, path, message))


def _walk(value: Any, path: str = "$", key: str = "") -> Iterable[tuple[str, str, Any]]:
    yield path, key, value
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            child_path = f"{path}.{child_key_text}" if path else child_key_text
            yield from _walk(child_value, child_path, child_key_text)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child_value in enumerate(value):
            yield from _walk(child_value, f"{path}[{index}]", key)


def _has_allowed_command_prefix(command: tuple[str, ...]) -> bool:
    return any(command[: len(prefix)] == prefix for prefix in _ALLOWED_VALIDATION_COMMANDS)


def _is_nonempty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) > 0


def _lower_text(value: Any) -> str:
    return value.lower() if isinstance(value, str) else ""


def _contains_token(text: str, tokens: Iterable[str]) -> bool:
    normalized = text.replace("-", "_")
    return any(token in normalized for token in tokens)


def _looks_like_private_or_raw_path(value: str) -> bool:
    normalized = PurePosixPath(value.replace("\\", "/")).as_posix().lower()
    forbidden_segments = (
        "/.auth/",
        "/.devhub/",
        "/cookies/",
        "/downloads/",
        "/har/",
        "/raw/",
        "/sessions/",
        "/storage_state/",
        "/traces/",
    )
    return any(segment in f"/{normalized}/" for segment in forbidden_segments)
