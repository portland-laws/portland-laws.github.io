from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any

from ppd.contracts.processor_archive_manifest import validate_processor_archive_manifest


FIXTURE_ROOT = Path(__file__).parent / "fixtures"
MANIFEST_PATH = FIXTURE_ROOT / "processor-archive" / "processor_archive_handoff_manifest.json"
SOURCE_INDEX_PATH = FIXTURE_ROOT / "source-index" / "source_index_records.json"


class ProcessorArchiveManifestValidationTest(unittest.TestCase):
    def test_manifest_references_processor_provenance_source_index_and_normalized_ids(self) -> None:
        manifest = _load_json(MANIFEST_PATH)
        source_index = _load_source_index_records()

        errors = validate_processor_archive_manifest(manifest, source_index)

        self.assertEqual([], errors)
        normalized_ids = {
            record["normalizedDocument"]["id"]
            for record in manifest["records"]
        }
        self.assertEqual(
            {"normalized-ppd-home-html", "normalized-devhub-faq-html"},
            normalized_ids,
        )

    def test_manifest_rejects_unknown_source_index_record(self) -> None:
        manifest = _load_json(MANIFEST_PATH)
        source_index = _load_source_index_records()
        mutated = copy.deepcopy(manifest)
        mutated["records"][0]["sourceIndexRecordId"] = "missing-source-index-record"

        errors = validate_processor_archive_manifest(mutated, source_index)

        self.assertTrue(any("does not reference a committed source-index record" in error for error in errors))

    def test_manifest_rejects_unstable_normalized_document_id(self) -> None:
        manifest = _load_json(MANIFEST_PATH)
        source_index = _load_source_index_records()
        mutated = copy.deepcopy(manifest)
        mutated["records"][0]["normalizedDocument"]["id"] = "https://www.portland.gov/ppd"

        errors = validate_processor_archive_manifest(mutated, source_index)

        self.assertTrue(any("normalizedDocument.id" in error for error in errors))

    def test_manifest_rejects_raw_or_private_artifacts(self) -> None:
        manifest = _load_json(MANIFEST_PATH)
        source_index = _load_source_index_records()
        mutated = copy.deepcopy(manifest)
        forbidden = mutated["records"][0]["forbiddenArtifacts"]
        forbidden["responseBodyIncluded"] = True
        forbidden["rawCrawlOutputPath"] = "ppd/data/raw/live-response.html"
        forbidden["privateDevhubArtifactPath"] = "ppd/data/private/devhub-auth-state.json"

        errors = validate_processor_archive_manifest(mutated, source_index)

        joined = "\n".join(errors)
        self.assertIn("responseBodyIncluded must be false", joined)
        self.assertIn("forbidden artifact path must not be present", joined)

    def test_manifest_rejects_processor_outside_ipfs_datasets_py_processors(self) -> None:
        manifest = _load_json(MANIFEST_PATH)
        source_index = _load_source_index_records()
        mutated = copy.deepcopy(manifest)
        mutated["records"][0]["processorProvenance"]["backendPath"] = "ppd/crawler/local-archive"
        mutated["records"][0]["processorProvenance"]["sourceModule"] = "ppd.crawler.local_archive"

        errors = validate_processor_archive_manifest(mutated, source_index)

        joined = "\n".join(errors)
        self.assertIn("read-only ipfs_datasets_py processor suite", joined)
        self.assertIn("sourceModule must stay under ipfs_datasets_py", joined)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return data


def _load_source_index_records() -> dict[str, dict[str, Any]]:
    fixture = _load_json(SOURCE_INDEX_PATH)
    records = fixture.get("records")
    if not isinstance(records, list):
        raise AssertionError("source index fixture must contain records")
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise AssertionError("source index records must be objects")
        record_id = record.get("id")
        if not isinstance(record_id, str):
            raise AssertionError("source index record id is required")
        by_id[record_id] = record
    return by_id


if __name__ == "__main__":
    unittest.main()
