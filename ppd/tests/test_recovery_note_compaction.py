from __future__ import annotations

import json
import unittest
from pathlib import Path

from ppd.daemon.recovery_note_compaction import (
    compact_task_board_repair_notes,
    extract_repair_notes,
    summarize_recovery_notes,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "recovery_notes" / "repeated_supervisor_repair_notes.json"


class RecoveryNoteCompactionTest(unittest.TestCase):
    def test_repeated_supervisor_repair_notes_are_summarized_for_prompt_context(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        board = fixture["taskBoardMarkdown"]

        notes = extract_repair_notes(board)
        summary = summarize_recovery_notes(notes, max_items=2, max_chars=360)
        prompt_text = compact_task_board_repair_notes(board, max_items=2, max_chars=360)

        self.assertEqual(fixture["expectedTotalNotes"], summary.total_notes)
        self.assertEqual(fixture["expectedUniqueNotes"], summary.unique_notes)
        self.assertLess(len(prompt_text), len(board))
        self.assertIn("Supervisor repair notes summarized: total=3 unique=2", prompt_text)
        self.assertIn("Parked repeated LLM parse/runtime loop", prompt_text)
        self.assertIn("Parked open generated blocked-cascade daemon-repair tasks", prompt_text)
        self.assertNotIn("regular task-board note mentions repair", prompt_text)

    def test_summary_truncates_before_future_prompt_construction(self) -> None:
        repeated_notes = [
            "Parked repeated repair note " + str(index) + " " + ("detail " * 40)
            for index in range(10)
        ]

        prompt_text = summarize_recovery_notes(repeated_notes, max_items=3, max_chars=180).to_prompt_text()

        self.assertLessEqual(len(prompt_text), 260)
        self.assertIn("total=10 unique=10", prompt_text)
        self.assertTrue(prompt_text.endswith("...") or "additional unique note(s) omitted" in prompt_text)


if __name__ == "__main__":
    unittest.main()
