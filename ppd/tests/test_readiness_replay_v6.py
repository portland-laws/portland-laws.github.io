from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from ppd.logic.readiness_replay_v6 import (
    REQUIRED_REFERENCE_FIELDS,
    REQUIRED_RESPONSE_CHECKS,
    ValidationIssue,
    assert_post_recompile_agent_readiness_replay_v6,
    validate_post_recompile_agent_readiness_replay_v6,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_valid_packet() -> dict[str, object]:
    return json.loads((FIXTURE_DIR / "readiness_replay_v6_valid.json").read_text(encoding="utf-8"))


class ReadinessReplayV6ValidationTest(unittest.TestCase):
    def test_valid_fixture_passes(self) -> None:
        packet = load_valid_packet()
        self.assertEqual([], validate_post_recompile_agent_readiness_replay_v6(packet))
        assert_post_recompile_agent_readiness_replay_v6(packet)

    def test_rejects_missing_reviewer_and_inactive_guardrail_references(self) -> None:
        for field in REQUIRED_REFERENCE_FIELDS:
            packet = load_valid_packet()
            required_references = deepcopy(packet["required_references"])
            self.assertIsInstance(required_references, dict)
            del required_references[field]
            packet["required_references"] = required_references

            issues = validate_post_recompile_agent_readiness_replay_v6(packet)

            self.assertIssue(issues, "missing_required_reference", f"required_references.{field}")

    def test_rejects_active_guardrail_staging_reference(self) -> None:
        packet = load_valid_packet()
        packet["required_references"] = {
            "reviewer_packet_ref": "ppd://reviewer-packets/replay-v6/reviewer-packet.json",
            "inactive_guardrail_staging_ref": {"ref": "ppd://guardrails/staging/replay-v6.json", "active": True},
        }

        issues = validate_post_recompile_agent_readiness_replay_v6(packet)

        self.assertIssue(
            issues,
            "active_guardrail_staging_reference",
            "required_references.inactive_guardrail_staging_ref.active",
        )

    def test_rejects_each_missing_response_check(self) -> None:
        for field in REQUIRED_RESPONSE_CHECKS:
            packet = load_valid_packet()
            response_checks = deepcopy(packet["response_checks"])
            self.assertIsInstance(response_checks, dict)
            del response_checks[field]
            packet["response_checks"] = response_checks

            issues = validate_post_recompile_agent_readiness_replay_v6(packet)

            self.assertIssue(issues, "missing_response_check", f"response_checks.{field}")

    def test_rejects_missing_validation_commands(self) -> None:
        packet = load_valid_packet()
        packet["validation_commands"] = []

        issues = validate_post_recompile_agent_readiness_replay_v6(packet)

        self.assertIssue(issues, "missing_validation_commands", "validation_commands")

    def test_rejects_active_activation_live_crawl_official_guarantee_and_mutation_claims(self) -> None:
        forbidden_fields = (
            "active_activation_claims",
            "live_crawl_execution_claims",
            "official_action_completion_claims",
            "legal_or_permitting_guarantees",
            "active_mutation_flags",
        )
        for field in forbidden_fields:
            packet = load_valid_packet()
            packet[field] = True

            issues = validate_post_recompile_agent_readiness_replay_v6(packet)

            self.assertIssue(issues, "forbidden_active_claim", field)

    def test_rejects_private_session_auth_trace_and_raw_crawl_artifacts(self) -> None:
        forbidden_examples = {
            "cookies": {"session": "abc"},
            "auth_state_path": "playwright/.auth/devhub.json",
            "trace_path": "tmp/trace.zip",
            "har_path": "tmp/devhub.har",
            "raw_crawl_output": "tmp/raw-crawl/devhub.html",
            "payment_details": {"card_token": "tok_test"},
        }
        for key, value in forbidden_examples.items():
            packet = load_valid_packet()
            packet[key] = value

            issues = validate_post_recompile_agent_readiness_replay_v6(packet)

            self.assertTrue(
                any(issue.code == "forbidden_private_or_auth_artifact" for issue in issues),
                f"expected private artifact rejection for {key}; got {issues!r}",
            )

    def test_rejects_forbidden_claims_embedded_in_text(self) -> None:
        packet = load_valid_packet()
        packet["notes"] = ["The agent activated and submitted permit successfully."]

        issues = validate_post_recompile_agent_readiness_replay_v6(packet)

        self.assertIssue(issues, "forbidden_readiness_claim", "$.notes[0]")

    def test_assert_helper_raises_with_issue_details(self) -> None:
        packet = load_valid_packet()
        packet["validation_commands"] = []

        with self.assertRaisesRegex(ValueError, "validation_commands"):
            assert_post_recompile_agent_readiness_replay_v6(packet)

    def assertIssue(self, issues: list[ValidationIssue], code: str, path: str) -> None:
        self.assertTrue(
            any(issue.code == code and issue.path == path for issue in issues),
            f"missing issue {code} at {path}; got {issues!r}",
        )


if __name__ == "__main__":
    unittest.main()
