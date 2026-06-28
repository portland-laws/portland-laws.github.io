from __future__ import annotations

import unittest
from pathlib import Path

from ppd.devhub.readonly_pilot_evidence_review import (
    build_readonly_pilot_evidence_review_packet,
    load_json_fixture,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "devhub_readonly_pilot_evidence_review"


class DevHubReadonlyPilotEvidenceReviewTests(unittest.TestCase):
    def test_builds_fixture_first_review_packet_without_private_artifacts(self) -> None:
        runbook = load_json_fixture(FIXTURE_DIR / "attended_readonly_pilot_runbook_candidate.json")
        observation = load_json_fixture(FIXTURE_DIR / "redacted_observation_packet.json")
        drift = load_json_fixture(FIXTURE_DIR / "surface_drift_comparison_packet.json")

        packet = build_readonly_pilot_evidence_review_packet(runbook, observation, drift)

        self.assertEqual(packet["pilot_id"], "devhub-readonly-pilot-fixture-001")
        self.assertFalse(packet["browser_launched"])
        self.assertFalse(packet["private_artifacts_persisted"])
        self.assertEqual(len(packet["synthetic_surface_review_findings"]), 2)
        self.assertEqual(len(packet["selector_confidence_notes"]), 3)
        self.assertEqual(len(packet["redaction_attestations"]), 2)
        self.assertEqual(len(packet["surface_registry_candidate_references"]), 2)

        statuses = {
            finding["surface_id"]: finding["review_status"]
            for finding in packet["synthetic_surface_review_findings"]
        }
        self.assertEqual(statuses["devhub-home-readonly"], "accepted_read_only")
        self.assertEqual(statuses["devhub-permit-detail-readonly"], "manual_review_required")
        self.assertTrue(
            any(
                checkpoint["checkpoint_id"] == "handoff-devhub-permit-detail-readonly"
                for checkpoint in packet["manual_handoff_checkpoints"]
            )
        )

    def test_rejects_raw_authenticated_values(self) -> None:
        runbook = load_json_fixture(FIXTURE_DIR / "attended_readonly_pilot_runbook_candidate.json")
        observation = load_json_fixture(FIXTURE_DIR / "redacted_observation_packet.json")
        drift = load_json_fixture(FIXTURE_DIR / "surface_drift_comparison_packet.json")
        observation["raw_authenticated_values_present"] = True

        with self.assertRaises(ValueError):
            build_readonly_pilot_evidence_review_packet(runbook, observation, drift)

    def test_rejects_session_artifact_capture(self) -> None:
        runbook = load_json_fixture(FIXTURE_DIR / "attended_readonly_pilot_runbook_candidate.json")
        observation = load_json_fixture(FIXTURE_DIR / "redacted_observation_packet.json")
        drift = load_json_fixture(FIXTURE_DIR / "surface_drift_comparison_packet.json")
        observation["captured_artifacts"]["auth_state"] = {"path": "private-state.json"}

        with self.assertRaises(ValueError):
            build_readonly_pilot_evidence_review_packet(runbook, observation, drift)


if __name__ == "__main__":
    unittest.main()
