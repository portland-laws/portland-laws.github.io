from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import unittest

from ppd.agent_readiness.release_blocker_reconciliation import (
    require_agent_readiness_release_blocker_reconciliation_packet,
    validate_agent_readiness_release_blocker_reconciliation_packet,
)


_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "agent_readiness" / "release_blocker_reconciliation_packets.json"


class ReleaseBlockerReconciliationValidationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixtures = json.loads(_FIXTURE_PATH.read_text(encoding="utf-8"))
        self.now = datetime(2026, 5, 28, tzinfo=timezone.utc)

    def test_valid_blocked_packet_is_accepted(self) -> None:
        result = validate_agent_readiness_release_blocker_reconciliation_packet(
            self.fixtures["valid"],
            now=self.now,
        )

        self.assertTrue(result.ready)
        self.assertEqual((), result.problems)

    def test_invalid_packet_rejects_release_reconciliation_hazards(self) -> None:
        result = validate_agent_readiness_release_blocker_reconciliation_packet(
            self.fixtures["invalid"],
            now=self.now,
        )

        self.assertFalse(result.ready)
        joined = "\n".join(result.problems)
        self.assertIn("lacks source_evidence_ids", joined)
        self.assertIn("lacks prerequisite_links", joined)
        self.assertIn("private or session artifact", joined)
        self.assertIn("local private path", joined)
        self.assertIn("raw crawl/download/archive reference", joined)
        self.assertIn("claimed current without acknowledgement", joined)
        self.assertIn("production-ready release label", joined)
        self.assertIn("legal or permitting outcome guarantee", joined)
        self.assertIn("live network or DevHub execution claim", joined)
        self.assertIn("enabled consequential control", joined)

    def test_require_raises_value_error_for_invalid_packet(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid_release_blocker_reconciliation_packet"):
            require_agent_readiness_release_blocker_reconciliation_packet(
                self.fixtures["invalid"],
                now=self.now,
            )


if __name__ == "__main__":
    unittest.main()
