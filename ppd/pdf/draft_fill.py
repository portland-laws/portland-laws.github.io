"""Real local PDF draft filling for PP&D form previews.

The filler writes a user-controlled draft output PDF from a local input PDF and
field-value map. It does not upload the result, submit a permit, certify a
statement, pay fees, or download source documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, TextStringObject


FORBIDDEN_OUTPUT_PARTS = {
    "private",
    "raw",
    "downloads",
    "traces",
    "screenshots",
}


@dataclass(frozen=True)
class PdfDraftFillRequest:
    input_pdf: Path
    output_pdf: Path
    field_values: Mapping[str, str | bool | int | float]
    allow_overwrite: bool = False
    metadata: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class PdfDraftFillResult:
    status: str
    output_pdf: Path
    filled_fields: tuple[str, ...]
    errors: tuple[str, ...]
    official_upload_performed: bool = False
    official_submission_performed: bool = False

    @property
    def ok(self) -> bool:
        return self.status == "filled"


def fill_pdf_draft(request: PdfDraftFillRequest) -> PdfDraftFillResult:
    """Fill a local PDF form draft using pypdf."""

    errors = validate_pdf_draft_fill_request(request)
    if errors:
        return PdfDraftFillResult(
            status="refused",
            output_pdf=request.output_pdf,
            filled_fields=(),
            errors=tuple(errors),
        )

    reader = PdfReader(str(request.input_pdf))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    if reader.trailer.get("/Root", {}).get("/AcroForm") is not None:
        writer._root_object.update({NameObject("/AcroForm"): reader.trailer["/Root"]["/AcroForm"]})
        writer.set_need_appearances_writer(True)

    normalized_values = {
        str(name): _pdf_value(value)
        for name, value in request.field_values.items()
    }
    for page in writer.pages:
        writer.update_page_form_field_values(page, normalized_values)
    _update_widget_values(writer, normalized_values)

    if request.metadata:
        writer.add_metadata({str(key): str(value) for key, value in request.metadata.items()})

    request.output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with request.output_pdf.open("wb") as output_file:
        writer.write(output_file)

    return PdfDraftFillResult(
        status="filled",
        output_pdf=request.output_pdf,
        filled_fields=tuple(sorted(normalized_values)),
        errors=(),
    )


def validate_pdf_draft_fill_request(request: PdfDraftFillRequest) -> list[str]:
    errors: list[str] = []
    if not request.input_pdf.is_file():
        errors.append("input_pdf must be an existing local PDF")
    if request.input_pdf.suffix.lower() != ".pdf":
        errors.append("input_pdf must have .pdf extension")
    if request.output_pdf.suffix.lower() != ".pdf":
        errors.append("output_pdf must have .pdf extension")
    if request.output_pdf.exists() and not request.allow_overwrite:
        errors.append("output_pdf already exists and allow_overwrite is false")
    if not request.field_values:
        errors.append("field_values must include at least one PDF field")
    if _is_forbidden_output_path(request.output_pdf):
        errors.append("output_pdf must not be written under private, raw, trace, screenshot, or download paths")
    for field_name, value in request.field_values.items():
        if not str(field_name).strip():
            errors.append("PDF field names must not be blank")
        if value is None:
            errors.append(f"PDF field {field_name!r} value must not be None")
    return errors


def _pdf_value(value: str | bool | int | float) -> str:
    if isinstance(value, bool):
        return "Yes" if value else "Off"
    return str(value)


def _update_widget_values(writer: PdfWriter, values: Mapping[str, str]) -> None:
    for page in writer.pages:
        annotations = page.get("/Annots", ())
        for annotation_ref in annotations:
            annotation = annotation_ref.get_object()
            field_name = annotation.get("/T")
            if field_name is None:
                continue
            field_key = str(field_name)
            if field_key in values:
                annotation.update({NameObject("/V"): TextStringObject(values[field_key])})


def _is_forbidden_output_path(path: Path) -> bool:
    parts = {part.strip().lower() for part in path.parts}
    return bool(parts.intersection(FORBIDDEN_OUTPUT_PARTS))
