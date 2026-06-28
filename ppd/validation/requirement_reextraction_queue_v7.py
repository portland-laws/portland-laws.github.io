"""Validation for downstream requirement re-extraction queue v7 payloads."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


REQUIRED_ENTRY_FIELDS = (
    "source_freshness_diff_ref",
    "source_to_extraction_work_rows",
    "changed_section_placeholders",
    "citation_span_refresh_expectations",
    "requirement_family_hints",
    "stale_evidence_hold_carry_forward_rows",
    "reviewer_assignment_placeholders",
    "validation_commands",
)

FORBIDDEN_KEYS = {
    "active_mutation_flags",
    "auth_artifacts",
    "auth_state_path",
    "crawl_output_path",
    "crawl_run_id",
    "crawled_live",
    "devhub_session_path",
    "downloaded_artifacts",
    "downloaded_document_path",
    "guaranteed_approval",
    "legal_guarantee",
    "live_crawl_executed",
    "live_crawl_execution_claims",
    "mutation_enabled",
    "official_action_completed",
    "permit_submitted",
    "permitting_guarantee",
    "private_artifacts",
    "raw_crawl_artifacts",
    "raw_html_path",
    "session_artifacts",
    "session_cookie_path",
    "storage_state_path",
    "submission_completed",
    "submit_enabled",
    "trace_path",
    "writes_enabled",
}

FORBIDDEN_TEXT = (
    "live crawl executed",
    "downloaded artifact",
    "raw crawl artifact",
    "private session",
    "auth artifact",
    "official action completed",
    "permit submitted",
    "legal guarantee",
    "permitting guarantee",
    "guaranteed approval",
    "active mutation",
)


@dataclass(frozen=True)
class QueueValidationError:
    """A single deterministic validation error."""

    path: str
    message: str


def validate_requirement_reextraction_queue_v7(payload: Mapping[str, Any]) -> list[QueueValidationError]:
    """Return validation errors for a downstream re-extraction queue v7 payload."""

    errors: list[QueueValidationError] = []
    entries = payload.get("entries", payload.get("items"))
    if not isinstance(entries, Sequence) or isinstance(entries, (str, bytes)):
        return [QueueValidationError("entries", "queue must contain an entries or items list")]

    for index, entry in enumerate(entries):
        entry_path = f"entries[{index}]"
        if not isinstance(entry, Mapping):
            errors.append(QueueValidationError(entry_path, "entry must be an object"))
            continue

        for field in REQUIRED_ENTRY_FIELDS:
            if _is_missing(entry.get(field)):
                errors.append(QueueValidationError(f"{entry_path}.{field}", "required re-extraction queue v7 field is missing or empty"))

        commands = entry.get("validation_commands")
        if not _is_validation_commands(commands):
            errors.append(QueueValidationError(f"{entry_path}.validation_commands", "validation commands must be non-empty argv lists"))

        errors.extend(_find_forbidden_values(entry, entry_path))

    return errors


def assert_valid_requirement_reextraction_queue_v7(payload: Mapping[str, Any]) -> None:
    """Raise ValueError when a queue payload violates v7 requirements."""

    errors = validate_requirement_reextraction_queue_v7(payload)
    if errors:
        detail = "; ".join(f"{error.path}: {error.message}" for error in errors)
        raise ValueError(detail)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return len(value) == 0
    return False


def _is_validation_commands(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or not value:
        return False
    for command in value:
        if not isinstance(command, Sequence) or isinstance(command, (str, bytes)) or not command:
            return False
        if not all(isinstance(part, str) and part.strip() for part in command):
            return False
    return True


def _find_forbidden_values(value: Any, path: str) -> list[QueueValidationError]:
    errors: list[QueueValidationError] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            key_text = str(key).strip().lower()
            if key_text in FORBIDDEN_KEYS and not _is_missing(child):
                errors.append(QueueValidationError(child_path, "forbidden crawl/session/action/guarantee/mutation field is populated"))
            errors.extend(_find_forbidden_values(child, child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            errors.extend(_find_forbidden_values(child, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        for phrase in FORBIDDEN_TEXT:
            if phrase in lowered:
                errors.append(QueueValidationError(path, f"forbidden claim text: {phrase}"))
    return errors
