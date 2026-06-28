from __future__ import annotations

import unittest

from ppd.public_refresh_authorization_v7 import validate_public_refresh_authorization_packet_v7


def valid_packet() -> dict[str, object]:
    return {
        "packet_version": 7,
        "compatibility_refs": ["agent-api-compatibility-matrix-v7"],
        "smoke_replay_refs": ["post-decision-smoke-replay-v5"],
        "rollback_readiness_refs": ["rollback-packet-v6"],
        "source_registry_refs": ["source-registry-schedule-update-candidate"],
        "next_refresh_watch_rows": [
            {
                "source_id": "ppd-devhub-faq",
                "next_refresh_due": "2026-06-03",
                "owner_placeholder": "ppd-public-refresh-reviewer",
            }
        ],
        "stale_source_risk_notes": ["Review stale DevHub FAQ citations before promotion."],
        "citation_repair_owner_placeholders": [
            {"citation_id": "cite-devhub-faq-001", "owner_placeholder": "ppd-citation-repair-owner"}
        ],
        "guarded_automation_hold_conditions": [
            "Hold crawler, browser, processor, registry, requirement, and guardrail mutation until offline validation passes."
        ],
        "public_recrawl_authorization_prerequisites": [
            "Allowlist and robots preflight evidence is present.",
            "Raw artifact prohibition remains in force.",
        ],
        "validation_commands": [["python3", "ppd/daemon/ppd_daemon.py", "--self-test"]],
    }


class PublicRefreshAuthorizationV7Test(unittest.TestCase):
    def test_accepts_complete_fixture_first_handoff(self) -> None:
        result = validate_public_refresh_authorization_packet_v7(valid_packet())
        self.assertTrue(result.valid, result.errors)

    def test_rejects_each_missing_required_handoff_section(self) -> None:
        expected_errors = {
            "compatibility_refs": "missing compatibility references",
            "smoke_replay_refs": "missing smoke replay references",
            "rollback_readiness_refs": "missing rollback references",
            "source_registry_refs": "missing source registry references",
            "next_refresh_watch_rows": "missing next-refresh watch rows",
            "stale_source_risk_notes": "missing stale-source risk notes",
            "citation_repair_owner_placeholders": "missing citation repair owner placeholders",
            "guarded_automation_hold_conditions": "missing guarded automation hold conditions",
            "public_recrawl_authorization_prerequisites": "missing public recrawl authorization prerequisites",
            "validation_commands": "missing validation commands",
        }
        for key, message in expected_errors.items():
            with self.subTest(key=key):
                packet = valid_packet()
                packet.pop(key)
                result = validate_public_refresh_authorization_packet_v7(packet)
                self.assertFalse(result.valid)
                self.assertIn(message, result.errors)

    def test_rejects_unsafe_claims_and_artifacts(self) -> None:
        unsafe_cases = (
            ({"claim": "live crawl was executed"}, "rejects live crawl execution claims"),
            ({"downloaded_document": "public form pdf"}, "rejects downloaded or raw crawl artifacts"),
            ({"session_state": {"path": "state.json"}}, "rejects private/session/auth artifacts"),
            ({"official_action_completion": "completed"}, "rejects official-action completion claims"),
            ({"claim": "permit guarantee"}, "rejects legal or permitting guarantees"),
            ({"active_mutation_flags": ["registry"]}, "rejects active mutation flags"),
        )
        for extra, message in unsafe_cases:
            with self.subTest(message=message):
                packet = valid_packet()
                packet.update(extra)
                result = validate_public_refresh_authorization_packet_v7(packet)
                self.assertFalse(result.valid)
                self.assertIn(message, result.errors)

    def test_rejects_malformed_validation_commands(self) -> None:
        packet = valid_packet()
        packet["validation_commands"] = ["python3 ppd/daemon/ppd_daemon.py --self-test"]
        result = validate_public_refresh_authorization_packet_v7(packet)
        self.assertFalse(result.valid)
        self.assertIn("validation commands must be non-empty argv arrays", result.errors)


if __name__ == "__main__":
    unittest.main()
