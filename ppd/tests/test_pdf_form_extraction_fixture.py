import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "pdf_form_extraction"
    / "synthetic_public_form_metadata.json"
)


FORBIDDEN_BINARY_KEYS = {
    "pdf_binary",
    "binary",
    "base64",
    "raw_body",
    "raw_pdf",
    "document_bytes",
}


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def test_synthetic_public_form_fixture_is_normalized_metadata_only():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    assert fixture["fixture_type"] == "normalized_pdf_form_extraction"
    assert fixture["source"]["source_type"] == "public_form"
    assert fixture["source"]["no_pdf_binary_stored"] is True
    assert fixture["source"]["raw_body_persisted"] is False

    for node in _walk(fixture):
        assert FORBIDDEN_BINARY_KEYS.isdisjoint(node.keys())


def test_synthetic_public_form_fixture_covers_required_extraction_shapes():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    page_anchor_ids = {anchor["anchor_id"] for anchor in fixture["page_anchors"]}
    assert {"page-1-intake-summary", "page-2-document-checklist", "page-3-certification"}.issubset(page_anchor_ids)

    checklist_items = fixture["checklist_items"]
    assert any(item["required"] is True for item in checklist_items)
    assert any(item.get("condition") for item in checklist_items)
    assert all(item["page_anchor_id"] in page_anchor_ids for item in checklist_items)

    fields = fixture["fillable_fields"]
    field_names = {field["field_name"] for field in fields}
    assert "applicant.full_name" in field_names
    assert "project.site_address" in field_names
    assert "certification.applicant_signature" in field_names
    assert {"text", "radio", "checkbox", "signature", "date"}.issubset(
        {field["field_type"] for field in fields}
    )
    assert all(field["page_anchor_id"] in page_anchor_ids for field in fields)

    certifications = fixture["signature_and_certification_blocks"]
    assert certifications
    assert all(block["requires_signature"] for block in certifications)
    assert all("confirmation" in block["guardrail"] for block in certifications)

    prep_rules = {instruction["normalized_rule"] for instruction in fixture["file_preparation_instructions"]}
    assert "plans_one_pdf_supporting_documents_separate_pdfs" in prep_rules
    assert "prefer_searchable_pdf_text" in prep_rules
    assert "descriptive_document_type_and_address_filename" in prep_rules


def test_synthetic_public_form_fixture_marks_ocr_confidence_and_review_status():
    fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    flags = fixture["ocr_confidence_flags"]
    assert any(flag["derived_from_ocr"] is True for flag in flags)
    assert any(flag["derived_from_ocr"] is False for flag in flags)

    for flag in flags:
        assert 0 <= flag["confidence"] <= 1
        assert flag["human_review_status"] in {"not_required", "review_recommended", "required"}
        assert flag["page_anchor_id"] in {anchor["anchor_id"] for anchor in fixture["page_anchors"]}
