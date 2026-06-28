from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


REQUIRED_TEMPLATE_ID = "devhub-attended-pilot-evidence-template-v1"
REQUIRED_TEMPLATE_KIND = "fixture_first_attended_devhub_pilot_evidence_template"
REQUIRED_RUN_MODE = "fixture_first_manual_read_only_followup"

REQUIRED_SCOPE_FIELDS = (
    "operator_session_mode",
    "manual_read_only_session_only",
    "observation_started_at_redacted",
    "observation_finished_at_redacted",
    "surfaces_observed",
    "surfaces_excluded",
)
REQUIRED_HEADING_FIELDS = (
    "journal_event_id",
    "stable_surface_id",
    "redacted_heading_text",
    "heading_level",
    "observation_scope_id",
)
REQUIRED_LABEL_FIELDS = (
    "journal_event_id",
    "stable_surface_id",
    "redacted_label_text",
    "label_category",
    "observation_scope_id",
)
REQUIRED_STATUS_FIELDS = (
    "journal_event_id",
    "stable_surface_id",
    "status_category",
    "status_context",
    "observation_scope_id",
)
REQUIRED_ABORT_FIELDS = (
    "journal_event_id",
    "abort_condition_id",
    "abort_category",
    "redacted_operator_note",
    "observed_before_action",
)
REQUIRED_JOURNAL_FIELDS = (
    "journal_event_id",
    "event_type",
    "redacted_timestamp",
    "commit_safe",
    "stores_private_values",
    "stores_browser_artifacts",
)
REQUIRED_PROHIBITED_ARTIFACTS = (
    "cookies",
    "auth_state",
    "session_storage",
    "local_storage",
    "screenshots",
    "traces",
    "har_files",
    "raw_dom",
    "raw_authenticated_text",
    "private_field_values",
    "payment_details",
    "downloaded_documents",
    "local_private_file_paths",
)
REQUIRED_ABORT_TERMS = (
    "credential",
    "mfa",
    "captcha",
    "payment",
    "upload",
    "submit",
    "certify",
    "schedule",
    "cancel",
    "private field value",
    "browser artifact",
)
ALLOWED_JOURNAL_EVENT_TYPES = frozenset(
    {
        "DevHub attended preflight",
        "manual handoff",
        "redacted read-only observation",
        "refused action",
        "post-action hardening review",
        "completion evidence",
    }
)
FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b"),
    re.compile(r"\b\d{1,6}\s+[A-Za-z0-9 .'-]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln)\b", re.IGNORECASE),
    re.compile(r"\b(password|token|secret|cookie|set-cookie)\s*[:=]", re.IGNORECASE),
    re.compile(r"\b(storageState|localStorage|sessionStorage|HAR|trace\.zip)\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class EvidenceTemplateValidationResult:
    template_id: str
    ok: bool
    errors: tuple[str, ...]


def load_evidence_template(path: str | Path) -> dict[str, Any]:
    template_path = Path(path)
    with template_path.open("r", encoding="utf-8") as handle:
        template = json.load(handle)
    if not isinstance(template, dict):
        raise ValueError("evidence template must be a JSON object")
    return template


def validate_evidence_template(template: Mapping[str, Any]) -> EvidenceTemplateValidationResult:
    errors: list[str] = []
    template_id = _text(template.get("template_id"))

    _require(errors, template_id == REQUIRED_TEMPLATE_ID, "template_id must identify the attended pilot evidence template")
    _require(errors, template.get("template_kind") == REQUIRED_TEMPLATE_KIND, "template_kind must be fixture_first_attended_devhub_pilot_evidence_template")
    _require(errors, template.get("run_mode") == REQUIRED_RUN_MODE, "run_mode must be fixture_first_manual_read_only_followup")
    _require(errors, template.get("live_session_performed") is False, "committed template must not claim a live session was performed")
    _require(errors, template.get("read_only_only") is True, "template must be limited to read-only observations")
    _require(errors, template.get("allows_private_values") is False, "template must reject private values")
    _require(errors, template.get("allows_browser_artifacts") is False, "template must reject browser artifacts")

    _require_all_present(errors, _string_tuple(template.get("prohibited_artifacts")), REQUIRED_PROHIBITED_ARTIFACTS, "prohibited_artifacts")
    _require_all_terms(errors, _string_tuple(template.get("abort_conditions")), REQUIRED_ABORT_TERMS, "abort_conditions")

    sections = _mapping(template.get("evidence_sections"))
    _validate_section(errors, sections, "observation_scope", REQUIRED_SCOPE_FIELDS)
    _validate_section(errors, sections, "redacted_headings", REQUIRED_HEADING_FIELDS)
    _validate_section(errors, sections, "redacted_labels", REQUIRED_LABEL_FIELDS)
    _validate_section(errors, sections, "status_categories", REQUIRED_STATUS_FIELDS)
    _validate_section(errors, sections, "abort_conditions", REQUIRED_ABORT_FIELDS)
    _validate_section(errors, sections, "journal_event_ids", REQUIRED_JOURNAL_FIELDS)

    for event in _sequence(template.get("journal_event_templates")):
        event_map = _mapping(event)
        event_type = _text(event_map.get("event_type"))
        _require(errors, event_type in ALLOWED_JOURNAL_EVENT_TYPES, f"journal event type is not allowed: {event_type}")
        _require(errors, event_map.get("commit_safe") is True, f"journal event {event_type} must be commit-safe")
        _require(errors, event_map.get("stores_private_values") is False, f"journal event {event_type} must not store private values")
        _require(errors, event_map.get("stores_browser_artifacts") is False, f"journal event {event_type} must not store browser artifacts")

    for path, value in _walk(template):
        if isinstance(value, str) and _contains_forbidden_value(value):
            errors.append(f"{path} contains a private value or browser artifact marker")

    return EvidenceTemplateValidationResult(template_id=template_id, ok=not errors, errors=tuple(errors))


def assert_valid_evidence_template(template: Mapping[str, Any]) -> None:
    result = validate_evidence_template(template)
    if not result.ok:
        raise AssertionError("; ".join(result.errors))


def _validate_section(errors: list[str], sections: Mapping[str, Any], section_name: str, required_fields: tuple[str, ...]) -> None:
    section = _mapping(sections.get(section_name))
    _require(errors, section.get("record_private_values") is False, f"{section_name} must not record private values")
    _require(errors, section.get("record_browser_artifacts") is False, f"{section_name} must not record browser artifacts")
    _require_all_present(errors, _string_tuple(section.get("fields")), required_fields, f"{section_name}.fields")


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _sequence(value: Any) -> tuple[Any, ...]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return tuple(value)
    return ()


def _string_tuple(value: Any) -> tuple[str, ...]:
    return tuple(item for item in _sequence(value) if isinstance(item, str))


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return ""


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _require_all_present(errors: list[str], values: tuple[str, ...], required: tuple[str, ...], label: str) -> None:
    present = {value.casefold() for value in values}
    missing = [value for value in required if value.casefold() not in present]
    if missing:
        errors.append(f"{label} missing: " + ", ".join(missing))


def _require_all_terms(errors: list[str], values: tuple[str, ...], terms: tuple[str, ...], label: str) -> None:
    haystack = "\n".join(values).casefold()
    missing = [term for term in terms if term.casefold() not in haystack]
    if missing:
        errors.append(f"{label} missing required terms: " + ", ".join(missing))


def _walk(value: Any, path: str = "$") -> tuple[tuple[str, Any], ...]:
    items: list[tuple[str, Any]] = [(path, value)]
    if isinstance(value, Mapping):
        for key, child in value.items():
            items.extend(_walk(child, f"{path}.{key}"))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            items.extend(_walk(child, f"{path}[{index}]"))
    return tuple(items)


def _contains_forbidden_value(value: str) -> bool:
    return any(pattern.search(value) for pattern in FORBIDDEN_VALUE_PATTERNS)
