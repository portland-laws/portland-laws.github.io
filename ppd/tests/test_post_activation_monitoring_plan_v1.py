from __future__ import annotations

from pathlib import Path
import copy
import unittest

from ppd.agent_readiness.post_activation_monitoring_plan_v1 import (
    EXACT_OFFLINE_VALIDATION_COMMANDS,
    REQUIRED_PLAN_SECTIONS,
    build_post_activation_monitoring_plan_v1_from_fixture,
    validate_post_activation_monitoring_plan_v1,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "post_activation_monitoring_plan_v1" / "inactive_activation_rehearsal_rows.json"


class PostActivationMonitoringPlanV1Tests(unittest.TestCase):
    def valid_packet(self) -> dict[str, object]:
        return build_post_activation_monitoring_plan_v1_from_fixture(FIXTURE_PATH)

    def assert_rejected(self, packet: dict[str, object], expected_fragment: str) -> None:
        errors = validate_post_activation_monitoring_plan_v1(packet)
        self.assertTrue(errors, "packet should be rejected")
        self.assertTrue(
            any(expected_fragment in error for error in errors),
            f"expected {expected_fragment!r} in {errors!r}",
        )

    def test_fixture_builds_valid_packet(self) -> None:
        packet = self.valid_packet()
        self.assertEqual([], validate_post_activation_monitoring_plan_v1(packet))
        self.assertEqual(EXACT_OFFLINE_VALIDATION_COMMANDS, packet["validation_commands"])

    def test_rejects_missing_required_sections(self) -> None:
        for section in REQUIRED_PLAN_SECTIONS:
            with self.subTest(section=section):
                packet = self.valid_packet()
                packet[section] = []
                self.assert_rejected(packet, f"{section} must be a non-empty list")

    def test_rejects_missing_activation_checklist_references_in_each_section(self) -> None:
        for section in REQUIRED_PLAN_SECTIONS:
            with self.subTest(section=section):
                packet = self.valid_packet()
                rows = copy.deepcopy(packet[section])
                self.assertIsInstance(rows, list)
                rows = rows[:-1]
                packet[section] = rows
                self.assert_rejected(packet, f"{section} missing required checklist row reference")

    def test_rejects_unknown_activation_checklist_reference(self) -> None:
        packet = self.valid_packet()
        probes = copy.deepcopy(packet["offline_monitoring_probes"])
        self.assertIsInstance(probes, list)
        probes[0]["source_checklist_row_id"] = "unknown-checklist-row"
        packet["offline_monitoring_probes"] = probes
        self.assert_rejected(packet, "references unknown checklist row unknown-checklist-row")

    def test_rejects_missing_validation_commands(self) -> None:
        packet = self.valid_packet()
        packet["validation_commands"] = []
        self.assert_rejected(packet, "validation_commands must contain only the daemon self-test command")

    def test_rejects_private_raw_downloaded_artifact_fields(self) -> None:
        packet = self.valid_packet()
        packet["downloaded_document"] = "fixture-download.pdf"
        self.assert_rejected(packet, "forbidden private/session/browser/raw artifact field")

    def test_rejects_live_devhub_activation_promotion_official_legal_and_mutation_claims(self) -> None:
        forbidden_packets = [
            {"note": "live crawl completed"},
            {"note": "opened DevHub"},
            {"note": "release promoted"},
            {"note": "official action completed"},
            {"note": "permit approval guaranteed"},
            {"active_guardrail_mutation": True},
        ]
        for forbidden in forbidden_packets:
            with self.subTest(forbidden=forbidden):
                packet = self.valid_packet()
                packet.update(forbidden)
                self.assert_rejected(packet, "forbidden")


if __name__ == "__main__":
    unittest.main()
