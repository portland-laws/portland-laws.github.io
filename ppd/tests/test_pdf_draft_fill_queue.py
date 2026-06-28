from pathlib import Path

import pytest

from ppd.pdf import draft_fill_queue
from ppd.pdf.draft_fill_queue import (
    DraftFillJob,
    DraftFillQueueError,
    RedactedFact,
    field_values_from_manifest,
    load_manifest,
    run_draft_fill_job,
)


FIXTURES = Path(__file__).parent / "fixtures" / "pdf"


def test_field_values_map_public_manifest_to_redacted_facts() -> None:
    manifest = load_manifest(FIXTURES / "simple_manifest.json")
    values = field_values_from_manifest(
        manifest,
        (
            RedactedFact("applicant_name", "Ada Example"),
            RedactedFact("project_address", "100 SW Main St"),
        ),
    )

    assert values == {
        "ApplicantName": "Ada Example",
        "ProjectAddress": "100 SW Main St",
    }


def test_rejects_unredacted_fact() -> None:
    with pytest.raises(DraftFillQueueError):
        RedactedFact("applicant_name", "Ada Example", redacted=False)


def test_run_job_invokes_local_pypdf_filler(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls = []

    def fake_filler(template_pdf_path: Path, output_pdf_path: Path, values: dict[str, str]) -> None:
        calls.append((template_pdf_path, output_pdf_path, dict(values)))
        output_pdf_path.write_bytes(b"%PDF-1.4\n% local draft preview\n")

    monkeypatch.setattr(draft_fill_queue, "_load_pypdf_filler", lambda: fake_filler)
    template_path = FIXTURES / "sample-public-form.pdf"
    template_path.write_bytes(b"%PDF-1.4\n% fixture public template\n")

    try:
        output_path = tmp_path / "preview.pdf"
        result = run_draft_fill_job(
            DraftFillJob(
                form_id="sample-public-ppd-form",
                manifest_path=FIXTURES / "simple_manifest.json",
                output_pdf_path=output_path,
                facts=(RedactedFact("applicant_name", "Ada Example"),),
            )
        )
    finally:
        template_path.unlink(missing_ok=True)

    assert result.form_id == "sample-public-ppd-form"
    assert result.field_count == 1
    assert output_path.exists()
    assert calls == [
        (
            template_path.resolve(),
            output_path,
            {"ApplicantName": "Ada Example"},
        )
    ]


def test_remote_template_is_rejected(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        '{"template_pdf_path":"https://example.test/form.pdf","fields":[]}',
        encoding="utf-8",
    )

    with pytest.raises(DraftFillQueueError):
        run_draft_fill_job(
            DraftFillJob(
                form_id="remote-template",
                manifest_path=manifest_path,
                output_pdf_path=tmp_path / "preview.pdf",
                facts=(),
            )
        )
