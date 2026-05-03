from __future__ import annotations

import unittest

from ppd.daemon.ppd_supervisor import (
    builtin_replenish_goal_tasks,
    next_replenishment_heading,
    sanitize_agentic_replenishment_board,
)


class SupervisorReplenishmentSanitizationTest(unittest.TestCase):
    def test_duplicate_heading_and_repeated_titles_are_sanitized(self) -> None:
        board = "\n".join(
            [
                "- [x] Task checkbox-140: Done.",
                "",
                "## Built-In Goal Replenishment Tranche 5",
                "",
                "- [x] Task checkbox-152: Add a fixture-only public guidance conflict-resolution scenario plus focused validation.",
                "- [x] Task checkbox-153: Add a fixture-only DevHub upload-readiness checklist scenario plus focused validation.",
                "",
                "## Built-In Goal Replenishment Tranche 2",
                "",
                "- [ ] Task checkbox-156: Add a fixture-only public guidance conflict-resolution scenario plus focused validation.",
                "- [ ] Task checkbox-157: Add a fixture-only DevHub upload-readiness checklist scenario plus focused validation.",
                "- [ ] Task checkbox-158: Add supervisor replenishment rotation coverage proving third and later completed tranches do not duplicate the previous broad tranche titles.",
                "- [ ] Task checkbox-159: Add a fixture-only Playwright selector drift scenario plus focused validation.",
            ]
        )

        sanitized, changed = sanitize_agentic_replenishment_board(board)

        self.assertTrue(changed)
        self.assertIn("## Built-In Goal Replenishment Tranche 6", sanitized)
        self.assertNotIn("## Built-In Goal Replenishment Tranche 2\n\n- [ ] Task checkbox-156", sanitized)
        self.assertIn("deterministic-replenishment sanitization coverage", sanitized)
        self.assertIn("LLM result-durability coverage", sanitized)
        self.assertIn("cross-permit guardrail reuse scenario", sanitized)
        self.assertIn("human-review packet scenario", sanitized)

    def test_non_duplicate_latest_tranche_is_unchanged(self) -> None:
        board = "\n".join(
            [
                "## Built-In Goal Replenishment Tranche 5",
                "- [x] Task checkbox-152: Existing completed title.",
                "",
                "## Built-In Goal Replenishment Tranche 6",
                "- [ ] Task checkbox-156: Brand new title.",
            ]
        )

        sanitized, changed = sanitize_agentic_replenishment_board(board)

        self.assertFalse(changed)
        self.assertEqual(board, sanitized)

    def test_builtin_replenishment_uses_highest_heading_number(self) -> None:
        board = "\n".join(
            [
                "- [x] Task checkbox-140: Existing completed title.",
                "",
                "## Built-In Goal Replenishment Tranche 5",
                "- [x] Task checkbox-152: Prior tranche task.",
                "",
                "## Built-In Goal Replenishment Tranche 6",
                "- [x] Task checkbox-156: Later tranche task.",
            ]
        )

        self.assertEqual("## Built-In Goal Replenishment Tranche 7", next_replenishment_heading(board))

    def test_builtin_replenishment_skips_completed_duplicate_titles(self) -> None:
        board = "\n".join(
            [
                "- [x] Task checkbox-140: Add an end-to-end fixture-only handoff scenario plus focused validation linking processor archival evidence, extracted requirement nodes, formal-logic guardrails, and draft-only Playwright planning without live crawling, authenticated automation, raw browser state, or official DevHub actions.",
                "- [x] Task checkbox-141: Add a fixture-only user gap-resolution scenario plus focused validation that turns missing PP&D facts, stale evidence flags, and document placeholders into source-linked user questions and refuses autonomous completion while gaps remain.",
                "- [x] Task checkbox-142: Add supervisor adaptive-slice regression coverage proving completed board-level recovery tranches enable broader non-duplicate goal slices even when accepted daemon ledger rows lag behind manual validated recovery work.",
                "- [x] Task checkbox-143: Add an offline Playwright draft transcript fixture plus focused validation proving future agents can plan accessible-selector fills from redacted state while preserving exact-confirmation gates for upload, submit, payment, certification, cancellation, MFA, CAPTCHA, and inspection scheduling.",
                "- [x] Task checkbox-144: Add a fixture-only source-change impact scenario plus focused validation that routes updated PP&D public evidence through archival provenance, affected requirement IDs, stale guardrail invalidation, and human-review flags before agents reuse old answers.",
                "- [x] Task checkbox-145: Add a fixture-only agent work-order scenario plus focused validation that composes user document-store facts, missing PP&D facts, formal stop gates, and draft-only Playwright previews into an ordered autonomous-assistance plan without official DevHub actions.",
                "- [x] Task checkbox-146: Add daemon parse-failure recovery coverage proving repeated non-JSON LLM responses for a completed or manually satisfied task are parked or superseded instead of being retried indefinitely.",
                "- [x] Task checkbox-147: Add a fixture-only permit-process comparison scenario plus focused validation that contrasts two PP&D process types and preserves separate legal obligations, operational UI hints, document placeholders, fee notices, and exact-confirmation gates.",
                "- [x] Task checkbox-148: Add a fixture-only audit export scenario plus focused validation that records source evidence, user-question decisions, redacted draft previews, guardrail outcomes, and refused official actions for downstream human review.",
                "- [x] Task checkbox-149: Add a fixture-only stale-answer reconciliation scenario plus focused validation that compares user document-store facts against newer PP&D evidence and fails closed when citations, timestamps, or requirement IDs conflict.",
                "- [x] Task checkbox-150: Add supervisor replenishment rotation coverage proving third and later completed tranches do not duplicate the previous broad tranche titles.",
                "- [x] Task checkbox-151: Add a fixture-only Playwright selector drift scenario plus focused validation that detects changed accessible names, refuses low-confidence selectors, and asks for human review before draft-preview automation continues.",
                "",
                "## Built-In Goal Replenishment Tranche 6",
                "- [x] Task checkbox-156: Add supervisor deterministic-replenishment sanitization coverage proving agentic planner output with duplicate tranche headings or previously completed broad titles is rewritten to the next numbered non-duplicate tranche before the daemon starts.",
                "- [x] Task checkbox-157: Add daemon LLM result-durability coverage proving parse failures, validation interruption, child timeout, and vanished-child states write progress and result-log diagnostics before restart.",
                "- [x] Task checkbox-158: Add a fixture-only cross-permit guardrail reuse scenario plus focused validation that reuses common stop gates across two PP&D permit types while preserving process-specific citations and exact-confirmation requirements.",
                "- [x] Task checkbox-159: Add a fixture-only human-review packet scenario plus focused validation bundling conflicting evidence, stale answers, upload readiness, fee notices, and blocked DevHub transitions into one redacted review handoff.",
            ]
        )

        replenished, labels = builtin_replenish_goal_tasks(board, rows=[])

        self.assertEqual(("checkbox-160", "checkbox-161", "checkbox-162", "checkbox-163"), labels)
        self.assertIn("## Built-In Goal Replenishment Tranche 7", replenished)
        self.assertIn("task-board de-duplication coverage", replenished)
        self.assertIn("processor archival-suite readiness scenario", replenished)
        self.assertNotIn("- [ ] Task checkbox-160: Add a fixture-only source-change impact scenario", replenished)

    def test_late_replenishment_rotates_to_second_followup_before_old_recovery_titles(self) -> None:
        board = "\n".join(
            [
                "## Built-In Goal Replenishment Tranche 7",
                "- [x] Task checkbox-160: Add supervisor task-board de-duplication coverage proving deterministic replenishment uses the highest existing tranche number and skips any task titles already completed anywhere on the board.",
                "- [x] Task checkbox-161: Add daemon stale-worker recovery coverage proving a dead child recorded as calling_llm or applying_files is converted into a selectable pending task with a durable diagnostic before restart.",
                "- [x] Task checkbox-162: Add a fixture-only processor archival-suite readiness scenario plus focused validation that routes PP&D public URLs through ipfs_datasets_py processor handoff metadata, content-hash placeholders, and source-linked extraction batches without live crawling.",
                "- [x] Task checkbox-163: Add a fixture-only Playwright autonomous-form planning scenario plus focused validation that future agents may fill reversible draft fields from redacted user facts while refusing upload, submit, payment, certification, cancellation, MFA, CAPTCHA, and inspection scheduling without exact confirmation.",
            ]
        )

        replenished, labels = builtin_replenish_goal_tasks(board, rows=[])

        self.assertEqual(("checkbox-164", "checkbox-165", "checkbox-166", "checkbox-167"), labels)
        self.assertIn("## Built-In Goal Replenishment Tranche 8", replenished)
        self.assertIn("compact-prompt retry coverage", replenished)
        self.assertIn("evidence-to-guardrail trace matrix", replenished)
        self.assertNotIn("forbidden-marker self-triggering fixture fields", replenished)

    def test_replenishment_after_second_followup_rotates_to_third_followup(self) -> None:
        board = "\n".join(
            [
                "## Built-In Goal Replenishment Tranche 7",
                "- [x] Task checkbox-160: Add supervisor task-board de-duplication coverage proving deterministic replenishment uses the highest existing tranche number and skips any task titles already completed anywhere on the board.",
                "- [x] Task checkbox-161: Add daemon stale-worker recovery coverage proving a dead child recorded as calling_llm or applying_files is converted into a selectable pending task with a durable diagnostic before restart.",
                "- [x] Task checkbox-162: Add a fixture-only processor archival-suite readiness scenario plus focused validation that routes PP&D public URLs through ipfs_datasets_py processor handoff metadata, content-hash placeholders, and source-linked extraction batches without live crawling.",
                "- [x] Task checkbox-163: Add a fixture-only Playwright autonomous-form planning scenario plus focused validation that future agents may fill reversible draft fields from redacted user facts while refusing upload, submit, payment, certification, cancellation, MFA, CAPTCHA, and inspection scheduling without exact confirmation.",
                "",
                "## Built-In Goal Replenishment Tranche 8",
                "- [x] Task checkbox-164: Add daemon compact-prompt retry coverage proving repeated durable parse or LLM diagnostics produce a smaller task-focused JSON prompt instead of resending the broad PP&D workspace context.",
                "- [x] Task checkbox-165: Add daemon JSON-output recovery coverage proving compact retry mode includes strict one-object schema guidance, minimal fixture/test scope, and no extra prose allowance for llm_router backends.",
                "- [x] Task checkbox-166: Add supervisor replenishment coverage proving completed recovery tranches rotate into fresh PP&D archival, formal-logic, and Playwright planning tasks instead of reusing already satisfied supervisor hardening titles.",
                "- [x] Task checkbox-167: Add a fixture-only evidence-to-guardrail trace matrix plus focused validation linking processor handoff IDs, extracted requirement nodes, user document-store facts, missing facts, and exact-confirmation stop gates.",
            ]
        )

        replenished, labels = builtin_replenish_goal_tasks(board, rows=[])

        self.assertEqual(("checkbox-168", "checkbox-169", "checkbox-170", "checkbox-171"), labels)
        self.assertIn("## Built-In Goal Replenishment Tranche 9", replenished)
        self.assertIn("prompt-budget enforcement coverage", replenished)
        self.assertIn("autonomous-assistance dry-run transcript", replenished)
        self.assertNotIn("forbidden-marker self-triggering fixture fields", replenished)

    def test_replenishment_after_static_followups_generates_unique_titles(self) -> None:
        board = "\n".join(
            [
                "## Built-In Goal Replenishment Tranche 7",
                "- [x] Task checkbox-160: Add supervisor task-board de-duplication coverage proving deterministic replenishment uses the highest existing tranche number and skips any task titles already completed anywhere on the board.",
                "- [x] Task checkbox-161: Add daemon stale-worker recovery coverage proving a dead child recorded as calling_llm or applying_files is converted into a selectable pending task with a durable diagnostic before restart.",
                "- [x] Task checkbox-162: Add a fixture-only processor archival-suite readiness scenario plus focused validation that routes PP&D public URLs through ipfs_datasets_py processor handoff metadata, content-hash placeholders, and source-linked extraction batches without live crawling.",
                "- [x] Task checkbox-163: Add a fixture-only Playwright autonomous-form planning scenario plus focused validation that future agents may fill reversible draft fields from redacted user facts while refusing upload, submit, payment, certification, cancellation, MFA, CAPTCHA, and inspection scheduling without exact confirmation.",
                "",
                "## Built-In Goal Replenishment Tranche 8",
                "- [x] Task checkbox-164: Add daemon compact-prompt retry coverage proving repeated durable parse or LLM diagnostics produce a smaller task-focused JSON prompt instead of resending the broad PP&D workspace context.",
                "- [x] Task checkbox-165: Add daemon JSON-output recovery coverage proving compact retry mode includes strict one-object schema guidance, minimal fixture/test scope, and no extra prose allowance for llm_router backends.",
                "- [x] Task checkbox-166: Add supervisor replenishment coverage proving completed recovery tranches rotate into fresh PP&D archival, formal-logic, and Playwright planning tasks instead of reusing already satisfied supervisor hardening titles.",
                "- [x] Task checkbox-167: Add a fixture-only evidence-to-guardrail trace matrix plus focused validation linking processor handoff IDs, extracted requirement nodes, user document-store facts, missing facts, and exact-confirmation stop gates.",
                "",
                "## Built-In Goal Replenishment Tranche 9",
                "- [x] Task checkbox-168: Add daemon llm_router prompt-budget enforcement coverage proving compact retry prompts stay under a strict character cap before the child process is invoked.",
                "- [x] Task checkbox-169: Add supervisor repair-prompt compaction coverage proving repeated daemon parse diagnostics produce a bounded self-heal prompt with recent diagnostics, task board summary, and no accepted-work dump.",
                "- [x] Task checkbox-170: Add a fixture-only formal-logic export bundle plus focused validation mapping PP&D requirement nodes into obligations, prerequisites, stop gates, and exact-confirmation predicates for downstream agents.",
                "- [x] Task checkbox-171: Add a fixture-only autonomous-assistance dry-run transcript plus focused validation showing known user document-store facts, missing fact questions, reversible draft actions, and refused official actions in order.",
            ]
        )

        replenished, labels = builtin_replenish_goal_tasks(board, rows=[])

        self.assertEqual(("checkbox-172", "checkbox-173", "checkbox-174", "checkbox-175"), labels)
        self.assertIn("## Built-In Goal Replenishment Tranche 10", replenished)
        self.assertIn("generated-replenishment continuation coverage for tranche 10", replenished)
        self.assertIn("requirement-risk register scenario for tranche 10", replenished)
        self.assertNotIn("forbidden-marker self-triggering fixture fields", replenished)


if __name__ == "__main__":
    unittest.main()
