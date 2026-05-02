from pathlib import Path
import unittest


class SupervisorRepairGuideTest(unittest.TestCase):
    def setUp(self):
        self.guide = Path(__file__).resolve().parents[1] / "daemon" / "SUPERVISOR_REPAIR_GUIDE.md"
        self.text = self.guide.read_text(encoding="utf-8")

    def test_guide_targets_recent_syntax_failure_patterns(self):
        required_fragments = [
            "page_number None",
            "page_number list[str]",
            "page_count list[str]",
            "if self.page_count list[str]",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, self.text)

    def test_guide_requires_small_syntax_valid_retries(self):
        required_fragments = [
            "One syntax-valid Python unittest file",
            "One small JSON fixture plus one syntax-valid Python unittest file",
            "Every Python conditional uses complete comparisons",
            "No Python file contains TypeScript-style expression fragments",
        ]
        for fragment in required_fragments:
            self.assertIn(fragment, self.text)

    def test_guide_keeps_repair_separate_from_domain_implementation(self):
        self.assertIn("must not implement the stalled PP&D domain task directly", self.text)
        self.assertIn("does not download documents", self.text)
        self.assertIn("private DevHub artifacts", self.text)


if __name__ == "__main__":
    unittest.main()
