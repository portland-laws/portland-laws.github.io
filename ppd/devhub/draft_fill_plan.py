"""Validation for reversible DevHub draft-fill planning fixtures.

The validator in this module is intentionally side-effect free. It checks a
committed plan fixture before any browser automation is allowed to fill DevHub
fields. The plan must be source-grounded, case-fact-grounded, attended,
reversible, and previewed by the user.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


SAFE_ACTION_TYPE = "devhub_field_fill"
CONSEQUENTIAL_ACTION_TYPES = {
    "account_create",
    "captcha",
    "certify",
    "mfa",
    "payment",
    "schedule_inspection",
    "submit",
    "upload",
}


@dataclass(frozen=True)
class DraftFillValidationResult:
    """Result returned by draft-fill plan validation."""

    allowed: bool
    errors: tuple[str, ...]

    def require_allowed(self) -> None:
        if not self.allowed:
            raise ValueError("DevHub draft-fill plan is not allowed: " + "; ".join(self.errors))


def load_draft_fill_plan(path: str | Path) -> dict[str, Any]:
    """Load a draft-fill planning fixture from JSON."""

    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("draft-fill plan fixture must be a JSON object")
    return data


def validate_draft_fill_plan(plan: Mapping[str, Any]) -> DraftFillValidationResult:
    """Validate that a DevHub draft-fill plan may proceed to field-fill only.

    This does not perform any DevHub automation. It only determines whether a
    reversible field-fill action is eligible for a later attended executor.
    """

    errors: list[str] = []

    action = _mapping(plan.get("action"), "action", errors)
    attendance = _mapping(plan.get("attendance"), "attendance", errors)
    preview = _mapping(plan.get("preview"), "preview", errors)
    fields = _sequence(plan.get("fields"), "fields", errors)
    evidence_ids = _indexed_ids(plan.get("source_evidence"), "source_evidence", "evidence_id", errors)
    fact_ids = _indexed_ids(plan.get("user_case_facts"), "user_case_facts", "fact_id", errors)

    action_type = action.get("action_type")
    if action_type != SAFE_ACTION_TYPE:
        errors.append(f"action.action_type must be {SAFE_ACTION_TYPE!r}")
    if action_type in CONSEQUENTIAL_ACTION_TYPES:
        errors.append(f"consequential action {action_type!r} is not allowed by draft-fill planning")
    if action.get("reversible") is not True:
        errors.append("action.reversible must be true")
    if action.get("requires_attendance") is not True:
        errors.append("action.requires_attendance must be true")
    if action.get("executor") not in {None, "planning_fixture_only"}:
        errors.append("action.executor must not name a live DevHub executor")

    if attendance.get("user_present") is not True:
        errors.append("attendance.user_present must be true")
    if attendance.get("mode") != "attended_user_session":
        errors.append("attendance.mode must be 'attended_user_session'")

    if preview.get("rendered") is not True:
        errors.append("preview.rendered must be true")
    if preview.get("acknowledged_by_user") is not True:
        errors.append("preview.acknowledged_by_user must be true")
    if not _non_empty_string(preview.get("preview_id")):
        errors.append("preview.preview_id is required")

    if not fields:
        errors.append("fields must include at least one draft-fill value")

    for index, raw_field in enumerate(fields):
        if not isinstance(raw_field, Mapping):
            errors.append(f"fields[{index}] must be an object")
            continue
        field_id = raw_field.get("field_id")
        field_name = field_id if _non_empty_string(field_id) else f"fields[{index}]"
        if not _non_empty_string(field_id):
            errors.append(f"fields[{index}].field_id is required")
        if raw_field.get("fill_action") != "set_draft_value":
            errors.append(f"{field_name}.fill_action must be 'set_draft_value'")
        if raw_field.get("value") in (None, ""):
            errors.append(f"{field_name}.value is required")
        if raw_field.get("reversible") is not True:
            errors.append(f"{field_name}.reversible must be true")

        field_evidence_ids = _string_list(raw_field.get("source_evidence_ids"), f"{field_name}.source_evidence_ids", errors)
        field_fact_ids = _string_list(raw_field.get("user_case_fact_ids"), f"{field_name}.user_case_fact_ids", errors)
        if not field_evidence_ids:
            errors.append(f"{field_name}.source_evidence_ids must include at least one evidence ID")
        if not field_fact_ids:
            errors.append(f"{field_name}.user_case_fact_ids must include at least one fact ID")

        for evidence_id in field_evidence_ids:
            if evidence_id not in evidence_ids:
                errors.append(f"{field_name}.source_evidence_ids references unknown evidence ID {evidence_id!r}")
        for fact_id in field_fact_ids:
            if fact_id not in fact_ids:
                errors.append(f"{field_name}.user_case_fact_ids references unknown fact ID {fact_id!r}")

    return DraftFillValidationResult(allowed=not errors, errors=tuple(errors))


def require_draft_fill_allowed(plan: Mapping[str, Any]) -> None:
    """Raise ValueError unless the plan is eligible for field-fill."""

    validate_draft_fill_plan(plan).require_allowed()


def _mapping(value: Any, name: str, errors: list[str]) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    errors.append(f"{name} must be an object")
    return {}


def _sequence(value: Any, name: str, errors: list[str]) -> Sequence[Any]:
    if isinstance(value, list):
        return value
    errors.append(f"{name} must be a list")
    return []


def _indexed_ids(value: Any, name: str, key: str, errors: list[str]) -> set[str]:
    items = _sequence(value, name, errors)
    indexed: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            errors.append(f"{name}[{index}] must be an object")
            continue
        item_id = item.get(key)
        if not _non_empty_string(item_id):
            errors.append(f"{name}[{index}].{key} is required")
            continue
        indexed.add(item_id)
    return indexed


def _string_list(value: Any, name: str, errors: list[str]) -> tuple[str, ...]:
    if not isinstance(value, list):
        errors.append(f"{name} must be a list")
        return ()
    strings: list[str] = []
    for index, item in enumerate(value):
        if not _non_empty_string(item):
            errors.append(f"{name}[{index}] must be a non-empty string")
            continue
        strings.append(item)
    return tuple(strings)


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
