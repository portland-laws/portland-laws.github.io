"""Reversible PP&D draft-assistance orchestration.

This module intentionally prepares attended save-for-later draft guidance only.
It does not execute DevHub uploads, submissions, certifications, cancellations,
inspection scheduling, or payments.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

REFUSED_ACTIONS = frozenset(
    {
        "upload",
        "submit",
        "certify",
        "cancel",
        "inspection",
        "schedule_inspection",
        "payment",
        "pay",
    }
)

SAFE_ACTIONS = frozenset({"draft", "preview", "save_for_later"})

SENSITIVE_FACT_KEYS = (
    "password",
    "token",
    "secret",
    "ssn",
    "social_security",
    "card",
    "credit_card",
    "cvv",
    "bank",
)


@dataclass(frozen=True)
class FieldManifest:
    """Small DevHub field manifest used for deterministic draft planning."""

    source: str
    fields: tuple[str, ...]
    required: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "FieldManifest":
        source = str(value.get("source", "unknown"))
        fields = tuple(str(item) for item in value.get("fields", ()))
        required = tuple(str(item) for item in value.get("required", ()))
        return cls(source=source, fields=fields, required=required)


@dataclass(frozen=True)
class PdfPreview:
    """Local preview metadata for a PDF or rendered text sidecar."""

    path: str
    exists: bool
    size_bytes: int | None = None

    @classmethod
    def from_local_path(cls, path: str | Path) -> "PdfPreview":
        preview_path = Path(path)
        if not preview_path.exists() or not preview_path.is_file():
            return cls(path=str(preview_path), exists=False)
        return cls(path=str(preview_path), exists=True, size_bytes=preview_path.stat().st_size)


@dataclass(frozen=True)
class DraftAssistanceRequest:
    """Inputs for a reversible attended draft-assistance plan."""

    user_facts: Mapping[str, Any]
    manifests: Sequence[FieldManifest]
    pdf_previews: Sequence[PdfPreview] = ()
    requested_actions: Sequence[str] = ("draft",)


@dataclass(frozen=True)
class DraftAssistancePlan:
    """Output that callers can render for an attended operator."""

    redacted_facts: Mapping[str, Any]
    field_sources: Mapping[str, str]
    missing_required_fields: tuple[str, ...]
    pdf_previews: tuple[PdfPreview, ...]
    allowed_actions: tuple[str, ...]
    refused_actions: tuple[str, ...]
    attended_save_for_later: bool
    reversible: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)


def redact_user_facts(user_facts: Mapping[str, Any]) -> dict[str, Any]:
    """Return user facts with sensitive keys removed or masked."""

    redacted: dict[str, Any] = {}
    for key, value in user_facts.items():
        normalized = key.lower()
        if any(marker in normalized for marker in SENSITIVE_FACT_KEYS):
            redacted[key] = "[REDACTED]"
        else:
            redacted[key] = value
    return redacted


def _classify_actions(actions: Sequence[str]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    allowed: list[str] = []
    refused: list[str] = []
    for action in actions:
        normalized = action.strip().lower()
        if normalized in REFUSED_ACTIONS:
            refused.append(normalized)
        elif normalized in SAFE_ACTIONS:
            allowed.append(normalized)
        else:
            refused.append(normalized)
    return tuple(sorted(set(allowed))), tuple(sorted(set(refused)))


def build_draft_assistance_plan(request: DraftAssistanceRequest) -> DraftAssistancePlan:
    """Combine redacted facts, manifests, previews, and safe attended actions."""

    redacted = redact_user_facts(request.user_facts)
    field_sources: dict[str, str] = {}
    required_fields: set[str] = set()

    for manifest in request.manifests:
        for field_name in manifest.fields:
            field_sources.setdefault(field_name, manifest.source)
        required_fields.update(manifest.required)

    missing = tuple(sorted(field for field in required_fields if not redacted.get(field)))
    allowed, refused = _classify_actions(request.requested_actions)

    notes = [
        "Draft assistance is reversible and intended for attended operator review.",
        "Execution actions are refused by default; only save-for-later draft guidance is allowed.",
    ]
    if refused:
        notes.append("One or more requested actions were refused by safety policy.")

    return DraftAssistancePlan(
        redacted_facts=redacted,
        field_sources=field_sources,
        missing_required_fields=missing,
        pdf_previews=tuple(request.pdf_previews),
        allowed_actions=allowed,
        refused_actions=refused,
        attended_save_for_later="save_for_later" in allowed,
        notes=tuple(notes),
    )
