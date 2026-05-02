#!/usr/bin/env python3
"""Fixture tests for the PP&D archive adapter contract."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.contracts.archive_adapter import (
    IPFS_DATASETS_PROCESSOR_BACKEND,
    ArchiveAdapterPolicyDecision,
    ArchivePolicyDecision,
    ArchivePolicyReason,
    ArchiveProcessorFamily,
    ArchiveProcessorIdentity,
    PpdArchiveAdapterRecord,
    archive_adapter_manifest_from_dict,
)


class PpdArchiveAdapterContractTests(unittest.TestCase):
    def test_fixture_manifest_records_processor_backend_and_policy_decision(self) -> None:
        fixture_path = Path(__file__).parent / "fixtures" / "archive-adapter" / "archive_adapter_manifest.json"
        manifest = archive_adapter_manifest_from_dict(json.loads(fixture_path.read_text(encoding="utf-8")))

        self.assertEqual([], manifest.validate())
        self.assertEqual(2, len(manifest.records))
        for record in manifest.records:
            self.assertEqual(IPFS_DATASETS_PROCESSOR_BACKEND, record.processor.backend_path)
            self.assertTrue(record.processor.name)
            self.assertTrue(record.processor.version)
            self.assertTrue(record.content_hash.startswith("sha256:"))
            self.assertTrue(record.source_url.startswith("https://www.portland.gov/ppd/"))
            self.assertEqual(ArchivePolicyDecision.ALLOW, record.policy_decision.decision)
            self.assertTrue(record.should_invoke_processor())

    def test_policy_refusal_prevents_processor_invocation(self) -> None:
        record = PpdArchiveAdapterRecord(
            id="private-devhub-refusal",
            source_url="https://devhub.portlandoregon.gov/private/my-permits",
            canonical_url="https://devhub.portlandoregon.gov/private/my-permits",
            content_hash="sha256:3333333333333333333333333333333333333333333333333333333333333333",
            created_at="2026-05-01T19:00:00Z",
            processor=ArchiveProcessorIdentity(
                name="web_archiving.capture_public_url",
                version="fixture-2026-05-01",
                family=ArchiveProcessorFamily.WEB_ARCHIVING,
            ),
            policy_decision=ArchiveAdapterPolicyDecision(
                decision=ArchivePolicyDecision.REFUSE,
                reasons=(ArchivePolicyReason.PRIVATE_DEVHUB_PATH,),
                evaluated_at="2026-05-01T18:59:00Z",
            ),
        )

        self.assertEqual([], record.validate())
        self.assertFalse(record.should_invoke_processor())

    def test_raw_body_persistence_and_wrong_backend_are_invalid(self) -> None:
        record = PpdArchiveAdapterRecord(
            id="bad-backend",
            source_url="https://www.portland.gov/ppd/example",
            canonical_url="https://www.portland.gov/ppd/example",
            content_hash="sha256:4444444444444444444444444444444444444444444444444444444444444444",
            created_at="2026-05-01T19:00:00Z",
            manifest_only=False,
            processor=ArchiveProcessorIdentity(
                name="forked.processor",
                version="fixture-2026-05-01",
                family=ArchiveProcessorFamily.WEB_ARCHIVING,
                backend_path="ppd/crawler/forked_processor",
            ),
            policy_decision=ArchiveAdapterPolicyDecision(
                decision=ArchivePolicyDecision.ALLOW,
                reasons=(ArchivePolicyReason.PUBLIC_PPD_ALLOWLISTED, ArchivePolicyReason.ROBOTS_ALLOWED),
                evaluated_at="2026-05-01T18:59:00Z",
            ),
        )

        errors = record.validate()
        self.assertTrue(any("manifest_only" in error for error in errors))
        self.assertTrue(any("backend_path" in error for error in errors))
        self.assertFalse(record.should_invoke_processor())


if __name__ == "__main__":
    unittest.main()
