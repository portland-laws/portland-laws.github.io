import unittest

from ppd.daemon.supervisor_resume_policy import (
    RECOVERY_CHECKBOXES,
    recommend_resume_policy,
    recent_syntax_failure_count,
)


class SupervisorResumePolicyTest(unittest.TestCase):
    def test_recommends_one_constrained_resume_after_recovery_tasks_pass(self):
        runtime_status = {
            "active_target_task": "Task checkbox-113: Task checkbox-108: Add a fixture-only public crawl frontier checkpoint"
        }
        progress = {
            "task_counts": {"blocked": 1, "needed": 0, "in_progress": 0},
            "recent_results": [
                {"target_task": f"Task checkbox-{number}: recovery", "validation_passed": True}
                for number in sorted(RECOVERY_CHECKBOXES)
            ],
        }

        decision = recommend_resume_policy(runtime_status, progress)

        self.assertTrue(decision.may_resume)
        self.assertIn("strict syntax-first", decision.reason)
        self.assertIn("one_json_fixture_plus_one_python_unittest", decision.allowed_file_shapes)
        self.assertTrue(any("Do not perform network access" in guardrail for guardrail in decision.required_guardrails))

    def test_blocks_resume_until_all_recovery_checkboxes_pass(self):
        runtime_status = {"active_target_task": "Task checkbox-113: blocked task"}
        progress = {
            "task_counts": {"blocked": 1, "needed": 0, "in_progress": 0},
            "recent_results": [
                {"target_task": "Task checkbox-112: recovery", "validation_passed": True},
                {"target_task": "Task checkbox-113: recovery", "validation_passed": True},
                {"target_task": "Task checkbox-114: recovery", "validation_passed": True},
                {"target_task": "Task checkbox-115: recovery", "validation_passed": True},
            ],
        }

        decision = recommend_resume_policy(runtime_status, progress)

        self.assertFalse(decision.may_resume)
        self.assertIn("checkbox-116", decision.reason)

    def test_policy_does_not_apply_when_selectable_work_remains(self):
        runtime_status = {"active_target_task": "Task checkbox-113: blocked task"}
        progress = {
            "task_counts": {"blocked": 1, "needed": 1, "in_progress": 0},
            "recent_results": [
                {"target_task": f"Task checkbox-{number}: recovery", "validation_passed": True}
                for number in sorted(RECOVERY_CHECKBOXES)
            ],
        }

        decision = recommend_resume_policy(runtime_status, progress)

        self.assertFalse(decision.may_resume)
        self.assertIn("exactly one blocked task", decision.reason)

    def test_counts_recent_syntax_failures_from_kind_or_error_text(self):
        recent_results = [
            {"failure_kind": "syntax_preflight", "errors": []},
            {"failure_kind": "validation", "errors": ["python3 -m py_compile failed with SyntaxError"]},
            {"failure_kind": "validation", "errors": ["TypeScript TS1005 parser failure"]},
            {"failure_kind": "validation", "errors": ["ordinary assertion failure"]},
        ]

        self.assertEqual(recent_syntax_failure_count(recent_results), 3)


if __name__ == "__main__":
    unittest.main()
