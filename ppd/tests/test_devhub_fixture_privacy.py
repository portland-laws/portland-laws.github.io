"""Validate DevHub workflow fixture privacy checks."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.devhub.privacy_validation import (
    validate_devhub_fixture_privacy,
    validate_devhub_fixture_privacy_file,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_privacy"
WORKFLOW_FIXTURE = Path(__file__).parent / "fixtures" / "devhub-workflows" / "mock_workflow_snapshots.json"


class DevHubFixturePrivacyTests(unittest.TestCase):
    def test_redacted_fixture_passes_privacy_validation(self) -> None:
        errors = validate_devhub_fixture_privacy_file(FIXTURE_DIR / "redacted_workflow_fixture.json")
        self.assertEqual(errors, [])

    def test_existing_mock_workflow_snapshot_passes_privacy_validation(self) -> None:
        errors = validate_devhub_fixture_privacy_file(WORKFLOW_FIXTURE)
        self.assertEqual(errors, [])

    def test_unsafe_fixture_rejects_credentials_auth_traces_and_pii(self) -> None:
        errors = validate_devhub_fixture_privacy_file(FIXTURE_DIR / "unsafe_workflow_fixture.json")
        joined = "\n".join(errors)
        self.assertIn("authState contains sensitive DevHub/session artifact data", joined)
        self.assertIn("traceFile contains sensitive DevHub/session artifact data", joined)
        self.assertIn("screenshot contains sensitive DevHub/session artifact data", joined)
        self.assertIn("unredacted email address", joined)
        self.assertIn("unredacted US phone number", joined)

    def test_inline_values_reject_secret_markers(self) -> None:
        errors = validate_devhub_fixture_privacy(
            {
                "safe": "[REDACTED]",
                "notes": "Bearer abc123 should not be committed",
                "storageStatePath": "storage-state.json"
            }
        )
        joined = "\n".join(errors)
        self.assertIn("sensitive artifact marker 'bearer '", joined)
        self.assertIn("storageStatePath contains sensitive DevHub/session artifact data", joined)


if __name__ == "__main__":
    unittest.main()
