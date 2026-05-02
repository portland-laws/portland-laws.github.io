"""Fixture-only DevHub Playwright form state contracts.

These contracts describe mocked or manually redacted DevHub form states for
selector and missing-information validation. They intentionally store semantic
Playwright selector bases instead of browser traces, screenshots, authentication
state, raw HTML, or private user values.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Mapping, Optional
from urllib.parse import urlparse


REDACTED_VALUES = {"[REDACTED]", "[EMPTY]", "[SELECTED_OPTION_REDACTED]", "[CHECKED_REDACTED]"}
PRIVATE_VALUE_RE = re.compile(
    r"(" 
    r"[^@\s]+@[^@\s]+\.[^@\s]+|"
    r"\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b|"
    r"\b\d{5}\s+[A-Za-z0-9 .'-]+\b|"
    r"password|token|cookie|secret|storage[_-]?state|auth[_-]?state"
    r")",
    re.IGNORECASE,
)


class DevHubFieldRequirementStatus(str, Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    CONDITIONALLY_REQUIRED = "conditionally_required"
    UNKNOWN = "unknown"


class DevHubFieldRole(str, Enum):
    TEXTBOX = "textbox"
    COMBOBOX = "combobox"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SPINBUTTON = "spinbutton"
    BUTTON = "button"
    LINK = "link"


@dataclass(frozen=True)
class DevHubUrlState:
    stable_url: str
    state_name: str
    path: str
    query_state: Optional[str] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        parsed = urlparse(self.stable_url)
        if parsed.scheme != "https":
            errors.append("urlState.stableUrl must be an HTTPS URL")
        if parsed.netloc != "devhub.portlandoregon.gov":
            errors.append("urlState.stableUrl must stay on devhub.portlandoregon.gov")
        if parsed.fragment:
            errors.append("urlState.stableUrl must not include a fragment")
        if not self.state_name.strip():
            errors.append("urlState.stateName is required")
        if not self.path.startswith("/"):
            errors.append("urlState.path must be a URL path beginning with /")
        if parsed.path != self.path:
            errors.append("urlState.path must match stableUrl path")
        if self.query_state is not None and self.query_state not in REDACTED_VALUES:
            errors.append("urlState.queryState must be redacted when present")
        return errors


@dataclass(frozen=True)
class DevHubSelectorBasis:
    accessible_name: str
    label_text: str
    role: DevHubFieldRole
    nearby_heading: str
    url_state: DevHubUrlState
    playwright_locator: str

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.accessible_name.strip():
            errors.append("selectorBasis.accessibleName is required")
        if not self.label_text.strip():
            errors.append("selectorBasis.labelText is required")
        if not self.nearby_heading.strip():
            errors.append("selectorBasis.nearbyHeading is required")
        if not self.playwright_locator.strip():
            errors.append("selectorBasis.playwrightLocator is required")
        if "getByRole" not in self.playwright_locator:
            errors.append("selectorBasis.playwrightLocator must use an accessible role selector")
        if self.role.value not in self.playwright_locator:
            errors.append("selectorBasis.playwrightLocator must include the field role")
        if self.accessible_name not in self.playwright_locator:
            errors.append("selectorBasis.playwrightLocator must include the accessible name")
        errors.extend(self.url_state.validate())
        return errors


@dataclass(frozen=True)
class DevHubRedactedValue:
    status: str
    value: str

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.status not in {"redacted", "empty", "selected_redacted", "checked_redacted"}:
            errors.append("redactedValue.status has an invalid value")
        if self.value not in REDACTED_VALUES:
            errors.append("redactedValue.value must be an approved redaction token")
        if PRIVATE_VALUE_RE.search(self.value):
            errors.append("redactedValue.value appears to contain private data")
        return errors


@dataclass(frozen=True)
class DevHubFormFieldState:
    id: str
    selector_basis: DevHubSelectorBasis
    requirement_status: DevHubFieldRequirementStatus
    redacted_value: DevHubRedactedValue
    validation_message: Optional[str] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("field id is required")
        errors.extend(self.selector_basis.validate())
        errors.extend(self.redacted_value.validate())
        if self.validation_message is not None and PRIVATE_VALUE_RE.search(self.validation_message):
            errors.append(f"field {self.id} validationMessage appears to contain private data")
        return errors


@dataclass(frozen=True)
class DevHubFormStateFixture:
    schema_version: int
    fixture_kind: str
    captured_from: str
    generated_at: str
    form_state_id: str
    form_heading: str
    url_state: DevHubUrlState
    fields: tuple[DevHubFormFieldState, ...]

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.schema_version != 1:
            errors.append("schemaVersion must be 1")
        if self.fixture_kind != "devhub_playwright_form_state":
            errors.append("fixtureKind must be devhub_playwright_form_state")
        if self.captured_from != "mocked_redacted_fixture":
            errors.append("capturedFrom must be mocked_redacted_fixture")
        if not self.generated_at.endswith("Z"):
            errors.append("generatedAt must be an ISO UTC timestamp ending in Z")
        if not self.form_state_id.strip():
            errors.append("formStateId is required")
        if not self.form_heading.strip():
            errors.append("formHeading is required")
        errors.extend(self.url_state.validate())
        if not self.fields:
            errors.append("at least one form field is required")
        seen_ids: set[str] = set()
        for field in self.fields:
            if field.id in seen_ids:
                errors.append(f"duplicate field id {field.id}")
            seen_ids.add(field.id)
            errors.extend(f"field {field.id}: {error}" for error in field.validate())
            if field.selector_basis.url_state != self.url_state:
                errors.append(f"field {field.id}: selector URL state must match fixture URL state")
        return errors


def devhub_form_state_fixture_from_dict(data: Mapping[str, Any]) -> DevHubFormStateFixture:
    url_state = _url_state_from_dict(_mapping(data.get("urlState")))
    fields = tuple(_field_from_dict(item) for item in data.get("fields", ()))
    return DevHubFormStateFixture(
        schema_version=int(data.get("schemaVersion", 0)),
        fixture_kind=str(data.get("fixtureKind", "")),
        captured_from=str(data.get("capturedFrom", "")),
        generated_at=str(data.get("generatedAt", "")),
        form_state_id=str(data.get("formStateId", "")),
        form_heading=str(data.get("formHeading", "")),
        url_state=url_state,
        fields=fields,
    )


def _field_from_dict(data: Mapping[str, Any]) -> DevHubFormFieldState:
    selector_data = _mapping(data.get("selectorBasis"))
    redacted_value_data = _mapping(data.get("redactedValue"))
    return DevHubFormFieldState(
        id=str(data.get("id", "")),
        selector_basis=DevHubSelectorBasis(
            accessible_name=str(selector_data.get("accessibleName", "")),
            label_text=str(selector_data.get("labelText", "")),
            role=DevHubFieldRole(str(selector_data.get("role", ""))),
            nearby_heading=str(selector_data.get("nearbyHeading", "")),
            url_state=_url_state_from_dict(_mapping(selector_data.get("urlState"))),
            playwright_locator=str(selector_data.get("playwrightLocator", "")),
        ),
        requirement_status=DevHubFieldRequirementStatus(str(data.get("requirementStatus", ""))),
        redacted_value=DevHubRedactedValue(
            status=str(redacted_value_data.get("status", "")),
            value=str(redacted_value_data.get("value", "")),
        ),
        validation_message=data.get("validationMessage"),
    )


def _url_state_from_dict(data: Mapping[str, Any]) -> DevHubUrlState:
    query_state = data.get("queryState")
    return DevHubUrlState(
        stable_url=str(data.get("stableUrl", "")),
        state_name=str(data.get("stateName", "")),
        path=str(data.get("path", "")),
        query_state=None if query_state is None else str(query_state),
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}
