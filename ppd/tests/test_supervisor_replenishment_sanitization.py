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


if __name__ == "__main__":
    unittest.main()
