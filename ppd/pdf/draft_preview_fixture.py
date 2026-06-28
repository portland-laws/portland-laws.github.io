"""Deterministic PDF draft-preview fixture helpers.

This module intentionally works only with synthetic fixture dictionaries. It does
not open, parse, write, or mutate PDF binaries; callers provide fillable-field
metadata that has already been modeled for local preview tests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

BLOCKED_FIELD_PURPOSES = frozenset(
    {
        "certification",
        "signature",
        "submission",
        "upload",
        "payment",
    }
)


def load_preview_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed synthetic preview fixture from JSON."""
    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)
    if not isinstance(data, dict):
        raise ValueError("PDF draft-preview fixture must be a JSON object")
    return data


def analyze_preview_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    """Map synthetic user facts to synthetic field metadata for preview only.

    The returned report is safe to commit because it contains no PDF bytes,
    credentials, session state, screenshots, private local paths, or official
    submission artifacts.
    """
    facts = fixture.get("user_facts", {})
    fields = fixture.get("fillable_fields", [])

    if not isinstance(facts, dict):
        raise ValueError("fixture user_facts must be an object")
    if not isinstance(fields, list):
        raise ValueError("fixture fillable_fields must be a list")

    field_previews: list[dict[str, Any]] = []
    missing_facts: list[dict[str, str]] = []
    blocked_certification_fields: list[dict[str, str]] = []

    for field in fields:
        if not isinstance(field, dict):
            raise ValueError("each fillable field must be an object")

        field_name = _required_string(field, "field_name")
        fact_key = field.get("fact_key")
        purpose = str(field.get("purpose", "data_entry"))
        required = bool(field.get("required", False))
        fact_value = facts.get(fact_key) if isinstance(fact_key, str) else None
        has_value = _has_preview_value(fact_value)
        is_blocked = purpose in BLOCKED_FIELD_PURPOSES or bool(field.get("requires_confirmation", False))

        if required and isinstance(fact_key, str) and not has_value:
            missing_facts.append(
                {
                    "fact_key": fact_key,
                    "field_name": field_name,
                    "reason": "required synthetic fact is missing for preview mapping",
                }
            )

        if is_blocked:
            blocked_certification_fields.append(
                {
                    "field_name": field_name,
                    "purpose": purpose,
                    "reason": "field requires attended review and exact confirmation",
                }
            )

        field_previews.append(
            {
                "field_name": field_name,
                "fact_key": fact_key,
                "preview_value": fact_value if has_value and not is_blocked else None,
                "status": _field_status(required=required, has_value=has_value, is_blocked=is_blocked),
            }
        )

    return {
        "case_id": str(fixture.get("case_id", "synthetic-case")),
        "document_id": str(fixture.get("document_id", "synthetic-document")),
        "preview_only": True,
        "pdf_binary_io": False,
        "field_previews": field_previews,
        "missing_facts": missing_facts,
        "blocked_certification_fields": blocked_certification_fields,
        "next_safe_actions": ["ask_for_missing_facts", "show_local_preview_report"],
    }


def _field_status(*, required: bool, has_value: bool, is_blocked: bool) -> str:
    if is_blocked:
        return "blocked_requires_confirmation"
    if required and not has_value:
        return "missing_fact"
    if has_value:
        return "preview_mapped"
    return "not_required_blank"


def _has_preview_value(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _required_string(mapping: dict[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"fillable field missing required string: {key}")
    return value
