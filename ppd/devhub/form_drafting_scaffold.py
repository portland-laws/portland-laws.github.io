"""Fixture-only DevHub form drafting scaffold.

This module deliberately does not import or drive Playwright. It consumes mocked
DevHub form-state fixtures that were captured or synthesized for tests, validates
that a requested edit is reversible draft entry, and returns an action preview
that a future guarded Playwright layer can review before any browser action.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence


class DraftPreviewError(ValueError):
    """Raised when a draft preview request violates PP&D DevHub guardrails."""


class DraftFieldKind(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    DATE = "date"
    NUMBER = "number"
    EMAIL = "email"
    TEL = "tel"


class DraftActionClassification(str, Enum):
    REVERSIBLE_DRAFT_EDIT = "reversible_draft_edit"


REFUSED_FIELD_KINDS = {
    "file",
    "upload",
    "submit",
    "button",
    "payment",
    "signature",
    "certification",
    "captcha",
    "mfa",
    "password",
    "account_creation",
    "password_recovery",
    "inspection_schedule",
    "cancellation",
}

MOCKED_FIXTURE_MARKERS = {"mocked_devhub_fixture", "synthetic_devhub_fixture"}
REDACTED_VALUE = "[REDACTED]"


@dataclass(frozen=True)
class DraftSelectorBasis:
    accessible_name: str
    label_text: str
    role: str
    nearby_heading: str
    url_state: str

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "DraftSelectorBasis":
        return cls(
            accessible_name=str(data.get("accessibleName", data.get("accessible_name", ""))),
            label_text=str(data.get("labelText", data.get("label_text", ""))),
            role=str(data.get("role", "")),
            nearby_heading=str(data.get("nearbyHeading", data.get("nearby_heading", ""))),
            url_state=str(data.get("urlState", data.get("url_state", ""))),
        )

    def validate(self, field_id: str) -> list[str]:
        errors: list[str] = []
        if not self.accessible_name.strip():
            errors.append(f"field {field_id}: accessible-name selector is required")
        if not self.label_text.strip():
            errors.append(f"field {field_id}: label text is required")
        if not self.role.strip():
            errors.append(f"field {field_id}: role is required")
        if not self.nearby_heading.strip():
            errors.append(f"field {field_id}: nearby heading is required")
        if not self.url_state.strip():
            errors.append(f"field {field_id}: URL state is required")
        return errors

    def to_json(self) -> dict[str, str]:
        return {
            "accessibleName": self.accessible_name,
            "labelText": self.label_text,
            "role": self.role,
            "nearbyHeading": self.nearby_heading,
            "urlState": self.url_state,
        }


@dataclass(frozen=True)
class DraftableField:
    field_id: str
    kind: str
    selector_basis: DraftSelectorBasis
    reversible: bool
    required: bool
    current_value: str
    allowed_values: tuple[str, ...] = ()
    source_requirement_id: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "DraftableField":
        selector_data = data.get("selectorBasis", data.get("selector_basis", {}))
        if not isinstance(selector_data, Mapping):
            selector_data = {}
        allowed_values = data.get("allowedValues", data.get("allowed_values", ()))
        if not isinstance(allowed_values, Sequence) or isinstance(allowed_values, (str, bytes)):
            allowed_values = ()
        return cls(
            field_id=str(data.get("fieldId", data.get("field_id", ""))),
            kind=str(data.get("kind", "")),
            selector_basis=DraftSelectorBasis.from_mapping(selector_data),
            reversible=bool(data.get("reversible", False)),
            required=bool(data.get("required", False)),
            current_value=str(data.get("currentValue", data.get("current_value", REDACTED_VALUE))),
            allowed_values=tuple(str(value) for value in allowed_values),
            source_requirement_id=_optional_string(data.get("sourceRequirementId", data.get("source_requirement_id"))),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.field_id.strip():
            errors.append("draftable field id is required")
        if not self.kind.strip():
            errors.append(f"field {self.field_id or ''}: kind is required")
        if self.kind in REFUSED_FIELD_KINDS:
            errors.append(f"field {self.field_id}: field kind {self.kind} is not draftable")
        elif self.kind not in {kind.value for kind in DraftFieldKind}:
            errors.append(f"field {self.field_id}: unsupported draft field kind {self.kind}")
        if not self.reversible:
            errors.append(f"field {self.field_id}: only reversible draft fields may be previewed")
        if self.current_value != REDACTED_VALUE:
            errors.append(f"field {self.field_id}: fixture current value must be redacted")
        errors.extend(self.selector_basis.validate(self.field_id))
        return errors


@dataclass(frozen=True)
class DraftActionPreview:
    preview_id: str
    fixture_id: str
    workflow_state_id: str
    mode: str
    touches_live_devhub: bool
    actions: tuple[dict[str, Any], ...]
    refused_actions: tuple[dict[str, str], ...]

    def to_json(self) -> dict[str, Any]:
        return {
            "previewId": self.preview_id,
            "fixtureId": self.fixture_id,
            "workflowStateId": self.workflow_state_id,
            "mode": self.mode,
            "touchesLiveDevhub": self.touches_live_devhub,
            "actions": list(self.actions),
            "refusedActions": list(self.refused_actions),
        }


def build_draft_action_preview(
    fixture: Mapping[str, Any],
    proposed_values: Mapping[str, Any],
    *,
    preview_id: str = "draft-preview-001",
) -> DraftActionPreview:
    """Return a deterministic preview for reversible draft field edits.

    The fixture must identify itself as mocked or synthetic, and every proposed
    field must be present in the fixture as a reversible draft field. The return
    value is an action preview only; this function never touches a browser or a
    live DevHub session.
    """

    fixture_id = str(fixture.get("fixtureId", fixture.get("fixture_id", "")))
    workflow_state_id = str(fixture.get("workflowStateId", fixture.get("workflow_state_id", "")))
    fixture_source = str(fixture.get("fixtureSource", fixture.get("fixture_source", "")))
    environment = str(fixture.get("environment", ""))

    fixture_errors = _validate_fixture_boundary(fixture_id, workflow_state_id, fixture_source, environment)
    fields = _fields_by_id(fixture.get("fields", ()))
    for field in fields.values():
        fixture_errors.extend(field.validate())

    if fixture_errors:
        raise DraftPreviewError("; ".join(fixture_errors))

    actions: list[dict[str, Any]] = []
    refused_actions: list[dict[str, str]] = []
    for field_id, proposed_value in proposed_values.items():
        normalized_field_id = str(field_id)
        field = fields.get(normalized_field_id)
        if field is None:
            refused_actions.append(
                {
                    "fieldId": normalized_field_id,
                    "reason": "field is absent from mocked DevHub fixture",
                }
            )
            continue
        refusal = _validate_proposed_value(field, proposed_value)
        if refusal is not None:
            refused_actions.append({"fieldId": normalized_field_id, "reason": refusal})
            continue
        actions.append(_preview_action(field, proposed_value))

    return DraftActionPreview(
        preview_id=preview_id,
        fixture_id=fixture_id,
        workflow_state_id=workflow_state_id,
        mode="preview_only",
        touches_live_devhub=False,
        actions=tuple(actions),
        refused_actions=tuple(refused_actions),
    )


def assert_preview_does_not_touch_live_devhub(preview: DraftActionPreview) -> None:
    """Fail closed if a preview claims it would touch live DevHub."""

    if preview.touches_live_devhub:
        raise DraftPreviewError("draft preview must not touch live DevHub")
    if preview.mode != "preview_only":
        raise DraftPreviewError("draft scaffold only supports preview_only mode")


def _validate_fixture_boundary(
    fixture_id: str,
    workflow_state_id: str,
    fixture_source: str,
    environment: str,
) -> list[str]:
    errors: list[str] = []
    if not fixture_id.strip():
        errors.append("fixtureId is required")
    if not workflow_state_id.strip():
        errors.append("workflowStateId is required")
    if fixture_source not in MOCKED_FIXTURE_MARKERS:
        errors.append("form drafting scaffold accepts only mocked DevHub fixtures")
    if environment != "mocked":
        errors.append("form drafting scaffold requires environment=mocked")
    return errors


def _fields_by_id(raw_fields: Any) -> dict[str, DraftableField]:
    if not isinstance(raw_fields, Sequence) or isinstance(raw_fields, (str, bytes)):
        raise DraftPreviewError("fixture fields must be a list")
    fields: dict[str, DraftableField] = {}
    for raw_field in raw_fields:
        if not isinstance(raw_field, Mapping):
            raise DraftPreviewError("each fixture field must be an object")
        field = DraftableField.from_mapping(raw_field)
        if field.field_id in fields:
            raise DraftPreviewError(f"duplicate fixture field id {field.field_id}")
        fields[field.field_id] = field
    return fields


def _validate_proposed_value(field: DraftableField, proposed_value: Any) -> str | None:
    if field.kind in {"select", "radio"} and field.allowed_values:
        if str(proposed_value) not in field.allowed_values:
            return "proposed value is not one of the mocked fixture options"
    if field.kind == "checkbox" and not isinstance(proposed_value, bool):
        return "checkbox draft value must be boolean"
    if field.kind in {"text", "textarea", "date", "number", "email", "tel", "select", "radio"}:
        if not isinstance(proposed_value, (str, int, float)):
            return "draft value must be scalar text-compatible data"
    return None


def _preview_action(field: DraftableField, proposed_value: Any) -> dict[str, Any]:
    return {
        "classification": DraftActionClassification.REVERSIBLE_DRAFT_EDIT.value,
        "operation": "fill" if field.kind != "checkbox" else "check" if proposed_value else "uncheck",
        "fieldId": field.field_id,
        "fieldKind": field.kind,
        "selectorBasis": field.selector_basis.to_json(),
        "sourceRequirementId": field.source_requirement_id,
        "beforeRedactedValue": REDACTED_VALUE,
        "afterPreviewValue": _redact_preview_value(proposed_value),
        "requiresExactUserConfirmation": False,
        "browserExecution": "not_performed",
    }


def _redact_preview_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return REDACTED_VALUE


def _optional_string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text.strip() else None
