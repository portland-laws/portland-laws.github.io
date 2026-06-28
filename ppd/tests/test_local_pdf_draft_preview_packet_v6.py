from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ppd.agent_readiness.local_pdf_draft_preview_packet_v6 import (
    build_local_pdf_draft_preview_packet_v6,
    load_fixture_packet,
    validate_local_pdf_draft_preview_packet_v6,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "local_pdf_draft_preview_packet_v6"


def _load_json(name: str) -> dict:
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


class LocalPdfDraftPreviewPacketV6Test(unittest.TestCase):
    def test_fixture_first_preview_packet_matches_expected_output(self) -> None:
        handoff = load_fixture_packet(FIXTURE_DIR / "guarded_handoff_packet_v6.json")
        fields = load_fixture_packet(FIXTURE_DIR / "synthetic_fillable_pdf_fields.json")
        expected = _load_json("expected_local_pdf_draft_preview_packet_v6.json")

        self.assertEqual(
            build_local_pdf_draft_preview_packet_v6(
                guarded_handoff_packet_v6=handoff,
                synthetic_fillable_pdf_fields=fields,
            ),
            expected,
        )

    def test_preview_packet_is_local_only_and_stop_gated(self) -> None:
        packet = build_local_pdf_draft_preview_packet_v6(
            guarded_handoff_packet_v6=_load_json("guarded_handoff_packet_v6.json"),
            synthetic_fillable_pdf_fields=_load_json("synthetic_fillable_pdf_fields.json"),
        )

        self.assertEqual(validate_local_pdf_draft_preview_packet_v6(packet), [])
        self.assertTrue(all(row["local_only"] and row["preview_only"] for row in packet["field_mapping_rows"]))
        self.assertTrue(all(row["writes_pdf"] is False for row in packet["field_mapping_rows"]))
        self.assertEqual({gate["topic"] for gate in packet["stop_gates"]}, {"upload", "submission", "certification", "payment"})

    def test_missing_user_fact_prompt_is_field_scoped_and_cited(self) -> None:
        packet = build_local_pdf_draft_preview_packet_v6(
            guarded_handoff_packet_v6=_load_json("guarded_handoff_packet_v6.json"),
            synthetic_fillable_pdf_fields=_load_json("synthetic_fillable_pdf_fields.json"),
        )

        prompts = {prompt["fact_id"]: prompt for prompt in packet["missing_user_fact_prompts"]}
        self.assertEqual(set(prompts), {"fact::applicant-email"})
        self.assertEqual(prompts["fact::applicant-email"]["blocks_field_ids"], ["pdf-field::applicant-email"])
        self.assertEqual(prompts["fact::applicant-email"]["source_evidence_ids"], ["src::devhub-submit-guide::dynamic-questions"])

    def test_rejects_non_synthetic_or_private_field_fixture(self) -> None:
        handoff = _load_json("guarded_handoff_packet_v6.json")
        fields = _load_json("synthetic_fillable_pdf_fields.json")
        fields["synthetic"] = False
        fields["fields"][0]["pdf_field_name"] = "/home/person/private.pdf"

        with self.assertRaises(ValueError):
            build_local_pdf_draft_preview_packet_v6(
                guarded_handoff_packet_v6=handoff,
                synthetic_fillable_pdf_fields=fields,
            )

    def test_rejects_missing_required_packet_sections_and_fixture_refs(self) -> None:
        packet = build_local_pdf_draft_preview_packet_v6(
            guarded_handoff_packet_v6=_load_json("guarded_handoff_packet_v6.json"),
            synthetic_fillable_pdf_fields=_load_json("synthetic_fillable_pdf_fields.json"),
        )
        required_lists = (
            "field_mapping_rows",
            "missing_user_fact_prompts",
            "source_evidence_references",
            "preview_only_rendering_notes",
            "no_private_document_placeholders",
            "stop_gates",
            "manual_review_notes",
            "validation_commands",
        )
        for section in required_lists:
            unsafe_packet = copy.deepcopy(packet)
            unsafe_packet[section] = []
            with self.assertRaisesRegex(ValueError, section):
                validate_local_pdf_draft_preview_packet_v6(unsafe_packet)
        for ref_field in ("handoff_packet_ref", "synthetic_field_fixture_ref"):
            unsafe_packet = copy.deepcopy(packet)
            unsafe_packet[ref_field] = ""
            with self.assertRaisesRegex(ValueError, ref_field):
                validate_local_pdf_draft_preview_packet_v6(unsafe_packet)

    def test_rejects_missing_local_mapping_evidence_prompt_note_and_commands(self) -> None:
        packet = build_local_pdf_draft_preview_packet_v6(
            guarded_handoff_packet_v6=_load_json("guarded_handoff_packet_v6.json"),
            synthetic_fillable_pdf_fields=_load_json("synthetic_fillable_pdf_fields.json"),
        )
        unsafe_packet = copy.deepcopy(packet)
        unsafe_packet["field_mapping_rows"][0]["local_only"] = False
        unsafe_packet["field_mapping_rows"][0]["source_evidence_ids"] = []
        unsafe_packet["missing_user_fact_prompts"][0]["source_evidence_ids"] = []
        unsafe_packet["preview_only_rendering_notes"][0]["source_evidence_ids"] = []
        unsafe_packet["manual_review_notes"][0]["source_evidence_ids"] = []
        unsafe_packet["validation_commands"] = [["python3", "unexpected.py"]]

        with self.assertRaises(ValueError) as raised:
            validate_local_pdf_draft_preview_packet_v6(unsafe_packet)
        message = str(raised.exception)
        self.assertIn("field mapping rows must be local preview rows", message)
        self.assertIn("field mapping rows must cite source evidence", message)
        self.assertIn("missing user-fact prompts must cite source evidence", message)
        self.assertIn("preview_only_rendering_notes entries must cite source evidence", message)
        self.assertIn("manual_review_notes entries must cite source evidence", message)
        self.assertIn("validation_commands must exactly match", message)

    def test_rejects_official_action_claims_private_artifacts_and_live_access(self) -> None:
        forbidden_examples = [
            "Opened DevHub and used an authenticated DevHub session.",
            "The application submitted successfully.",
            "Payment completed in the official workflow.",
            "Permit approval is guaranteed.",
            "Click submit in DevHub now.",
            "browser_state/auth_state.json",
            "PRIVATE_FACT: local document value",
        ]
        for text in forbidden_examples:
            packet = build_local_pdf_draft_preview_packet_v6(
                guarded_handoff_packet_v6=_load_json("guarded_handoff_packet_v6.json"),
                synthetic_fillable_pdf_fields=_load_json("synthetic_fillable_pdf_fields.json"),
            )
            packet["manual_review_notes"].append(
                {
                    "note_id": "unsafe",
                    "note": text,
                    "source_evidence_ids": ["fixture::unsafe"],
                }
            )
            with self.assertRaises(ValueError):
                validate_local_pdf_draft_preview_packet_v6(packet)

    def test_rejects_private_document_reads_and_active_mutation_flags(self) -> None:
        packet = build_local_pdf_draft_preview_packet_v6(
            guarded_handoff_packet_v6=_load_json("guarded_handoff_packet_v6.json"),
            synthetic_fillable_pdf_fields=_load_json("synthetic_fillable_pdf_fields.json"),
        )
        packet["no_effect_policy"]["reads_private_documents"] = True
        packet["field_mapping_rows"][0]["uses_private_document"] = True
        packet["active_mutation_flags"] = True
        packet["release_state_mutation"] = True

        with self.assertRaises(ValueError) as raised:
            validate_local_pdf_draft_preview_packet_v6(packet)
        message = str(raised.exception)
        self.assertIn("no_effect_policy.reads_private_documents must be false", message)
        self.assertIn("field mapping rows must not write PDFs or use private documents", message)
        self.assertIn("forbidden true flag", message)
        self.assertIn("forbidden active mutation flag", message)


if __name__ == "__main__":
    unittest.main()
