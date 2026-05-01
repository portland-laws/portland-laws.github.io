"""Deterministic PP&D public guidance requirement diff contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RequirementDiffKind(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


@dataclass(frozen=True)
class PublicGuidanceRequirement:
    id: str
    source_id: str
    source_url: str
    anchor_id: str
    requirement_type: str
    text: str
    evidence_text: str
    content_hash: str
    page_number: Optional[int] = None

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("requirement id is required")
        if not self.source_id.strip():
            errors.append(f"requirement {self.id} source_id is required")
        if not self.source_url.startswith("https://"):
            errors.append(f"requirement {self.id} source_url must be HTTPS")
        if not self.anchor_id.strip():
            errors.append(f"requirement {self.id} anchor_id is required")
        if not self.requirement_type.strip():
            errors.append(f"requirement {self.id} requirement_type is required")
        if not self.text.strip():
            errors.append(f"requirement {self.id} text is required")
        if not self.evidence_text.strip():
            errors.append(f"requirement {self.id} evidence_text is required")
        if not self.content_hash.startswith("sha256:"):
            errors.append(f"requirement {self.id} content_hash must be sha256")
        if self.page_number is not None and self.page_number < 1:
            errors.append(f"requirement {self.id} page_number must be positive")
        return errors


@dataclass(frozen=True)
class RequirementDiff:
    id: str
    kind: RequirementDiffKind
    requirement_id: str
    before: Optional[PublicGuidanceRequirement] = None
    after: Optional[PublicGuidanceRequirement] = None
    changed_fields: tuple[str, ...] = field(default_factory=tuple)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.id.strip():
            errors.append("diff id is required")
        if not self.requirement_id.strip():
            errors.append(f"diff {self.id} requirement_id is required")
        if self.kind == RequirementDiffKind.ADDED and self.after is None:
            errors.append(f"diff {self.id} added requires after")
        if self.kind == RequirementDiffKind.REMOVED and self.before is None:
            errors.append(f"diff {self.id} removed requires before")
        if self.kind == RequirementDiffKind.CHANGED:
            if self.before is None or self.after is None:
                errors.append(f"diff {self.id} changed requires before and after")
            if not self.changed_fields:
                errors.append(f"diff {self.id} changed requires changed_fields")
        if self.before is not None:
            errors.extend(self.before.validate())
        if self.after is not None:
            errors.extend(self.after.validate())
        return errors


@dataclass(frozen=True)
class RequirementDiffReport:
    report_id: str
    generated_at: str
    before_snapshot_id: str
    after_snapshot_id: str
    diffs: tuple[RequirementDiff, ...]

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.report_id.strip():
            errors.append("report_id is required")
        if not self.generated_at.endswith("Z"):
            errors.append("generated_at must end in Z")
        if not self.before_snapshot_id.strip() or not self.after_snapshot_id.strip():
            errors.append("snapshot ids are required")
        if not self.diffs:
            errors.append("at least one diff is required")
        diff_ids: set[str] = set()
        for diff in self.diffs:
            if diff.id in diff_ids:
                errors.append(f"duplicate diff id {diff.id}")
            diff_ids.add(diff.id)
            errors.extend(diff.validate())
        return errors


def classify_requirement_diffs(
    before: tuple[PublicGuidanceRequirement, ...],
    after: tuple[PublicGuidanceRequirement, ...],
) -> tuple[RequirementDiff, ...]:
    before_by_id = {item.id: item for item in before}
    after_by_id = {item.id: item for item in after}
    diffs: list[RequirementDiff] = []

    for requirement_id in sorted(after_by_id.keys() - before_by_id.keys()):
        diffs.append(RequirementDiff(f"diff-added-{requirement_id}", RequirementDiffKind.ADDED, requirement_id, after=after_by_id[requirement_id]))
    for requirement_id in sorted(before_by_id.keys() - after_by_id.keys()):
        diffs.append(RequirementDiff(f"diff-removed-{requirement_id}", RequirementDiffKind.REMOVED, requirement_id, before=before_by_id[requirement_id]))
    for requirement_id in sorted(before_by_id.keys() & after_by_id.keys()):
        before_item = before_by_id[requirement_id]
        after_item = after_by_id[requirement_id]
        changed_fields = tuple(
            field_name
            for field_name in ("text", "evidence_text", "content_hash", "anchor_id", "requirement_type")
            if getattr(before_item, field_name) != getattr(after_item, field_name)
        )
        if changed_fields:
            diffs.append(
                RequirementDiff(
                    id=f"diff-changed-{requirement_id}",
                    kind=RequirementDiffKind.CHANGED,
                    requirement_id=requirement_id,
                    before=before_item,
                    after=after_item,
                    changed_fields=changed_fields,
                )
            )
    return tuple(diffs)
