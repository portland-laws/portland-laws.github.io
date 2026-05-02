from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from ppd.contracts.source_diff import PublicGuidanceRequirement, RequirementDiffKind, classify_requirement_diffs


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source-diff" / "changed_requirement_evidence_continuity.json"


class SourceDiffChangedRequirementEvidenceTest(unittest.TestCase):
    def load_fixture(self) -> dict[str, Any]:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_changed_requirement_preserves_evidence_and_fails_closed(self) -> None:
        fixture = self.load_fixture()
        errors = validate_changed_requirement_source_diff_fixture(fixture)
        self.assertEqual([], errors)

    def test_contract_classifier_keeps_changed_requirement_id_stable(self) -> None:
        fixture = self.load_fixture()
        before_requirement = fixture["beforeRequirements"][0]
        after_requirement = fixture["afterRequirements"][0]
        evidence_by_id = {item["id"]: item for item in fixture["sourceEvidence"]}
        before_evidence = evidence_by_id[before_requirement["sourceEvidenceIds"][0]]
        after_evidence = evidence_by_id[after_requirement["sourceEvidenceIds"][0]]

        diffs = classify_requirement_diffs(
            (
                PublicGuidanceRequirement(
                    id=before_requirement["requirementId"],
                    source_id=before_evidence["sourceId"],
                    source_url=before_evidence["sourceUrl"],
                    anchor_id=before_evidence["anchorId"],
                    requirement_type=before_requirement["requirementType"],
                    text=f"{before_requirement['action']} {before_requirement['object']}",
                    evidence_text=before_evidence["evidenceText"],
                    content_hash=before_evidence["contentHash"],
                ),
            ),
            (
                PublicGuidanceRequirement(
                    id=after_requirement["requirementId"],
                    source_id=after_evidence["sourceId"],
                    source_url=after_evidence["sourceUrl"],
                    anchor_id=after_evidence["anchorId"],
                    requirement_type=after_requirement["requirementType"],
                    text=f"{after_requirement['action']} {after_requirement['object']}",
                    evidence_text=after_evidence["evidenceText"],
                    content_hash=after_evidence["contentHash"],
                ),
            ),
        )

        self.assertEqual(1, len(diffs))
        self.assertEqual(RequirementDiffKind.CHANGED, diffs[0].kind)
        self.assertEqual("req-single-pdf-process-upload-format", diffs[0].requirement_id)

    def test_changed_diff_rejects_missing_prior_source_evidence(self) -> None:
        fixture = self.load_fixture()
        fixture["diffs"][0]["previousSourceEvidenceIds"] = []
        errors = validate_changed_requirement_source_diff_fixture(fixture)
        self.assertIn("diff diff-changed-req-single-pdf-process-upload-format must preserve previousSourceEvidenceIds", errors)

    def test_changed_diff_rejects_unstable_requirement_ids(self) -> None:
        fixture = self.load_fixture()
        fixture["diffs"][0]["afterRequirementId"] = "req-renumbered-after-change"
        errors = validate_changed_requirement_source_diff_fixture(fixture)
        self.assertIn("diff diff-changed-req-single-pdf-process-upload-format changed requirements must keep before/after requirement ids stable", errors)

    def test_changed_diff_rejects_non_fail_closed_agent_summary(self) -> None:
        fixture = self.load_fixture()
        fixture["diffs"][0]["agentImpactSummary"]["mayUseForAutomation"] = True
        errors = validate_changed_requirement_source_diff_fixture(fixture)
        self.assertIn("diff diff-changed-req-single-pdf-process-upload-format agentImpactSummary must fail closed for automation", errors)


