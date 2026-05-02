"""Tests for mocked DevHub exact-confirmation checkpoint fixtures."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.devhub.exact_confirmation_checkpoint import (
    validate_exact_confirmation_checkpoint_contract,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "exact_confirmation_checkpoint_contract.json"


class DevHubExactConfirmationCheckpointContractTest(unittest.TestCase):
    def test_fixture_contract_is_valid_and_refuses_by_default(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

        findings = validate_exact_confirmation_checkpoint_contract(fixture)

        self.assertEqual([], [f"{finding.path}: {finding.message}" for finding in findings])
        self.assertFalse(fixture["liveDevHubUsed"])
        self.assertFalse(fixture["browserLaunched"])
        self.assertTrue(fixture["fixtureOnly"])

        classifications = {checkpoint["classification"] for checkpoint in fixture["checkpoints"]}
        self.assertEqual({"consequential", "financial"}, classifications)
        for checkpoint in fixture["checkpoints"]:
            confirmation = checkpoint["confirmation"]
            self.assertFalse(confirmation["exactUserConfirmationPresent"])
            self.assertEqual("refuse", confirmation["defaultDecision"])
            self.assertTrue(confirmation["refusedBeforeConfirmation"])
            self.assertFalse(confirmation["executable"])
            self.assertTrue(checkpoint["auditEventRef"].startswith("ppd-audit-event:"))
            self.assertTrue(checkpoint["actionPreview"]["redactedTarget"].startswith("[REDACTED:"))
            self.assertFalse(checkpoint["actionPreview"]["containsPrivateValues"])
            self.assertTrue(checkpoint["consequenceSummary"]["sourceEvidenceIds"])

    def test_fixture_has_no_executed_forbidden_actions(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        assertions = fixture["nonAutomationAssertions"]

        self.assertTrue(assertions["noUpload"])
        self.assertTrue(assertions["noSubmit"])
        self.assertTrue(assertions["noCertification"])
        self.assertTrue(assertions["noPayment"])
        self.assertTrue(assertions["noCancellation"])
        self.assertTrue(assertions["noInspectionScheduling"])
        self.assertTrue(assertions["noMfaAutomation"])
        self.assertTrue(assertions["noCaptchaAutomation"])
        self.assertTrue(assertions["noAccountCreation"])
        self.assertTrue(assertions["noPasswordRecovery"])


if __name__ == "__main__":
    unittest.main()
