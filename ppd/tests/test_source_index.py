from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from ppd.source_index import SourceIndexError, export_fixture_source_index

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source_index" / "synthetic_source_index_bundle.json"


def _fixture() -> dict:
    return json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))


def test_export_fixture_source_index_is_deterministic_metadata_only() -> None:
    fixture = _fixture()

    first = export_fixture_source_index(fixture)
    second = export_fixture_source_index(copy.deepcopy(fixture))

    assert first == second
    assert first == {
        "schema_version": "ppd-source-index-fixture-v1",
        "source_registry_id": "synthetic-portland-ppd-registry-v1",
        "archive_manifest_id": "synthetic-portland-ppd-archive-v1",
        "documents": [
            {
                "archive_path": "fixtures/archive/appeal-001.pdf",
                "content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "document_id": "appeal-001",
                "jurisdiction": "Portland, OR",
                "public_url": "https://www.portland.gov/ppd/appeals/appeal-001",
                "source_id": "portland-ppd-appeals",
                "source_title": "Synthetic Portland PP&D Appeals",
            },
            {
                "archive_path": "fixtures/archive/permit-001.pdf",
                "content_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "document_id": "permit-001",
                "jurisdiction": "Portland, OR",
                "public_url": "https://www.portland.gov/ppd/permits/permit-001",
                "source_id": "portland-ppd-permits",
                "source_title": "Synthetic Portland PP&D Permits",
            },
        ],
        "citations": [
            {
                "citation_id": "appeal-001-cite-001",
                "content_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "document_id": "appeal-001",
                "locator": "p. 1",
            },
            {
                "citation_id": "permit-001-cite-001",
                "content_sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "document_id": "permit-001",
                "locator": "p. 2",
            },
        ],
        "index_sha256": "8599b275b09a38e0cfcbd67422e2dfe765fe6af1e3d3f7aa3e8665326a41da28",
    }


def test_export_fixture_source_index_rejects_raw_body_fields() -> None:
    fixture = _fixture()
    fixture["document_records"][0]["raw_body"] = "private crawl body"

    with pytest.raises(SourceIndexError, match="raw body"):
        export_fixture_source_index(fixture)


def test_export_fixture_source_index_rejects_private_urls_and_paths() -> None:
    fixture = _fixture()
    fixture["document_records"][0]["public_url"] = "http://127.0.0.1/private"

    with pytest.raises(SourceIndexError, match="private"):
        export_fixture_source_index(fixture)

    fixture = _fixture()
    fixture["document_records"][0]["archive_path"] = "/home/user/private.pdf"

    with pytest.raises(SourceIndexError, match="local path|absolute"):
        export_fixture_source_index(fixture)


def test_export_fixture_source_index_rejects_invented_hashes() -> None:
    fixture = _fixture()
    fixture["citation_integrity"][0]["content_sha256"] = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"

    with pytest.raises(SourceIndexError, match="invented"):
        export_fixture_source_index(fixture)
