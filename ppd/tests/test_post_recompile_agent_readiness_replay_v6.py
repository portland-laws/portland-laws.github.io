import json
import subprocess
import sys
import unittest
from pathlib import Path

from ppd.agent_readiness.post_recompile_agent_readiness_replay_v6 import (
    FIXTURE_DIR,
    OFFLINE_VALIDATION_COMMANDS,
    REQUIRED_SCENARIOS,
    ReplayFixtureError,
    build_replay,
    load_manifest,
    validate_replay,
)


class PostRecompileAgentReadinessReplayV6Test(unittest.TestCase):
    def test_manifest_allows_only_guardrail_reviewer_and_inactive_staging_fixtures(self):
        manifest = load_manifest()
        kinds = {entry["kind"] for entry in manifest["fixtures"]}
        self.assertEqual(
            kinds,
            {
                "guardrail_recompile_reviewer_packet_v6",
                "inactive_guardrail_staging_agent_responses_v6",
            },
        )
        for entry in manifest["fixtures"]:
            self.assertFalse(entry["file"].startswith("."))
            self.assertNotIn("/", entry["file"])
            self.assertTrue((FIXTURE_DIR / entry["file"]).is_file())

    def test_replay_covers_required_agent_facing_responses_without_side_effects(self):
        replay = build_replay()
        self.assertEqual(replay["mode"], "fixture_first_offline_only")
        self.assertFalse(replay["guardrails_active"])
        self.assertFalse(replay["opened_devhub"])
        self.assertFalse(replay["live_sites_crawled"])
        self.assertFalse(replay["private_documents_read"])
        self.assertEqual(tuple(replay["offline_validation_commands"]), OFFLINE_VALIDATION_COMMANDS)

        cases = {case["scenario"]: case for case in replay["cases"]}
        self.assertEqual(set(REQUIRED_SCENARIOS), set(cases))
        self.assertEqual(cases["missing_information"]["response_type"], "ask_for_missing_information")
        self.assertEqual(cases["stale_evidence"]["evidence_status"], "stale")
        self.assertEqual(cases["reversible_draft"]["response_type"], "reversible_draft")
        self.assertIn("local PDF preview", cases["local_pdf_preview"]["response"])
        self.assertIn("exact confirmation", cases["exact_confirmation_checkpoint"]["response"])
        self.assertEqual(cases["refused_consequential_action"]["response_type"], "refusal")
        self.assertEqual(cases["refused_financial_action"]["response_type"], "refusal")
        self.assertEqual(cases["rollback_visibility"]["response_type"], "rollback_visibility")
        self.assertEqual(cases["manual_handoff"]["response_type"], "manual_handoff")

    def test_replay_responses_do_not_claim_forbidden_actions_or_guarantees(self):
        replay = build_replay()
        forbidden_phrases = (
            "I uploaded",
            "I submitted",
            "I certified",
            "I paid",
            "I scheduled",
            "I opened DevHub",
            "I crawled",
            "I guarantee approval",
        )
        for case in replay["cases"]:
            for phrase in forbidden_phrases:
                self.assertNotIn(phrase, case["response"])

    def test_validator_rejects_guardrail_activation(self):
        replay = build_replay()
        replay["guardrails_active"] = True
        with self.assertRaises(ReplayFixtureError):
            validate_replay(replay)

    def test_module_fixtures_only_command_is_offline_and_deterministic(self):
        result = subprocess.run(
            [sys.executable, "-m", "ppd.agent_readiness.post_recompile_agent_readiness_replay_v6", "--fixtures-only"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        payload = json.loads(result.stdout)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["case_count"], len(REQUIRED_SCENARIOS))
        self.assertEqual(tuple(payload["commands"]), OFFLINE_VALIDATION_COMMANDS)
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
