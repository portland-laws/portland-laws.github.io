from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "human_review" / "human_review_packet.json"
FORBIDDEN_MARKERS = (
    "ppd/data/private",
    "auth-state",
    "storage-state",
    "trace.zip",
    ".har",
    "cookie",
    "password",
    "token",
    "card_number",
    "routing_number",
    "account_number",
    "cvv",
)


class HumanReviewPacketTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_packet_bundles_all_unresolved_review_inputs(self) -> None:
        self.assertEqual("human_review_packet", self.fixture["fixtureKind"])
        self.assertTrue(self.fixture["conflictingEvidence"])
        self.assertTrue(self.fixture["staleAnswers"])
        self.assertTrue(self.fixture["uploadReadiness"])
        self.assertTrue(self.fixture["feeNotices"])
        self.assertTrue(self.fixture["blockedDevhubTransitions"])

    def test_review_items_are_redacted_and_source_linked(self) -> None:
        source_ids = {item["sourceEvidenceId"] for item in self.fixture["sourceEvidence"]}
        for source in self.fixture["sourceEvidence"]:
            self.assertTrue(source["sourceUrl"].startswith("https://www.portland.gov/ppd/"))
            self.assertTrue(source["citation"]["locator"])
            self.assertTrue(source["citation"]["paraphrase"])

        for conflict in self.fixture["conflictingEvidence"]:
            self.assertEqual("human_review", conflict["defaultOutcome"])
            for candidate in conflict["candidateValues"]:
                self.assertTrue(candidate["redactedDisplay"].startswith("[REDACTED_"))
                self.assertTrue(set(candidate["sourceEvidenceIds"]).issubset(source_ids))

        for answer in self.fixture["staleAnswers"]:
            self.assertEqual("ask_user", answer["defaultOutcome"])
            self.assertTrue(answer["redactedDisplay"].startswith("[REDACTED_"))
            self.assertTrue(set(answer["sourceEvidenceIds"]).issubset(source_ids))

    def test_upload_fee_and_blocked_transitions_fail_closed(self) -> None:
        for upload_item in self.fixture["uploadReadiness"]:
            self.assertTrue(upload_item["metadataOnly"])
            self.assertFalse(upload_item["contentStored"])
            self.assertEqual("metadata_present_needs_human_review", upload_item["readiness"])

        for notice in self.fixture["feeNotices"]:
            self.assertTrue(notice["noticeOnly"])
            self.assertFalse(notice["amountStored"])
            self.assertTrue(notice["redactedDisplay"].startswith("[REDACTED_"))

        for transition in self.fixture["blockedDevhubTransitions"]:
            self.assertTrue(transition["blockedByDefault"])
            self.assertTrue(transition["requiresExactConfirmation"])
            self.assertFalse(transition["exactConfirmationPresent"])

    def test_reviewer_actions_and_planner_keep_human_in_loop(self) -> None:
        actions = set(self.fixture["reviewerActions"])
        self.assertTrue(
            {
                "review_conflicting_public_evidence",
                "request_updated_user_answer",
                "review_redacted_file_metadata",
                "acknowledge_notice_only_fee_guidance",
                "refuse_official_action_without_exact_confirmation",
            }.issubset(actions)
        )
        outcome = self.fixture["plannerOutcome"]
        self.assertEqual("prepare_human_review_handoff", outcome["nextAgentAction"])
        self.assertFalse(outcome["draftPreviewAllowed"])
        self.assertFalse(outcome["officialSubmissionAllowed"])
        self.assertFalse(outcome["paymentAutomationAllowed"])

    def test_private_values_and_runtime_artifacts_are_absent(self) -> None:
        boundary = self.fixture["boundary"]
        self.assertTrue(boundary["fixtureOnly"])
        self.assertFalse(boundary["liveDevhubAccess"])
        self.assertFalse(boundary["browserLaunchRequested"])
        self.assertFalse(boundary["officialActionAllowed"])
        self.assertFalse(boundary["privateArtifactStored"])
        self.assertFalse(boundary["paymentDataStored"])

        serialized = json.dumps(self.fixture, sort_keys=True).lower()
        for marker in FORBIDDEN_MARKERS:
            self.assertNotIn(marker, serialized)
        self.assertEqual([], find_unredacted_private_values(self.fixture))


def find_unredacted_private_values(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in {"rawvalue", "privatevalue", "knownvalue", "filecontents"}:
                findings.append(f"{path}.{key}")
            findings.extend(find_unredacted_private_values(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(find_unredacted_private_values(child, f"{path}[{index}]"))
    elif isinstance(value, str) and not value.startswith("[REDACTED_") and "real user" in value.lower():
        findings.append(path)
    return findings


if __name__ == "__main__":
    unittest.main()
