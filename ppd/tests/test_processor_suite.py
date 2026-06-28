from __future__ import annotations

import json
from pathlib import Path

from ppd.crawler.processor_suite import build_processor_suite


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "processor_suite" / "public_ppd_inputs.json"


def test_public_ppd_pages_and_pdfs_flow_through_processor_suite() -> None:
    inputs = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    suite = build_processor_suite(inputs)

    assert len(suite["archive_manifests"]) == 2
    assert len(suite["normalized_documents"]) == 2
    assert len(suite["pdf_metadata"]) == 1
    assert len(suite["requirement_batches"]) == 2
    assert len(suite["formal_logic_source_evidence"]) == 4

    manifest_urls = {entry["url"] for entry in suite["archive_manifests"]}
    document_urls = {entry["source_url"] for entry in suite["normalized_documents"]}
    assert manifest_urls == document_urls

    pdf_document = next(doc for doc in suite["normalized_documents"] if doc["kind"] == "pdf")
    assert suite["pdf_metadata"][0]["document_id"] == pdf_document["document_id"]
    assert suite["pdf_metadata"][0]["page_count"] == 3

    document_ids = {doc["document_id"] for doc in suite["normalized_documents"]}
    archive_hashes = {item["sha256"] for item in suite["archive_manifests"]}

    for batch in suite["requirement_batches"]:
        assert batch["document_id"] in document_ids
        assert batch["requirements"]
        for requirement in batch["requirements"]:
            assert requirement["source_evidence_id"].startswith(batch["document_id"] + "#evidence-")

    evidence_ids = {item["evidence_id"] for item in suite["formal_logic_source_evidence"]}
    assert len(evidence_ids) == 4
    for evidence in suite["formal_logic_source_evidence"]:
        assert evidence["document_id"] in document_ids
        assert evidence["archive_sha256"] in archive_hashes
        assert evidence["quote"]
