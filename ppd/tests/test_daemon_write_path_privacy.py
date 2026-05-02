#!/usr/bin/env python3
"""Regression tests for daemon write-path privacy filtering."""

from __future__ import annotations

import unittest

from ppd.daemon.ppd_daemon import validate_write_path


class DaemonWritePathPrivacyTests(unittest.TestCase):
    def test_supersession_fixture_names_are_not_private_session_artifacts(self) -> None:
        allowed_paths = [
            "ppd/tests/fixtures/daemon/checkbox_130_checkbox_108_supersession_decision.json",
            "ppd/tests/test_checkbox_130_supersession_decision_fixture.py",
        ]
        for path in allowed_paths:
            with self.subTest(path=path):
                self.assertEqual([], validate_write_path(path))

    def test_session_and_auth_state_artifacts_remain_blocked(self) -> None:
        blocked_paths = [
            "ppd/data/private/devhub/session.json",
            "ppd/tests/fixtures/devhub/auth-state.json",
            "ppd/tests/fixtures/devhub/storage-state.json",
            "ppd/tests/fixtures/devhub/session-state.json",
        ]
        for path in blocked_paths:
            with self.subTest(path=path):
                self.assertTrue(
                    any("private/session artifacts" in error for error in validate_write_path(path)),
                    validate_write_path(path),
                )


if __name__ == "__main__":
    unittest.main()
