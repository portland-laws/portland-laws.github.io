"""Fixture-first next-release integration rehearsal packet builder.

This module is intentionally side-effect free. It reads committed synthetic
fixtures and returns release recommendations for reviewer rehearsal only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

OFFLINE_VALIDATION_COMMANDS: List[List[str]] = [
    ["python3", "-m", "py_compile", "ppd/next_release_rehearsal.py"],
    ["python3", "-m", "pytest", "ppd/tests/test_next_release_rehearsal.py"],
]

_ALLOWED_CATEGORIES = {"release-ready", "release-held", "release-rejected"}


@dataclass(frozen=True)
class RehearsalCandidate:
    """Synthetic candidate for release-decision rehearsal."""

    candidate_id: str
    title: str
    synthetic_source_freshness_delta: Mapping[str, Any]
    requirement_extraction_delta: Mapping[str, Any]
    process_dependency_delta: Mapping[str, Any]
    guardrail_impact_delta: Mapping[str, Any]
    agent_gap_analysis_delta: Mapping[str, Any]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RehearsalCandidate":
        required = [
            "candidate_id",
            "title",
            "synthetic_source_freshness_delta",
            "requirement_extraction_delta",
            "process_dependency_delta",
            "guardrail_impact_delta",
            "agent_gap_analysis_delta",
        ]
        missing = [key for key in required if key not in value]
        if missing:
            raise ValueError(f"candidate is missing required fields: {', '.join(missing)}")
        return cls(
            candidate_id=_require_string(value, "candidate_id"),
            title=_require_string(value, "title"),
            synthetic_source_freshness_delta=_require_mapping(value, "synthetic_source_freshness_delta"),
            requirement_extraction_delta=_require_mapping(value, "requirement_extraction_delta"),
            process_dependency_delta=_require_mapping(value, "process_dependency_delta"),
            guardrail_impact_delta=_require_mapping(value, "guardrail_impact_delta"),
            agent_gap_analysis_delta=_require_mapping(value, "agent_gap_analysis_delta"),
        )


def load_fixture_packet(path: Path) -> Dict[str, Any]:
    """Load a committed rehearsal fixture packet from disk."""

    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("rehearsal fixture packet must be a JSON object")
    return value


def build_rehearsal_packet(fixture_packet: Mapping[str, Any]) -> Dict[str, Any]:
    """Build a release rehearsal packet from deterministic fixture data."""

    packet_id = _require_string(fixture_packet, "packet_id")
    packet_version = _require_string(fixture_packet, "packet_version")
    generated_from = _require_string(fixture_packet, "generated_from")
    candidates_value = fixture_packet.get("candidates")
    if not isinstance(candidates_value, list):
        raise ValueError("fixture packet must include a candidates list")

    candidates = [RehearsalCandidate.from_mapping(item) for item in candidates_value]
    recommendations = [_recommend(candidate) for candidate in candidates]

    return {
        "packet_id": packet_id,
        "packet_version": packet_version,
        "generated_from": generated_from,
        "mode": "fixture-first-offline-rehearsal",
        "mutation_policy": {
            "release_promotion": "forbidden",
            "live_crawling": "forbidden",
            "devhub_access": "forbidden",
            "private_files": "forbidden",
            "uploads_submissions_certifications_payments_scheduling": "forbidden",
            "state_mutation": "forbidden",
        },
        "recommendations": recommendations,
        "recommendation_counts": _count_categories(recommendations),
        "dependency_ordering": _global_dependency_ordering(recommendations),
        "offline_validation_commands": [list(command) for command in OFFLINE_VALIDATION_COMMANDS],
    }


def packet_to_json(packet: Mapping[str, Any]) -> str:
    """Serialize a rehearsal packet deterministically for snapshots or CLI use."""

    return json.dumps(packet, indent=2, sort_keys=True) + "\n"


def _recommend(candidate: RehearsalCandidate) -> Dict[str, Any]:
    freshness = candidate.synthetic_source_freshness_delta
    extraction = candidate.requirement_extraction_delta
    dependency = candidate.process_dependency_delta
    guardrail = candidate.guardrail_impact_delta
    gap = candidate.agent_gap_analysis_delta

    blockers = list(_strings(freshness.get("blocking_issues")))
    blockers.extend(_strings(extraction.get("blocking_issues")))
    blockers.extend(_strings(dependency.get("blocking_issues")))
    blockers.extend(_strings(guardrail.get("blocking_issues")))
    blockers.extend(_strings(gap.get("blocking_issues")))

    review_items = list(_strings(freshness.get("review_items")))
    review_items.extend(_strings(extraction.get("review_items")))
    review_items.extend(_strings(dependency.get("review_items")))
    review_items.extend(_strings(guardrail.get("review_items")))
    review_items.extend(_strings(gap.get("review_items")))

    consequential_actions = set(_strings(guardrail.get("consequential_actions")))
    active_mutation_requested = bool(guardrail.get("active_mutation_requested", False))
    source_is_current = freshness.get("status") == "current"
    requirements_complete = bool(extraction.get("all_required_requirements_extracted", False))
    dependencies_satisfied = bool(dependency.get("all_required_dependencies_satisfied", False))
    gap_ready = bool(gap.get("agent_gap_delta_resolved", False))

    if blockers or active_mutation_requested or "payment_execution" in consequential_actions:
        category = "release-rejected"
        disposition = "reject"
    elif review_items or not dependencies_satisfied or not gap_ready:
        category = "release-held"
        disposition = "hold-for-review"
    elif source_is_current and requirements_complete:
        category = "release-ready"
        disposition = "approve-for-next-release-review"
    else:
        category = "release-held"
        disposition = "hold-for-review"

    if category not in _ALLOWED_CATEGORIES:
        raise ValueError(f"unsupported recommendation category: {category}")

    return {
        "candidate_id": candidate.candidate_id,
        "title": candidate.title,
        "recommendation": category,
        "reviewer_disposition": disposition,
        "synthetic_source_freshness_delta": dict(freshness),
        "requirement_extraction_delta": dict(extraction),
        "process_dependency_delta": dict(dependency),
        "guardrail_impact_delta": dict(guardrail),
        "agent_gap_analysis_delta": dict(gap),
        "dependency_order": _dependency_order(candidate),
        "rollback_notes": _rollback_notes(category, candidate),
        "offline_validation_commands": [list(command) for command in OFFLINE_VALIDATION_COMMANDS],
    }


def _dependency_order(candidate: RehearsalCandidate) -> List[str]:
    declared = list(_strings(candidate.process_dependency_delta.get("dependency_order")))
    if declared:
        return declared
    return [
        "synthetic_source_freshness_delta",
        "requirement_extraction_delta",
        "process_dependency_delta",
        "guardrail_impact_delta",
        "agent_gap_analysis_delta",
        f"recommendation:{candidate.candidate_id}",
    ]


def _rollback_notes(category: str, candidate: RehearsalCandidate) -> List[str]:
    base = [
        "No release promotion was performed by this rehearsal packet.",
        "Rollback is limited to removing the generated rehearsal artifact from review notes because no crawler, DevHub, prompt, guardrail, process-model, requirement, contract, source, archive, document, release, or daemon state is mutated.",
    ]
    if category == "release-ready":
        base.append("If validation fails, hold this candidate and rerun the exact offline validation commands before reviewer disposition changes.")
    elif category == "release-held":
        base.append("Keep the candidate out of release promotion until reviewer-held items and dependency ordering concerns are resolved in a new fixture packet.")
    else:
        base.append("Reject the candidate for this release rehearsal and require a new fixture delta before reconsideration.")
    base.append(f"Candidate rollback scope: {candidate.candidate_id}.")
    return base


def _global_dependency_ordering(recommendations: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    ordered = []
    for item in recommendations:
        ordered.append(
            {
                "candidate_id": item["candidate_id"],
                "recommendation": item["recommendation"],
                "dependency_order": list(item["dependency_order"]),
            }
        )
    return ordered


def _count_categories(recommendations: Iterable[Mapping[str, Any]]) -> Dict[str, int]:
    counts = {category: 0 for category in sorted(_ALLOWED_CATEGORIES)}
    for item in recommendations:
        category = item.get("recommendation")
        if category not in counts:
            raise ValueError(f"unsupported recommendation category in output: {category}")
        counts[str(category)] += 1
    return counts


def _strings(value: Any) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("expected a list of strings")
    result = []
    for item in value:
        if not isinstance(item, str) or not item:
            raise ValueError("expected only non-empty strings")
        result.append(item)
    return result


def _require_string(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item:
        raise ValueError(f"{key} must be a non-empty string")
    return item


def _require_mapping(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    item = value.get(key)
    if not isinstance(item, dict):
        raise ValueError(f"{key} must be an object")
    return item
