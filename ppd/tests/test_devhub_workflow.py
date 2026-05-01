"""Tests for side-effect-free DevHub workflow recorder contracts."""

from __future__ import annotations

import unittest

from ppd.contracts.processes import ActionGateClassification
from ppd.devhub import (
    DevHubActionKind,
    DevHubField,
    DevHubFieldKind,
    DevHubWorkflowAction,
    DevHubWorkflowState,
    DevHubWorkflowStateKind,
    classify_workflow_action,
)


class DevHubWorkflowContractTests(unittest.TestCase):
    def test_valid_state_records_schema_without_private_values(self) -> None:
        state = DevHubWorkflowState(
            id="draft-building-permit",
            workflow="building_permit_application",
            kind=DevHubWorkflowStateKind.APPLICATION_FORM,
            url_pattern="https://devhub.portlandoregon.gov/**/draft/**",
            heading="Building Permit Request",
            captured_at="2026-05-01T00:00:00Z",
            fields=(
                DevHubField(
                    id="project-description",
                    label="Project description",
                    kind=DevHubFieldKind.TEXT,
                    required=True,
                    redacted_value_present=True,
                ),
            ),
            actions=(
                DevHubWorkflowAction(
                    id="save-draft",
                    label="Save draft",
                    kind=DevHubActionKind.SAVE_DRAFT,
                ),
            ),
            private_values_redacted=True,
        )

        self.assertEqual(state.validate(), [])

    def test_consequential_actions_require_confirmation(self) -> None:
        action = DevHubWorkflowAction(
            id="submit",
            label="Submit",
            kind=DevHubActionKind.SUBMIT_APPLICATION,
        )
        self.assertIn("action submit requires confirmation text", action.validate())

    def test_action_classification_matches_guardrail_levels(self) -> None:
        self.assertEqual(
            classify_workflow_action(DevHubWorkflowAction("read", "Read status", DevHubActionKind.READ_STATUS)),
            ActionGateClassification.SAFE_READ_ONLY,
        )
        self.assertEqual(
            classify_workflow_action(DevHubWorkflowAction("save", "Save", DevHubActionKind.SAVE_DRAFT)),
            ActionGateClassification.REVERSIBLE_DRAFT_EDIT,
        )
        self.assertEqual(
            classify_workflow_action(
                DevHubWorkflowAction(
                    "upload",
                    "Upload corrections",
                    DevHubActionKind.OFFICIAL_UPLOAD,
                    confirmation_text="Upload these correction files",
                )
            ),
            ActionGateClassification.POTENTIALLY_CONSEQUENTIAL,
        )
        self.assertEqual(
            classify_workflow_action(
                DevHubWorkflowAction(
                    "pay",
                    "Pay fees",
                    DevHubActionKind.PAY_FEE,
                    confirmation_text="Pay the listed fees",
                )
            ),
            ActionGateClassification.FINANCIAL,
        )

    def test_state_validation_rejects_unredacted_private_values(self) -> None:
        state = DevHubWorkflowState(
            id="my-permits",
            workflow="permit_status",
            kind=DevHubWorkflowStateKind.MY_PERMITS,
            url_pattern="https://devhub.portlandoregon.gov/**/my-permits",
            heading="My Permits",
            captured_at="2026-05-01T00:00:00Z",
            private_values_redacted=False,
        )

        self.assertIn("state my-permits must redact private values", state.validate())


if __name__ == "__main__":
    unittest.main()
