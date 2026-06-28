from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ppd.processor_suite.archive_manifest_validation import (
    ArchiveManifestValidationError,
    deterministic_handoff_id,
    validate_manifest,
    validate_manifest_file,
)


FIXTURES = Path(__file__).parent / "fixtures" / "processor_archive_integration"


class ProcessorArchiveIntegrationManifestValidationTest(unittest.TestCase):
    def load_valid_manifest(self) -> dict:
        return json.loads((FIXTURES / "valid_manifest.json").read_text(encoding="utf-8"))

    def test_valid_manifest_proves_citation_backed_public_provenance(self) -> None:
        manifest = self.load_valid_manifest()

        result = validate_manifest_file(FIXTURES / "valid_manifest.json")

        self.assertEqual(
            {
                "formalLogicHandoffId": deterministic_handoff_id(manifest["archivedPublicSources"]),
                "archivedPublicSourceCount": 2,
            },
            result,
        )

    def test_rejects_missing_citation_backing(self) -> None:
        manifest = json.loads((FIXTURES / "invalid_manifest.json").read_text(encoding="utf-8"))

        with self.assertRaisesRegex(ArchiveManifestValidationError, "citations"):
            validate_manifest(manifest)

    def test_rejects_private_devhub_marker_without_committing_private_artifact(self) -> None:
        manifest = self.load_valid_manifest()
        manifest["reviewNote"] = "private value would have been in ppd/data/private/devhub-state.json"
        manifest["formalLogicHandoffId"] = deterministic_handoff_id(manifest["archivedPublicSources"])

        with self.assertRaisesRegex(ArchiveManifestValidationError, "forbidden"):
            validate_manifest(manifest)

    def test_rejects_raw_crawl_or_download_flags(self) -> None:
        manifest = self.load_valid_manifest()
        manifest["rawCrawlOutputIncluded"] = True
        manifest["documentsDownloaded"] = True
        manifest["archivedPublicSources"][0]["processorInput"]["persistRawBody"] = True
        manifest["formalLogicHandoffId"] = deterministic_handoff_id(manifest["archivedPublicSources"])

        with self.assertRaisesRegex(ArchiveManifestValidationError, "rawCrawlOutputIncluded"):
            validate_manifest(manifest)

    def test_rejects_non_deterministic_formal_logic_handoff_id(self) -> None:
        manifest = self.load_valid_manifest()
        changed = copy.deepcopy(manifest)
        changed["formalLogicHandoffId"] = "logic-handoff-not-derived-from-public-sources"

        with self.assertRaisesRegex(ArchiveManifestValidationError, "formalLogicHandoffId"):
            validate_manifest(changed)


if __name__ == "__main__":
    unittest.main()
