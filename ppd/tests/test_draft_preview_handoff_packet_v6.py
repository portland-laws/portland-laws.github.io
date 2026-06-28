from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.devhub.draft_preview_handoff_packet_v6 import (
    build_guarded_draft_preview_handoff_packet_v6,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "draft_preview_handoff_packet_v6"


class DraftPreviewHandoffPacketV6Test(unittest.TestCase):
    def test_builds_expected_packet_from_v6_fixtures(self) -> None:
        guardrail = _load_json("agent_guardrail_api_compatibility_packet_v6.json")
        preflight = _load_json("attended_devhub_read_only_preflight_packet_v6.json")
        expected = _load_json("expected_guarded_draft_preview_handoff_packet_v6.json")

        actual = build_guarded_draft_preview_handoff_packet_v6(guardrail, preflight)

        self.assertEqual(actual, expected)

    def test_rejects_non_v6_inputs(self) -> None:
        guardrail = _load_json("agent_guardrail_api_compatibility_packet_v6.json")
        preflight = _load_json("attended_devhub_read_only_preflight_packet_v6.json")
        guardrail["packet_version"] = "v5"

        with self.assertRaises(ValueError):
            build_guarded_draft_preview_handoff_packet_v6(guardrail, preflight)

    def test_packet_blocks_consequential_actions(self) -> None:
        packet = build_guarded_draft_preview_handoff_packet_v6(
            _load_json("agent_guardrail_api_compatibility_packet_v6.json"),
            _load_json("attended_devhub_read_only_preflight_packet_v6.json"),
        )

        blocked = {
            action
            for gate in packet["stop_gates"]
            for action in gate["blocked_actions"]
        }
        self.assertIn("upload", blocked)
        self.assertIn("final_submit", blocked)
        self.assertIn("submit_payment", blocked)
        self.assertIn("certify", blocked)
        self.assertFalse(any(row["may_autofill_devhub"] for row in packet["reversible_draft_preview_rows"]))


def _load_json(name: str) -> dict:
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


if __name__ == "__main__":
    unittest.main()
