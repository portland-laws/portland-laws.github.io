"""Local-only draft-fill queue for public PP&D PDF form manifests.

This module deliberately handles only public form manifests and redacted user
facts. It does not upload, submit, crawl, authenticate, or persist private
source documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence


class DraftFillQueueError(ValueError):
    """Raised when a local draft-fill job is unsafe or malformed."""


@dataclass(frozen=True)
class RedactedFact:
    """A user fact that has already been reduced to the value needed by a form."""

    key: str
    value: str
    redacted: bool = True

    def __post_init__(self) -> None:
        if not self.key or not isinstance(self.key, str):
            raise DraftFillQueueError("redacted fact key must be a non-empty string")
        if not isinstance(self.value, str):
            raise DraftFillQueueError("redacted fact value must be a string")
        if not self.redacted:
            raise DraftFillQueueError("draft-fill facts must be explicitly redacted")


@dataclass(frozen=True)
class DraftFillJob:
    """One local preview job for a public PP&D form manifest."""

    form_id: str
    manifest_path: Path
    output_pdf_path: Path
    facts: Sequence[RedactedFact] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.form_id:
            raise DraftFillQueueError("form_id is required")
        if self.output_pdf_path.suffix.lower() != ".pdf":
            raise DraftFillQueueError("output_pdf_path must point to a PDF preview")


@dataclass(frozen=True)
class DraftFillResult:
    """Result metadata for a generated local preview."""

    form_id: str
    template_pdf_path: Path
    output_pdf_path: Path
    field_count: int


def load_manifest(path: Path) -> dict[str, Any]:
    """Load a public PP&D form field manifest from JSON."""

    manifest_path = Path(path)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise DraftFillQueueError("manifest must be a JSON object")
    return data


def field_values_from_manifest(
    manifest: Mapping[str, Any], facts: Sequence[RedactedFact]
) -> dict[str, str]:
    """Map manifest PDF field names to redacted user fact values."""

    fact_values = {fact.key: fact.value for fact in facts}
    fields = manifest.get("fields")
    if not isinstance(fields, list):
        raise DraftFillQueueError("manifest must contain a fields list")

    values: dict[str, str] = {}
    for field_data in fields:
        if not isinstance(field_data, dict):
            raise DraftFillQueueError("each manifest field must be an object")
        field_name = field_data.get("name")
        fact_key = field_data.get("fact_key") or field_data.get("redacted_fact_key")
        if not isinstance(field_name, str) or not field_name:
            raise DraftFillQueueError("manifest field is missing a PDF field name")
        if not isinstance(fact_key, str) or not fact_key:
            continue
        if fact_key in fact_values:
            values[field_name] = fact_values[fact_key]
    return values


def run_draft_fill_job(job: DraftFillJob) -> DraftFillResult:
    """Run a local pypdf draft-fill preview job.

    The manifest must reference a local public template PDF using
    ``template_pdf_path`` or ``public_pdf_path``. URL templates are rejected so
    this queue never downloads or uploads documents.
    """

    manifest = load_manifest(job.manifest_path)
    template_value = manifest.get("template_pdf_path") or manifest.get("public_pdf_path")
    if not isinstance(template_value, str) or not template_value:
        raise DraftFillQueueError("manifest must reference a local public template PDF")
    if template_value.startswith(("http://", "https://")):
        raise DraftFillQueueError("draft-fill queue does not fetch remote PDFs")

    template_pdf_path = (job.manifest_path.parent / template_value).resolve()
    if template_pdf_path.suffix.lower() != ".pdf":
        raise DraftFillQueueError("manifest template must be a PDF")

    field_values = field_values_from_manifest(manifest, job.facts)
    filler = _load_pypdf_filler()
    job.output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    filler(template_pdf_path, job.output_pdf_path, field_values)
    return DraftFillResult(
        form_id=job.form_id,
        template_pdf_path=template_pdf_path,
        output_pdf_path=job.output_pdf_path,
        field_count=len(field_values),
    )


def _load_pypdf_filler() -> Callable[[Path, Path, Mapping[str, str]], None]:
    """Find the local pypdf draft filler without binding to one module name."""

    candidates = (
        "ppd.pdf.pypdf_draft_filler",
        "ppd.pdf.pypdf_draft_fill",
        "ppd.pdf.draft_filler",
    )
    for module_name in candidates:
        try:
            module = import_module(module_name)
        except ModuleNotFoundError:
            continue
        for function_name in ("fill_pdf_draft", "fill_draft_pdf", "fill_pdf"):
            function = getattr(module, function_name, None)
            if callable(function):
                return function
    raise DraftFillQueueError("no local pypdf draft filler is available")
