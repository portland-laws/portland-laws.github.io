import json
import re
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "public_capture_assembler"
    / "normalized_document_record_candidates.json"
)
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
RAW_CONTENT_KEYS = {"content", "html", "body", "text", "markdown", "pdf_bytes"}


def load_fixture():
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def test_expected_document_records_are_ordered_hash_only_candidates():
    fixture = load_fixture()
    records = fixture["expected_document_records"]

    assert [record["section_order"] for record in records] == sorted(
        record["section_order"] for record in records
    )
    assert [record["capture_id"] for record in records] == [
        "html:zoning-code-guide",
        "pdf:building-permit-application",
    ]

    for record in records:
        assert RAW_CONTENT_KEYS.isdisjoint(record)
        assert record["source_id"] == "archive:ppd-zoning-2026-05"
        assert record["content_hash"]["algorithm"] == "sha256"
        assert HASH_RE.match(record["content_hash"]["value"])
        assert isinstance(record["citation_spans"], list)
        assert 0.0 <= record["extraction_confidence"] <= 1.0


def test_expected_records_match_manifest_and_extraction_metadata():
    fixture = load_fixture()
    manifest_items = {
        item["capture_id"]: item
        for manifest in fixture["archive_manifests"]
        for item in manifest["items"]
    }
    extraction_items = {
        extraction["capture_id"]: extraction
        for extraction in fixture["html_extractions"] + fixture["pdf_form_extractions"]
    }

    for record in fixture["expected_document_records"]:
        manifest_item = manifest_items[record["capture_id"]]
        extraction_item = extraction_items[record["capture_id"]]

        assert record["source_url"] == manifest_item["url"]
        assert record["media_type"] == manifest_item["media_type"]
        assert record["title"] == manifest_item["title"]
        assert record["section_order"] == manifest_item["section_order"]
        assert record["content_hash"]["value"] == manifest_item["content_sha256"]
        assert record["content_hash"]["value"] == extraction_item["content_sha256"]
        assert record["citation_spans"] == extraction_item["citation_spans"]
        assert record["extraction_confidence"] == extraction_item["confidence"]

        expected_form_fields = extraction_item.get("form_fields", [])
        assert record["form_fields"] == expected_form_fields
