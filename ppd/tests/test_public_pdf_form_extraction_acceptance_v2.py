import json
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_pdf_form_extraction_acceptance_v2.json"

EXPECTED_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/tests/test_public_pdf_form_extraction_acceptance_v2.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_public_pdf_form_extraction_acceptance_v2.py"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

REQUIRED_DOCUMENT_KEYS = {
    "document_id",
    "source_id",
    "title",
    "document_type",
    "language",
    "content_hash",
    "extraction_confidence",
    "pdf_pages",
    "tables",
    "checklist_items",
    "required_document_labels",
    "signature_certification_block_labels",
    "form_fields",
    "ocr_review",
}

REQUIRED_FIELD_TYPES = {"text", "checkbox", "radio", "signature"}
PROHIBITED_POLICY_FLAGS = {
    "real_pdf_read",
    "document_download",
    "ocr_execution",
    "devhub_access",
    "private_file_access",
    "uploads_or_submissions",
    "payments_or_scheduling",
    "mutates_process_models",
    "mutates_guardrails",
    "mutates_sources_or_archives",
}


def load_packet():
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def assert_page_anchor(anchor, document_id):
    assert isinstance(anchor, str)
    assert anchor.startswith(f"{document_id}#page=")
    page_value = anchor.rsplit("=", 1)[1]
    assert page_value.isdigit()
    assert int(page_value) >= 1


def test_packet_is_fixture_first_and_offline_only():
    packet = load_packet()

    assert packet["packet_id"] == "public-pdf-form-extraction-acceptance-v2"
    assert packet["version"] == 2
    assert packet["fixture_policy"]["synthetic_only"] is True
    for flag in PROHIBITED_POLICY_FLAGS:
        assert packet["fixture_policy"][flag] is False
    assert packet["validation_commands"] == EXPECTED_VALIDATION_COMMANDS


def test_document_records_cover_pdf_text_tables_forms_and_review_holds():
    packet = load_packet()
    documents = packet["documents"]

    assert len(documents) >= 2
    assert any(document["ocr_review"]["hold_required"] for document in documents)

    for document in documents:
        assert REQUIRED_DOCUMENT_KEYS.issubset(document)
        assert document["document_type"] in {"public_pdf_fixture", "public_form_pdf_fixture"}
        assert document["language"] == "en"
        assert document["content_hash"].startswith("sha256:fixture-")
        assert document["extraction_confidence"] >= 0.90

        page_numbers = {page["page_number"] for page in document["pdf_pages"]}
        assert page_numbers
        for page in document["pdf_pages"]:
            assert_page_anchor(page["page_anchor"], document["document_id"])
            assert page["page_number"] >= 1
            assert page["text_extraction_confidence"] >= 0.90
            assert page["extracted_text"].strip()
            assert "deadline_language" in page
            assert "file_preparation_instructions" in page

        assert any(page["deadline_language"] for page in document["pdf_pages"])
        assert any(page["file_preparation_instructions"] for page in document["pdf_pages"])

        assert document["tables"]
        for table in document["tables"]:
            assert table["kind"] == "fee_schedule"
            assert_page_anchor(table["page_anchor"], document["document_id"])
            assert len(table["headers"]) >= 3
            assert len(table["rows"]) >= 2

        assert document["checklist_items"]
        assert any(item["required"] is True for item in document["checklist_items"])
        for item in document["checklist_items"]:
            assert item["label"].strip()
            assert_page_anchor(item["page_anchor"], document["document_id"])
            assert isinstance(item["required"], bool)

        assert document["required_document_labels"]
        assert all(label.strip() for label in document["required_document_labels"])
        assert document["signature_certification_block_labels"]
        assert all(label.strip() for label in document["signature_certification_block_labels"])

        field_types = {field["field_type"] for field in document["form_fields"]}
        assert field_types.issubset(REQUIRED_FIELD_TYPES)
        assert "text" in field_types
        assert field_types.intersection({"checkbox", "radio"})
        for field in document["form_fields"]:
            assert field["name"].strip()
            assert_page_anchor(field["page_anchor"], document["document_id"])
            assert isinstance(field["required"], bool)
            if field["field_type"] in {"checkbox", "radio"}:
                assert field.get("options")
                assert all(option.strip() for option in field["options"])

        ocr_review = document["ocr_review"]
        assert ocr_review["ocr_attempted"] is False
        assert isinstance(ocr_review["hold_required"], bool)
        assert ocr_review["hold_reason"].strip()


def test_packet_does_not_reference_live_or_private_artifacts():
    raw_packet = FIXTURE_PATH.read_text(encoding="utf-8").lower()

    forbidden_fragments = [
        "devhub.portlandoregon.gov",
        "sessionstorage",
        "localstorage",
        "cookie",
        "password",
        "captcha",
        "mfa",
        "upload",
        "submit payment",
        "real_pdf_path",
        "/home/",
        "c:\\",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in raw_packet