def validate_changed_requirement_source_diff_fixture(fixture: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if fixture.get("fixtureKind") != "source_diff_changed_requirement_evidence_continuity":
        errors.append("fixtureKind must be source_diff_changed_requirement_evidence_continuity")
    if fixture.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    if not str(fixture.get("generatedAt", "")).endswith("Z"):
        errors.append("generatedAt must end in Z")
    if not fixture.get("beforeSnapshotId") or not fixture.get("afterSnapshotId"):
        errors.append("beforeSnapshotId and afterSnapshotId are required")

    source_evidence = fixture.get("sourceEvidence")
    before_requirements = fixture.get("beforeRequirements")
    after_requirements = fixture.get("afterRequirements")
    diffs = fixture.get("diffs")
    if not isinstance(source_evidence, list) or not source_evidence:
        errors.append("sourceEvidence must be a non-empty array")
        source_evidence = []
    if not isinstance(before_requirements, list) or not before_requirements:
        errors.append("beforeRequirements must be a non-empty array")
        before_requirements = []
    if not isinstance(after_requirements, list) or not after_requirements:
        errors.append("afterRequirements must be a non-empty array")
        after_requirements = []
    if not isinstance(diffs, list) or not diffs:
        errors.append("diffs must be a non-empty array")
        diffs = []

    evidence_ids = set()
    for index, evidence in enumerate(source_evidence):
        if not isinstance(evidence, dict):
            errors.append(f"sourceEvidence[{index}] must be an object")
            continue
        evidence_id = evidence.get("id")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            errors.append(f"sourceEvidence[{index}].id is required")
            continue
        evidence_ids.add(evidence_id)
        if not str(evidence.get("sourceUrl", "")).startswith("https://"):
            errors.append(f"sourceEvidence {evidence_id} sourceUrl must be HTTPS")
        if not str(evidence.get("contentHash", "")).startswith("sha256:"):
            errors.append(f"sourceEvidence {evidence_id} contentHash must be sha256")
        if not str(evidence.get("evidenceText", "")).strip():
            errors.append(f"sourceEvidence {evidence_id} evidenceText is required")

    before_by_id = _requirements_by_id(before_requirements, "beforeRequirements", evidence_ids, errors)
    after_by_id = _requirements_by_id(after_requirements, "afterRequirements", evidence_ids, errors)

    for index, diff in enumerate(diffs):
        if not isinstance(diff, dict):
            errors.append(f"diffs[{index}] must be an object")
            continue
        diff_id = str(diff.get("id", ""))
        label = diff_id or f"diffs[{index}]"
        if not diff_id.strip():
            errors.append(f"{label} id is required")
        if diff.get("kind") != "changed":
            errors.append(f"diff {label} kind must be changed")
            continue

        requirement_id = diff.get("requirementId")
        before_requirement_id = diff.get("beforeRequirementId")
        after_requirement_id = diff.get("afterRequirementId")
        if not requirement_id or not before_requirement_id or not after_requirement_id:
            errors.append(f"diff {label} requirementId, beforeRequirementId, and afterRequirementId are required")
        elif requirement_id != before_requirement_id or requirement_id != after_requirement_id:
            errors.append(f"diff {label} changed requirements must keep before/after requirement ids stable")
        if requirement_id not in before_by_id or requirement_id not in after_by_id:
            errors.append(f"diff {label} changed requirement must exist in before and after snapshots")

        previous_ids = diff.get("previousSourceEvidenceIds")
        current_ids = diff.get("currentSourceEvidenceIds")
        if not isinstance(previous_ids, list) or not previous_ids:
            errors.append(f"diff {label} must preserve previousSourceEvidenceIds")
            previous_ids = []
        if not isinstance(current_ids, list) or not current_ids:
            errors.append(f"diff {label} must preserve currentSourceEvidenceIds")
            current_ids = []
        for evidence_id in previous_ids + current_ids:
            if evidence_id not in evidence_ids:
                errors.append(f"diff {label} references unknown source evidence id {evidence_id}")

        if requirement_id in before_by_id and previous_ids:
            expected_previous = set(before_by_id[requirement_id].get("sourceEvidenceIds", []))
            if not expected_previous.issubset(set(previous_ids)):
                errors.append(f"diff {label} previousSourceEvidenceIds must include the before requirement evidence")
        if requirement_id in after_by_id and current_ids:
            expected_current = set(after_by_id[requirement_id].get("sourceEvidenceIds", []))
            if not expected_current.issubset(set(current_ids)):
                errors.append(f"diff {label} currentSourceEvidenceIds must include the after requirement evidence")

        if not diff.get("reviewNeeded"):
            errors.append(f"diff {label} reviewNeeded must be true for changed requirements")
        review_reasons = diff.get("reviewReasons")
        if not isinstance(review_reasons, list) or not all(str(reason).strip() for reason in review_reasons):
            errors.append(f"diff {label} reviewReasons must explain why review is needed")
        if not isinstance(diff.get("changedFields"), list) or not diff["changedFields"]:
            errors.append(f"diff {label} changedFields must be non-empty")

        impact = diff.get("agentImpactSummary")
        if not isinstance(impact, dict):
            errors.append(f"diff {label} agentImpactSummary is required")
            continue
        if impact.get("mode") != "fail_closed":
            errors.append(f"diff {label} agentImpactSummary mode must be fail_closed")
        if impact.get("mayUseForAutomation") is not False:
            errors.append(f"diff {label} agentImpactSummary must fail closed for automation")
        if impact.get("requiresHumanReview") is not True:
            errors.append(f"diff {label} agentImpactSummary must require human review")
        if not str(impact.get("summary", "")).strip():
            errors.append(f"diff {label} agentImpactSummary summary is required")
        blocked_actions = impact.get("blockedAgentActions")
        if not isinstance(blocked_actions, list) or not blocked_actions:
            errors.append(f"diff {label} agentImpactSummary must list blockedAgentActions")

    return errors


def _requirements_by_id(
    requirements: list[Any],
    field: str,
    evidence_ids: set[str],
    errors: list[str],
) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for index, requirement in enumerate(requirements):
        if not isinstance(requirement, dict):
            errors.append(f"{field}[{index}] must be an object")
            continue
        requirement_id = requirement.get("requirementId")
        if not isinstance(requirement_id, str) or not requirement_id.strip():
            errors.append(f"{field}[{index}].requirementId is required")
            continue
        if requirement_id in by_id:
            errors.append(f"{field} duplicate requirementId {requirement_id}")
        by_id[requirement_id] = requirement
        source_evidence_ids = requirement.get("sourceEvidenceIds")
        if not isinstance(source_evidence_ids, list) or not source_evidence_ids:
            errors.append(f"{field} {requirement_id} sourceEvidenceIds must be non-empty")
            continue
        for evidence_id in source_evidence_ids:
            if evidence_id not in evidence_ids:
                errors.append(f"{field} {requirement_id} references unknown source evidence id {evidence_id}")
    return by_id


if __name__ == "__main__":
    unittest.main()
