from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

FORBIDDEN_KEYS = {
    "authState",
    "auth_state",
    "body",
    "cookies",
    "downloadPath",
    "download_path",
    "html",
    "password",
    "rawBody",
    "rawOutputPath",
    "rawProcessorOutputPath",
    "raw_body",
    "raw_output_path",
    "screenshotPath",
    "screenshot_path",
    "sessionState",
    "session_state",
    "storageState",
    "storage_state",
    "token",
    "tracePath",
    "trace_path",
}

FORBIDDEN_VALUE_MARKERS = (
    "ppd/data/private",
    "ppd/data/raw",
    "devhub/.auth",
    "storage-state",
    "auth-state",
    "trace.zip",
    ".har",
    "private devhub",
)

BLOCKED_ACTIONS = {
    "network_request",
    "read_raw_processor_output",
    "read_private_devhub_artifact",
    "launch_browser",
    "authenticate",
    "upload",
    "submit",
    "certify",
    "pay",
    "cancel",
    "schedule_inspection",
    "automate_mfa_or_captcha",
}


class ProcessorToFormalLogicHandoffManifestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture_path = (
            Path(__file__).parent
            / "fixtures"
            / "handoff"
            / "processor_to_formal_logic_handoff_manifest.json"
        )
        self.manifest = json.loads(self.fixture_path.read_text(encoding="utf-8"))

    def test_manifest_declares_fixture_only_boundary(self) -> None:
        self.assertEqual(self.manifest["fixtureKind"], "processor_to_formal_logic_handoff_manifest")
        self.assertEqual(self.manifest["schemaVersion"], 1)
        self.assertTrue(self.manifest["manifestOnly"])
        self.assertFalse(self.manifest["networkAccess"])
        self.assertFalse(self.manifest["rawProcessorOutputIncluded"])
        self.assertFalse(self.manifest["privateDevhubArtifactsIncluded"])
        self.assertTrue(self.manifest["generatedAt"].endswith("Z"))

    def test_records_link_processor_documents_requirements_evidence_and_guardrails(self) -> None:
        archive_ids = {record["id"] for record in self.manifest["processorArchiveRecords"]}
        evidence_ids = {record["id"] for record in self.manifest["sourceEvidence"]}
        document_ids = {record["id"] for record in self.manifest["normalizedDocuments"]}
        requirement_ids = {record["id"] for record in self.manifest["extractedRequirements"]}
        bundle_ids = {record["id"] for record in self.manifest["guardrailBundles"]}

        self.assertTrue(archive_ids)
        self.assertTrue(evidence_ids)
        self.assertTrue(document_ids)
        self.assertTrue(requirement_ids)
        self.assertTrue(bundle_ids)

        for document in self.manifest["normalizedDocuments"]:
            self.assertIn(document["processorArchiveRecordId"], archive_ids)
            self.assertTrue(document["fixturePath"].startswith("ppd/tests/fixtures/"))
            self.assertRegex(document["contentHash"], SHA256_RE)
            self.assertTrue(set(document["sourceEvidenceIds"]).issubset(evidence_ids))

        for requirement in self.manifest["extractedRequirements"]:
            self.assertIn(requirement["normalizedDocumentId"], document_ids)
            self.assertTrue(set(requirement["sourceEvidenceIds"]).issubset(evidence_ids))
            self.assertGreaterEqual(requirement["confidence"], 0.0)
            self.assertLessEqual(requirement["confidence"], 1.0)
            self.assertEqual(requirement["formalizationStatus"], "ready_for_guardrail_fixture")

        for bundle in self.manifest["guardrailBundles"]:
            self.assertTrue(set(bundle["requirementIds"]).issubset(requirement_ids))
            self.assertTrue(set(bundle["sourceEvidenceIds"]).issubset(evidence_ids))
            self.assertRegex(bundle["bundleHash"], SHA256_RE)

        for handoff in self.manifest["handoffs"]:
            self.assertEqual(handoff["fromProcessorManifestId"], self.manifest["processorManifestId"])
            self.assertIn(handoff["toFormalLogicBundleId"], bundle_ids)
            self.assertTrue(set(handoff["normalizedDocumentIds"]).issubset(document_ids))
            self.assertTrue(set(handoff["requirementIds"]).issubset(requirement_ids))
            self.assertTrue(set(handoff["sourceEvidenceIds"]).issubset(evidence_ids))
            self.assertTrue(set(handoff["guardrailBundleIds"]).issubset(bundle_ids))

    def test_handoff_refuses_network_raw_output_and_private_devhub_artifacts(self) -> None:
        for handoff in self.manifest["handoffs"]:
            self.assertFalse(BLOCKED_ACTIONS.intersection(handoff["allowedActions"]))
            self.assertTrue(BLOCKED_ACTIONS.issubset(set(handoff["forbiddenActions"])))

        findings = list(self._forbidden_artifact_findings(self.manifest))
        self.assertEqual(findings, [])

    def test_source_evidence_is_public_and_hash_backed(self) -> None:
        for evidence in self.manifest["sourceEvidence"]:
            self.assertTrue(evidence["sourceUrl"].startswith("https://www.portland.gov/ppd"))
            self.assertTrue(evidence["canonicalUrl"].startswith("https://www.portland.gov/ppd"))
            self.assertTrue(evidence["capturedAt"].endswith("Z"))
            self.assertRegex(evidence["contentHash"], SHA256_RE)
            self.assertIn(evidence["documentId"], {doc["id"] for doc in self.manifest["normalizedDocuments"]})

    def _forbidden_artifact_findings(self, value: Any, path: str = "$", key: str = "") -> list[str]:
        findings: list[str] = []
        if key in FORBIDDEN_KEYS:
            findings.append(f"{path}.{key}")
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                findings.extend(self._forbidden_artifact_findings(child_value, f"{path}.{child_key}", str(child_key)))
        elif isinstance(value, list):
            for index, child_value in enumerate(value):
                findings.extend(self._forbidden_artifact_findings(child_value, f"{path}[{index}]", key))
        elif isinstance(value, str):
            lowered = value.lower()
            if any(marker in lowered for marker in FORBIDDEN_VALUE_MARKERS):
                findings.append(path)
        return findings


if __name__ == "__main__":
    unittest.main()
