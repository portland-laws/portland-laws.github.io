"""Validation for PP&D ProcessModel impact candidate v5.

The validator is intentionally fail-closed: a candidate must include every
required review, delta, caveat, rollback, and validation field before it can be
accepted for further PP&D daemon handling.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


JsonObject = Mapping[str, Any]


@dataclass(frozen=True)
class CandidateValidationError:
    code: str
    message: str


@dataclass(frozen=True)
class CandidateValidationReport:
    ok: bool
    errors: tuple[CandidateValidationError, ...]

    def require_ok(self) -> None:
        if not self.ok:
            joined = "; ".join(f"{error.code}: {error.message}" for error in self.errors)
            raise ValueError(joined)


_REQUIRED_FIELD_GROUPS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "missing_requirement_queue_refs",
        ("requirement_queue_refs", "requirement_queue_references", "requirement_queue"),
        "candidate must cite the requirement queue references it resolves",
    ),
    (
        "missing_inactive_process_model_delta_rows",
        ("inactive_process_model_delta_rows", "inactive_process_model_deltas", "process_model_delta_rows"),
        "candidate must include inactive ProcessModel delta rows instead of mutating the active model",
    ),
    (
        "missing_eligibility_deltas",
        ("eligibility_deltas", "eligibility_delta_rows"),
        "candidate must include eligibility deltas",
    ),
    (
        "missing_fact_deltas",
        ("fact_deltas", "required_user_fact_deltas", "user_fact_deltas"),
        "candidate must include required fact deltas",
    ),
    (
        "missing_document_deltas",
        ("document_deltas", "required_document_deltas"),
        "candidate must include required document deltas",
    ),
    (
        "missing_file_rule_deltas",
        ("file_rule_deltas", "file_rules_deltas", "upload_file_rule_deltas"),
        "candidate must include file-rule deltas",
    ),
    (
        "missing_fee_caveats",
        ("fee_caveats", "fee_caveat_notes"),
        "candidate must include fee caveats",
    ),
    (
        "missing_deadline_caveats",
        ("deadline_caveats", "deadline_caveat_notes"),
        "candidate must include deadline caveats",
    ),
    (
        "missing_unsupported_path_handling",
        ("unsupported_path_handling", "unsupported_paths", "unsupported_path_notes"),
        "candidate must state unsupported-path handling",
    ),
    (
        "missing_devhub_reference_caveats",
        ("devhub_reference_caveats", "devhub_surface_caveats", "devhub_ref_caveats"),
        "candidate must include DevHub reference caveats",
    ),
    (
        "missing_reviewer_holds",
        ("reviewer_holds", "human_reviewer_holds", "review_holds"),
        "candidate must include reviewer holds",
    ),
    (
        "missing_rollback_notes",
        ("rollback_notes", "rollback_plan", "rollback"),
        "candidate must include rollback notes",
    ),
    (
        "missing_validation_commands",
        ("validation_commands", "validation"),
        "candidate must include validation commands",
    ),
)

_ACTIVE_MUTATION_FLAGS = (
    "active_model_mutation",
    "mutates_active_model",
    "mutate_active_model",
    "writes_active_model",
    "active_mutation",
    "active_mutation_flag",
    "commit_to_active_model",
    "mark_active",
)

_PRIVATE_ARTIFACT_KEYS = (
    "auth_state",
    "storage_state",
    "session_state",
    "session_cookie",
    "cookies",
    "credential",
    "credentials",
    "password",
    "token",
    "trace",
    "trace_path",
    "har",
    "har_path",
    "screenshot",
    "screenshot_path",
    "downloaded_document",
    "raw_crawl_output",
)

_PRIVATE_ARTIFACT_SUFFIXES = (
    ".har",
    ".trace",
    ".zip",
    ".webm",
    ".png",
    ".jpg",
    ".jpeg",
    ".storageState.json",
)

_PROHIBITED_TEXT_PATTERNS = (
    ("active_model_mutation_claim", "mutate active processmodel"),
    ("active_model_mutation_claim", "mutates active processmodel"),
    ("active_model_mutation_claim", "updated the active processmodel"),
    ("active_model_mutation_claim", "writes to the active model"),
    ("official_action_completion_claim", "permit submitted"),
    ("official_action_completion_claim", "application submitted"),
    ("official_action_completion_claim", "payment completed"),
    ("official_action_completion_claim", "fee paid"),
    ("official_action_completion_claim", "inspection scheduled"),
    ("official_action_completion_claim", "official action completed"),
    ("legal_or_permitting_guarantee", "guarantee approval"),
    ("legal_or_permitting_guarantee", "guaranteed approval"),
    ("legal_or_permitting_guarantee", "legal advice"),
    ("legal_or_permitting_guarantee", "permit will be approved"),
    ("legal_or_permitting_guarantee", "approval is guaranteed"),
)


class ProcessModelImpactCandidateV5Error(ValueError):
    """Raised when a ProcessModel impact candidate v5 is invalid."""



def validate_process_model_impact_candidate_v5(candidate: JsonObject) -> CandidateValidationReport:
    """Return a validation report for a ProcessModel impact candidate v5."""

    errors: list[CandidateValidationError] = []

    if not isinstance(candidate, Mapping):
        return CandidateValidationReport(
            ok=False,
            errors=(
                CandidateValidationError(
                    "candidate_not_object",
                    "candidate must be a JSON object",
                ),
            ),
        )

    for code, names, message in _REQUIRED_FIELD_GROUPS:
        if not _has_non_empty_field(candidate, names):
            errors.append(CandidateValidationError(code, message))

    inactive_rows = _first_present(candidate, ("inactive_process_model_delta_rows", "inactive_process_model_deltas", "process_model_delta_rows"))
    errors.extend(_validate_inactive_delta_rows(inactive_rows))
    errors.extend(_validate_validation_commands(_first_present(candidate, ("validation_commands", "validation"))))
    errors.extend(_find_active_mutation_flags(candidate))
    errors.extend(_find_private_artifacts(candidate))
    errors.extend(_find_prohibited_text(candidate))

    return CandidateValidationReport(ok=not errors, errors=tuple(errors))


def assert_valid_process_model_impact_candidate_v5(candidate: JsonObject) -> None:
    """Raise ProcessModelImpactCandidateV5Error if the candidate is invalid."""

    report = validate_process_model_impact_candidate_v5(candidate)
    if report.ok:
        return
    joined = "; ".join(f"{error.code}: {error.message}" for error in report.errors)
    raise ProcessModelImpactCandidateV5Error(joined)


def load_candidate(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ProcessModelImpactCandidateV5Error("candidate file must contain a JSON object")
    return loaded


def validate_candidate_file(path: str | Path) -> CandidateValidationReport:
    return validate_process_model_impact_candidate_v5(load_candidate(path))


def _has_non_empty_field(candidate: JsonObject, names: Sequence[str]) -> bool:
    return _is_non_empty(_first_present(candidate, names))


def _first_present(candidate: JsonObject, names: Sequence[str]) -> Any:
    for name in names:
        if name in candidate:
            return candidate[name]
    return None


def _is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return True
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return len(value) > 0
    return True


def _validate_inactive_delta_rows(value: Any) -> tuple[CandidateValidationError, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return ()

    errors: list[CandidateValidationError] = []
    for index, row in enumerate(value):
        if not isinstance(row, Mapping):
            errors.append(
                CandidateValidationError(
                    "invalid_process_model_delta_row",
                    f"inactive ProcessModel delta row {index} must be an object",
                )
            )
            continue

        active_value = row.get("active")
        status_value = str(row.get("status", row.get("state", ""))).lower()
        target_value = str(row.get("target", row.get("target_model", ""))).lower()
        operation_value = str(row.get("operation", row.get("op", ""))).lower()

        marks_inactive = active_value is False or status_value == "inactive" or target_value in {"inactive", "staged"}
        mutates_active = active_value is True or target_value == "active" or "active" in operation_value and "inactive" not in operation_value

        if not marks_inactive:
            errors.append(
                CandidateValidationError(
                    "delta_row_not_inactive",
                    f"ProcessModel delta row {index} must be explicitly inactive or staged",
                )
            )
        if mutates_active:
            errors.append(
                CandidateValidationError(
                    "delta_row_mutates_active_model",
                    f"ProcessModel delta row {index} claims an active model mutation",
                )
            )

    return tuple(errors)


def _validate_validation_commands(value: Any) -> tuple[CandidateValidationError, ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return (
            CandidateValidationError(
                "invalid_validation_commands",
                "validation_commands must be a non-empty list of argv lists",
            ),
        )

    errors: list[CandidateValidationError] = []
    for index, command in enumerate(value):
        if not isinstance(command, Sequence) or isinstance(command, (str, bytes, bytearray)) or not command:
            errors.append(
                CandidateValidationError(
                    "invalid_validation_command",
                    f"validation command {index} must be a non-empty argv list",
                )
            )
            continue
        if not all(isinstance(part, str) and part.strip() for part in command):
            errors.append(
                CandidateValidationError(
                    "invalid_validation_command_part",
                    f"validation command {index} must contain only non-empty strings",
                )
            )
    return tuple(errors)


def _find_active_mutation_flags(value: Any, path: str = "$") -> tuple[CandidateValidationError, ...]:
    errors: list[CandidateValidationError] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if key_text in _ACTIVE_MUTATION_FLAGS and child is not False and child is not None:
                errors.append(
                    CandidateValidationError(
                        "active_mutation_flag",
                        f"{child_path} must not request or claim active model mutation",
                    )
                )
            errors.extend(_find_active_mutation_flags(child, child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            errors.extend(_find_active_mutation_flags(child, f"{path}[{index}]"))
    return tuple(errors)


def _find_private_artifacts(value: Any, path: str = "$") -> tuple[CandidateValidationError, ...]:
    errors: list[CandidateValidationError] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if _looks_like_private_artifact_key(key_text):
                errors.append(
                    CandidateValidationError(
                        "private_session_or_auth_artifact",
                        f"{child_path} must not be committed in a PP&D candidate",
                    )
                )
            errors.extend(_find_private_artifacts(child, child_path))
    elif isinstance(value, str):
        lowered = value.lower()
        if any(lowered.endswith(suffix.lower()) for suffix in _PRIVATE_ARTIFACT_SUFFIXES):
            errors.append(
                CandidateValidationError(
                    "private_session_or_auth_artifact",
                    f"{path} references a private session, trace, screenshot, HAR, or browser artifact",
                )
            )
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            errors.extend(_find_private_artifacts(child, f"{path}[{index}]"))
    return tuple(errors)


def _looks_like_private_artifact_key(key: str) -> bool:
    lowered = key.lower().replace("-", "_")
    return any(token in lowered for token in _PRIVATE_ARTIFACT_KEYS)


def _find_prohibited_text(value: Any, path: str = "$") -> tuple[CandidateValidationError, ...]:
    errors: list[CandidateValidationError] = []
    if isinstance(value, str):
        normalized = " ".join(value.lower().split())
        for code, pattern in _PROHIBITED_TEXT_PATTERNS:
            if pattern in normalized:
                errors.append(
                    CandidateValidationError(
                        code,
                        f"{path} contains prohibited claim: {pattern}",
                    )
                )
    elif isinstance(value, Mapping):
        for key, child in value.items():
            errors.extend(_find_prohibited_text(child, f"{path}.{key}"))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            errors.extend(_find_prohibited_text(child, f"{path}[{index}]"))
    return tuple(errors)


__all__ = [
    "CandidateValidationError",
    "CandidateValidationReport",
    "ProcessModelImpactCandidateV5Error",
    "assert_valid_process_model_impact_candidate_v5",
    "load_candidate",
    "validate_candidate_file",
    "validate_process_model_impact_candidate_v5",
]
