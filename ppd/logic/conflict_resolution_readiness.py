"""Fixture-only readiness checks for contradictory PP&D requirement nodes.

The checker is intentionally conservative: when two cited requirement nodes make
opposite claims about the same scoped requirement key, it blocks formalization
and asks for missing information or human review. It never chooses a winning
requirement automatically.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


BLOCKING_REQUIREMENT_PAIRS = frozenset(
    {
        frozenset(("obligation", "prohibition")),
        frozenset(("permission", "prohibition")),
        frozenset(("document_requirement", "prohibition")),
        frozenset(("action_gate", "permission")),
    }
)


@dataclass(frozen=True)
class ConflictPrompt:
    """A cited prompt emitted when a contradiction blocks formalization."""

    prompt_type: str
    message: str
    requirement_ids: tuple[str, ...]
    citation_ids: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "prompt_type": self.prompt_type,
            "message": self.message,
            "requirement_ids": list(self.requirement_ids),
            "citation_ids": list(self.citation_ids),
        }


@dataclass(frozen=True)
class RequirementConflict:
    """A contradiction between two scoped requirement nodes."""

    conflict_id: str
    requirement_ids: tuple[str, str]
    citation_ids: tuple[str, ...]
    conflict_key: tuple[Any, ...]
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "requirement_ids": list(self.requirement_ids),
            "citation_ids": list(self.citation_ids),
            "conflict_key": list(self.conflict_key),
            "reason": self.reason,
        }


def load_conflict_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed conflict-readiness fixture from disk."""

    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("conflict readiness fixture must be a JSON object")
    return data


def evaluate_conflict_resolution_readiness(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate whether requirement nodes are ready for formalization.

    The returned payload is serializable and intentionally explicit so tests and
    daemon checks can assert that conflicts block formalization without relying
    on live crawl state or authenticated DevHub data.
    """

    nodes = _requirement_nodes(fixture)
    conflicts = _find_conflicts(nodes)
    if not conflicts:
        return {
            "readiness_status": "ready_for_formalization",
            "formalization_allowed": True,
            "selected_requirement_id": None,
            "conflicts": [],
            "prompts": [],
            "requirement_statuses": {
                node["requirement_id"]: "ready_for_formalization" for node in nodes
            },
        }

    blocked_ids = sorted(
        {
            requirement_id
            for conflict in conflicts
            for requirement_id in conflict.requirement_ids
        }
    )
    prompts = _build_prompts(conflicts, nodes)
    return {
        "readiness_status": "blocked_by_contradictory_requirements",
        "formalization_allowed": False,
        "selected_requirement_id": None,
        "conflicts": [conflict.as_dict() for conflict in conflicts],
        "prompts": [prompt.as_dict() for prompt in prompts],
        "requirement_statuses": {
            node["requirement_id"]: (
                "blocked_pending_human_review"
                if node["requirement_id"] in blocked_ids
                else "ready_for_formalization"
            )
            for node in nodes
        },
    }


def _requirement_nodes(fixture: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_nodes = fixture.get("requirement_nodes")
    if not isinstance(raw_nodes, list):
        raise ValueError("fixture must contain a requirement_nodes list")

    nodes: list[dict[str, Any]] = []
    for index, raw_node in enumerate(raw_nodes):
        if not isinstance(raw_node, dict):
            raise ValueError(f"requirement_nodes[{index}] must be an object")
        requirement_id = raw_node.get("requirement_id")
        if not isinstance(requirement_id, str) or not requirement_id:
            raise ValueError(f"requirement_nodes[{index}] must have a requirement_id")
        evidence_ids = raw_node.get("source_evidence_ids")
        if not isinstance(evidence_ids, list) or not evidence_ids:
            raise ValueError(
                f"requirement {requirement_id} must have cited source_evidence_ids"
            )
        if not all(isinstance(evidence_id, str) for evidence_id in evidence_ids):
            raise ValueError(
                f"requirement {requirement_id} source_evidence_ids must be strings"
            )
        nodes.append(dict(raw_node))
    return nodes


def _find_conflicts(nodes: Iterable[Mapping[str, Any]]) -> list[RequirementConflict]:
    materialized = list(nodes)
    conflicts: list[RequirementConflict] = []
    for left_index, left in enumerate(materialized):
        for right in materialized[left_index + 1 :]:
            if not _has_same_scope(left, right):
                continue
            if not _is_blocking_pair(left, right):
                continue
            left_id = str(left["requirement_id"])
            right_id = str(right["requirement_id"])
            citation_ids = tuple(
                sorted(
                    set(_string_list(left.get("source_evidence_ids")))
                    | set(_string_list(right.get("source_evidence_ids")))
                )
            )
            conflicts.append(
                RequirementConflict(
                    conflict_id=f"conflict::{left_id}::{right_id}",
                    requirement_ids=(left_id, right_id),
                    citation_ids=citation_ids,
                    conflict_key=_conflict_key(left),
                    reason=(
                        "Contradictory requirement types share the same subject, "
                        "action, object, permit type, stage, and conditions."
                    ),
                )
            )
    return conflicts


def _has_same_scope(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    return _conflict_key(left) == _conflict_key(right)


def _is_blocking_pair(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    pair = frozenset(
        (
            str(left.get("requirement_type", "")),
            str(right.get("requirement_type", "")),
        )
    )
    if pair in BLOCKING_REQUIREMENT_PAIRS:
        return True
    return _normalized(left.get("object")) == _normalized(
        right.get("object")
    ) and _normalized(left.get("action")) != _normalized(right.get("action"))


def _conflict_key(node: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        _normalized(node.get("subject")),
        _normalized(node.get("object")),
        _normalized(node.get("process_stage")),
        tuple(sorted(_normalized(value) for value in _string_list(node.get("permit_types")))),
        tuple(sorted(_normalized(value) for value in _string_list(node.get("conditions")))),
        _normalized(node.get("deadline_or_temporal_scope")),
    )


def _build_prompts(
    conflicts: Iterable[RequirementConflict], nodes: Iterable[Mapping[str, Any]]
) -> list[ConflictPrompt]:
    node_by_id = {str(node["requirement_id"]): node for node in nodes}
    prompts: list[ConflictPrompt] = []
    for conflict in conflicts:
        left = node_by_id[conflict.requirement_ids[0]]
        right = node_by_id[conflict.requirement_ids[1]]
        label = _prompt_label(left)
        prompts.append(
            ConflictPrompt(
                prompt_type="missing_information",
                message=(
                    f"Confirm which cited PP&D instruction controls {label}; "
                    "the fixture contains contradictory requirement nodes."
                ),
                requirement_ids=conflict.requirement_ids,
                citation_ids=conflict.citation_ids,
            )
        )
        prompts.append(
            ConflictPrompt(
                prompt_type="human_review",
                message=(
                    "Human review is required before formalizing this rule; "
                    "the checker cannot choose between cited contradictory nodes."
                ),
                requirement_ids=conflict.requirement_ids,
                citation_ids=conflict.citation_ids,
            )
        )
        _ = right
    return prompts


def _prompt_label(node: Mapping[str, Any]) -> str:
    subject = str(node.get("subject", "the requirement")).strip() or "the requirement"
    action = str(node.get("action", "applies to")).strip() or "applies to"
    object_value = str(node.get("object", "the cited object")).strip() or "the cited object"
    return f"{subject} {action} {object_value}"


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _normalized(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().lower().split())
