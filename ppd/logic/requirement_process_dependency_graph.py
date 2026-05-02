"""Validation for PP&D requirement-to-process dependency graph fixtures.

The graph fixtures are deterministic guardrail artifacts. They connect extracted
requirements, process steps, missing-information facts, and agent action gates
without carrying private user values or live DevHub state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


BLOCKING_CLASSIFICATIONS = {"consequential", "potentially_consequential", "financial"}
PRIVATE_VALUE_KEYS = {
    "actual_value",
    "after_value",
    "before_value",
    "field_value",
    "private_value",
    "raw_value",
    "user_value",
    "value",
}
SAFE_REDACTED_VALUES = {"[REDACTED]", "[UNKNOWN]", "", "REDACTED"}


@dataclass(frozen=True)
class DependencyGraphFinding:
    """A deterministic validation finding for a dependency graph fixture."""

    path: str
    reason: str


def validate_requirement_process_dependency_graph(graph: Mapping[str, Any]) -> list[DependencyGraphFinding]:
    """Validate a committed PP&D requirement-to-process dependency graph fixture."""

    findings: list[DependencyGraphFinding] = []
    nodes_value = graph.get("nodes", [])
    edges_value = graph.get("edges", [])

    if not isinstance(nodes_value, list):
        return [DependencyGraphFinding("nodes", "nodes must be a list")]
    if not isinstance(edges_value, list):
        return [DependencyGraphFinding("edges", "edges must be a list")]

    known_nodes: set[str] = set()
    for index, node in enumerate(nodes_value):
        path = f"nodes[{index}]"
        if not isinstance(node, Mapping):
            findings.append(DependencyGraphFinding(path, "node must be an object"))
            continue

        node_id = _text(node.get("id"))
        if not node_id:
            findings.append(DependencyGraphFinding(path, "node id is required"))
        elif node_id in known_nodes:
            findings.append(DependencyGraphFinding(path, f"duplicate node id {node_id}"))
        else:
            known_nodes.add(node_id)

        citations = node.get("citations", [])
        if not _has_citations(citations):
            findings.append(DependencyGraphFinding(path, "node must include at least one citation"))

        classification = _classification(node)
        if classification in BLOCKING_CLASSIFICATIONS:
            if node.get("blockedByDefault") is not True:
                findings.append(
                    DependencyGraphFinding(
                        path,
                        f"{classification} node must set blockedByDefault to true",
                    )
                )
            if node.get("explicitConfirmationDefault") is not False:
                findings.append(
                    DependencyGraphFinding(
                        path,
                        f"{classification} node must set explicitConfirmationDefault to false",
                    )
                )
            if node.get("failClosed") is not True:
                findings.append(
                    DependencyGraphFinding(path, f"{classification} node must set failClosed to true")
                )

        findings.extend(_validate_no_private_values(node, path))

    for index, edge in enumerate(edges_value):
        path = f"edges[{index}]"
        if not isinstance(edge, Mapping):
            findings.append(DependencyGraphFinding(path, "edge must be an object"))
            continue

        source = _text(edge.get("source"))
        target = _text(edge.get("target"))
        if not source:
            findings.append(DependencyGraphFinding(path, "edge source is required"))
        elif source not in known_nodes:
            findings.append(DependencyGraphFinding(path, f"edge source {source} is not a known node"))
        if not target:
            findings.append(DependencyGraphFinding(path, "edge target is required"))
        elif target not in known_nodes:
            findings.append(DependencyGraphFinding(path, f"edge target {target} is not a known node"))
        if not _has_citations(edge.get("citations", [])):
            findings.append(DependencyGraphFinding(path, "edge must include at least one citation"))
        if edge.get("failClosed") is not True:
            findings.append(DependencyGraphFinding(path, "edge must set failClosed to true"))

        findings.extend(_validate_no_private_values(edge, path))

    return findings


def assert_requirement_process_dependency_graph(graph: Mapping[str, Any]) -> None:
    """Raise AssertionError with compact diagnostics when a fixture is invalid."""

    findings = validate_requirement_process_dependency_graph(graph)
    if findings:
        details = "; ".join(f"{finding.path}: {finding.reason}" for finding in findings)
        raise AssertionError(details)


def _classification(node: Mapping[str, Any]) -> str:
    for key in ("actionClassification", "classification", "action_classification"):
        value = _text(node.get(key)).lower()
        if value:
            return value
    return ""


def _has_citations(value: Any) -> bool:
    if not isinstance(value, list) or not value:
        return False
    for citation in value:
        if isinstance(citation, Mapping) and _text(citation.get("sourceEvidenceId")):
            return True
        if isinstance(citation, str) and citation.strip():
            return True
    return False


def _validate_no_private_values(value: Any, path: str) -> list[DependencyGraphFinding]:
    findings: list[DependencyGraphFinding] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = _text(key)
            nested_path = f"{path}.{key_text}"
            if _normalized_key(key_text) in PRIVATE_VALUE_KEYS:
                if nested is not None and nested not in SAFE_REDACTED_VALUES:
                    findings.append(
                        DependencyGraphFinding(nested_path, "private values must be redacted or unknown")
                    )
            findings.extend(_validate_no_private_values(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            findings.extend(_validate_no_private_values(nested, f"{path}[{index}]"))
    return findings


def _normalized_key(value: str) -> str:
    chars: list[str] = []
    for char in value:
        if char.isupper() and chars:
            chars.append("_")
        chars.append(char.lower() if char.isalnum() else "_")
    return "_".join(part for part in "".join(chars).split("_") if part)


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
