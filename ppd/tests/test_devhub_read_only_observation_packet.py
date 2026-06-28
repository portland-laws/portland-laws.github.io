from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

from ppd.devhub.read_only_observation_packet import (
    assert_devhub_read_only_observation_packet,
    validate_devhub_read_only_observation_packet,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub" / "read_only_observation_packet_valid.json"


class DevHubReadOnlyObservationPacketTest(unittest.TestCase):
    def load_packet(self) -> dict:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def finding_codes(self, packet: dict) -> set[str]:
        return {finding.code for finding in validate_devhub_read_only_observation_packet(packet).findings}

    def test_valid_fixture_passes(self) -> None:
        packet = self.load_packet()
        result = validate_devhub_read_only_observation_packet(packet)
        self.assertTrue(result.ok, result.messages())
        assert_devhub_read_only_observation_packet(packet)

    def test_rejects_private_session_artifacts_and_browser_artifact_paths(self) -> None:
        packet = self.load_packet()
        packet["observations"][0]["screenshot_path"] = "/home/example/devhub-shot.png"
        packet["observations"][0]["trace_path"] = "trace.zip"
        packet["observations"][0]["har_path"] = "network.har"
        packet["observations"][0]["storage_state"] = {"cookies": []}

        codes = self.finding_codes(packet)

        self.assertIn("private_session_artifact", codes)
        self.assertIn("local_private_path", codes)

    def test_rejects_raw_authenticated_values(self) -> None:
        packet = self.load_packet()
        packet["observations"][0]["raw_authenticated_value"] = "permit number 26-000000-000-00-CO"
        packet["observations"][0]["notes"] = "raw authenticated text from the private permit page"

        self.assertIn("raw_authenticated_value", self.finding_codes(packet))

    def test_rejects_unsafe_captcha_mfa_and_account_creation_automation_claims(self) -> None:
        packet = self.load_packet()
        packet["automation_claims"] = [
            "Agent will solve CAPTCHA if prompted.",
            "Agent can bypass MFA for the session.",
            "Agent will create a DevHub account automatically."
        ]

        self.assertIn("unsafe_automation_claim", self.finding_codes(packet))

    def test_allows_abort_prompts_that_name_unsupported_automation(self) -> None:
        packet = self.load_packet()
        packet["abort_prompts"].append("Do not automate CAPTCHA, MFA, account creation, payment, upload, submission, scheduling, cancellation, or certification.")

        result = validate_devhub_read_only_observation_packet(packet)

        self.assertTrue(result.ok, result.messages())

    def test_rejects_missing_reviewer_notes_and_abort_prompts(self) -> None:
        packet = self.load_packet()
        del packet["reviewer_notes"]
        packet["observations"][0]["abort_prompts"] = []

        codes = self.finding_codes(packet)

        self.assertIn("missing_reviewer_notes", codes)
        self.assertIn("missing_abort_prompts", codes)

    def test_rejects_enabled_consequential_controls(self) -> None:
        base = self.load_packet()
        for control_id in ("upload", "submission", "payment", "scheduling", "cancellation", "certification"):
            packet = copy.deepcopy(base)
            packet["observations"][0]["controls"] = [
                {"control_id": control_id, "enabled": True, "allowed": True, "control_state": "enabled"}
            ]
            with self.subTest(control_id=control_id):
                self.assertIn("enabled_consequential_control", self.finding_codes(packet))


if __name__ == "__main__":
    unittest.main()
