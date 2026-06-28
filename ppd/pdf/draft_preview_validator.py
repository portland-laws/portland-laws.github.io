"""Local-only PDF draft preview validation for PP&D synthetic fixtures.

The validator intentionally does not write PDFs, upload documents, submit forms, or
inspect private user files beyond the explicit paths passed by a caller. It is a
small guardrail used to prove that a draft preview request is limited to known
synthetic fixture fields before later work adds real PDF filling support.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

_ALLOWED_FIELD_TYPES = {"text", "checkbox", "date", "choice"}
_BLOCKED_NAME_TOKENS = (
    "acknowledge",
    "certify",
    "certification",
    "pay",
    "payment",
    "schedule",
    "signature",
    "submit",
    "upload",
)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class DraftField:
    """A synthetic form field that may be shown in a local draft preview."""

    name: str
    field_type: str
    required: bool = False
    draftable: bool = True
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class FieldPreview:
    """Validated draft value for one field."""

    name: str
    field_type: str
    value: object


@dataclass(frozen=True)
class DraftPreviewValidationResult:
    """Result of a local-only draft preview validation."""

    ok: bool
    document_id: str
    field_previews: tuple[FieldPreview, ...]
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "document_id": self.document_id,
            "field_previews": [
                {"name": item.name, "field_type": item.field_type, "value": item.value}
                for item in self.field_previews
            ],
            "warnings": list(self.warnings),
            "errors": list(self.errors),
        }


def validate_pdf_draft_preview(
    pdf_path: Path | str,
    form_fixture_path: Path | str,
    draft_values: Mapping[str, object],
) -> DraftPreviewValidationResult:
    """Validate a draft preview request against a synthetic PDF/form fixture.

    This function is intentionally conservative. A request is accepted only when:
    - the PDF is a minimal parseable PDF-like fixture, not encrypted/scripted;
    - the form fixture declares itself synthetic;
    - every draft value targets a known draftable field;
    - values match simple deterministic field type checks.
    """

    pdf = Path(pdf_path)
    form_fixture = Path(form_fixture_path)
    errors: list[str] = []
    warnings: list[str] = []
    previews: list[FieldPreview] = []

    pdf_bytes = _read_pdf_fixture(pdf, errors)
    payload = _read_form_fixture(form_fixture, errors)
    document_id = _document_id(payload)
    fields = _fields_from_payload(payload, errors)

    if errors:
        return DraftPreviewValidationResult(False, document_id, (), tuple(warnings), tuple(errors))

    _validate_pdf_bytes(pdf_bytes, errors)
    field_by_name = {field.name: field for field in fields}

    for name, value in draft_values.items():
        field = field_by_name.get(name)
        if field is None:
            errors.append(f"unknown draft field: {name}")
            continue
        if not field.draftable or _looks_consequential(name):
            errors.append(f"field is not draftable in local preview: {name}")
            continue
        coerced = _coerce_value(field, value, errors)
        if coerced is not None:
            previews.append(FieldPreview(name=field.name, field_type=field.field_type, value=coerced))

    for field in fields:
        if field.required and field.name not in draft_values:
            warnings.append(f"required fixture field is missing from preview: {field.name}")

    return DraftPreviewValidationResult(
        ok=not errors,
        document_id=document_id,
        field_previews=tuple(previews),
        warnings=tuple(warnings),
        errors=tuple(errors),
    )


def _read_pdf_fixture(path: Path, errors: list[str]) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        errors.append(f"could not read PDF fixture {path.name}: {exc}")
        return b""


def _read_form_fixture(path: Path, errors: list[str]) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"could not read form fixture {path.name}: {exc}")
        return {}
    if not isinstance(payload, dict):
        errors.append("form fixture root must be an object")
        return {}
    if payload.get("fixture_kind") != "synthetic_pdf_form":
        errors.append("form fixture must declare fixture_kind=synthetic_pdf_form")
    return payload


def _document_id(payload: Mapping[str, Any]) -> str:
    value = payload.get("document_id")
    return value if isinstance(value, str) and value else "unknown-document"


def _fields_from_payload(payload: Mapping[str, Any], errors: list[str]) -> tuple[DraftField, ...]:
    raw_fields = payload.get("fields")
    if not isinstance(raw_fields, list):
        errors.append("form fixture fields must be a list")
        return ()

    fields: list[DraftField] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_fields):
        if not isinstance(raw, dict):
            errors.append(f"field {index} must be an object")
            continue
        name = raw.get("name")
        field_type = raw.get("type")
        if not isinstance(name, str) or not name:
            errors.append(f"field {index} is missing a name")
            continue
        if name in seen:
            errors.append(f"duplicate field name: {name}")
            continue
        if field_type not in _ALLOWED_FIELD_TYPES:
            errors.append(f"unsupported field type for {name}: {field_type}")
            continue
        raw_options = raw.get("options", [])
        if raw_options is None:
            raw_options = []
        if not isinstance(raw_options, list) or not all(isinstance(item, str) for item in raw_options):
            errors.append(f"options for {name} must be strings")
            continue
        seen.add(name)
        fields.append(
            DraftField(
                name=name,
                field_type=field_type,
                required=bool(raw.get("required", False)),
                draftable=bool(raw.get("draftable", True)),
                options=tuple(raw_options),
            )
        )
    return tuple(fields)


def _validate_pdf_bytes(pdf_bytes: bytes, errors: list[str]) -> None:
    if not pdf_bytes.startswith(b"%PDF-"):
        errors.append("PDF fixture does not start with a PDF header")
    if b"%%EOF" not in pdf_bytes[-1024:]:
        errors.append("PDF fixture does not contain an EOF marker")
    lower = pdf_bytes.lower()
    if b"/encrypt" in lower:
        errors.append("encrypted PDFs are not valid draft preview fixtures")
    if b"/javascript" in lower or b"/js" in lower:
        errors.append("scripted PDFs are not valid draft preview fixtures")


def _looks_consequential(name: str) -> bool:
    lowered = name.lower()
    return any(token in lowered for token in _BLOCKED_NAME_TOKENS)


def _coerce_value(field: DraftField, value: object, errors: list[str]) -> object | None:
    if field.field_type == "text":
        if not isinstance(value, str):
            errors.append(f"text field {field.name} requires a string")
            return None
        return value
    if field.field_type == "checkbox":
        if not isinstance(value, bool):
            errors.append(f"checkbox field {field.name} requires a boolean")
            return None
        return value
    if field.field_type == "date":
        if not isinstance(value, str) or not _DATE_RE.match(value):
            errors.append(f"date field {field.name} requires YYYY-MM-DD")
            return None
        return value
    if field.field_type == "choice":
        if not isinstance(value, str):
            errors.append(f"choice field {field.name} requires a string")
            return None
        if field.options and value not in field.options:
            errors.append(f"choice field {field.name} received unsupported option: {value}")
            return None
        return value
    errors.append(f"unsupported field type for {field.name}: {field.field_type}")
    return None
