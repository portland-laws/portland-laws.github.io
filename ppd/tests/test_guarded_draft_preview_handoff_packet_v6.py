from __future__ import annotations

import copy
import unittest

from ppd.agent_readiness.guarded_draft_preview_handoff_packet_v6 import (
    EXACT_VALIDATION_COMMANDS,
    PACKET_VERSION,
    assert_valid_guarded_draft_preview_handoff_packet_v6,
    validate_guarded_draft_preview_handoff_packet_v6,
)


def _valid_packet() -> dict[str, object]:
    return {
        "packet_version": PACKET_VERSION,
        "fixture_first": True,
        "agent_api_compatibility_refs": [
            {
                "ref_id": "agent-api-compat-v6",
                "reference_kind": "agent_api_compatibility",
                "source_evidence_ids": ["agent-api-compat-fixture-v6"],
            }
        ],
        "attended_preflight_refs": [
            {
                "ref_id": "devhub-read-only-preflight-v6",
                "reference_kind": "attended_preflight",
                "source_evidence_ids": ["devhub-read-only-preflight-fixture-v6"],
            }
        ],
        "reversible_draft_preview_rows": [
            {
                "row_id": "fixture-local-preview-row",
                "reversible": True,
                "local_only": True,
                "requires_user_review": True,
                "official_action": False,
                "devhub_mutation": False,
                "pdf_write": False,
                "upload_ready": False,
                "source_evidence_ids": ["public-source-fixture"],
                "user_fact_provenance_requirements": ["user supplied address source and document source are required"],
                "selector_confidence_caveats": ["Synthetic selectors are caveated and cannot support unattended execution."],
                "local_pdf_preview_boundaries": ["Preview metadata only; no PDF write or private path."],
            }
        ],
        "user_fact_provenance_requirements": [
            {
                "fact_id": "site_address",
                "requires_user_supplied_provenance": True,
                "allow_inference_without_source": False,
            }
        ],
        "selector_confidence_caveats": [
            {
                "caveat_id": "synthetic-selector-confidence-only",
                "blocks_unattended_execution": True,
                "allows_live_selector_claim": False,
            }
        ],
        "stop_gates": [
            {
                "topic": "upload",
                "automated": False,
                "requires_attended_user": True,
                "requires_exact_confirmation": True,
                "disposition": "stop_and_manual_handoff",
            },
            {
                "topic": "submission",
                "automated": False,
                "requires_attended_user": True,
                "requires_exact_confirmation": True,
                "disposition": "stop_and_manual_handoff",
            },
            {
                "topic": "payment",
                "automated": False,
                "requires_attended_user": True,
                "requires_exact_confirmation": True,
                "disposition": "stop_and_manual_handoff",
            },
            {
                "topic": "certification",
                "automated": False,
                "requires_attended_user": True,
                "requires_exact_confirmation": True,
                "disposition": "stop_and_manual_handoff",
            },
        ],
        "local_pdf_preview_boundaries": [
            {
                "boundary_id": "metadata-only-local-pdf-preview",
                "local_preview_only": True,
                "writes_pdf": False,
                "uses_private_file_path": False,
            }
        ],
        "exact_confirmation_checkpoint_reminders": [
            {
                "reminder_id": "official-action-exact-confirmation",
                "reminder": "Official actions remain stopped until the user is present and gives action-specific exact confirmation.",
                "source_evidence_ids": ["non-negotiable-boundaries"],
            }
        ],
        "manual_handoff_notes": [
            {
                "note_id": "manual-devhub-handoff",
                "note": "Hand off to the user for attended DevHub review before consequential actions.",
                "source_evidence_ids": ["authenticated-devhub-automation-plan"],
            }
        ],
        "no_effect_policy": {
            "live_devhub_access": False,
            "private_session_auth_artifacts": False,
            "official_action_completion_claims": False,
            "legal_or_permitting_guarantees": False,
            "active_mutation_flags": False,
            "opens_devhub": False,
            "uses_authenticated_session": False,
            "stores_auth_state": False,
            "stores_cookies": False,
            "creates_traces": False,
            "creates_screenshots": False,
            "creates_har_files": False,
            "uploads": False,
            "submits": False,
            "pays": False,
            "certifies": False,
            "schedules": False,
            "cancels": False,
            "mutates_release_state": False,
            "mutates_guardrails": False,
            "mutates_prompts": False,
            "writes_pdf": False,
        },
        "validation_commands": EXACT_VALIDATION_COMMANDS,
    }


