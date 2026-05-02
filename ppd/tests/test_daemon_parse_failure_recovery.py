from __future__ import annotations

import unittest

from ppd.daemon.parse_failure_recovery import (
    ParseFailureAttempt,
    count_recent_non_json_failures,
    decide_parse_failure_recovery,
)


class DaemonParseFailureRecoveryTest(unittest.TestCase):
    def test_completed_task_parse_failures_are_superseded_not_retried(self) -> None:
        label = "Task checkbox-140: Add integrated handoff fixture."
        attempts = (
            ParseFailureAttempt(task_label=label, failure_kind="parse"),
            ParseFailureAttempt(task_label=label, failure_kind="parse"),
        )

        decision = decide_parse_failure_recovery(
            attempts,
            task_label=label,
            completed_task_labels=frozenset({label}),
            manually_satisfied_task_labels=frozenset(),
        )

        self.assertEqual("supersede_completed_task_parse_failures", decision.action)
        self.assertFalse(decision.should_retry_task)
        self.assertFalse(decision.should_park_task)
        self.assertTrue(decision.should_mark_superseded)

    def test_manually_satisfied_task_parse_failures_are_superseded_not_retried(self) -> None:
        label = "Task checkbox-145: Add agent work-order scenario."

        decision = decide_parse_failure_recovery(
            (ParseFailureAttempt(task_label=label, failure_kind="parse"),),
            task_label=label,
            completed_task_labels=frozenset(),
            manually_satisfied_task_labels=frozenset({label}),
        )

        self.assertEqual("supersede_manually_satisfied_task_parse_failures", decision.action)
        self.assertFalse(decision.should_retry_task)
        self.assertTrue(decision.should_mark_superseded)

    def test_repeated_active_non_json_failures_are_parked_after_threshold(self) -> None:
        label = "Task checkbox-146: Add parse-failure recovery coverage."
        attempts = (
            ParseFailureAttempt(task_label="Task checkbox-1: Older task.", failure_kind="parse"),
            ParseFailureAttempt(task_label=label, failure_kind="parse"),
            ParseFailureAttempt(task_label=label, failure_kind="parse"),
        )

        self.assertEqual(2, count_recent_non_json_failures(attempts, label))
        decision = decide_parse_failure_recovery(
            attempts,
            task_label=label,
            completed_task_labels=frozenset(),
            manually_satisfied_task_labels=frozenset(),
            threshold=2,
        )

        self.assertEqual("park_repeated_parse_failure_task", decision.action)
        self.assertFalse(decision.should_retry_task)
        self.assertTrue(decision.should_park_task)
        self.assertFalse(decision.should_mark_superseded)

    def test_single_active_non_json_failure_gets_json_only_retry_window(self) -> None:
        label = "Task checkbox-146: Add parse-failure recovery coverage."

        decision = decide_parse_failure_recovery(
            (ParseFailureAttempt(task_label=label, failure_kind="parse"),),
            task_label=label,
            completed_task_labels=frozenset(),
            manually_satisfied_task_labels=frozenset(),
            threshold=2,
        )

        self.assertEqual("retry_with_json_only_prompt", decision.action)
        self.assertTrue(decision.should_retry_task)
        self.assertFalse(decision.should_park_task)
        self.assertFalse(decision.should_mark_superseded)

    def test_changed_file_or_non_parse_attempt_breaks_non_json_streak(self) -> None:
        label = "Task checkbox-146: Add parse-failure recovery coverage."
        attempts = (
            ParseFailureAttempt(task_label=label, failure_kind="parse"),
            ParseFailureAttempt(task_label=label, failure_kind="parse", changed_files=("ppd/tests/example.py",)),
        )

        self.assertEqual(0, count_recent_non_json_failures(attempts, label))


if __name__ == "__main__":
    unittest.main()
