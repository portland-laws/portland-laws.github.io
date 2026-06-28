import json
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "citation_integrity" / "round_trip_fixture.json"

FORBIDDEN_KEYS = {
    "auth_state",
    "body",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "har",
    "html",
    "local_private_file_path",
    "mfa",
    "password",
    "payment_details",
    "private_value",
    "raw_body",
    "raw_crawl_body",
    "screenshot",
    "session_state",
    "token",
    "trace",
}

FORBIDDEN_VALUE_FRAGMENTS = (
    "BEGIN PRIVATE",
    "cookie=",
    "password=",
    "raw crawl body",
    "session_token",
)


def load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)
    assert isinstance(data, dict)
    return data


def walk_json(value: Any) -> Any:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_json(child)
    else:
        yield value


def require_unique(items: list[dict[str, Any]], id_field: str) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for item in items:
        item_id = item.get(id_field)
        assert isinstance(item_id, str) and item_id, f"missing {id_field}: {item!r}"
        assert item_id not in indexed, f"duplicate {id_field}: {item_id}"
        indexed[item_id] = item
    return indexed


def section_text_by_id(document: dict[str, Any]) -> dict[str, str]:
    sections = document.get("sections")
    assert isinstance(sections, list) and sections
    by_id: dict[str, str] = {}
    for section in sections:
        assert isinstance(section, dict)
        section_id = section.get("section_id")
        text = section.get("text")
        assert isinstance(section_id, str) and section_id
        assert isinstance(text, str) and text
        by_id[section_id] = text
    return by_id


def test_fixture_has_no_private_values_or_raw_crawl_bodies() -> None:
    data = load_fixture()
    for node in walk_json(data):
        if isinstance(node, dict):
            lowered_keys = {str(key).lower() for key in node.keys()}
            assert not (lowered_keys & FORBIDDEN_KEYS), lowered_keys & FORBIDDEN_KEYS
        elif isinstance(node, str):
            lowered_value = node.lower()
            for fragment in FORBIDDEN_VALUE_FRAGMENTS:
                assert fragment.lower() not in lowered_value

    for source in data["source_registry"]:
        assert source["privacy_classification"] == "public"

    for manifest in data["archive_manifests"]:
        assert manifest["no_raw_body_persisted"] is True
        assert manifest["archive_artifact_ref"] == "fixture-metadata-only"


def test_citation_spans_archive_manifests_and_requirements_round_trip() -> None:
    data = load_fixture()
    sources = require_unique(data["source_registry"], "source_id")
    manifests = require_unique(data["archive_manifests"], "manifest_id")
    documents = require_unique(data["document_records"], "document_id")
    requirements = require_unique(data["requirement_nodes"], "requirement_id")

    citations: dict[str, dict[str, Any]] = {}

    for manifest in manifests.values():
        source_id = manifest.get("source_id")
        document_id = manifest.get("normalized_document_id")
        assert source_id in sources
        assert document_id in documents
        document = documents[document_id]
        assert document["source_id"] == source_id
        assert manifest["canonical_url"] == sources[source_id]["canonical_url"]

    for document in documents.values():
        source_id = document.get("source_id")
        assert source_id in sources
        sections = section_text_by_id(document)
        spans = document.get("citation_spans")
        assert isinstance(spans, list) and spans

        for span in spans:
            assert isinstance(span, dict)
            span_id = span.get("citation_span_id")
            assert isinstance(span_id, str) and span_id
            assert span_id not in citations
            citations[span_id] = span

            manifest_id = span.get("archive_manifest_id")
            section_id = span.get("section_id")
            assert manifest_id in manifests
            assert section_id in sections
            assert span.get("source_id") == source_id
            assert span.get("document_id") == document["document_id"]
            assert manifests[manifest_id]["source_id"] == source_id
            assert manifests[manifest_id]["normalized_document_id"] == document["document_id"]

            start = span.get("start_offset")
            end = span.get("end_offset")
            cited_text = span.get("cited_text")
            text = sections[section_id]
            assert isinstance(start, int)
            assert isinstance(end, int)
            assert isinstance(cited_text, str) and cited_text
            assert 0 <= start < end <= len(text)
            assert text[start:end] == cited_text

    cited_by_requirements: set[str] = set()
    for requirement in requirements.values():
        evidence_ids = requirement.get("source_evidence_ids")
        assert isinstance(evidence_ids, list) and evidence_ids, requirement["requirement_id"]
        for evidence_id in evidence_ids:
            assert isinstance(evidence_id, str) and evidence_id in citations
            cited_by_requirements.add(evidence_id)

    assert cited_by_requirements == set(citations)
