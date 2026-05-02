from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "source_change"
    / "source_change_impact_scenario.json"
)

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FORBIDDEN_MARKERS = (
    "ppd/data/private",
    "ppd/data/raw",
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
    "raw_http_body",
)


class SourceChangeImpactScenarioTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_archive_provenance_is_manifest_only(self) -> None:
        provenance = self.fixture["archiveProvenance"]
        self.assertEqual("source_change_impact_scenario", self.fixture["fixtureKind"])
        self.assertEqual("ipfs_datasets_py.processor", provenance["processorPackage"])
        self.assertFalse(provenance["networkAccess"])
        self.assertFalse(provenance["rawBodiesIncluded"])
        self.assertTrue(provenance["previousArchiveManifestId"])
        self.assertTrue(provenance["currentArchiveManifestId"])

    def test_changed_evidence_routes_to_affected_requirements(self) -> None:
        evidence_ids = {item["sourceEvidenceId"] for item in self.fixture["changedEvidence"]}
        for evidence in self.fixture["changedEvidence"]:
            self.assertTrue(evidence["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertRegex(evidence["previousHashPlaceholder"], SHA256_RE)
            self.assertRegex(evidence["currentHashPlaceholder"], SHA256_RE)
            self.assertNotEqual(evidence["previousHashPlaceholder"], evidence["currentHashPlaceholder"])
            self.assertEqual("requirement_text_changed", evidence["changeClass"])
            self.assertTrue(evidence["citation"]["locator"])
            self.assertTrue(evidence["citation"]["paraphrase"])

        for requirement in self.fixture["affectedRequirements"]:
            self.assertTrue(set(requirement["sourceEvidenceIds"]).issubset(evidence_ids))
            self.assertEqual("stale_pending_review", requirement["currentStatus"])
            self.assertTrue(requirement["invalidatesGuardrailIds"])
            self.assertTrue(requirement["blocksReuseOfUserAnswerIds"])

    def test_guardrail_invalidation_fails_closed_and_requires_human_review(self) -> None:
        invalidated = self.fixture["guardrailInvalidations"]
        self.assertTrue(invalidated)
        for guardrail in invalidated:
            self.assertEqual("fail_closed", guardrail["defaultOutcome"])
            self.assertTrue(guardrail["requiresHumanReview"])
            self.assertIn("Do not reuse old", guardrail["agentImpact"])

        review = self.fixture["humanReviewQueue"][0]
        self.assertEqual("required_before_autonomous_assistance", review["priority"])
        self.assertTrue(review["requirementIds"])

    def test_planner_blocks_reuse_and_private_artifacts_are_absent(self) -> None:
        outcome = self.fixture["plannerOutcome"]
        self.assertFalse(outcome["reuseOldAnswersAllowed"])
        self.assertFalse(outcome["autonomousCompletionAllowed"])
        self.assertFalse(outcome["safeDraftPreviewAllowed"])
        self.assertEqual("request_human_review_of_changed_public_evidence", outcome["nextAgentAction"])

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)


if __name__ == "__main__":
    unittest.main()
