import copy
import unittest
from pathlib import Path

from ppd.readiness.release_readiness_snapshot import (
    build_release_readiness_snapshot,
    load_release_readiness_snapshot_fixture,
    validate_release_readiness_snapshot,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "readiness"
SNAPSHOT_FIXTURE = FIXTURE_DIR / "release_readiness_snapshot.json"


class ReleaseReadinessSnapshotTest(unittest.TestCase):
    def test_builds_non_production_snapshot_from_prerequisite_packets(self) -> None:
        snapshot = build_release_readiness_snapshot(
            burn_down_queue={
                "queue_id": "release-blocker-burndown-test",
                "queue_type": "ppd.release_blocker_burndown_queue.v1",
                "ordered_blockers": [
                    {
                        "blocker_id": "registry-candidate-not-promoted",
                        "summary": "Source registry candidate remains review-only.",
                        "priority_dimension": "source_freshness",
                    }
                ],
            },
            citation_normalization_packet={
                "packet_id": "source-evidence-citation-normalization-test",
                "packet_type": "ppd.source_evidence_citation_normalization_packet.v1",
            },
            stale_predicate_remediation_candidate={
                "candidate_id": "stale-predicate-remediation-candidate-v1",
                "packet_type": "ppd.stale_predicate_remediation_candidate.v1",
            },
            agent_regression_rerun_plan={
                "plan_id": "stale-predicate-remediation-agent-regression-rerun-v1",
                "plan_status": "fixture_only_no_llm_no_devhub_no_private_file_reads",
            },
            attended_pilot_dry_run_review={
                "packet_id": "attended-pilot-dry-run-review-v1",
                "packet_type": "attended_pilot_dry_run_review",
            },
        )

        self.assertEqual([], validate_release_readiness_snapshot(snapshot))
        self.assertEqual("non_production_operator_snapshot", snapshot["readiness_label"])
        self.assertFalse(snapshot["production_ready"])
        self.assertTrue(snapshot["unresolved_blockers"])
        self.assertTrue(snapshot["validation_summary"]["live_capabilities_disabled"])
        for value in snapshot["live_capabilities"].values():
            self.assertFalse(value)

    def test_committed_fixture_links_all_prerequisites_and_keeps_blockers_open(self) -> None:
        snapshot = load_release_readiness_snapshot_fixture(SNAPSHOT_FIXTURE)

        self.assertEqual([], validate_release_readiness_snapshot(snapshot))
        self.assertEqual(
            {
                "burn_down_queue",
                "citation_normalization_packet",
                "stale_predicate_remediation_candidate",
                "agent_regression_rerun_plan",
                "attended_pilot_dry_run_review",
            },
            set(snapshot["prerequisite_packets"]),
        )
        cited = set()
        for claim in snapshot["readiness_claims"]:
            cited.update(claim["citations"])
        self.assertEqual(set(snapshot["prerequisite_packets"]), cited)
        self.assertEqual(4, snapshot["validation_summary"]["unresolved_blocker_count"])
        self.assertTrue(all(blocker["status"] == "open" for blocker in snapshot["unresolved_blockers"]))

    def test_rejects_production_ready_label_with_unresolved_blockers(self) -> None:
        snapshot = load_release_readiness_snapshot_fixture(SNAPSHOT_FIXTURE)
        snapshot["production_ready"] = True
        snapshot["readiness_label"] = "production_ready"

        errors = validate_release_readiness_snapshot(snapshot)

        self.assertIn("production_ready must be false", errors)
        self.assertIn("readiness_label must be non_production_operator_snapshot", errors)

    def test_rejects_enabled_live_capabilities(self) -> None:
        snapshot = load_release_readiness_snapshot_fixture(SNAPSHOT_FIXTURE)
        snapshot["live_capabilities"]["live_crawl_enabled"] = True
        snapshot["live_capabilities"]["submission_enabled"] = True
        snapshot["disabled_capabilities"].remove("submission")

        errors = validate_release_readiness_snapshot(snapshot)

        self.assertIn("live_capabilities.live_crawl_enabled must be false", errors)
        self.assertIn("live_capabilities.submission_enabled must be false", errors)
        self.assertTrue(any("missing disabled capabilities" in error for error in errors), errors)

    def test_rejects_missing_prerequisite_claim_citation_and_private_artifact_marker(self) -> None:
        snapshot = copy.deepcopy(load_release_readiness_snapshot_fixture(SNAPSHOT_FIXTURE))
        del snapshot["prerequisite_packets"]["agent_regression_rerun_plan"]
        snapshot["readiness_claims"] = [snapshot["readiness_claims"][0]]
        snapshot["operator_next_actions"].append("Review trace.zip from an authenticated session.")

        errors = validate_release_readiness_snapshot(snapshot)

        self.assertTrue(any("prerequisite_packets.agent_regression_rerun_plan is required" in error for error in errors), errors)
        self.assertTrue(any("readiness_claims must cite every prerequisite packet" in error for error in errors), errors)
        self.assertTrue(any("forbidden private/session/raw artifact marker" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
