"""DevHub workflow recorder contracts.

These dataclasses model what a recorder may observe after a user-authorized
session exists. They are deliberately side-effect free and contain no browser
automation, login, submission, upload, payment, or scheduling behavior.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class DevHubWorkflowStateKind(str, Enum):
    PUBLIC_PORTAL = "public_portal"
    SIGN_IN_HANDOFF = "sign_in_handoff"
    ACCOUNT_HOME = "account_home"
    MY_PERMITS = "my_permits"
    DRAFT_REQUEST = "draft_request"
    APPLICATION_FORM = "application_form"
    DOCUMENT_UPLOAD = "document_upload"
    CORRECTIONS_UPLOAD = "corrections_upload"
    FEE_PAYMENT = "fee_payment"
    INSPECTION_SCHEDULING = "inspection_scheduling"
    REVIEW_STATUS = "review_status"
    UNKNOWN = "unknown"


class DevHubFieldKind(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SELECT = "select"
    FILE = "file"
    ACKNOWLEDGMENT = "acknowledgment"
    HIDDEN = "hidden"
    UNKNOWN = "unknown"


class DevHubActionKind(str, Enum):
    NAVIGATE = "navigate"
    READ_STATUS = "read_status"
    DOWNLOAD_OWN_DOCUMENT = "download_own_document"
    SAVE_DRAFT = "save_draft"
    FILL_FIELD = "fill_field"
    ATTACH_DRAFT_FILE = "attach_draft_file"
    OFFICIAL_UPLOAD = "official_upload"
    CERTIFY_ACKNOWLEDGMENT = "certify_acknowledgment"
    SUBMIT_APPLICATION = "submit_application"
    PAY_FEE = "pay_fee"
    ENTER_PAYMENT_DETAILS = "enter_payment_details"
    SCHEDULE_INSPECTION = "schedule_inspection"
    CANCEL_REQUEST = "cancel_request"
    OTHER = "other"


class DevHubSelectorKind(str, Enum):
    ROLE_NAME = "role_name"
    LABEL_TEXT = "label_text"
    HEADING_CONTEXT = "heading_context"
    TEST_ID = "test_id"
    CSS = "css"
    XPATH = "xpath"


@dataclass(frozen=True)
class DevHubSelector:
    kind: DevHubSelectorKind
    value: str
    description: str = ""


@dataclass(frozen=True)
class DevHubField:
    id: str
    label: str
    kind: DevHubFieldKind
    required: bool
    selector: Optional[DevHubSelector] = None
    help_text: str = ""
    options: tuple[str, ...] = field(default_factory=tuple)
    validation_messages: tuple[str, ...] = field(default_factory=tuple)
    redacted_value_present: bool = False

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("field id is required")
        if not self.label.strip():
            errors.append(f"field {self.id} label is required")
        if self.kind in {DevHubFieldKind.SELECT, DevHubFieldKind.RADIO} and not self.options:
            errors.append(f"field {self.id} must include options")
        return errors


@dataclass(frozen=True)
class DevHubWorkflowAction:
    id: str
    label: str
    kind: DevHubActionKind
    selector: Optional[DevHubSelector] = None
    enabled: bool = True
    confirmation_text: Optional[str] = None
    consequence_summary: str = ""
    next_state_ids: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("action id is required")
        if not self.label.strip():
            errors.append(f"action {self.id} label is required")
        consequential = {
            DevHubActionKind.OFFICIAL_UPLOAD,
            DevHubActionKind.CERTIFY_ACKNOWLEDGMENT,
            DevHubActionKind.SUBMIT_APPLICATION,
            DevHubActionKind.PAY_FEE,
            DevHubActionKind.ENTER_PAYMENT_DETAILS,
            DevHubActionKind.SCHEDULE_INSPECTION,
            DevHubActionKind.CANCEL_REQUEST,
        }
        if self.kind in consequential and not (self.confirmation_text or "").strip():
            errors.append(f"action {self.id} requires confirmation text")
        return errors


@dataclass(frozen=True)
class DevHubWorkflowState:
    id: str
    workflow: str
    kind: DevHubWorkflowStateKind
    url_pattern: str
    heading: str
    captured_at: str
    fields: tuple[DevHubField, ...] = field(default_factory=tuple)
    actions: tuple[DevHubWorkflowAction, ...] = field(default_factory=tuple)
    validation_messages: tuple[str, ...] = field(default_factory=tuple)
    next_state_ids: tuple[str, ...] = field(default_factory=tuple)
    private_values_redacted: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("state id is required")
        if not self.workflow.strip():
            errors.append("workflow is required")
        if not self.heading.strip():
            errors.append(f"state {self.id} heading is required")
        if not self.captured_at.strip():
            errors.append(f"state {self.id} captured_at is required")
        if not self.private_values_redacted:
            errors.append(f"state {self.id} must redact private values")

        field_ids = set()
        for field_item in self.fields:
            field_ids.add(field_item.id)
            errors.extend(field_item.validate())

        action_ids = set()
        for action in self.actions:
            action_ids.add(action.id)
            errors.extend(action.validate())

        if len(field_ids) != len(self.fields):
            errors.append(f"state {self.id} has duplicate field ids")
        if len(action_ids) != len(self.actions):
            errors.append(f"state {self.id} has duplicate action ids")
        return errors
