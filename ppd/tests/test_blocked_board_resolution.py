from __future__ import annotations

import json
import unittest

from ppd.daemon.parser_clean_diagnostics import build_parser_clean_diagnostic
from ppd.daemon.prompt_scoping import (
    build_syntax_preflight_retry_instruction_json,
    validate_retry_instruction_scope,
)
from ppd.daemon.recovery_note_compaction import (
    compact_task_board_repair_notes,
    extract_repair_notes,
    summarize_recovery_notes,
)
from ppd.daemon.ppd_daemon import parse_tasks, select_task
from ppd.daemon.ppd_supervisor import task_board_summary
from ppd.devhub.draft_readiness import (
    REFUSED_OFFICIAL_ACTIONS,
    decisions_to_dicts,
    fixture_decision_matrix,
    validate_draft_readiness_matrix,
)


class BlockedBoardResolutionTest(unittest.TestCase):
    def test_checkbox_178_devhub_draft_readiness_matrix_is_fixture_only_and_fail_closed(self) -> None:
        decisions = fixture_decision_matrix()
        payload = decisions_to_dicts(decisions)

        self.assertEqual([], validate_draft_readiness_matrix(decisions))
        self.assertEqual(3, len(decisions))
        self.assertTrue(any(decision.ready_for_draft_preview for decision in decisions))
        self.assertTrue(any(decision.missing_facts for decision in decisions))
        self.assertTrue(any(decision.redacted_file_placeholders for decision in decisions))
        self.assertTrue(any(decision.selector_review_required for decision in decisions))
        self.assertTrue(any(decision.upload_blocked for decision in decisions))
        self.assertTrue(any(decision.fee_notice_required for decision in decisions))
        for item in payload:
            self.assertEqual(set(REFUSED_OFFICIAL_ACTIONS), set(item["refusedOfficialActions"]))
            self.assertTrue(item["sourceIds"])
            self.assertNotIn("session", json.dumps(item).lower())
            self.assertNotIn("trace.zip", json.dumps(item).lower())

    def test_checkbox_182_193_203_209_compact_diagnostics_cap_and_redact_raw_output(self) -> None:
        raw = (
            "not-json auth-state=secret storage-state=secret trace.zip .har cookie screenshot "
            "raw crawl output downloaded document "
        ) * 8

        diagnostic = build_parser_clean_diagnostic(
            target_task="Task checkbox-209: repeated non-JSON response",
            raw_response=[raw, raw],
            error="LLM response did not contain a JSON object",
        )

        self.assertEqual("non_json_llm_output", diagnostic["failure_kind"])
        self.assertIn("target_task", diagnostic)
        self.assertIn("compact_raw_response_summary", diagnostic)
        self.assertIn("next_action_hint", diagnostic)
        self.assertLessEqual(len(diagnostic["compact_raw_response_summary"]), 220)
        for forbidden in ("auth-state", "storage-state", "trace.zip", ".har", "cookie", "screenshot", raw):
            self.assertNotIn(forbidden, diagnostic["compact_raw_response_summary"].lower())
        self.assertIn("JSON-only", diagnostic["next_action_hint"])

    def test_checkbox_186_210_retry_scope_permits_one_file_and_rejects_bundles(self) -> None:
        history = (
            {
                "target_task": "Task checkbox-178",
                "failure_kind": "syntax_preflight",
                "files": ("ppd/devhub/draft_readiness.py",),
            },
            {
                "target_task": "Task checkbox-178",
                "failure_kind": "syntax_preflight",
                "files": ("ppd/devhub/draft_readiness.py",),
            },
        )

        instruction = build_syntax_preflight_retry_instruction_json(
            "Task checkbox-178: DevHub draft-readiness",
            history,
        )

        self.assertIsNotNone(instruction)
        assert instruction is not None
        parsed = json.loads(instruction)
        self.assertEqual(["ppd/devhub/draft_readiness.py"], parsed["retry_scope"]["allowed_files"])
        self.assertEqual(1, parsed["retry_scope"]["max_files"])
        self.assertEqual([], validate_retry_instruction_scope(instruction))
        self.assertIn("Repair exactly one parser-bearing PP&D file", " ".join(parsed["constraints"]))

    def test_checkbox_187_197_208_blocked_items_do_not_reopen_before_fresh_repair(self) -> None:
        board = "\n".join(
            (
                "- [!] Task checkbox-178: Blocked DevHub draft-readiness.",
                "- [!] Task checkbox-182: Blocked diagnostics.",
                "- [!] Task checkbox-186: Blocked retry scope.",
                "- [!] Task checkbox-187: Blocked selection.",
                "- [!] Task checkbox-191: Blocked note compaction.",
                "- [!] Task checkbox-193: Blocked diagnostic unittest.",
                "- [!] Task checkbox-194: Blocked recovery-note helper.",
                "- [!] Task checkbox-195: Blocked repair guide.",
                "- [!] Task checkbox-197: Blocked retry-scope helper.",
                "- [!] Task checkbox-198: Blocked repair guide exact phrase.",
                "- [!] Task checkbox-203: Blocked compact summaries.",
                "- [!] Task checkbox-208: Blocked stale calling_llm repair.",
                "- [ ] Task checkbox-219: Fresh daemon-repair task.",
            )
        )

        selected = select_task(parse_tasks(board), revisit_blocked=True)

        self.assertIsNotNone(selected)
        assert selected is not None
        self.assertEqual(219, selected.checkbox_id)

    def test_checkbox_191_194_recovery_notes_are_summarized_for_prompt_context(self) -> None:
        repeated_note = "- Parked repeated syntax-preflight loop for checkbox-178 before retrying blocked work."
        board = "\n".join(
            ["## Built-In Supervisor Repair Notes", repeated_note, repeated_note, repeated_note]
            + [f"- Appended deterministic blocked-cascade recovery tasks round {index}." for index in range(8)]
        )

        notes = extract_repair_notes(board)
        summary = summarize_recovery_notes(notes, max_items=2, max_chars=240)
        prompt_text = compact_task_board_repair_notes(board, max_items=2, max_chars=240)
        board_summary = json.loads(task_board_summary(board))

        self.assertGreater(summary.total_notes, summary.unique_notes)
        self.assertLessEqual(len(summary.summary), 240)
        self.assertIn("additional unique note(s) omitted", summary.summary)
        self.assertIn("Supervisor repair notes summarized", prompt_text)
        self.assertIn("repairNoteSummary", board_summary)


if __name__ == "__main__":
    unittest.main()
