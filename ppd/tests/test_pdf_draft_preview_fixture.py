from pathlib import Path

from ppd.pdf.draft_preview_fixture import analyze_preview_fixture, load_preview_fixture


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "pdf_draft_preview"
    / "synthetic_permit_application_preview.json"
)


def test_synthetic_pdf_preview_reports_missing_and_blocked_fields_without_pdf_io():
    fixture = load_preview_fixture(FIXTURE_PATH)

    report = analyze_preview_fixture(fixture)

    assert report["case_id"] == "synthetic-demo-case-001"
    assert report["preview_only"] is True
    assert report["pdf_binary_io"] is False

    missing_fact_keys = {item["fact_key"] for item in report["missing_facts"]}
    assert "contractor_license_number" in missing_fact_keys
    assert "owner_certification_initials" in missing_fact_keys

    blocked_field_names = {item["field_name"] for item in report["blocked_certification_fields"]}
    assert blocked_field_names == {
        "OwnerCertificationInitials",
        "ApplicantSignature",
        "SubmitApplication",
    }

    preview_by_field = {item["field_name"]: item for item in report["field_previews"]}
    assert preview_by_field["ApplicantName"]["preview_value"] == "Alex Example"
    assert preview_by_field["ProjectAddress"]["status"] == "preview_mapped"
    assert preview_by_field["ContractorLicenseNumber"]["status"] == "missing_fact"
    assert preview_by_field["OwnerCertificationInitials"]["status"] == "blocked_requires_confirmation"
    assert preview_by_field["ApplicantSignature"]["preview_value"] is None


def test_preview_fixture_path_is_test_local():
    assert FIXTURE_PATH.parts[-4:] == (
        "tests",
        "fixtures",
        "pdf_draft_preview",
        "synthetic_permit_application_preview.json",
    )
