"""Deterministic permit-type taxonomy validation for PP&D DevHub routing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


DEVHUB_SUPPORTED = "devhub_supported"
DEVHUB_UNSUPPORTED = "devhub_unsupported"
EMAIL_MANUAL = "email_manual"
PUBLIC_REFERENCE_ONLY = "public_reference_only"

MANUAL_HANDOFF_CATEGORIES = frozenset(
    {DEVHUB_UNSUPPORTED, EMAIL_MANUAL, PUBLIC_REFERENCE_ONLY}
)

BROWSER_AUTOMATION_ALLOWED_CATEGORIES = frozenset({DEVHUB_SUPPORTED})


@dataclass(frozen=True)
class PermitTypeRoute:
    """A narrow routing record for a PP&D permit type."""

    permit_type_id: str
    label: str
    category: str
    routing: str
    browser_automation_allowed: bool
    source_hint: str

    @classmethod
    def from_mapping(cls, record: Mapping[str, Any]) -> "PermitTypeRoute":
        return cls(
            permit_type_id=_required_text(record, "permit_type_id"),
            label=_required_text(record, "label"),
            category=_required_text(record, "category"),
            routing=_required_text(record, "routing"),
            browser_automation_allowed=bool(record.get("browser_automation_allowed")),
            source_hint=_required_text(record, "source_hint"),
        )


def load_permit_type_routes(path: Path) -> list[PermitTypeRoute]:
    """Load permit-type routing records from a committed JSON fixture."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("permit_types")
    if not isinstance(records, list):
        raise ValueError("permit taxonomy fixture must contain a permit_types list")
    return [PermitTypeRoute.from_mapping(record) for record in records]


def validate_permit_type_routes(routes: Iterable[PermitTypeRoute]) -> list[str]:
    """Return validation errors for unsafe or incomplete permit routing records."""

    errors: list[str] = []
    seen_ids: set[str] = set()

    for route in routes:
        if route.permit_type_id in seen_ids:
            errors.append(f"duplicate permit_type_id: {route.permit_type_id}")
        seen_ids.add(route.permit_type_id)

        if route.category not in MANUAL_HANDOFF_CATEGORIES | BROWSER_AUTOMATION_ALLOWED_CATEGORIES:
            errors.append(
                f"{route.permit_type_id}: unsupported category {route.category!r}"
            )

        if route.category in MANUAL_HANDOFF_CATEGORIES:
            if route.routing != "manual_handoff":
                errors.append(
                    f"{route.permit_type_id}: {route.category} must route to manual_handoff"
                )
            if route.browser_automation_allowed:
                errors.append(
                    f"{route.permit_type_id}: {route.category} must not allow browser automation"
                )

        if route.category == DEVHUB_SUPPORTED:
            if route.routing == "manual_handoff":
                errors.append(
                    f"{route.permit_type_id}: DevHub-supported permits should not default to manual handoff"
                )
            if not route.browser_automation_allowed:
                errors.append(
                    f"{route.permit_type_id}: DevHub-supported permit must explicitly allow attended automation"
                )

    return errors


def _required_text(record: Mapping[str, Any], field_name: str) -> str:
    value = record.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"permit taxonomy record is missing text field {field_name}")
    return value
