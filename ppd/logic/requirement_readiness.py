"""Deterministic readiness validation for PP&D guardrail requirement inputs.

This module intentionally accepts plain dictionaries instead of extending shared
contracts. It is a narrow preflight gate for compiled guardrail bundles: a
requirement node may feed a bundle only when the node and its cited evidence are
fresh, supported, human-reviewed, and formalization-ready.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

FRESH_STATUSES = frozenset({"fresh", "current"})
SUPPORTED_STATUSES = frozenset({"supported", "formalized", "ready"})
HUMAN_REVIEWED_STATUSES = frozenset({"approved", "reviewed", "human_reviewed"})
FORMALIZATION_READY_STATUSES = frozenset({"ready", "formalized"})


@dataclass(frozen=True)
class RequirementReadinessIssue:
    """A deterministic reason a requirement cannot feed a guardrail bundle."""

    requirement_id: str
    code: str
    message: str


@dataclass(frozen=True)
class RequirementReadinessReport:
    """Validation result for a proposed guardrail bundle input set."""

    bundle_id: str
    ready_requirement_ids: tuple[str, ...]
    blocked_requirement_ids: tuple[str, ...]
    issues: tuple[RequirementReadinessIssue, ...]

    @property
    def is_ready(self) -> bool:
        return not self.issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "is_ready": self.is_ready,
            "ready_requirement_ids": list(self.ready_requirement_ids),
            "blocked_requirement_ids": list(self.blocked_requirement_ids),
            "issues": [
                {
                    "requirement_id": issue.requirement_id,
                    "code": issue.code,
                    "message": issue.message,
                }
                for issue in self.issues
            ],
        }


def validate_guardrail_requirement_inputs(candidate: Mapping[str, Any]) -> RequirementReadinessReport:
    """Validate requirement nodes before guardrail bundle compilation.

    Expected input is a deterministic fixture or in-memory candidate shaped like:
    {
        "guardrail_bundle_id": "...",
        "requirements": [{...}],
        "source_evidence": [{"evidence_id": "...", "freshness_status": "fresh"}]
    }

    No network, file, crawler, or authenticated source reads are performed here.
    """

    bundle_id = _clean_text(candidate.get("guardrail_bundle_id")) or "unknown_bundle"
    requirements = _as_sequence(candidate.get("requirements"))
    evidence_by_id = _index_source_evidence(candidate.get("source_evidence"))

    ready_ids: list[str] = []
    blocked_ids: list[str] = []
    issues: list[RequirementReadinessIssue] = []

    for index, requirement in enumerate(requirements):
        if not isinstance(requirement, Mapping):
            requirement_id = f"requirement[{index}]"
            blocked_ids.append(requirement_id)
            issues.append(
                RequirementReadinessIssue(
                    requirement_id=requirement_id,
                    code="invalid_requirement_node",
                    message="Requirement node must be an object.",
                )
            )
            continue

        requirement_id = _clean_text(requirement.get("requirement_id")) or f"requirement[{index}]"
        node_issues = _validate_requirement_node(requirement_id, requirement, evidence_by_id)
        if node_issues:
            blocked_ids.append(requirement_id)
            issues.extend(node_issues)
        else:
            ready_ids.append(requirement_id)

    return RequirementReadinessReport(
        bundle_id=bundle_id,
        ready_requirement_ids=tuple(sorted(ready_ids)),
        blocked_requirement_ids=tuple(sorted(blocked_ids)),
        issues=tuple(issues),
    )


def ready_requirement_ids(candidate: Mapping[str, Any]) -> tuple[str, ...]:
    """Return only requirement IDs that are eligible for guardrail compilation."""

    return validate_guardrail_requirement_inputs(candidate).ready_requirement_ids


def _validate_requirement_node(
    requirement_id: str,
    requirement: Mapping[str, Any],
    evidence_by_id: Mapping[str, Mapping[str, Any]],
) -> tuple[RequirementReadinessIssue, ...]:
    issues: list[RequirementReadinessIssue] = []

    node_freshness = _normalized_status(requirement.get("freshness_status"))
    if node_freshness not in FRESH_STATUSES:
        issues.append(
            RequirementReadinessIssue(
                requirement_id=requirement_id,
                code="requirement_not_fresh",
                message="Requirement node freshness_status must be fresh/current.",
            )
        )

    support_status = _normalized_status(requirement.get("support_status"))
    if support_status not in SUPPORTED_STATUSES:
        issues.append(
            RequirementReadinessIssue(
                requirement_id=requirement_id,
                code="requirement_not_supported",
                message="Requirement node support_status must show source support.",
            )
        )

    human_review_status = _normalized_status(requirement.get("human_review_status"))
    if human_review_status not in HUMAN_REVIEWED_STATUSES:
        issues.append(
            RequirementReadinessIssue(
                requirement_id=requirement_id,
                code="requirement_not_human_reviewed",
                message="Requirement node must be approved by human review.",
            )
        )

    formalization_status = _normalized_status(requirement.get("formalization_status"))
    if formalization_status not in FORMALIZATION_READY_STATUSES:
        issues.append(
            RequirementReadinessIssue(
                requirement_id=requirement_id,
                code="requirement_not_formalization_ready",
                message="Requirement node formalization_status must be ready/formalized.",
            )
        )

    if bool(requirement.get("unsupported_path")):
        issues.append(
            RequirementReadinessIssue(
                requirement_id=requirement_id,
                code="unsupported_requirement_path",
                message="Unsupported requirement paths cannot feed guardrail bundles.",
            )
        )

    evidence_ids = tuple(_clean_text(value) for value in _as_sequence(requirement.get("source_evidence_ids")))
    evidence_ids = tuple(value for value in evidence_ids if value)
    if not evidence_ids:
        issues.append(
            RequirementReadinessIssue(
                requirement_id=requirement_id,
                code="missing_source_evidence",
                message="Requirement node must cite at least one source evidence id.",
            )
        )
        return tuple(issues)

    for evidence_id in evidence_ids:
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None:
            issues.append(
                RequirementReadinessIssue(
                    requirement_id=requirement_id,
                    code="unknown_source_evidence",
                    message=f"Source evidence id {evidence_id!r} is not present in the candidate.",
                )
            )
            continue

        evidence_freshness = _normalized_status(evidence.get("freshness_status"))
        if evidence_freshness not in FRESH_STATUSES:
            issues.append(
                RequirementReadinessIssue(
                    requirement_id=requirement_id,
                    code="source_evidence_not_fresh",
                    message=f"Source evidence id {evidence_id!r} must be fresh/current.",
                )
            )

    return tuple(issues)


def _index_source_evidence(raw_evidence: Any) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for item in _as_sequence(raw_evidence):
        if not isinstance(item, Mapping):
            continue
        evidence_id = _clean_text(item.get("evidence_id"))
        if evidence_id:
            indexed[evidence_id] = item
    return indexed


def _as_sequence(value: Any) -> Sequence[Any]:
    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return (value,)
    if isinstance(value, Sequence):
        return value
    return ()


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalized_status(value: Any) -> str:
    return _clean_text(value).lower().replace("-", "_").replace(" ", "_")
