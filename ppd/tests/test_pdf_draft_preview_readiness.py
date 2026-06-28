from __future__ import annotations

import unittest

from ppd.pdf.draft_preview_readiness import (
    REQUIRED_REVIEWER_CHECKPOINTS,
    assert_pdf_draft_preview_readiness_packet,
    validate_pdf_draft_preview_readiness_packet,
)


def safe_packet() -> dict[str, object]:
    return {
        "packet_id": "preview-ready-fixture",
        "mode": "local_pdf_preview_only",
        "source_evidence_ids": ["ppd-source-submit-plans-online"],
        "prompt": "Draft a reversible preview field map from cited PP&D guidance.",
        "reviewer_checkpoints": {name: "passed" for name in REQUIRED_REVIEWER_CHECKPOINTS},
        "controls": {
            "upload": {"enabled": False},
            "submission": {"enabled": False},
            "certification": {"enabled": False},
            "payment": {"enabled": False},
        },
        "preview_plan": {
            "fields": [{"name": "applicant_name", "value_source": "user_confirmed_fact"}],
            "execution": "No live PDF fill is performed; this packet is readiness metadata only.",
        },
    }


class PdfDraftPreviewReadinessTests(unittest.TestCase):
    def violation_codes(self, packet: dict[str, object]) -> set[str]:
        return {v.code for v in validate_pdf_draft_preview_readiness_packet(packet).violations}

    def test_accepts_cited_preview_only_packet_with_disabled_controls(self) -> None:
        packet = safe_packet()

        result = validate_pdf_draft_preview_readiness_packet(packet)

        self.assertTrue(result.ready)
        self.assertEqual((), result.violations)
        assert_pdf_draft_preview_readiness_packet(packet)

    def test_rejects_private_file_paths_and_raw_pdf_content(self) -> None:
        packet = safe_packet()
        packet["local_path"] = "/home/alex/private/permit.pdf"
        packet["raw_pdf"] = "%PDF-1.7 raw bytes are not commit safe"

        self.assertIn("private_file_path_present", self.violation_codes(packet))
        self.assertIn("raw_document_content_present", self.violation_codes(packet))
        self.assertIn("raw_pdf_content_present", self.violation_codes(packet))

    def test_rejects_downloaded_documents(self) -> None:
        packet = safe_packet()
        packet["documents"] = [{"source_kind": "downloaded_document", "title": "Downloaded application"}]

        self.assertIn("unsafe_artifact_kind", self.violation_codes(packet))

    def test_rejects_uncited_prompts(self) -> None:
        packet = safe_packet()
        packet.pop("source_evidence_ids")
        packet["prompt"] = "Draft the packet from memory."

        self.assertIn("uncited_prompt_present", self.violation_codes(packet))

    def test_rejects_legal_or_permitting_outcome_guarantees(self) -> None:
        packet = safe_packet()
        packet["preview_plan"] = {"summary": "This is legally sufficient and approval is certain."}

        self.assertIn("outcome_guarantee_present", self.violation_codes(packet))

    def test_rejects_live_pdf_fill_execution_claims(self) -> None:
        packet = safe_packet()
        packet["status"] = "Filled the PDF application and wrote the permit document."

        self.assertIn("live_pdf_fill_execution_claim_present", self.violation_codes(packet))

    def test_rejects_missing_reviewer_checkpoints(self) -> None:
        packet = safe_packet()
        packet["reviewer_checkpoints"] = {"source_citation_review": "passed"}

        codes = self.violation_codes(packet)

        self.assertIn("missing_reviewer_checkpoint", codes)

    def test_rejects_enabled_upload_submission_certification_and_payment_controls(self) -> None:
        packet = safe_packet()
        packet["controls"] = {
            "upload": {"enabled": True},
            "submission": {"enabled": "enabled"},
            "certification": {"clickable": True},
            "payment": {"active": True},
        }

        self.assertIn("consequential_control_enabled", self.violation_codes(packet))


if __name__ == "__main__":
    unittest.main()
