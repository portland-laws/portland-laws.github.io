import json
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "public_source_lineage"
    / "synthetic_public_source_chain.json"
)

RECORD_KEYS = (
    "source_registry",
    "archive_manifest",
    "document_record",
    "requirement_node",
    "process_model",
    "guardrail_bundle",
)

FORBIDDEN_RAW_BODY_KEYS = {
    "raw_body",
    "raw_html",
    "raw_text",
    "body",
    "html",
    "full_text",
    "content",
    "bytes",
    "payload",
    "downloaded_path",
    "local_path",
    "warc_payload",
    "archive_payload",
}


def _load_fixture():
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def _walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _assert_sha256(value):
    assert isinstance(value, str)
    assert value.startswith("sha256:")
    digest = value.removeprefix("sha256:")
    assert len(digest) == 64
    int(digest, 16)


def _assert_lineage(record, expected_source_id, expected_hash):
    lineage = record.get("lineage")
    assert isinstance(lineage, dict)
    assert lineage["source_id"] == expected_source_id
    assert lineage["canonical_url"].startswith("https://www.portland.gov/ppd/")
    assert lineage["content_hash"] == expected_hash
    assert lineage["last_seen_at"] == "2026-05-08T12:00:00Z"
    assert lineage["freshness_status"] == "current"
    assert lineage.get("evidence_ids")
    _assert_sha256(lineage["content_hash"])


def test_fixture_contains_one_complete_public_source_lineage_chain():
    fixture = _load_fixture()
    assert tuple(fixture[key] for key in RECORD_KEYS)

    source = fixture["source_registry"]
    archive = fixture["archive_manifest"]
    document = fixture["document_record"]
    requirement = fixture["requirement_node"]
    process = fixture["process_model"]
    guardrail = fixture["guardrail_bundle"]

    assert source["source_id"] == archive["source_id"] == document["source_id"]
    assert archive["normalized_document_id"] == document["document_id"]
    assert requirement["source_evidence_ids"] == ["ev_submit_plans_single_pdf"]
    assert requirement["requirement_id"] in process["file_rules"]
    assert process["guardrail_bundle_id"] == guardrail["guardrail_bundle_id"]
    assert guardrail["process_id"] == process["process_id"]

    assert source["canonical_url"] == archive["canonical_url"]
    assert archive["canonical_url"] == document["lineage"]["canonical_url"]
    assert document["citation_spans"][0]["citation_id"].startswith(document["document_id"])
    assert document["citation_spans"][0]["source_id"] == source["source_id"]


def test_lineage_records_retain_hashes_freshness_and_citation_ready_ids():
    fixture = _load_fixture()
    source_id = fixture["source_registry"]["source_id"]

    expected_hashes = {
        "source_registry": fixture["source_registry"]["lineage"]["content_hash"],
        "archive_manifest": fixture["archive_manifest"]["content_hash"],
        "document_record": fixture["document_record"]["content_hash"],
        "requirement_node": fixture["document_record"]["content_hash"],
        "process_model": fixture["document_record"]["content_hash"],
        "guardrail_bundle": fixture["document_record"]["content_hash"],
    }

    for record_key in RECORD_KEYS:
        record = fixture[record_key]
        _assert_lineage(record, source_id, expected_hashes[record_key])

    assert fixture["source_registry"]["last_seen_at"] == "2026-05-08T12:00:00Z"
    assert fixture["source_registry"]["crawl_frequency"] == "weekly"
    assert fixture["archive_manifest"]["capture_started_at"]
    assert fixture["archive_manifest"]["capture_finished_at"]
    assert fixture["document_record"]["citation_spans"][0]["evidence_id"] in fixture["requirement_node"]["source_evidence_ids"]


def test_fixture_preserves_no_raw_body_guarantee():
    fixture = _load_fixture()
    assert fixture["archive_manifest"]["no_raw_body_persisted"] is True

    for item in _walk_json(fixture):
        forbidden = FORBIDDEN_RAW_BODY_KEYS.intersection(item)
        assert not forbidden, f"raw body fields are not allowed in committed PP&D fixtures: {sorted(forbidden)}"

    assert fixture["archive_manifest"]["archive_artifact_ref"].startswith("fixture://")
    assert fixture["source_registry"]["processor_policy"] == "metadata_and_normalized_text_only"
    assert fixture["source_registry"]["privacy_classification"] == "public"
