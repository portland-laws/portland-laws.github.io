"""Validation for DevHub read-only observation intake schema v3.

The schema is intentionally conservative: committed intake packets must describe
only redacted, read-only observations and placeholders for later human review.
They must not claim live DevHub interaction, private session artifacts, uploads,
form filling, official completion, legal outcomes, or active mutation capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class ValidationError:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    errors: tuple[ValidationError, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


_REQUIRED_FIELDS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    (
        "missing_authorization_checklist_reference",
        ("authorization_checklist_reference",),
        "authorization checklist reference is required",
    ),
    (
        "missing_redacted_observation_row_placeholders",
        ("redacted_observation_rows",),
        "redacted observation row placeholders are required",
    ),
    ("missing_title", ("surface", "title"), "surface title is required"),
    ("missing_page_heading", ("surface", "page_heading"), "surface page heading is required"),
    ("missing_url_pattern", ("surface", "url_pattern"), "surface URL pattern is required"),
    (
        "missing_validation_message_placeholders",
        ("validation_message_placeholders",),
        "validation message placeholders are required",
    ),
    (
        "missing_non_action_upload_control_evidence_labels",
        ("non_action_upload_control_evidence_labels",),
        "non-action upload-control evidence labels are required",
    ),
    (
        "missing_state_transition_placeholders",
        ("state_transition_placeholders",),
        "state-transition placeholders are required",
    ),
    (
        "missing_selector_confidence_notes",
        ("selector_confidence_notes",),
        "selector-confidence notes are required",
    ),
    (
        "missing_source_evidence_placeholders",
        ("source_evidence_placeholders",),
        "source-evidence placeholders are required",
    ),
    ("missing_reviewer_holds", ("reviewer_holds",), "reviewer holds are required"),
    (
        "missing_validation_commands",
        ("validation_commands",),
        "validation commands are required",
    ),
)

_FORBIDDEN_TEXT: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "private_or_session_artifact_claim",
        (
            "auth state",
            "auth_state",
            "bearer ",
            "cookie",
            "credential",
            "localstorage",
            "password",
            "private file",
            "session state",
            "sessionstorage",
        ),
    ),
    ("screenshot_trace_or_har_claim", ("screenshot", "trace.zip", "playwright trace", " har ", ".har", "video capture")),
    (
        "live_devhub_interaction_claim",
        (
            "clicked in devhub",
            "interacted with live devhub",
            "live devhub",
            "logged into devhub",
            "real devhub session",
        ),
    ),
    (
        "form_fill_or_upload_claim",
        (
            "attached file",
            "filled form",
            "form was filled",
            "selected file",
            "uploaded",
            "upload completed",
        ),
    ),
    (
        "official_action_completion_claim",
        (
            "application submitted",
            "cancelled inspection",
            "certified",
            "fee paid",
            "inspection scheduled",
            "officially submitted",
            "payment submitted",
            "permit submitted",
            "submitted to pp&d",
        ),
    ),
    (
        "legal_or_permitting_guarantee",
        (
            "guarantee approval",
            "guaranteed approval",
            "legal advice",
            "permit approval is guaranteed",
            "permit will be approved",
        ),
    ),
)

_MUTATION_KEYS = {
    "active_mutation",
    "active_mutation_enabled",
    "active_mutation_flag",
    "can_cancel",
    "can_certify",
    "can_pay",
    "can_schedule",
    "can_submit",
    "can_upload",
    "mutation_enabled",
}

_MUTATION_TEXT_VALUES = {"active", "enabled", "live", "mutation", "mutating", "write"}


def validate_observation_intake_v3(payload: Mapping[str, Any]) -> ValidationResult:
    """Return schema v3 validation errors for a committed observation packet."""

    errors: list[ValidationError] = []

    for code, path, message in _REQUIRED_FIELDS:
        if _missing(_get(payload, path)):
            errors.append(ValidationError(code=code, path=_format_path(path), message=message))

    _validate_redacted_rows(payload, errors)
    _validate_landmarks_or_actions(payload, errors)
    _validate_upload_control_labels(payload, errors)
    _validate_validation_commands(payload, errors)
    _scan_for_forbidden_claims(payload, errors)

    return ValidationResult(errors=tuple(errors))


def assert_valid_observation_intake_v3(payload: Mapping[str, Any]) -> None:
    """Raise ValueError with deterministic messages when the packet is invalid."""

    result = validate_observation_intake_v3(payload)
    if result.ok:
        return
    details = "; ".join(f"{error.code} at {error.path}" for error in result.errors)
    raise ValueError(f"DevHub read-only observation intake schema v3 validation failed: {details}")


def _validate_redacted_rows(payload: Mapping[str, Any], errors: list[ValidationError]) -> None:
    rows = payload.get("redacted_observation_rows")
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        return
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            errors.append(
                ValidationError(
                    code="invalid_redacted_observation_row",
                    path=f"redacted_observation_rows[{index}]",
                    message="redacted observation row must be an object",
                )
            )
            continue
        placeholder = row.get("placeholder") or row.get("redacted_placeholder") or row.get("row_placeholder")
        if _missing(placeholder):
            errors.append(
                ValidationError(
                    code="missing_redacted_observation_row_placeholder",
                    path=f"redacted_observation_rows[{index}].placeholder",
                    message="each redacted observation row requires a placeholder",
                )
            )


def _validate_landmarks_or_actions(payload: Mapping[str, Any], errors: list[ValidationError]) -> None:
    landmarks = payload.get("accessible_landmarks")
    actions = payload.get("read_only_actions")
    has_landmark_label = _has_labeled_item(landmarks)
    has_action_label = _has_labeled_item(actions)
    if not has_landmark_label and not has_action_label:
        errors.append(
            ValidationError(
                code="missing_accessible_landmark_or_read_only_action_labels",
                path="accessible_landmarks|read_only_actions",
                message="at least one accessible landmark label or read-only action label is required",
            )
        )

    if isinstance(actions, Sequence) and not isinstance(actions, (str, bytes)):
        for index, action in enumerate(actions):
            if isinstance(action, Mapping) and _missing(action.get("label") or action.get("accessible_label")):
                errors.append(
                    ValidationError(
                        code="missing_read_only_action_label",
                        path=f"read_only_actions[{index}].label",
                        message="read-only action labels are required",
                    )
                )


def _validate_upload_control_labels(payload: Mapping[str, Any], errors: list[ValidationError]) -> None:
    controls = payload.get("upload_controls")
    if not isinstance(controls, Sequence) or isinstance(controls, (str, bytes)):
        return
    for index, control in enumerate(controls):
        if not isinstance(control, Mapping):
            errors.append(
                ValidationError(
                    code="invalid_upload_control_evidence_label",
                    path=f"upload_controls[{index}]",
                    message="upload-control evidence label must be an object",
                )
            )
            continue
        if _missing(control.get("evidence_label") or control.get("non_action_evidence_label")):
            errors.append(
                ValidationError(
                    code="missing_upload_control_evidence_label",
                    path=f"upload_controls[{index}].evidence_label",
                    message="upload controls require non-action evidence labels",
                )
            )


def _validate_validation_commands(payload: Mapping[str, Any], errors: list[ValidationError]) -> None:
    commands = payload.get("validation_commands")
    if _missing(commands):
        return
    if not isinstance(commands, Sequence) or isinstance(commands, (str, bytes)):
        errors.append(
            ValidationError(
                code="invalid_validation_commands",
                path="validation_commands",
                message="validation commands must be a list of command argument lists",
            )
        )
        return
    for index, command in enumerate(commands):
        if not isinstance(command, Sequence) or isinstance(command, (str, bytes)) or not command:
            errors.append(
                ValidationError(
                    code="invalid_validation_command",
                    path=f"validation_commands[{index}]",
                    message="validation command must be a non-empty list of strings",
                )
            )
            continue
        if any(not isinstance(part, str) or not part.strip() for part in command):
            errors.append(
                ValidationError(
                    code="invalid_validation_command_argument",
                    path=f"validation_commands[{index}]",
                    message="validation command arguments must be non-empty strings",
                )
            )


def _scan_for_forbidden_claims(payload: Any, errors: list[ValidationError]) -> None:
    for path, value in _walk(payload):
        if isinstance(value, str):
            normalized = f" {value.lower()} "
            compact = normalized.replace("-", "_")
            for code, needles in _FORBIDDEN_TEXT:
                if any(needle in normalized or needle in compact for needle in needles):
                    errors.append(
                        ValidationError(
                            code=code,
                            path=path,
                            message="committed read-only observation intake contains a prohibited claim",
                        )
                    )
            if path.split(".")[-1] in {"mutation_mode", "mode"} and value.strip().lower() in _MUTATION_TEXT_VALUES:
                errors.append(
                    ValidationError(
                        code="active_mutation_flag",
                        path=path,
                        message="active mutation flags are prohibited",
                    )
                )
        elif isinstance(value, bool) and value:
            key = path.split(".")[-1]
            if key in _MUTATION_KEYS:
                errors.append(
                    ValidationError(
                        code="active_mutation_flag",
                        path=path,
                        message="active mutation flags are prohibited",
                    )
                )


def _has_labeled_item(value: Any) -> bool:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return False
    for item in value:
        if isinstance(item, Mapping) and not _missing(item.get("label") or item.get("name") or item.get("accessible_label")):
            return True
    return False


def _get(payload: Mapping[str, Any], path: tuple[str, ...]) -> Any:
    current: Any = payload
    for part in path:
        if not isinstance(current, Mapping) or part not in current:
            return None
        current = current[part]
    return current


def _missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, Mapping):
        return not value
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return not value
    return False


def _walk(value: Any, path: str = "$.") -> Iterable[tuple[str, Any]]:
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}{key}" if path == "$." else f"{path}.{key}"
            yield from _walk(child, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            yield from _walk(child, f"{path}[{index}]")
    else:
        yield path.rstrip("."), value


def _format_path(path: tuple[str, ...]) -> str:
    return ".".join(path)
