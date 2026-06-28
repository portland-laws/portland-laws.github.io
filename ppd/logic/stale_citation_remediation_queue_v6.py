"""Validation for stale-citation remediation queue v6 artifacts.

The queue is intentionally metadata-only. It may describe remediation work that
needs review, but it must not claim live crawl execution, persist downloaded/raw
artifacts, store private browser/session material, or imply that official PP&D
actions or legal/permitting outcomes are complete or guaranteed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


class QueueValidationError(ValueError):
    """Raised when a stale-citation remediation queue is not acceptable."""


@dataclass(frozen=True)
class QueueViolation:
    """A single deterministic validation failure."""

    code: str
    path: str
    message: str


_REQUIRED_TABLES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "result_intake_refs",
        ("intake_ref", "source_id", "result_id"),
    ),
    (
        "cited_requirement_evidence_rows",
        ("requirement_id", "evidence_id", "citation_id", "source_hash"),
    ),
    (
        "unaffected_citation_rows",
        ("citation_id", "source_id", "source_hash", "unchanged_reason"),
    ),
    (
        "changed_source_hash_placeholders",
        ("source_id", "previous_source_hash", "changed_source_hash_placeholder"),
    ),
    (
        "human_review_hold_rows",
        ("hold_id", "reason", "status"),
    ),
    (
        "downstream_guardrail_bundle_impact_placeholders",
        ("guardrail_bundle_id", "impact_placeholder", "status"),
    ),
)

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
    "token",
    "trace",
)

_ARTIFACT_KEY_TOKENS = (
    "downloaded_artifact",
    "downloaded_document",
    "raw_artifact",
    "raw_body",
    "raw_crawl",
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
)

_MUTATION_KEYS = (
    "active_mutation",
    "allow_mutation",
    "can_mutate_official_record",
    "mutates_official_record",
    "mutation_enabled",
    "write_enabled",
)

_FORBIDDEN_TRUE_KEYS = (
    "live_crawl_executed",
    "official_action_completed",
    "payment_completed",
    "permit_submitted",
    "inspection_scheduled",
    "certification_completed",
) + _MUTATION_KEYS


_ALLOWED_VALIDATION_COMMANDS = (
    ("python3", "-m", "py_compile"),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
    ("python3", "-m", "pytest"),
    ("pytest",),
)


def validate_queue_v6(queue: Mapping[str, Any]) -> list[QueueViolation]:
    """Return deterministic validation failures for a queue v6 mapping."""

    violations: list[QueueViolation] = []

    if queue.get("queue_version") != 6:
        violations.append(
            QueueViolation(
                "invalid_queue_version",
                "queue_version",
                "stale-citation remediation queues must declare queue_version 6",
            )
        )

    for table_name, required_fields in _REQUIRED_TABLES:
        rows = queue.get(table_name)
        if not _is_nonempty_sequence(rows):
            violations.append(
                QueueViolation(
                    f"missing_{table_name}",
                    table_name,
                    f"{table_name} must contain at least one row",
                )
            )
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, Mapping):
                violations.append(
                    QueueViolation(
                        f"invalid_{table_name}_row",
                        f"{table_name}[{index}]",
                        "row must be an object",
                    )
                )
                continue
            _validate_required_fields(violations, table_name, index, row, required_fields)

    _validate_human_review_rows(queue, violations)
    _validate_guardrail_impact_placeholders(queue, violations)
    _validate_changed_hash_placeholders(queue, violations)
    _validate_validation_commands(queue, violations)
    _validate_forbidden_content(queue, violations)

    return violations


def assert_valid_queue_v6(queue: Mapping[str, Any]) -> None:
    """Raise QueueValidationError if queue v6 validation fails."""

    violations = validate_queue_v6(queue)
    if violations:
        rendered = "; ".join(
            f"{violation.code} at {violation.path}: {violation.message}"
            for violation in violations
        )
        raise QueueValidationError(rendered)


def _validate_required_fields(
    violations: list[QueueViolation],
    table_name: str,
    index: int,
    row: Mapping[str, Any],
    required_fields: Sequence[str],
) -> None:
    for field in required_fields:
        if _is_blank(row.get(field)):
            violations.append(
                QueueViolation(
                    f"missing_{table_name}_{field}",
                    f"{table_name}[{index}].{field}",
                    f"{field} is required",
                )
            )


def _validate_human_review_rows(
    queue: Mapping[str, Any], violations: list[QueueViolation]
) -> None:
    rows = queue.get("human_review_hold_rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            continue
        status = _lower_text(row.get("status"))
        if status not in {"hold", "pending_human_review", "requires_human_review"}:
            violations.append(
                QueueViolation(
                    "invalid_human_review_hold_status",
                    f"human_review_hold_rows[{index}].status",
                    "human review rows must keep remediation on hold",
                )
            )


def _validate_guardrail_impact_placeholders(
    queue: Mapping[str, Any], violations: list[QueueViolation]
) -> None:
    rows = queue.get("downstream_guardrail_bundle_impact_placeholders")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            continue
        status = _lower_text(row.get("status"))
        if status not in {"placeholder", "pending_impact_assessment", "pending_review"}:
            violations.append(
                QueueViolation(
                    "invalid_guardrail_impact_status",
                    f"downstream_guardrail_bundle_impact_placeholders[{index}].status",
                    "guardrail impacts must remain placeholders until reviewed",
                )
            )


def _validate_changed_hash_placeholders(
    queue: Mapping[str, Any], violations: list[QueueViolation]
) -> None:
    rows = queue.get("changed_source_hash_placeholders")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            continue
        placeholder = row.get("changed_source_hash_placeholder")
        if not isinstance(placeholder, str) or not placeholder.startswith("placeholder:"):
            violations.append(
                QueueViolation(
                    "invalid_changed_source_hash_placeholder",
                    f"changed_source_hash_placeholders[{index}].changed_source_hash_placeholder",
                    "changed source hashes must use placeholder: values until evidence is reviewed",
                )
            )


def _validate_validation_commands(
    queue: Mapping[str, Any], violations: list[QueueViolation]
) -> None:
    commands = queue.get("validation_commands")
    if not _is_nonempty_sequence(commands):
        violations.append(
            QueueViolation(
                "missing_validation_commands",
                "validation_commands",
                "at least one validation command is required",
            )
        )
        return

    for index, command in enumerate(commands):
        path = f"validation_commands[{index}]"
        if not _is_nonempty_sequence(command) or not all(
            isinstance(part, str) and part for part in command
        ):
            violations.append(
                QueueViolation(
                    "invalid_validation_command",
                    path,
                    "validation commands must be non-empty arrays of strings",
                )
            )
            continue
        if not _has_allowed_command_prefix(tuple(command)):
            violations.append(
                QueueViolation(
                    "unsupported_validation_command",
                    path,
                    "validation command must use an approved deterministic PP&D test command",
                )
            )


def _validate_forbidden_content(
    queue: Mapping[str, Any], violations: list[QueueViolation]
) -> None:
    for path, key, value in _walk(queue):
        key_text = key.lower()
        value_text = _lower_text(value)

        if key_text in _FORBIDDEN_TRUE_KEYS and value is True:
            violations.append(
                QueueViolation(
                    "forbidden_true_flag",
                    path,
                    f"{key} must not be true in a remediation queue",
                )
            )

        if _contains_token(key_text, _PRIVATE_KEY_TOKENS):
            violations.append(
                QueueViolation(
                    "private_or_session_artifact",
                    path,
                    "private, session, authentication, trace, HAR, or screenshot fields are not allowed",
                )
            )

        if _contains_token(key_text, _ARTIFACT_KEY_TOKENS):
            violations.append(
                QueueViolation(
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
                "queue must not claim live crawl execution",
            )
            _reject_phrases(
                violations,
                "official_action_completion_claim",
                path,
                lowered,
                _OFFICIAL_ACTION_PHRASES,
                "queue must not claim official action completion",
            )
            _reject_phrases(
                violations,
                "legal_or_permitting_guarantee",
                path,
                lowered,
                _GUARANTEE_PHRASES,
                "queue must not make legal or permitting guarantees",
            )
            if _looks_like_private_or_raw_path(value):
                violations.append(
                    QueueViolation(
                        "forbidden_artifact_path",
                        path,
                        "paths to private, session, downloaded, or raw crawl artifacts are not allowed",
                    )
                )

        if value_text in {"active mutation", "mutation enabled", "write enabled"}:
            violations.append(
                QueueViolation(
                    "active_mutation_flag",
                    path,
                    "active mutation flags are not allowed",
                )
            )


def _reject_phrases(
    violations: list[QueueViolation],
    code: str,
    path: str,
    lowered_value: str,
    phrases: Iterable[str],
    message: str,
) -> None:
    if any(phrase in lowered_value for phrase in phrases):
        violations.append(QueueViolation(code, path, message))


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


def _is_blank(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


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
