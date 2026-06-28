from __future__ import annotations

from ppd.public_crawl.manifest_normalization import (
    normalize_public_crawl_manifest,
    normalize_public_crawl_manifest_record,
)


def test_skipped_public_crawl_record_gets_stable_manifest_defaults() -> None:
    record = {
        "source_id": "ppd-devhub-example",
        "status": "skip",
        "reason": "public index unavailable",
    }

    normalized = normalize_public_crawl_manifest_record(record)

    assert normalized == {
        "source_id": "ppd-devhub-example",
        "status": "skipped",
        "reason": "public index unavailable",
        "skipped": True,
        "documents": [],
        "document_count": 0,
        "archive_items": [],
        "processor_handoff": [],
        "skip_reason": "public index unavailable",
    }
    assert record["status"] == "skip"


def test_skipped_record_preserves_existing_archive_and_handoff_fields() -> None:
    record = {
        "source_id": "ppd-devhub-example",
        "skipped": True,
        "documents": [{"id": "kept"}],
        "document_count": 1,
        "archive_items": [{"path": "archive/kept.json"}],
        "processor_handoff": [{"document_id": "kept"}],
        "skip_reason": "already classified",
    }

    normalized = normalize_public_crawl_manifest_record(record)

    assert normalized["status"] == "skipped"
    assert normalized["documents"] == [{"id": "kept"}]
    assert normalized["document_count"] == 1
    assert normalized["archive_items"] == [{"path": "archive/kept.json"}]
    assert normalized["processor_handoff"] == [{"document_id": "kept"}]
    assert normalized["skip_reason"] == "already classified"


def test_non_skipped_record_is_only_copied() -> None:
    record = {"source_id": "ppd-devhub-example", "status": "archived"}

    normalized = normalize_public_crawl_manifest_record(record)

    assert normalized == record
    assert normalized is not record


def test_manifest_list_normalization_keeps_order() -> None:
    records = [
        {"source_id": "first", "status": "skip"},
        {"source_id": "second", "status": "archived"},
    ]

    normalized = normalize_public_crawl_manifest(records)

    assert [record["source_id"] for record in normalized] == ["first", "second"]
    assert normalized[0]["status"] == "skipped"
    assert normalized[1]["status"] == "archived"
