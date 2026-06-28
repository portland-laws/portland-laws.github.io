from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


REQUIRED_TEMPLATE_KIND = "devhub_attended_pilot_evidence_template"

FORBIDDEN_ARTIFACT_FIELDS = frozenset(
    {
        "auth_state",
        "browser_trace",
        "cookies",
        "downloaded_documents",
        "har_files",
        "local_storage",
        "raw_authenticated_text",
        "raw_dom",
        "screenshots",
        "session_storage",
        "storage_state",
    }
)
FORBIDDEN_ACTION_FIELDS = frozenset(
    {
        "automated_login",
        "captcha_automation",
        "consequential_control_activation",
        "credential_capture",
        "mfa_automation",
    }
)
PRIVATE_VALUE_PATTERNS = (
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b\d{3}[-. ]\d{3}[-. ]\d{4}\b"),
    re.compile(r"\b(password|secret|token|set-cookie|authorization)\s*[:=]", re.IGNORECASE),
    re.compile(r"\b\d{1,6}\s+[A-Za-z0-9 .'-]+\s+(Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln)\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class AttendedEvidenceValidationResult:
    ok: bool
    errors: tuple[str, ...]


def load_attended_evidence_template(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("attended evidence template must be a JSON object")
    return value


def validate_attended_evidence_template(template: Mapping[str, Any]) -> AttendedEvidenceValidationResult:
    errors: list[str] = []

    _require(errors, template.get("template_kind") == REQUIRED_TEMPLATE_KIND, "template_kind must identify attended DevHub pilot evidence")
    _require(errors, template.get("attended_user_login_only") is True, "login must be attended by the user only")
    _require(errors, template.get("claims_login_was_automated") is False, "template must not claim login was automated")
    _require(errors, template.get("stores_private_values") is False, "template must reject private values")
    _require(errors, template.get("redaction_attestation_present") is True, "template must include redaction attestation")
    _require(errors, bool(_text(template.get("post_action_hardening_notes")).strip()), "template must include post-action hardening notes")

    artifacts = _mapping(template.get("stored_browser_artifacts"))
    for field in sorted(FORBIDDEN_ARTIFACT_FIELDS):
        _require(errors, artifacts.get(field) is False, f"stored browser artifact is not allowed: {field}")

    controls = _mapping(template.get("automation_boundaries"))
    for field in sorted(FORBIDDEN_ACTION_FIELDS):
        _require(errors, controls.get(field) is False, f"forbidden automation or consequential control is not allowed: {field}")

    for path, value in _walk(template):
        if isinstance(value, str) and _contains_private_value(value):
            errors.append(f"{path} contains private value material")

    return AttendedEvidenceValidationResult(ok=not errors, errors=tuple(errors))


def assert_valid_attended_evidence_template(template: Mapping[str, Any]) -> None:
    result = validate_attended_evidence_template(template)
    if not result.ok:
        raise AssertionError("; ".join(result.errors))


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value
    return ""


def _require(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def _contains_private_value(value: str) -> bool:
    return any(pattern.search(value) for pattern in PRIVATE_VALUE_PATTERNS)


def _walk(value: Any, path: str = "$. ") -> tuple[tuple[str, Any], ...]:
    normalized_path = path.replace("$. ", "$").rstrip(".")
    items = [(normalized_path, value)]
    if isinstance(value, Mapping):
        for key, child in value.items():
            items.extend(_walk(child, f"{normalized_path}.{key}"))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            items.extend(_walk(child, f"{normalized_path}[{index}]"))
    return tuple(items)
