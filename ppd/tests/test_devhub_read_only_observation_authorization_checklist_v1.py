from __future__ import annotations

from pathlib import Path
import copy
import unittest

from ppd.authorization.devhub_read_only_observation_authorization_checklist_v1 import (
    CHECKLIST_VERSION,
    assert_valid_authorization_checklist_v1,
    build_authorization_checklist_v1,
    load_json_packet,
    validate_authorization_checklist_v1,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub_read_only_observation_authorization_checklist_v1"
    / "seed_packet.json"
)


class DevHubReadOnlyObservationAuthorizationChecklistV1Test(unittest.TestCase):
    def test_builds_fixture_first_authorization_checklist_from_seed_packet(self) -> None:
        seed_packet = load_json_packet(FIXTURE_PATH)

        checklist = build_authorization_checklist_v1(seed_packet)

        self.assertEqual(checklist["checklist_version"], CHECKLIST_VERSION)
        self.assertTrue(checklist["fixture_first"])
        self.assertFalse(checklist["devhub_access_performed"])
        self.assertEqual(
            [row["target_id"] for row in checklist["per_target_attendance_prerequisites"]],
            [
                "target-synthetic-devhub-home-read-only",
                "target-synthetic-permit-detail-read-only",
            ],
        )
        self.assertEqual(validate_authorization_checklist_v1(checklist), [])

    def test_checklist_contains_required_authorization_sections(self) -> None:
        checklist = build_authorization_checklist_v1(load_json_packet(FIXTURE_PATH))

        self.assertTrue(checklist["account_scope_reminders"])
        self.assertTrue(checklist["read_only_route_expectations"])
        self.assertTrue(checklist["manual_login_handoff_notes"])
        self.assertTrue(checklist["prohibited_capture_artifact_reminders"])
        self.assertTrue(checklist["redaction_acceptance_prerequisites"])
        self.assertTrue(checklist["reviewer_routing"])
        self.assertTrue(checklist["rollback_notes"])
        self.assertIn(["python3", "ppd/daemon/ppd_daemon.py", "--self-test"], checklist["offline_validation_commands"])

    def test_checklist_blocks_live_access_artifacts_and_official_actions(self) -> None:
        checklist = build_authorization_checklist_v1(load_json_packet(FIXTURE_PATH))

        self.assertTrue(all(value is False for value in checklist["artifact_policy"].values()))
        for key in (
            "opens_devhub",
            "logs_in",
            "stores_auth_artifacts",
            "stores_session_artifacts",
            "stores_screenshots",
            "stores_traces",
            "stores_har_files",
            "stores_private_values",
            "stores_raw_crawl_output",
            "stores_downloaded_documents",
            "performs_form_fills",
            "performs_uploads",
            "performs_submissions",
            "performs_payments",
            "performs_scheduling",
            "performs_other_official_actions",
        ):
            self.assertFalse(checklist["artifact_policy"][key])

    def test_builder_consumes_input_without_mutating_seed_packet(self) -> None:
        seed_packet = load_json_packet(FIXTURE_PATH)
        before = copy.deepcopy(seed_packet)

        build_authorization_checklist_v1(seed_packet)

        self.assertEqual(seed_packet, before)

    def test_validator_rejects_missing_required_section(self) -> None:
        checklist = build_authorization_checklist_v1(load_json_packet(FIXTURE_PATH))
        checklist["reviewer_routing"] = []

        issues = validate_authorization_checklist_v1(checklist)

        self.assertIn("missing_required_section", {issue.code for issue in issues})

    def test_validator_rejects_private_artifact_text_outside_policy_notes(self) -> None:
        checklist = build_authorization_checklist_v1(load_json_packet(FIXTURE_PATH))
        checklist["account_scope_reminders"][0]["reminder"] = "Store storage_state for later review."

        issues = validate_authorization_checklist_v1(checklist)

        self.assertIn("forbidden_private_or_artifact_text", {issue.code for issue in issues})

    def test_validator_rejects_non_exact_validation_commands(self) -> None:
        checklist = build_authorization_checklist_v1(load_json_packet(FIXTURE_PATH))
        checklist["offline_validation_commands"] = [["python3", "-m", "pytest"]]

        issues = validate_authorization_checklist_v1(checklist)

        self.assertIn("unsupported_validation_command", {issue.code for issue in issues})
        self.assertIn("incomplete_validation_commands", {issue.code for issue in issues})

    def test_assert_valid_raises_stable_error(self) -> None:
        checklist = build_authorization_checklist_v1(load_json_packet(FIXTURE_PATH))
        checklist["artifact_policy"]["stores_screenshots"] = True

        with self.assertRaisesRegex(AssertionError, "artifact_policy.stores_screenshots must be false"):
            assert_valid_authorization_checklist_v1(checklist)


if __name__ == "__main__":
    unittest.main()
