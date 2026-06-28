from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from ppd.crawler.public_metadata_recrawl_execution_plan import (
    build_public_metadata_recrawl_execution_plan,
    validate_public_metadata_recrawl_execution_plan,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "public_metadata_recrawl_execution_plan" / "execution_inputs.json"


class PublicMetadataRecrawlExecutionPlanTests(unittest.TestCase):
    def load_fixture(self) -> dict:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def build_plan(self) -> dict:
        fixture = self.load_fixture()
        return build_public_metadata_recrawl_execution_plan(
            fixture["reviewedRecrawlBatch"],
            fixture["implementationReadinessPacket"],
            generated_at=fixture["generatedAt"],
        )

    def test_builds_ordered_fixture_first_execution_plan(self) -> None:
        plan = self.build_plan()

        self.assertEqual(plan["planType"], "ppd_public_metadata_recrawl_execution_plan")
        self.assertEqual(validate_public_metadata_recrawl_execution_plan(plan), [])
        self.assertEqual(
            [step["stepId"] for step in plan["orderedDryRunSteps"]],
            [
                "validate_reviewed_recrawl_batch",
                "validate_implementation_readiness_packet",
                "robots_policy_checkpoint",
                "apply_host_rate_limit_windows",
                "prepare_processor_handoff_inputs",
                "stage_metadata_only_outputs",
                "record_rollback_notes",
            ],
        )
        self.assertTrue(all(step["networkAllowed"] is False for step in plan["orderedDryRunSteps"]))
        self.assertEqual(plan["executionPolicy"]["networkInvoked"], False)
        self.assertEqual(plan["executionPolicy"]["processorInvoked"], False)
        self.assertEqual(plan["executionPolicy"]["metadataOnly"], True)

    def test_includes_host_rate_limits_and_robots_policy_checkpoints(self) -> None:
        plan = self.build_plan()

        self.assertEqual(plan["hostRateLimitWindows"][0]["host"], "www.portland.gov")
        self.assertEqual(plan["hostRateLimitWindows"][0]["minDelaySeconds"], 10)
        self.assertEqual(plan["hostRateLimitWindows"][0]["maxRequestsPerWindow"], 6)
        self.assertEqual(plan["hostRateLimitWindows"][0]["networkInvoked"], False)

        checkpoint = plan["robotsPolicyCheckpoints"][0]
        self.assertEqual(checkpoint["sourceId"], "ppd-submit-plans-online")
        self.assertEqual(checkpoint["robotsStatus"], "allowed")
        self.assertEqual(checkpoint["policyStatus"], "approved")
        self.assertEqual(checkpoint["networkInvoked"], False)
        self.assertTrue(checkpoint["requiredBeforeProcessorInvocation"])

    def test_includes_processor_inputs_outputs_and_rollback_notes(self) -> None:
        plan = self.build_plan()

        processor_input = plan["processorHandoffInputs"][0]
        self.assertEqual(processor_input["processor"]["operation"], "capture_url_metadata_only")
        self.assertEqual(processor_input["arguments"]["metadataOnly"], True)
        self.assertEqual(processor_input["arguments"]["persistRawBody"], False)
        self.assertEqual(processor_input["arguments"]["downloadDocuments"], False)

        output = plan["metadataOnlyOutputPaths"][0]
        self.assertTrue(output["processorInputPath"].startswith("metadata_outputs/"))
        self.assertTrue(output["archiveManifestPath"].startswith("metadata_outputs/"))
        self.assertTrue(output["normalizedDocumentPath"].startswith("metadata_outputs/"))
        self.assertTrue(output["metadataOnly"])
        self.assertFalse(output["rawBodyPersisted"])
        self.assertFalse(output["downloadedDocumentsPersisted"])

        rollback = plan["rollbackNotes"][0]
        self.assertEqual(rollback["action"], "discard_staged_metadata_json_only")
        self.assertFalse(rollback["networkRollbackRequired"])
        self.assertFalse(rollback["privateArtifactCleanupRequired"])
        self.assertEqual(
            rollback["metadataArtifactsToRemove"],
            [
                output["processorInputPath"],
                output["archiveManifestPath"],
                output["normalizedDocumentPath"],
            ],
        )

    def test_rejects_live_network_flags_and_raw_artifact_fields(self) -> None:
        plan = self.build_plan()
        plan["executionPolicy"]["networkInvoked"] = True
        plan["processorHandoffInputs"][0]["arguments"]["raw_body"] = "not committed"

        errors = validate_public_metadata_recrawl_execution_plan(plan)

        self.assertIn("executionPolicy.networkInvoked must be false", errors)
        self.assertTrue(any("raw_body is not allowed" in error for error in errors))
        self.assertTrue(any("must not enable live-network execution" in error for error in errors))

    def test_rejects_outside_allowlist_hosts(self) -> None:
        plan = self.build_plan()
        plan["processorHandoffInputs"][0]["canonicalUrl"] = "https://example.com/ppd"
        plan["processorHandoffInputs"][0]["arguments"]["url"] = "https://example.com/ppd"
        plan["hostRateLimitWindows"][0]["host"] = "example.com"

        errors = validate_public_metadata_recrawl_execution_plan(plan)

        self.assertTrue(any("host is not PP&D allowlisted: example.com" in error for error in errors))

    def test_rejects_authenticated_or_private_urls(self) -> None:
        plan = self.build_plan()
        plan["processorHandoffInputs"][0]["requestedUrl"] = "https://devhub.portlandoregon.gov/permits/123"
        plan["robotsPolicyCheckpoints"][0]["canonicalUrl"] = "https://www.portland.gov/ppd?token=private"

        errors = validate_public_metadata_recrawl_execution_plan(plan)

        self.assertTrue(any("private DevHub account paths" in error for error in errors))
        self.assertTrue(any("authenticated or private query parameters" in error for error in errors))

    def test_rejects_raw_body_persistence_and_downloaded_document_paths(self) -> None:
        plan = self.build_plan()
        plan["processorHandoffInputs"][0]["arguments"]["persistRawBody"] = True
        plan["processorHandoffInputs"][0]["arguments"]["downloadDocuments"] = True
        plan["metadataOnlyOutputPaths"][0]["downloadedDocumentsPersisted"] = True
        plan["metadataOnlyOutputPaths"][0]["downloaded_document_path"] = "/tmp/private.pdf"

        errors = validate_public_metadata_recrawl_execution_plan(plan)

        self.assertIn("processorHandoffInputs[0].arguments.persistRawBody must be false", errors)
        self.assertIn("processorHandoffInputs[0].arguments.downloadDocuments must be false", errors)
        self.assertIn("metadataOnlyOutputPaths[0].downloadedDocumentsPersisted must be false", errors)
        self.assertTrue(any("downloaded_document_path is not allowed" in error for error in errors))

    def test_rejects_missing_checkpoint_for_processor_source(self) -> None:
        plan = self.build_plan()
        plan["robotsPolicyCheckpoints"] = []

        errors = validate_public_metadata_recrawl_execution_plan(plan)

        self.assertIn("robotsPolicyCheckpoints must be a non-empty list", errors)

    def test_rejects_missing_rate_limit_window_for_processor_source(self) -> None:
        plan = self.build_plan()
        plan["hostRateLimitWindows"] = []

        errors = validate_public_metadata_recrawl_execution_plan(plan)

        self.assertIn("hostRateLimitWindows must be a non-empty list", errors)
        self.assertIn("hostRateLimitWindows must cover every processor handoff source", errors)

    def test_rejects_missing_dry_run_rollback_notes(self) -> None:
        plan = self.build_plan()
        plan["rollbackNotes"] = []

        errors = validate_public_metadata_recrawl_execution_plan(plan)

        self.assertIn("rollbackNotes must be a non-empty list", errors)
        self.assertIn("rollbackNotes must cover every metadata-only output source", errors)

    def test_rejects_unapproved_readiness_packet_before_plan_build(self) -> None:
        fixture = self.load_fixture()
        readiness = copy.deepcopy(fixture["implementationReadinessPacket"])
        readiness["policy_status"] = "blocked"

        with self.assertRaises(ValueError):
            build_public_metadata_recrawl_execution_plan(
                fixture["reviewedRecrawlBatch"],
                readiness,
                generated_at=fixture["generatedAt"],
            )


if __name__ == "__main__":
    unittest.main()
