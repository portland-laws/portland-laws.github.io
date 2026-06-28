from __future__ import annotations

import unittest

from ppd.devhub.live_action_executor import LiveDevHubActionKind
from ppd.surfaces.registry import (
    AutomationMode,
    SurfaceKind,
    binding_for_devhub_action,
    build_agentic_completion_contract,
    ppd_surface_registry,
)


class PpdSurfaceRegistryTest(unittest.TestCase):
    def test_every_live_devhub_action_has_a_surface_binding(self) -> None:
        mapped = {
            action
            for binding in ppd_surface_registry()
            for action in binding.devhub_actions
        }

        self.assertEqual(set(LiveDevHubActionKind), mapped)

    def test_official_and_payment_surfaces_remain_attended_or_manual(self) -> None:
        official_actions = {
            LiveDevHubActionKind.OFFICIAL_UPLOAD,
            LiveDevHubActionKind.SUBMIT_APPLICATION,
            LiveDevHubActionKind.CERTIFY_STATEMENT,
            LiveDevHubActionKind.CANCEL_REQUEST,
            LiveDevHubActionKind.SCHEDULE_INSPECTION,
        }
        for action in official_actions:
            binding = binding_for_devhub_action(action)
            self.assertEqual(AutomationMode.ATTENDED_EXACT_CONFIRMATION, binding.automation_mode)
            self.assertIn("exact action confirmation", binding.required_guardrails)
            self.assertIn("post-action hardening", binding.required_guardrails)

        self.assertEqual(
            AutomationMode.MANUAL_HANDOFF,
            binding_for_devhub_action(LiveDevHubActionKind.PAY_FEE).automation_mode,
        )
        self.assertEqual(
            AutomationMode.MANUAL_HANDOFF,
            binding_for_devhub_action(LiveDevHubActionKind.ENTER_PAYMENT_DETAILS).automation_mode,
        )

    def test_completion_contract_covers_public_to_closeout_chain(self) -> None:
        contract = build_agentic_completion_contract()
        ordered = contract["orderedSurfaces"]

        self.assertEqual(SurfaceKind.PUBLIC_GUIDANCE.value, ordered[0])
        self.assertIn(SurfaceKind.PROCESSOR_ARCHIVE.value, ordered)
        self.assertIn(SurfaceKind.REQUIREMENT_LOGIC.value, ordered)
        self.assertIn(SurfaceKind.PDF_DRAFT_FILL.value, ordered)
        self.assertIn(SurfaceKind.DEVHUB_UPLOAD.value, ordered)
        self.assertIn(SurfaceKind.DEVHUB_PAYMENT.value, ordered)
        self.assertIn(SurfaceKind.DEVHUB_SUBMISSION.value, ordered)
        self.assertIn(SurfaceKind.COMPLETION_EVIDENCE.value, ordered)
        self.assertIn("post-action hardening", contract["completionRule"])
        self.assertIn("completion evidence ids", contract["completionRule"])

    def test_registry_modules_stay_ppd_scoped_and_side_effect_free(self) -> None:
        for binding in ppd_surface_registry():
            self.assertTrue(binding.modules, binding.surface.value)
            for module in binding.modules:
                self.assertTrue(module.startswith("ppd."), module)
            if binding.automation_mode == AutomationMode.PUBLIC_READ_ONLY:
                self.assertNotIn("exact action confirmation", binding.required_guardrails)


if __name__ == "__main__":
    unittest.main()
