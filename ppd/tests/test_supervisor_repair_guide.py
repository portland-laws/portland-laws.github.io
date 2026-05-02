from pathlib import Path
import unittest


class SupervisorRepairGuideTest(unittest.TestCase):
    def setUp(self) -> None:
        self.guide = Path(__file__).resolve().parents[1] / "daemon" / "SUPERVISOR_REPAIR_GUIDE.md"
        self.text = self.guide.read_text(encoding="utf-8")

    def test_guide_exists_for_daemon_prompt_context(self) -> None:
        self.assertTrue(self.guide.exists())
        self.assertIn("Syntax-Preflight Recovery", self.text)
        self.assertIn("Replenishment Task Guidance", self.text)

    def test_rejects_recent_invalid_python_pattern(self) -> None:
        self.assertIn("if value list[str]", self.text)
        self.assertIn("if value tuple[str, ...]", self.text)
        self.assertIn("isinstance(value, list)", self.text)
        self.assertIn("python3 -m py_compile", self.text)

    def test_preserves_ppd_safety_boundaries(self) -> None:
        forbidden_actions = (
            "auth state",
            "uploads",
            "submissions",
            "payments",
            "certifications",
            "cancellations",
            "MFA",
            "CAPTCHA",
            "inspection scheduling",
        )
        for action in forbidden_actions:
            self.assertIn(action, self.text)


if __name__ == "__main__":
    unittest.main()
