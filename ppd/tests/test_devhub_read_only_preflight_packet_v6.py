from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ppd.agent_readiness.devhub_read_only_preflight_packet_v6 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    PACKET_VERSION,
    validate_devhub_read_only_preflight_packet_v6,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "devhub_read_only_preflight_packet_v6" / "preflight_packet.json"


def load_packet() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def issue_messages(packet: dict) -> list[str]:
    return [issue.message for issue in validate_devhub_read_only_preflight_packet_v6(packet)]


class DevHubReadOnlyPreflightPacketV6Test(unittest.TestCase):
    def assert_rejects(self, packet: dict, expected_fragment: str) -> None:
        messages = issue_messages(packet)
        self.assertTrue(messages, "packet unexpectedly validated")
        self.assertTrue(any(expected_fragment in message for message in messages), messages)

    def test_fixture_packet_passes(self) -> None:
        packet = load_packet()

        self.assertEqual(PACKET_VERSION, packet["packet_version"])
        self.assertEqual(EXACT_OFFLINE_VALIDATION_COMMANDS, packet["validation_commands"])
        self.assertEqual([], validate_devhub_read_only_preflight_packet_v6(packet))

    def test_consumes_only_guardrail_v6_and_synthetic_surface_fixtures(self) -> None:
        packet = load_packet()
        source_types = {row["source_type"] for row in packet["source_fixtures"]}

        self.assertEqual({"agent_guardrail_api_compat_v6", "synthetic_devhub_surface_fixture"}, source_types)
        self.assertTrue(all(row["fixture_path"].startswith("ppd/tests/fixtures/") for row in packet["source_fixtures"]))

        packet = load_packet()
        packet["source_fixtures"] = packet["source_fixtures"][:1]
        self.assert_rejects(packet, "source_fixtures must include guardrail compatibility v6 and synthetic DevHub surface fixtures")

        packet = load_packet()
        packet["source_fixtures"][0]["source_type"] = "live_devhub_observation"
        self.assert_rejects(packet, "source fixture must be agent_guardrail_api_compat_v6 or synthetic_devhub_surface_fixture")

        packet = load_packet()
        packet["source_fixtures"][0]["live_fetch_performed"] = True
        self.assert_rejects(packet, "source fixture must not be live-fetched")

    def test_requires_manual_login_handoff_without_auth_storage(self) -> None:
        packet = load_packet()
        prereq_text = " ".join(row["requirement"] for row in packet["manual_login_handoff_prerequisites"])

        self.assertIn("user-owned account", prereq_text)
        self.assertIn("manually complete sign-in", prereq_text)
        self.assertFalse(packet["auth_state_stored"])

        packet = load_packet()
        packet["manual_login_handoff_prerequisites"] = [packet["manual_login_handoff_prerequisites"][0]]
        self.assert_rejects(packet, "manual-login handoff must require a user-owned account, manual sign-in, and read-only confirmation")

        packet = load_packet()
        packet["auth_state_stored"] = True
        self.assert_rejects(packet, "packet must not store auth state")

    def test_read_only_page_categories_are_exact(self) -> None:
        packet = load_packet()
        packet["allowed_read_only_page_categories"].append("edit_application")

        self.assert_rejects(packet, "allowed page categories must exactly match the read-only DevHub category set")

    def test_refuses_captcha_mfa_and_account_creation_paths(self) -> None:
        packet = load_packet()
        topics = {row["topic"] for row in packet["refused_paths"]}

        self.assertTrue({"captcha", "mfa", "account_creation"}.issubset(topics))
        self.assertTrue(all(row["disposition"] == "refuse_and_manual_handoff" for row in packet["refused_paths"]))
        self.assertTrue(all(row["automated"] is False for row in packet["refused_paths"]))

        packet = load_packet()
        packet["refused_paths"] = [row for row in packet["refused_paths"] if row["topic"] != "captcha"]
        self.assert_rejects(packet, "refused paths must cover CAPTCHA, MFA, and account creation")

        packet = load_packet()
        packet["refused_paths"][0]["automated"] = True
        self.assert_rejects(packet, "refused paths must not be automated")

    def test_requires_redaction_rules_synthetic_accessible_fields_and_private_exclusions(self) -> None:
        packet = load_packet()
        self.assertIn("synthetic_accessible_name", packet["accessible_structure_capture_fields"])
        self.assertIn("screenshots", packet["private_artifact_exclusions"])
        self.assertIn("har_files", packet["private_artifact_exclusions"])
        self.assertIn("private_documents", packet["private_artifact_exclusions"])

        packet = load_packet()
        packet["redaction_requirements"] = [packet["redaction_requirements"][0]]
        self.assert_rejects(packet, "redaction requirements must require synthetic placeholders, non-capture of private artifacts, and synthetic metadata only")

        packet = load_packet()
        packet["accessible_structure_capture_fields"].remove("synthetic_accessible_name")
        self.assert_rejects(packet, "accessible capture fields must include the required synthetic structure fields")

        packet = load_packet()
        packet["accessible_structure_capture_fields"].append("raw_value")
        self.assert_rejects(packet, "capture fields must be synthetic metadata fields")

        packet = load_packet()
        packet["private_artifact_exclusions"].remove("traces")
        self.assert_rejects(packet, "private artifact exclusions must cover auth, browser artifacts, private documents, raw values, paths, and payment details")

    def test_timeout_abort_and_review_placeholders_have_no_captured_data(self) -> None:
        packet = load_packet()
        self.assertTrue(all(row["action"] == "abort_without_artifact_capture" for row in packet["timeout_abort_criteria"]))
        self.assertTrue(all(row["status"] == "placeholder_only" for row in packet["post_capture_review_placeholders"]))
        self.assertTrue(all(row["contains_captured_devhub_data"] is False for row in packet["post_capture_review_placeholders"]))

        packet = load_packet()
        packet["timeout_abort_criteria"][0]["action"] = "save_screenshot_then_abort"
        self.assert_rejects(packet, "timeout action must abort without artifact capture")

        packet = load_packet()
        packet["post_capture_review_placeholders"][0]["contains_captured_devhub_data"] = True
        self.assert_rejects(packet, "review placeholders must not contain captured DevHub data")

    def test_no_effect_policy_blocks_private_artifacts_and_official_actions(self) -> None:
        for key in packet_no_effect_keys():
            packet = load_packet()
            packet["no_effect_policy"][key] = True
            self.assert_rejects(packet, f"no_effect_policy.{key} must be false")

    def test_validation_commands_are_exact_offline_commands(self) -> None:
        packet = load_packet()
        packet["validation_commands"] = [["python3", "-m", "unittest", "discover"]]

        self.assert_rejects(packet, "validation_commands must exactly match the offline packet commands")

    def test_rejects_live_access_claims_private_artifacts_completion_guarantees_and_mutation_flags(self) -> None:
        base = load_packet()

        cases: list[tuple[dict, str]] = []

        packet = copy.deepcopy(base)
        packet["devhub_opened"] = True
        cases.append((packet, "packet must not open DevHub"))

        packet = copy.deepcopy(base)
        packet["operator_claim"] = "live DevHub access completed"
        cases.append((packet, "packet must not claim live DevHub access"))

        packet = copy.deepcopy(base)
        packet["auth_state"] = {"storage_state": "private"}
        cases.append((packet, "packet must not include private session, auth, browser, document, or payment artifacts"))

        packet = copy.deepcopy(base)
        packet["submitted"] = True
        cases.append((packet, "packet must not claim official DevHub completion"))

        packet = copy.deepcopy(base)
        packet["legal_result"] = "permit approved"
        cases.append((packet, "packet must not make legal or permitting guarantees"))

        packet = copy.deepcopy(base)
        packet["active_mutation_enabled"] = True
        cases.append((packet, "packet must not enable active mutation flags"))

        for packet, expected in cases:
            with self.subTest(expected=expected):
                self.assert_rejects(packet, expected)


def packet_no_effect_keys() -> tuple[str, ...]:
    return (
        "opens_devhub",
        "stores_auth_state",
        "creates_traces",
        "creates_screenshots",
        "creates_har_files",
        "reads_private_documents",
        "uploads",
        "submits",
        "certifies",
        "pays",
        "schedules",
        "creates_accounts",
        "makes_legal_or_permitting_guarantees",
    )


if __name__ == "__main__":
    unittest.main()
