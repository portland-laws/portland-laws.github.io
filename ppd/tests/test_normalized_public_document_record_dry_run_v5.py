import copy
import json
from pathlib import Path

from ppd.agent_readiness.normalized_public_document_record_dry_run_v5 import (
    OFFLINE_VALIDATION_COMMANDS,
    assemble_document_records,
    assemble_document_records_from_fixture,
    validate_document_records,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "public_metadata_manifest_dry_run_v5"


def _valid_manifest() -> dict:
    return json.loads((FIXTURE_DIR / "manifest.json").read_text(encoding="utf-8"))


def test_assembles_synthetic_document_records_from_public_metadata_fixture_only() -> None:
    records = assemble_document_records_from_fixture(FIXTURE_DIR / "manifest.json")

    assert [record["document_id"] for record in records] == [
        "docrec-v5-ppd-online-tools-overview",
        "docrec-v5-ppd-fee-payment-guide-pdf",
        "docrec-v5-ppd-permit-application-form",
    ]
    assert all(record["title"] for record in records)
    assert all(record["document_type"] for record in records)
    assert all(record["sections"] for record in records)
    assert all(record["citation_spans"] for record in records)
    assert all(record["extraction_confidence"] for record in records)
    assert all(record["reviewer_holds"] for record in records)
    assert all(record["rollback_notes"] for record in records)
    assert all(record["validation_commands"] == [list(command) for command in OFFLINE_VALIDATION_COMMANDS] for record in records)


def test_pdf_and_form_placeholders_do_not_claim_document_download_or_raw_text() -> None:
    records = {record["source_id"]: record for record in assemble_document_records_from_fixture(FIXTURE_DIR / "manifest.json")}
    pdf_record = records["ppd-fee-payment-guide-pdf"]
    form_record = records["ppd-permit-application-form"]

    assert pdf_record["pdf_pages"] == [
        {"page_number": 1, "status": "placeholder_no_pdf_downloaded", "text_stored": False},
        {"page_number": 2, "status": "placeholder_no_pdf_downloaded", "text_stored": False},
    ]
    assert "document_download_and_extraction_not_performed" in pdf_record["reviewer_holds"]
    assert [field["status"] for field in form_record["form_fields"]] == [
        "placeholder_no_form_document_downloaded",
        "placeholder_no_form_document_downloaded",
    ]


def test_rejects_non_v5_or_side_effectful_manifest_fixture() -> None:
    manifest = _valid_manifest()
    manifest["dry_run"] = "public_metadata_manifest_dry_run_v4"
    try:
        assemble_document_records(manifest)
    except ValueError as exc:
        assert "unsupported manifest dry_run" in str(exc)
    else:
        raise AssertionError("expected dry-run version validation failure")

    manifest = _valid_manifest()
    manifest["live_crawl_performed"] = True
    try:
        assemble_document_records(manifest)
    except ValueError as exc:
        assert "live_crawl_performed=false" in str(exc)
    else:
        raise AssertionError("expected live crawl boundary validation failure")


def test_rejects_missing_metadata_manifest_references_and_synthetic_rows() -> None:
    manifest = _valid_manifest()
    del manifest["sources"][0]["metadata_manifest_ref"]
    try:
        assemble_document_records(manifest)
    except ValueError as exc:
        assert "metadata_manifest_ref" in str(exc)
    else:
        raise AssertionError("expected metadata manifest reference validation failure")

    manifest = _valid_manifest()
    manifest["expected_document_record_ids"] = manifest["expected_document_record_ids"][:-1]
    try:
        assemble_document_records(manifest)
    except ValueError as exc:
        assert "missing synthetic DocumentRecord rows" in str(exc)
    else:
        raise AssertionError("expected synthetic row validation failure")


def test_rejects_missing_required_document_record_placeholders() -> None:
    manifest = _valid_manifest()
    records = assemble_document_records(manifest)
    cases = [
        (0, "sections", "missing section placeholders"),
        (0, "tables", "missing table placeholders"),
        (0, "links", "missing link placeholders"),
        (1, "pdf_pages", "missing PDF page placeholders"),
        (2, "form_fields", "missing form-field placeholders"),
        (2, "citation_spans", "missing citation-span placeholders"),
        (2, "reviewer_holds", "missing reviewer holds"),
        (2, "rollback_notes", "missing rollback notes"),
    ]
    for index, key, message in cases:
        mutated = copy.deepcopy(records)
        mutated[index][key] = []
        try:
            validate_document_records(manifest, mutated)
        except ValueError as exc:
            assert message in str(exc)
        else:
            raise AssertionError(f"expected validation failure for {key}")

    mutated = copy.deepcopy(records)
    mutated[0]["extraction_confidence"] = ""
    try:
        validate_document_records(manifest, mutated)
    except ValueError as exc:
        assert "missing extraction confidence labels" in str(exc)
    else:
        raise AssertionError("expected extraction confidence validation failure")

    mutated = copy.deepcopy(records)
    mutated[0]["validation_commands"] = []
    try:
        validate_document_records(manifest, mutated)
    except ValueError as exc:
        assert "missing validation commands" in str(exc)
    else:
        raise AssertionError("expected validation command validation failure")


def test_rejects_prohibited_manifest_and_record_claims() -> None:
    rejection_cases = json.loads((FIXTURE_DIR / "rejection_cases.json").read_text(encoding="utf-8"))
    for case in rejection_cases["manifest_cases"]:
        manifest = _valid_manifest()
        target = manifest
        for part in case["path"][:-1]:
            target = target[part]
        target[case["path"][-1]] = case["value"]
        try:
            assemble_document_records(manifest)
        except ValueError as exc:
            assert case["message"] in str(exc)
        else:
            raise AssertionError(f"expected manifest rejection for {case['name']}")

    manifest = _valid_manifest()
    records = assemble_document_records(manifest)
    for case in rejection_cases["record_cases"]:
        mutated = copy.deepcopy(records)
        mutated[0][case["key"]] = case["value"]
        try:
            validate_document_records(manifest, mutated)
        except ValueError as exc:
            assert case["message"] in str(exc)
        else:
            raise AssertionError(f"expected record rejection for {case['name']}")
