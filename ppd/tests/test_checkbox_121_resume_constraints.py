from __future__ import annotations

import json
import unittest
from pathlib import Path


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "daemon" / "checkbox_121_resume_constraints.json"


class Checkbox121ResumeConstraintsTest(unittest.TestCase):
    def load_fixture(self) -> dict:
        with FIXTURE_PATH.open("r", encoding="utf-8") as fixture_file:
            data = json.load(fixture_file)
        self.assertIsInstance(data, dict)
        return data

    def test_checkbox_108_resume_is_gated_on_112_through_115_passing(self) -> None:
        data = self.load_fixture()

        self.assertEqual(data.get("current_task"), "checkbox-121")
        self.assertEqual(data.get("resume_task"), "checkbox-108")

        prerequisites = data.get("prerequisites")
        self.assertIsInstance(prerequisites, list)
        self.assertEqual(
            [item.get("task") for item in prerequisites],
            ["checkbox-112", "checkbox-113", "checkbox-114", "checkbox-115"],
        )
        self.assertTrue(all(item.get("required_result") == "pass" for item in prerequisites))

        resume_gate = data.get("resume_gate")
        self.assertIsInstance(resume_gate, dict)
        self.assertEqual(resume_gate.get("mode"), "all_prerequisites_must_pass")
        self.assertIs(resume_gate.get("block_if_any_prerequisite_missing"), True)
        self.assertIs(resume_gate.get("block_if_any_prerequisite_not_passed"), True)

    def test_resumed_attempt_is_limited_to_syntax_valid_python_or_small_fixture_pair(self) -> None:
        data = self.load_fixture()
        limits = data.get("attempt_limits")
        self.assertIsInstance(limits, dict)

        self.assertEqual(
            limits.get("allowed_file_shapes"),
            [
                "one_python_file",
                "one_small_json_fixture_plus_one_python_unittest_file",
            ],
        )
        self.assertEqual(limits.get("max_python_files"), 1)
        self.assertEqual(limits.get("max_json_fixture_files"), 1)
        self.assertEqual(limits.get("max_total_files"), 2)
        self.assertIs(limits.get("python_files_must_be_syntactically_valid"), True)
        self.assertIs(limits.get("python_unittest_required_when_json_fixture_is_present"), True)
        self.assertIs(limits.get("typescript_files_allowed"), False)

    def test_constraints_stay_inside_ppd_and_exclude_private_or_consequential_work(self) -> None:
        data = self.load_fixture()

        self.assertEqual(data.get("allowed_path_prefixes"), ["ppd/"])
        forbidden_prefixes = set(data.get("forbidden_path_prefixes", []))
        self.assertIn("src/lib/logic/", forbidden_prefixes)
        self.assertIn("public/corpus/portland-or/current/", forbidden_prefixes)
        self.assertIn("ipfs_datasets_py/.daemon/", forbidden_prefixes)

        forbidden_actions = set(data.get("forbidden_actions", []))
        self.assertIn("captcha", forbidden_actions)
        self.assertIn("mfa", forbidden_actions)
        self.assertIn("payment", forbidden_actions)
        self.assertIn("official_submission", forbidden_actions)
        self.assertIn("upload", forbidden_actions)


if __name__ == "__main__":
    unittest.main()
