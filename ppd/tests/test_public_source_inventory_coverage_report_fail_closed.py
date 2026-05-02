"""Validation-only fail-closed tests for public source inventory coverage reports."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "public_source_inventory"
    / "coverage_report_fail_closed.json"
)

PRIVATE_DEVHUB_PATH_PARTS = (
    "/secure/",
    "/account",
    "/accounts",
    "/dashboard",
    "/my-permits",
    "/my-permits/",
    "/permits/",
    "/requests/",
    "/sessions/",
)

RAW_BODY_KEYS = {"rawResponseBody", "raw_response_body", "body", "html", "responseText"}
CREDENTIAL_KEYS = {
    "credentialMaterial",
    "credential_material",
    "credentials",
    "password",
    "token",
    "authState",
    "auth_state",
    "storageState",
    "storage_state",
}
TRACE_KEYS = {"traceArtifact", "trace_artifact", "tracePath", "trace_path"}
SCREENSHOT_KEYS = {
    "screenshotArtifact",
    "screenshot_artifact",
    "screenshotPath",
    "screenshot_path",
}
DOWNLOADED_DOCUMENT_KEYS = {
    "downloadedDocumentPath",
    "downloaded_document_path",
    "downloadPath",
    "download_path",
    "localDocumentPath",
    "local_document_path",
}


class PublicSourceInventoryCoverageReportFailClosedTest(unittest.TestCase):
    def test_fixture_contains_one_targeted_failure_per_case(self) -> None:
        fixture = _load_fixture()
        self.assertEqual(fixture["schemaVersion"], 1)
        self.assertEqual(len(fixture["cases"]), 8)

        for case in fixture["cases"]:
            with self.subTest(case=case["id"]):
                findings = validate_coverage_report(case["coverageReport"])
                self.assertEqual(findings, case["expectedFindings"])

    def test_coverage_report_rejects_missing_metadata_and_private_artifacts(self) -> None:
        cases = {case["id"]: case for case in _load_fixture()["cases"]}

        expected = {
            "missing-authority-label": ["missing_authority_labels"],
            "missing-recrawl-cadence": ["missing_recrawl_cadence"],
            "private-devhub-path": ["private_devhub_path"],
            "raw-response-body": ["raw_response_body"],
            "credential-material": ["credential_material"],
            "trace-artifact": ["trace_artifact"],
            "screenshot-artifact": ["screenshot_artifact"],
            "downloaded-document": ["downloaded_document"],
        }

        self.assertEqual(set(cases), set(expected))
        for case_id, expected_findings in expected.items():
            with self.subTest(case=case_id):
                self.assertEqual(
                    validate_coverage_report(cases[case_id]["coverageReport"]),
                    expected_findings,
                )


def _load_fixture() -> dict[str, Any]:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


def validate_coverage_report(report: dict[str, Any]) -> list[str]:
    """Small validation oracle for committed coverage-report fixtures only."""
    findings: list[str] = []

    authority_labels = report.get("authorityLabels", report.get("authority_labels"))
    if not isinstance(authority_labels, list) or not any(
        isinstance(label, str) and label.strip() for label in authority_labels
    ):
        findings.append("missing_authority_labels")

    recrawl_cadence = report.get("recrawlCadence", report.get("recrawl_cadence"))
    if not isinstance(recrawl_cadence, str) or not recrawl_cadence.strip():
        findings.append("missing_recrawl_cadence")

    canonical_url = report.get("canonicalUrl", report.get("canonical_url", ""))
    if _is_private_devhub_url(canonical_url):
        findings.append("private_devhub_path")

    if _has_any_present_key(report, RAW_BODY_KEYS):
        findings.append("raw_response_body")
    if _has_any_present_key(report, CREDENTIAL_KEYS):
        findings.append("credential_material")
    if _has_any_present_key(report, TRACE_KEYS):
        findings.append("trace_artifact")
    if _has_any_present_key(report, SCREENSHOT_KEYS):
        findings.append("screenshot_artifact")
    if _has_any_present_key(report, DOWNLOADED_DOCUMENT_KEYS):
        findings.append("downloaded_document")

    return findings


def _has_any_present_key(value: Any, unsafe_keys: set[str]) -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in unsafe_keys and child not in (None, "", [], {}):
                return True
            if _has_any_present_key(child, unsafe_keys):
                return True
    elif isinstance(value, list):
        return any(_has_any_present_key(child, unsafe_keys) for child in value)
    return False


def _is_private_devhub_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    if parsed.netloc.lower() != "devhub.portlandoregon.gov":
        return False
    path = parsed.path.lower()
    return any(part in path for part in PRIVATE_DEVHUB_PATH_PARTS)


if __name__ == "__main__":
    unittest.main()
