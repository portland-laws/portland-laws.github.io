from __future__ import annotations

import unittest

from ppd.daemon.ppd_daemon import (
    format_failure_context,
    is_forbidden_absence_marker_validation_failure,
)
from ppd.daemon.ppd_supervisor import (
    is_forbidden_absence_marker_validation_failure as supervisor_detects_forbidden_marker_failure,
    recent_forbidden_absence_marker_failure_count,
)


class DaemonForbiddenMarkerFailureGuidanceTest(unittest.TestCase):
    def test_daemon_failure_context_names_neutral_absence_fields(self) -> None:
        failure = {
            "failure_kind": "validation",
            "summary": "Add audit export fixture.",
            "errors": ["Validation failed; file edits were rolled back."],
            "validation_results": [
                {
                    "command": ["python3", "-m", "unittest"],
                    "returncode": 1,
                    "stderr": "AssertionError: 'cookie' unexpectedly found in containsCookies",
                    "stdout": "",
                }
            ],
        }

        self.assertTrue(is_forbidden_absence_marker_validation_failure(failure))
        context = format_failure_context([failure])

        self.assertIn("Recovery guidance", context)
        self.assertIn("Return only one JSON object", context)
        self.assertIn("runtimeArtifactsStored", context)
        self.assertIn("visualArtifactsStored", context)
        self.assertIn("forbiddenArtifactsAbsent", context)
        self.assertIn("self-triggering absence fields", context)

    def test_supervisor_counts_current_task_forbidden_marker_validation_failures(self) -> None:
        row = {
            "target_task": "Task checkbox-148: Add audit export.",
            "failure_kind": "validation",
            "errors": ["Validation failed; file edits were rolled back."],
            "validation_results": [
                {
                    "command": ["python3", "-m", "unittest"],
                    "returncode": 1,
                    "stderr": "AssertionError: 'screenshot' unexpectedly found in screenshotsStored",
                }
            ],
        }

        self.assertTrue(supervisor_detects_forbidden_marker_failure(row))
        self.assertEqual(1, recent_forbidden_absence_marker_failure_count([row]))

    def test_supervisor_ignores_completed_task_marker_failures(self) -> None:
        row = {
            "target_task": "Task checkbox-148: Add audit export.",
            "failure_kind": "validation",
            "validation_results": [
                {
                    "returncode": 1,
                    "stderr": "AssertionError: 'cookie' unexpectedly found",
                }
            ],
        }

        self.assertEqual(
            0,
            recent_forbidden_absence_marker_failure_count(
                [row],
                completed_task_labels={"Task checkbox-148: Add audit export."},
            ),
        )


if __name__ == "__main__":
    unittest.main()
