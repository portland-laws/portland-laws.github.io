from __future__ import annotations

import json
from pathlib import Path
import unittest

from ppd.daemon.proposal_validation import validate_python_replacements_before_discovery


class ProposalPythonCompileValidationTests(unittest.TestCase):
    def test_syntax_error_fixture_is_rejected_without_blind_retry(self) -> None:
        fixture_path = Path(__file__).parent / "fixtures" / "daemon" / "proposal_with_python_syntax_error.json"
        proposal = json.loads(fixture_path.read_text(encoding="utf-8"))

        result = validate_python_replacements_before_discovery(proposal)

        self.assertFalse(result.accepted)
        self.assertFalse(result.retry_same_task)
        self.assertEqual(len(result.failures), 1)
        failure = result.failures[0]
        self.assertEqual(failure.path, "ppd/tests/fixtures/generated/bad_replacement.py")
        self.assertEqual(failure.kind, "python_syntax_error")
        self.assertFalse(failure.retry_same_task)
        self.assertTrue(failure.signature.startswith("py_compile:"))
        self.assertIn("invalid syntax", failure.message.lower())

    def test_valid_python_replacements_pass_pre_discovery_validation(self) -> None:
        proposal = {
            "files": [
                {
                    "path": "ppd/example_valid_replacement.py",
                    "content": "VALUE = 1\n\ndef answer() -> int:\n    return VALUE\n",
                },
                {
                    "path": "ppd/example_notes.txt",
                    "content": "Text replacements do not go through py_compile.\n",
                },
            ]
        }

        result = validate_python_replacements_before_discovery(proposal)

        self.assertTrue(result.accepted)
        self.assertTrue(result.retry_same_task)
        self.assertEqual(result.failures, ())


if __name__ == "__main__":
    unittest.main()
