from __future__ import annotations

import copy
from pathlib import Path
import unittest

from ppd.agent_readiness.public_refresh_reviewer_disposition_packet_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    build_public_refresh_reviewer_disposition_packet_from_fixture,
    build_public_refresh_reviewer_disposition_packet_v1,
    load_public_refresh_reviewer_disposition_fixture,
    validate_public_refresh_reviewer_disposition_packet_v1,
)

FIXTURE = Path(__file__).parent / "fixtures" / "public_refresh_reviewer_disposition_packet_v1.json"


class PublicRefreshReviewerDispositionPacketV1Tests(unittest.TestCase):
    def test_builds_fixture_first_disposition_packet_from_synthetic_handoff_rows(self) -> None:
        packet = build_public_refresh_reviewer_disposition_packet_from_fixture(FIXTURE)

        self.assertEqual(packet["packet_version"], "public-refresh-reviewer-disposition-packet-v1")
        self.assertEqual(packet["input_contract"], "synthetic_public_refresh_reviewer_handoff_rows_only")
        self.assertEqual(packet["handoff_row_count"], 4)
        self.assertEqual(
            {row["seed_decision"] for row in packet["seed_decisions"]},
            {"approved", "held", "skipped", "needs_human_review"},
        )
        self.assertEqual(
            packet["exact_offline_validation_commands"],
            [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS],
        )
        validate_public_refresh_reviewer_disposition_packet_v1(packet)

    def test_records_priority_dispositions_stale_outcomes_signoffs_dependencies_and_rollbacks(self) -> None:
        packet = build_public_refresh_reviewer_disposition_packet_from_fixture(FIXTURE)

        self.assertEqual(len(packet["citation_refresh_priority_dispositions"]), 4)
        self.assertEqual(len(packet["stale_source_hold_outcomes"]), 4)
        self.assertEqual(len(packet["owner_signoff_placeholders"]), 4)
        self.assertEqual(len(packet["dependency_sequencing"]), 4)
        self.assertEqual(len(packet["rollback_checkpoints"]), 4)
        self.assertTrue(all(row["signed_off"] is False for row in packet["owner_signoff_placeholders"]))
        sequence_by_row = {
            row["row_id"]: row["ordered_steps"]
            for row in packet["dependency_sequencing"]
        }
        self.assertIn("record seed decision", sequence_by_row["seed-approved-001"])
        self.assertIn("confirm rollback checkpoint", sequence_by_row["seed-needs-human-review-001"])

    def test_rejects_non_synthetic_handoff_rows(self) -> None:
        rows = list(load_public_refresh_reviewer_disposition_fixture(FIXTURE))
        bad_row = dict(rows[0])
        bad_row["synthetic_public_refresh_reviewer_handoff_row"] = False
        rows[0] = bad_row

        with self.assertRaisesRegex(ValueError, "synthetic_public_refresh_reviewer_handoff_row true"):
            build_public_refresh_reviewer_disposition_packet_v1(rows)

    def test_rejects_live_or_mutating_handoff_flags(self) -> None:
        rows = list(load_public_refresh_reviewer_disposition_fixture(FIXTURE))
        bad_row = dict(rows[0])
        bad_row["live_crawl"] = True
        rows[0] = bad_row

        with self.assertRaisesRegex(ValueError, "live_crawl false"):
            build_public_refresh_reviewer_disposition_packet_v1(rows)

    def test_rejects_raw_or_private_runtime_keys(self) -> None:
        rows = list(load_public_refresh_reviewer_disposition_fixture(FIXTURE))
        bad_row = dict(rows[0])
        bad_row["raw_output"] = "fixture must not include raw runtime material"
        rows[0] = bad_row

        with self.assertRaisesRegex(ValueError, "raw_output"):
            build_public_refresh_reviewer_disposition_packet_v1(rows)

    def test_rejects_missing_exact_offline_validation_commands(self) -> None:
        packet = build_public_refresh_reviewer_disposition_packet_from_fixture(FIXTURE)
        packet = copy.deepcopy(packet)
        packet["exact_offline_validation_commands"] = []

        with self.assertRaisesRegex(ValueError, "exact offline validation commands"):
            validate_public_refresh_reviewer_disposition_packet_v1(packet)

    def test_rejects_packet_missing_required_seed_decision_category(self) -> None:
        packet = build_public_refresh_reviewer_disposition_packet_from_fixture(FIXTURE)
        packet = copy.deepcopy(packet)
        packet["seed_decisions"] = [
            row for row in packet["seed_decisions"] if row["seed_decision"] != "skipped"
        ]

        with self.assertRaisesRegex(ValueError, "all seed decision categories"):
            validate_public_refresh_reviewer_disposition_packet_v1(packet)


if __name__ == "__main__":
    unittest.main()