class GuardedDraftPreviewHandoffPacketV6Test(unittest.TestCase):
    def test_valid_packet_passes(self) -> None:
        packet = _valid_packet()
        self.assertEqual(validate_guarded_draft_preview_handoff_packet_v6(packet), [])
        assert_valid_guarded_draft_preview_handoff_packet_v6(packet)

    def test_rejects_missing_required_sections(self) -> None:
        for section in (
            "agent_api_compatibility_refs",
            "attended_preflight_refs",
            "reversible_draft_preview_rows",
            "user_fact_provenance_requirements",
            "selector_confidence_caveats",
            "stop_gates",
            "local_pdf_preview_boundaries",
            "exact_confirmation_checkpoint_reminders",
            "manual_handoff_notes",
            "validation_commands",
        ):
            packet = _valid_packet()
            packet[section] = []
            issues = validate_guarded_draft_preview_handoff_packet_v6(packet)
            self.assertIn(("missing_section", section), {(issue.code, issue.path) for issue in issues})

    def test_rejects_missing_reversible_row_controls(self) -> None:
        packet = _valid_packet()
        row = packet["reversible_draft_preview_rows"][0]
        assert isinstance(row, dict)
        row["reversible"] = False
        row["user_fact_provenance_requirements"] = []
        row["selector_confidence_caveats"] = []
        row["local_pdf_preview_boundaries"] = []
        issues = validate_guarded_draft_preview_handoff_packet_v6(packet)
        codes = {issue.code for issue in issues}
        self.assertIn("unsafe_preview_row", codes)
        self.assertIn("missing_user_fact_provenance", codes)
        self.assertIn("missing_selector_caveats", codes)
        self.assertIn("missing_local_pdf_boundaries", codes)

    def test_rejects_missing_stop_gate_topics(self) -> None:
        packet = _valid_packet()
        packet["stop_gates"] = [gate for gate in packet["stop_gates"] if gate["topic"] != "payment"]
        issues = validate_guarded_draft_preview_handoff_packet_v6(packet)
        self.assertIn("missing_stop_gate_topics", {issue.code for issue in issues})

    def test_rejects_invalid_no_effect_policy_and_validation_commands(self) -> None:
        packet = _valid_packet()
        policy = packet["no_effect_policy"]
        assert isinstance(policy, dict)
        policy["live_devhub_access"] = True
        policy["active_mutation_flags"] = True
        packet["validation_commands"] = [["python3", "unexpected.py"]]
        issues = validate_guarded_draft_preview_handoff_packet_v6(packet)
        codes = {issue.code for issue in issues}
        self.assertIn("unsafe_no_effect_policy", codes)
        self.assertIn("forbidden_active_flag", codes)
        self.assertIn("invalid_validation_commands", codes)

    def test_rejects_forbidden_claims_and_private_artifacts(self) -> None:
        forbidden_examples = [
            ("Opened DevHub and used an authenticated DevHub session.", "live_devhub_access_claim"),
            ("The application submitted successfully.", "official_action_completion_claim"),
            ("Permit approval is guaranteed.", "legal_or_permitting_guarantee"),
            ("Click submit in DevHub now.", "final_action_language"),
            ("browser_state/auth_state.json", "private_artifact_reference"),
        ]
        for text, expected_code in forbidden_examples:
            packet = copy.deepcopy(_valid_packet())
            packet["manual_handoff_notes"].append(
                {
                    "note_id": "unsafe-note",
                    "note": text,
                    "source_evidence_ids": ["fixture"],
                }
            )
            issues = validate_guarded_draft_preview_handoff_packet_v6(packet)
            self.assertIn(expected_code, {issue.code for issue in issues})


if __name__ == "__main__":
    unittest.main()
