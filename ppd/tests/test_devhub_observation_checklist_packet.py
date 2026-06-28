import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "devhub_attended_read_only"
    / "devhub_observation_checklist_packet.json"
)

REQUIRED_SECTION_IDS = {
    "synthetic_surface_evidence": "synthetic-surface-evidence",
    "accessible_heading_checks": "accessible-heading-checks",
    "status_label_checks": "status-label-checks",
    "attachment_list_label_checks": "attachment-list-label-checks",
    "fee_notice_label_checks": "fee-notice-label-checks",
    "correction_request_label_checks": "correction-request-label-checks",
    "inspection_result_label_checks": "inspection-result-label-checks",
    "redaction_rules": "redaction-rules",
    "manual_stop_conditions": "manual-stop-conditions",
}

REQUIRED_EVIDENCE_TYPES = {
    "accessible_headings",
    "status_labels",
    "attachment_list_labels",
    "fee_notice_labels",
    "correction_request_labels",
    "inspection_result_labels",
}

FORBIDDEN_ARTIFACT_KEYS = {
    "screenshot",
    "screenshots",
    "trace",
    "traces",
    "har",
    "cookies",
    "auth_state",
    "storage_state",
    "browser_state",
    "credentials",
    "raw_crawl_output",
    "downloaded_documents",
    "payment_data",
}

PROHIBITED_STORAGE_TERMS = {
    "screenshots",
    "traces",
    "HAR data",
    "cookies",
    "auth state",
    "storage state",
    "credentials",
    "payment data",
}

MANUAL_STOP_TERMS = {
    "MFA",
    "CAPTCHA",
    "private values",
    "download",
    "payment",
    "upload",
    "submit",
    "certify",
    "schedule",
    "auth state",
}


def load_packet() -> dict[str, Any]:
    with FIXTURE_PATH.open(encoding="utf-8") as fixture_file:
        packet = json.load(fixture_file)
    if not isinstance(packet, dict):
        raise AssertionError("checklist packet fixture must be a JSON object")
    return packet


def walk_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(walk_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(walk_keys(child))
    return keys


class DevHubObservationChecklistPacketTest(unittest.TestCase):
    def test_packet_links_required_read_only_checklist_sections(self) -> None:
        packet = load_packet()

        self.assertEqual(packet["packet_type"], "devhub_read_only_observation_checklist_packet")
        self.assertIs(packet["fixture_first"], True)
        self.assertIs(packet["synthetic_only"], True)
        self.assertEqual(packet["capture_mode"], "committed_fixture_metadata_only")
        self.assertFalse(packet["workflow"]["live_devhub_allowed"])
        self.assertFalse(packet["workflow"]["official_actions_allowed"])

        for section_name, section_id in REQUIRED_SECTION_IDS.items():
            self.assertEqual(packet["linked_sections"][section_name], f"#{section_id}")
            self.assertEqual(packet[section_name]["section_id"], section_id)

    def test_synthetic_evidence_maps_to_every_observation_surface(self) -> None:
        packet = load_packet()
        evidence_items = packet["synthetic_surface_evidence"]["evidence_items"]

        self.assertEqual(
            {item["evidence_type"] for item in evidence_items},
            REQUIRED_EVIDENCE_TYPES,
        )
        for item in evidence_items:
            mapped_section = item["maps_to"]
            self.assertIn(mapped_section, REQUIRED_SECTION_IDS)
            self.assertTrue(item["synthetic_signal"].strip())
            self.assertTrue(item["checklist_label"].strip())
            self.assertIn(item["evidence_id"], json.dumps(packet))

    def test_label_sections_are_accessible_metadata_only(self) -> None:
        packet = load_packet()

        self.assertIn("Dashboard", packet["accessible_heading_checks"]["required_headings"])
        self.assertIn("In Review", packet["status_label_checks"]["generic_status_labels"])
        self.assertIn("Attachments", packet["attachment_list_label_checks"]["allowed_labels"])
        self.assertIn("Payment required", packet["fee_notice_label_checks"]["allowed_labels"])
        self.assertIn("Corrections Requested", packet["correction_request_label_checks"]["allowed_labels"])
        self.assertIn("Passed", packet["inspection_result_label_checks"]["allowed_labels"])

        serialized = json.dumps(packet, sort_keys=True).lower()
        for unsafe_value in ("@", "555-", "4111", "/home/", "file://"):
            self.assertNotIn(unsafe_value, serialized)

    def test_redaction_rules_forbid_private_artifacts_and_auth_state(self) -> None:
        packet = load_packet()
        redaction_rules = packet["redaction_rules"]

        self.assertEqual(redaction_rules["classification"], "commit_safe_redacted_metadata_only")
        must_redact = " ".join(redaction_rules["must_redact"])
        for term in ("permit numbers", "application numbers", "uploaded file names", "payment data", "browser session identifiers"):
            self.assertIn(term, must_redact)

        prohibited_storage = " ".join(redaction_rules["prohibited_storage"])
        for term in PROHIBITED_STORAGE_TERMS:
            self.assertIn(term, prohibited_storage)

        self.assertTrue(walk_keys(packet).isdisjoint(FORBIDDEN_ARTIFACT_KEYS))

    def test_manual_stop_conditions_cover_consequential_and_private_surfaces(self) -> None:
        packet = load_packet()
        stops = " ".join(packet["manual_stop_conditions"]["stop_immediately_when"])

        for term in MANUAL_STOP_TERMS:
            self.assertIn(term, stops)
        self.assertIn("manual handoff reason", packet["manual_stop_conditions"]["operator_result"])


if __name__ == "__main__":
    unittest.main()
