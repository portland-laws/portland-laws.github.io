"""DevHub workflow snapshot contracts for redacted, fixture-only tests.

These contracts model observed DevHub screen states without storing private
session state, screenshots, traces, credentials, or unredacted user values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


REDACTED_VALUE = "[REDACTED]"


class WorkflowFieldKind(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    DATE = "date"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SELECT = "select"
    FILE = "file"
    DISPLAY = "display"
    UNKNOWN = "unknown"


class WorkflowActionKind(str, Enum):
    NAVIGATE = "navigate"
    SAVE_DRAFT = "save_draft"
    CONTINUE = "continue"
    BACK = "back"
    CANCEL = "cancel"
    SUBMIT = "submit"
    UPLOAD = "upload"
    DOWNLOAD = "download"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SemanticSelector:
    role: str
    accessible_name: str
    label_text: Optional[str] = None
    nearby_heading: Optional[str] = None
    url_state: Optional[str] = None
    test_id: Optional[str] = None
    fallback_css: Optional[str] = None
    fallback_xpath: Optional[str] = None

    def validate(self, context: str) -> list[str]:
        errors: list[str] = []
        if not self.role.strip():
            errors.append(f"{context} selector role is required")
        if not self.accessible_name.strip():
            errors.append(f"{context} selector accessible_name is required")
        if not (self.label_text or self.nearby_heading or self.url_state or self.test_id):
            errors.append(f"{context} selector needs semantic context beyond role/name")
        if self.fallback_css and not self.fallback_css.strip():
            errors.append(f"{context} fallback_css must not be blank")
        if self.fallback_xpath and not self.fallback_xpath.strip():
            errors.append(f"{context} fallback_xpath must not be blank")
        return errors


@dataclass(frozen=True)
class WorkflowValidationMessage:
    id: str
    text: str
    severity: str
    field_id: Optional[str] = None
    selector: Optional[SemanticSelector] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("validation message id is required")
        if not self.text.strip():
            errors.append(f"validation message {self.id} text is required")
        if self.severity not in {"error", "warning", "info"}:
            errors.append(f"validation message {self.id} severity is invalid")
        if self.selector:
            errors.extend(self.selector.validate(f"validation message {self.id}"))
        return errors


@dataclass(frozen=True)
class WorkflowUploadControl:
    id: str
    label: str
    required: bool
    accepted_file_types: tuple[str, ...]
    max_file_size_hint: Optional[str] = None
    naming_rule_hint: Optional[str] = None
    selector: Optional[SemanticSelector] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("upload control id is required")
        if not self.label.strip():
            errors.append(f"upload control {self.id} label is required")
        if not self.accepted_file_types:
            errors.append(f"upload control {self.id} requires accepted_file_types")
        for file_type in self.accepted_file_types:
            if "/" not in file_type and not file_type.startswith("."):
                errors.append(f"upload control {self.id} has invalid file type hint {file_type}")
        if self.selector:
            errors.extend(self.selector.validate(f"upload control {self.id}"))
        return errors


@dataclass(frozen=True)
class WorkflowField:
    id: str
    label: str
    kind: WorkflowFieldKind
    required: bool
    selector: SemanticSelector
    value_state: str = REDACTED_VALUE
    options: tuple[str, ...] = field(default_factory=tuple)
    validation_message_ids: tuple[str, ...] = field(default_factory=tuple)
    description: Optional[str] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("field id is required")
        if not self.label.strip():
            errors.append(f"field {self.id} label is required")
        if self.value_state != REDACTED_VALUE:
            errors.append(f"field {self.id} value_state must be [REDACTED]")
        if self.kind in {WorkflowFieldKind.SELECT, WorkflowFieldKind.RADIO} and not self.options:
            errors.append(f"field {self.id} requires options")
        errors.extend(self.selector.validate(f"field {self.id}"))
        return errors


@dataclass(frozen=True)
class WorkflowAction:
    id: str
    label: str
    kind: WorkflowActionKind
    selector: SemanticSelector
    enabled: bool
    target_state_id: Optional[str] = None
    confirmation_required: bool = False

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("action id is required")
        if not self.label.strip():
            errors.append(f"action {self.id} label is required")
        if self.kind in {WorkflowActionKind.SUBMIT, WorkflowActionKind.UPLOAD, WorkflowActionKind.CANCEL} and not self.confirmation_required:
            errors.append(f"action {self.id} must require confirmation in fixtures")
        errors.extend(self.selector.validate(f"action {self.id}"))
        return errors


@dataclass(frozen=True)
class WorkflowNavigationEdge:
    from_state_id: str
    action_id: str
    to_state_id: str
    guard: str

    def validate(self, known_states: set[str]) -> list[str]:
        errors: list[str] = []
        if self.from_state_id not in known_states:
            errors.append(f"navigation edge from unknown state {self.from_state_id}")
        if self.to_state_id not in known_states:
            errors.append(f"navigation edge to unknown state {self.to_state_id}")
        if not self.action_id.strip():
            errors.append("navigation edge action_id is required")
        if not self.guard.strip():
            errors.append(f"navigation edge {self.from_state_id}->{self.to_state_id} guard is required")
        return errors


@dataclass(frozen=True)
class DevHubWorkflowState:
    id: str
    workflow: str
    url_pattern: str
    heading: str
    captured_at: str
    fields: tuple[WorkflowField, ...] = field(default_factory=tuple)
    actions: tuple[WorkflowAction, ...] = field(default_factory=tuple)
    validation_messages: tuple[WorkflowValidationMessage, ...] = field(default_factory=tuple)
    upload_controls: tuple[WorkflowUploadControl, ...] = field(default_factory=tuple)
    next_states: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("workflow state id is required")
        if not self.workflow.strip():
            errors.append(f"workflow state {self.id} workflow is required")
        if not self.url_pattern.startswith("https://devhub.portlandoregon.gov/"):
            errors.append(f"workflow state {self.id} url_pattern must be a DevHub HTTPS URL pattern")
        if not self.heading.strip():
            errors.append(f"workflow state {self.id} heading is required")
        if not self.captured_at.endswith("Z"):
            errors.append(f"workflow state {self.id} captured_at must end in Z")

        field_ids: set[str] = set()
        message_ids = {message.id for message in self.validation_messages}
        for field_item in self.fields:
            if field_item.id in field_ids:
                errors.append(f"workflow state {self.id} duplicate field id {field_item.id}")
            field_ids.add(field_item.id)
            errors.extend(field_item.validate())
            for message_id in field_item.validation_message_ids:
                if message_id not in message_ids:
                    errors.append(f"field {field_item.id} references unknown validation message {message_id}")

        action_ids: set[str] = set()
        for action in self.actions:
            if action.id in action_ids:
                errors.append(f"workflow state {self.id} duplicate action id {action.id}")
            action_ids.add(action.id)
            errors.extend(action.validate())

        for message in self.validation_messages:
            errors.extend(message.validate())
            if message.field_id and message.field_id not in field_ids:
                errors.append(f"validation message {message.id} references unknown field {message.field_id}")

        for upload in self.upload_controls:
            errors.extend(upload.validate())
        return errors


def _selector_from_dict(data: dict[str, Any]) -> SemanticSelector:
    return SemanticSelector(
        role=str(data.get("role", "")),
        accessible_name=str(data.get("accessibleName", "")),
        label_text=data.get("labelText"),
        nearby_heading=data.get("nearbyHeading"),
        url_state=data.get("urlState"),
        test_id=data.get("testId"),
        fallback_css=data.get("fallbackCss"),
        fallback_xpath=data.get("fallbackXpath"),
    )


def state_from_dict(data: dict[str, Any]) -> DevHubWorkflowState:
    messages = tuple(
        WorkflowValidationMessage(
            id=str(item.get("id", "")),
            text=str(item.get("text", "")),
            severity=str(item.get("severity", "")),
            field_id=item.get("fieldId"),
            selector=_selector_from_dict(item["selector"]) if isinstance(item.get("selector"), dict) else None,
        )
        for item in data.get("validationMessages", [])
    )
    fields = tuple(
        WorkflowField(
            id=str(item.get("id", "")),
            label=str(item.get("label", "")),
            kind=WorkflowFieldKind(str(item.get("kind", "unknown"))),
            required=bool(item.get("required", False)),
            selector=_selector_from_dict(item.get("selector", {})),
            value_state=str(item.get("valueState", "")),
            options=tuple(str(option) for option in item.get("options", [])),
            validation_message_ids=tuple(str(message_id) for message_id in item.get("validationMessageIds", [])),
            description=item.get("description"),
        )
        for item in data.get("fields", [])
    )
    actions = tuple(
        WorkflowAction(
            id=str(item.get("id", "")),
            label=str(item.get("label", "")),
            kind=WorkflowActionKind(str(item.get("kind", "unknown"))),
            selector=_selector_from_dict(item.get("selector", {})),
            enabled=bool(item.get("enabled", False)),
            target_state_id=item.get("targetStateId"),
            confirmation_required=bool(item.get("confirmationRequired", False)),
        )
        for item in data.get("actions", [])
    )
    uploads = tuple(
        WorkflowUploadControl(
            id=str(item.get("id", "")),
            label=str(item.get("label", "")),
            required=bool(item.get("required", False)),
            accepted_file_types=tuple(str(value) for value in item.get("acceptedFileTypes", [])),
            max_file_size_hint=item.get("maxFileSizeHint"),
            naming_rule_hint=item.get("namingRuleHint"),
            selector=_selector_from_dict(item["selector"]) if isinstance(item.get("selector"), dict) else None,
        )
        for item in data.get("uploadControls", [])
    )
    return DevHubWorkflowState(
        id=str(data.get("id", "")),
        workflow=str(data.get("workflow", "")),
        url_pattern=str(data.get("urlPattern", "")),
        heading=str(data.get("heading", "")),
        captured_at=str(data.get("capturedAt", "")),
        fields=fields,
        actions=actions,
        validation_messages=messages,
        upload_controls=uploads,
        next_states=tuple(str(state_id) for state_id in data.get("nextStates", [])),
    )


def edge_from_dict(data: dict[str, Any]) -> WorkflowNavigationEdge:
    return WorkflowNavigationEdge(
        from_state_id=str(data.get("fromStateId", "")),
        action_id=str(data.get("actionId", "")),
        to_state_id=str(data.get("toStateId", "")),
        guard=str(data.get("guard", "")),
    )
