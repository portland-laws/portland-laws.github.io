from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ppd.public_source_refresh_operator_dry_run import (
    assert_valid_public_source_refresh_operator_dry_run_transcript,
    build_public_source_refresh_operator_dry_run_transcript,
    validate_public_source_refresh_operator_dry_run_transcript,
)


class PublicSourceRefreshOperatorDryRunTest(unittest.TestCase):
    def _build_transcript(self) -> dict[str, object]:
        fixture_path = (
            Path(__file__).parent
            / "fixtures"
            / "public_source_refresh_operator_dry_run"
            / "input_packets.json"
        )
        packets = json.loads(fixture_path.read_text(encoding="utf-8"))

        return build_public_source_refresh_operator_dry_run_transcript(
            packets["source_refresh_runbook_candidate"],
            packets["public_source_refresh_batch_packet"],
            packets["public_source_refresh_intake_evidence_packet"],
            packets["source_registry_schedule_update_candidate"],
            reviewer="ppd-reviewer",
            owner="ppd-source-refresh-owner",
        )

    def test_builds_metadata_only_operator_transcript_from_fixture_packets(self) -> None:
        transcript = self._build_transcript()

        self.assertEqual(
            transcript["packet_type"],
            "public_source_refresh_operator_dry_run_transcript",
        )
        self.assertEqual(transcript["mode"], "fixture_first_dry_run")
        self.assertEqual(transcript["sources"], ["portland-auditor-code"])
        self.assertEqual(transcript["reviewer"], "ppd-reviewer")
        self.assertEqual(transcript["owner"], "ppd-source-refresh-owner")
        self.assertEqual(
            [step["order"] for step in transcript["ordered_simulated_operator_steps"]],
            [1, 2, 3, 4, 5],
        )
        self.assertIn(
            "fixture://allowlist/portland-auditor-code.json",
            transcript["allowlist_evidence_refs"],
        )
        self.assertIn(
            "fixture://robots/portland-auditor-code.txt",
            transcript["robots_evidence_refs"],
        )
        self.assertTrue(transcript["abort_or_rollback_checkpoints"])
        self.assertEqual(
            transcript["attestations"],
            {
                "no_fetch": True,
                "no_processor": True,
                "no_download": True,
                "no_schedule_mutation": True,
                "no_registry_mutation": True,
                "metadata_only_observations": True,
            },
        )
        assert_valid_public_source_refresh_operator_dry_run_transcript(transcript)

    def test_rejects_unsafe_operator_dry_run_transcript_packets(self) -> None:
        transcript = copy.deepcopy(self._build_transcript())
        steps = transcript["ordered_simulated_operator_steps"]
        self.assertIsInstance(steps, list)
        steps[1]["order"] = 4
        steps[2].pop("observation_citations")
        steps[2]["target_url"] = "https://example.invalid/login"
        transcript["allowlist_evidence_refs"] = []
        transcript["robots_evidence_refs"] = []
        transcript["abort_or_rollback_checkpoints"] = [
            {"checkpoint": "operator-review-only", "operator_action": "pause for reviewer"}
        ]
        transcript["reviewer"] = ""
        transcript["owner"] = ""
        transcript["raw_body_ref"] = "raw_crawl/output/body.html"
        transcript["live_crawl_executed"] = True
        transcript["processor_execution_note"] = "processor executed against source refresh target"
        transcript["legal_statement"] = "permit will be approved after this refresh"
        transcript["active_registry_mutation"] = True
        transcript["active_schedule_mutation"] = True

        errors = validate_public_source_refresh_operator_dry_run_transcript(transcript)
        joined = "\n".join(errors)

        self.assertIn("ordered_steps_unordered", errors)
        self.assertIn("allowlist_evidence_refs_missing", errors)
        self.assertIn("robots_evidence_refs_missing", errors)
        self.assertIn("ordered_steps[2].metadata_observation_uncited", errors)
        self.assertIn("abort_checkpoint_missing", errors)
        self.assertIn("rollback_checkpoint_missing", errors)
        self.assertIn("reviewer_missing", errors)
        self.assertIn("owner_missing", errors)
        self.assertIn("non_allowlisted_url", joined)
        self.assertIn("authenticated_url", joined)
        self.assertIn("raw_reference_field", joined)
        self.assertIn("raw_reference_value", joined)
        self.assertIn("live_execution_claim", joined)
        self.assertIn("legal_or_permitting_outcome_guarantee", joined)
        self.assertIn("active_mutation_flag", joined)


if __name__ == "__main__":
    unittest.main()
