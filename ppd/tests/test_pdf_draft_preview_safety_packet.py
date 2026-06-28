from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import unittest

from ppd.pdf.draft_preview_safety_packet import (
    build_draft_preview_safety_packet,
    load_safety_packet_fixture,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pdf_draft_preview" / "safety_packet_case.json"


class DraftPreviewSafetyPacketTest(unittest.TestCase):
    def test_builds_fixture_first_non_persistent_packet(self) -> None:
        packet = build_draft_preview_safety_packet(load_safety_packet_fixture(FIXTURE_PATH))

        self.assertEqual(packet["packet_kind"], "local_pdf_draft_preview_safety_packet")
        self.assertTrue(packet["synthetic_fixture"])
        self.assertTrue(packet["non_persistent_preview_output"])
        self.assertFalse(packet["pdf_binary_read"])
        self.assertFalse(packet["pdf_binary_written"])
        self.assertFalse(packet["document_artifact_written"])
        self.assertEqual(packet["allowed_actions"], ["render_non_persistent_local_preview", "ask_for_missing_synthetic_facts"])

    def test_maps_fields_to_facts_and_citation_evidence(self) -> None:
        packet = build_draft_preview_safety_packet(load_safety_packet_fixture(FIXTURE_PATH))
        evidence_ids = {item["evidence_id"] for item in packet["citation_evidence"]}
        mappings = {item["field_name"]: item for item in packet["field_mappings"]}

        self.assertEqual(mappings["project_address"]["draft_value"], "1234 SW Fixture Ave")
        self.assertEqual(mappings["applicant_phone"]["draft_value"], "[REDACTED:PHONE]")
        self.assertEqual(mappings["applicant_phone"]["mapping_status"], "redacted_for_preview")
        for mapping in packet["field_mappings"]:
            self.assertTrue(set(mapping["source_evidence_ids"]).issubset(evidence_ids))

    def test_surfaces_missing_required_facts(self) -> None:
        packet = build_draft_preview_safety_packet(load_safety_packet_fixture(FIXTURE_PATH))

        self.assertEqual(
            packet["missing_facts"],
            [
                {
                    "fact_id": "contractor_license_number",
                    "field_name": "contractor_license_number",
                    "reason": "required synthetic fact is absent from the local preview fixture",
                    "source_evidence_ids": ["ppd-devhub-guide-field-evidence"],
                }
            ],
        )
        contractor_mapping = next(item for item in packet["field_mappings"] if item["field_name"] == "contractor_license_number")
        self.assertEqual(contractor_mapping["mapping_status"], "missing_fact")
        self.assertIsNone(contractor_mapping["draft_value"])

    def test_blocks_signature_and_certification_fields(self) -> None:
        packet = build_draft_preview_safety_packet(load_safety_packet_fixture(FIXTURE_PATH))
        blocked_names = {item["field_name"] for item in packet["blocked_signature_certification_fields"]}

        self.assertEqual(blocked_names, {"applicant_signature", "certification_acknowledgement"})
        for blocked in packet["blocked_signature_certification_fields"]:
            self.assertEqual(blocked["status"], "blocked_requires_attended_exact_confirmation")
        self.assertIn("sign", packet["blocked_actions"])
        self.assertIn("certify", packet["blocked_actions"])
        self.assertIn("upload", packet["blocked_actions"])
        self.assertIn("submit", packet["blocked_actions"])

    def test_rejects_private_paths_in_fixture_values(self) -> None:
        fixture = load_safety_packet_fixture(FIXTURE_PATH)
        fixture["case_facts"][0]["value"] = "/home/person/private/application.pdf"

        with self.assertRaisesRegex(ValueError, "private local path"):
            build_draft_preview_safety_packet(fixture)

    def test_rejects_raw_pdf_persistence(self) -> None:
        fixture = load_safety_packet_fixture(FIXTURE_PATH)
        fixture["raw_pdf_persisted"] = True

        with self.assertRaisesRegex(ValueError, "raw PDF persistence"):
            build_draft_preview_safety_packet(fixture)

    def test_rejects_missing_field_citations(self) -> None:
        fixture = load_safety_packet_fixture(FIXTURE_PATH)
        fixture["fillable_pdf_fields"][0]["source_evidence_ids"] = []

        with self.assertRaisesRegex(ValueError, "missing source evidence citations"):
            build_draft_preview_safety_packet(fixture)

    def test_rejects_unredacted_private_values(self) -> None:
        fixture = load_safety_packet_fixture(FIXTURE_PATH)
        fixture["case_facts"][2] = {
            "fact_id": "applicant_phone",
            "label": "Applicant phone",
            "value": "503-555-0100",
            "sensitivity": "contact",
        }

        with self.assertRaisesRegex(ValueError, "unredacted private value"):
            build_draft_preview_safety_packet(fixture)

    def test_rejects_filled_signature_or_certification_fields(self) -> None:
        fixture = load_safety_packet_fixture(FIXTURE_PATH)
        fixture["case_facts"].append(
            {
                "fact_id": "applicant_signature",
                "label": "Applicant signature",
                "value": "Fixture Applicant",
                "sensitivity": "ordinary",
            }
        )

        with self.assertRaisesRegex(ValueError, "filled signature or certification field"):
            build_draft_preview_safety_packet(fixture)

    def test_rejects_official_upload_staging(self) -> None:
        fixture = load_safety_packet_fixture(FIXTURE_PATH)
        fixture["official_upload_staged"] = True

        with self.assertRaisesRegex(ValueError, "official upload staging"):
            build_draft_preview_safety_packet(fixture)

    def test_rejects_ready_for_submission_claims(self) -> None:
        fixture = deepcopy(load_safety_packet_fixture(FIXTURE_PATH))
        fixture["readiness_summary"] = "This local draft is ready for submission."

        with self.assertRaisesRegex(ValueError, "ready for submission"):
            build_draft_preview_safety_packet(fixture)


if __name__ == "__main__":
    unittest.main()
