from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.devhub.correction_upload_boundary import (
    assert_correction_upload_boundary_packet,
    validate_correction_upload_boundary_packet,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "correction_upload_boundary"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


class CorrectionUploadBoundaryTests(unittest.TestCase):
    def test_accepts_safe_cited_review_packet(self) -> None:
        packet = load_fixture("safe_packet.json")

        result = validate_correction_upload_boundary_packet(packet)

        self.assertTrue(result.ok)
        self.assertEqual((), result.violations)
        assert_correction_upload_boundary_packet(packet)

    def test_rejects_private_artifacts_completion_claims_and_unsafe_actions(self) -> None:
        packet = load_fixture("unsafe_packet.json")

        result = validate_correction_upload_boundary_packet(packet)

        self.assertFalse(result.ok)
        codes = {violation.code for violation in result.violations}
        self.assertIn("official_completion_claim", codes)
        self.assertIn("private_document_content", codes)
        self.assertIn("local_private_path", codes)
        self.assertIn("browser_state", codes)
        self.assertIn("browser_capture_artifact", codes)
        self.assertIn("uncited_correction_requirement", codes)
        self.assertIn("unsafe_next_action", codes)

    def test_assertion_reports_all_relevant_failure_codes(self) -> None:
        packet = load_fixture("unsafe_packet.json")

        with self.assertRaises(ValueError) as raised:
            assert_correction_upload_boundary_packet(packet)

        message = str(raised.exception)
        self.assertIn("official_completion_claim", message)
        self.assertIn("unsafe_next_action", message)
        self.assertIn("uncited_correction_requirement", message)

    def test_rejects_unclear_next_action_even_when_not_explicitly_final(self) -> None:
        packet = load_fixture("safe_packet.json")
        packet["next_actions"] = ["Proceed in DevHub."]

        result = validate_correction_upload_boundary_packet(packet)

        self.assertFalse(result.ok)
        self.assertIn("unbounded_next_action", {violation.code for violation in result.violations})


if __name__ == "__main__":
    unittest.main()
