import json
import unittest
from pathlib import Path

from ppd.contracts.source_diff import (
    PublicGuidanceRequirement,
    RequirementDiffKind,
    RequirementDiffReport,
    classify_requirement_diffs,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "source_diff_requirement_report.json"


def build_requirement(item: dict) -> PublicGuidanceRequirement:
    return PublicGuidanceRequirement(
        id=item["id"],
        source_id=item["sourceId"],
        source_url=item["sourceUrl"],
        anchor_id=item["anchorId"],
        requirement_type=item["requirementType"],
        text=item["text"],
        evidence_text=item["evidenceText"],
        content_hash=item["contentHash"],
        page_number=item.get("pageNumber"),
    )


class SourceDiffComparatorTests(unittest.TestCase):
    def load_fixture(self) -> dict:
        return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_classifies_added_removed_and_changed_requirements(self) -> None:
        fixture = self.load_fixture()
        before = tuple(build_requirement(item) for item in fixture["before"])
        after = tuple(build_requirement(item) for item in fixture["after"])
        diffs = classify_requirement_diffs(before, after)
        by_kind = {
            kind.value: sorted(diff.requirement_id for diff in diffs if diff.kind == kind)
            for kind in (RequirementDiffKind.ADDED, RequirementDiffKind.REMOVED, RequirementDiffKind.CHANGED)
        }
        self.assertEqual(by_kind, fixture["expectedDiffKinds"])

    def test_diff_report_validates(self) -> None:
        fixture = self.load_fixture()
        diffs = classify_requirement_diffs(
            tuple(build_requirement(item) for item in fixture["before"]),
            tuple(build_requirement(item) for item in fixture["after"]),
        )
        report = RequirementDiffReport(
            report_id=fixture["reportId"],
            generated_at=fixture["generatedAt"],
            before_snapshot_id=fixture["beforeSnapshotId"],
            after_snapshot_id=fixture["afterSnapshotId"],
            diffs=diffs,
        )
        self.assertFalse(report.validate())


if __name__ == "__main__":
    unittest.main()
