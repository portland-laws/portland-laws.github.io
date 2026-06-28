"""Normalize fixture-backed PP&D process dependency graphs.

This module is intentionally side-effect free. It does not crawl public pages,
open browsers, infer permit rules, or assume domain dependencies beyond the
process model fields supplied by deterministic fixtures or callers.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Iterable, Mapping, Sequence


_NODE_ID_RE = re.compile(r"[^a-z0-9]+")


class ProcessDependencyGraphError(ValueError):
    """Raised when a supplied process dependency graph is structurally invalid."""


@dataclass(frozen=True)
class _NodeSeed:
    node_id: str
    node_type: str
    label: str
    source_evidence_ids: tuple[str, ...]
    payload: Mapping[str, Any]


def normalize_process_dependency_graph(process_model: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic dependency graph for a PP&D process model.

    Supported input is deliberately small:
    - ``process_id`` and optional ``permit_type`` metadata.
    - ``stages`` as strings or mappings. Stage mappings may include
      ``stage_id``/``id``, ``name``/``label``, ``depends_on``,
      ``required_user_facts``, ``required_documents``, and
      ``source_evidence_ids``.
    - Top-level ``required_user_facts`` and ``required_documents`` as strings
      or mappings. Mappings may include explicit ``stage``/``process_stage``
      to connect them to a stage.

    The normalizer only creates edges from explicit evidence in the supplied
    model plus the order of the supplied stages. It does not infer PP&D permit
    semantics.
    """

    if not isinstance(process_model, Mapping):
        raise ProcessDependencyGraphError("process_model must be a mapping")

    process_id = _required_text(process_model, "process_id")
    graph_id = _stable_id("graph", process_id)

    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}

    stage_nodes = [_coerce_stage(stage, index) for index, stage in enumerate(_sequence(process_model.get("stages", [])))]
    stage_aliases: dict[str, str] = {}

    for stage in stage_nodes:
        _add_node(nodes, stage)
        stage_aliases[_alias(stage.label)] = stage.node_id
        stage_aliases[_alias(stage.node_id)] = stage.node_id

    for earlier, later in zip(stage_nodes, stage_nodes[1:]):
        _add_edge(edges, earlier.node_id, later.node_id, "stage_order", "listed stage order", earlier.source_evidence_ids + later.source_evidence_ids)

    for stage in stage_nodes:
        for dependency in _sequence(stage.payload.get("depends_on", [])):
            dependency_id = _resolve_stage_reference(dependency, stage_aliases)
            _add_edge(edges, dependency_id, stage.node_id, "explicit_dependency", "stage depends_on", stage.source_evidence_ids)

        for fact in _sequence(stage.payload.get("required_user_facts", [])):
            fact_node = _coerce_requirement_node(fact, "fact", stage.source_evidence_ids)
            _add_node(nodes, fact_node)
            _add_edge(edges, fact_node.node_id, stage.node_id, "required_fact", "stage required_user_facts", fact_node.source_evidence_ids + stage.source_evidence_ids)

        for document in _sequence(stage.payload.get("required_documents", [])):
            document_node = _coerce_requirement_node(document, "document", stage.source_evidence_ids)
            _add_node(nodes, document_node)
            _add_edge(edges, document_node.node_id, stage.node_id, "required_document", "stage required_documents", document_node.source_evidence_ids + stage.source_evidence_ids)

    for fact in _sequence(process_model.get("required_user_facts", [])):
        fact_node = _coerce_requirement_node(fact, "fact", _source_ids(process_model.get("source_evidence_ids", [])))
        _add_node(nodes, fact_node)
        stage_id = _stage_for_item(fact, stage_aliases)
        if stage_id is not None:
            _add_edge(edges, fact_node.node_id, stage_id, "required_fact", "required_user_facts stage", fact_node.source_evidence_ids)

    for document in _sequence(process_model.get("required_documents", [])):
        document_node = _coerce_requirement_node(document, "document", _source_ids(process_model.get("source_evidence_ids", [])))
        _add_node(nodes, document_node)
        stage_id = _stage_for_item(document, stage_aliases)
        if stage_id is not None:
            _add_edge(edges, document_node.node_id, stage_id, "required_document", "required_documents stage", document_node.source_evidence_ids)

    normalized_nodes = [nodes[node_id] for node_id in sorted(nodes)]
    normalized_edges = [edges[key] for key in sorted(edges)]

    return {
        "graph_id": graph_id,
        "process_id": process_id,
        "permit_type": _optional_text(process_model.get("permit_type")),
        "nodes": normalized_nodes,
        "edges": normalized_edges,
        "validation": _validate_graph(normalized_nodes, normalized_edges),
    }


def _coerce_stage(stage: Any, index: int) -> _NodeSeed:
    if isinstance(stage, str):
        label = _clean_text(stage, f"stages[{index}]")
        payload: Mapping[str, Any] = {}
        source_ids: tuple[str, ...] = ()
        raw_id = label
    elif isinstance(stage, Mapping):
        label = _clean_text(stage.get("name") or stage.get("label") or stage.get("stage") or stage.get("stage_id") or stage.get("id"), f"stages[{index}]")
        payload = stage
        source_ids = _source_ids(stage.get("source_evidence_ids", []))
        raw_id = _optional_text(stage.get("stage_id") or stage.get("id")) or label
    else:
        raise ProcessDependencyGraphError(f"stages[{index}] must be a string or mapping")

    return _NodeSeed(
        node_id=_stable_id("stage", raw_id),
        node_type="stage",
        label=label,
        source_evidence_ids=source_ids,
        payload=payload,
    )


def _coerce_requirement_node(item: Any, node_type: str, fallback_source_ids: Iterable[str]) -> _NodeSeed:
    if isinstance(item, str):
        label = _clean_text(item, node_type)
        payload: Mapping[str, Any] = {}
        raw_id = label
        source_ids = tuple(fallback_source_ids)
    elif isinstance(item, Mapping):
        label = _clean_text(item.get("label") or item.get("name") or item.get("fact") or item.get("document") or item.get("id"), node_type)
        payload = item
        raw_id = _optional_text(item.get("id") or item.get("fact_id") or item.get("document_id")) or label
        source_ids = _source_ids(item.get("source_evidence_ids", fallback_source_ids))
    else:
        raise ProcessDependencyGraphError(f"{node_type} item must be a string or mapping")

    return _NodeSeed(
        node_id=_stable_id(node_type, raw_id),
        node_type=node_type,
        label=label,
        source_evidence_ids=source_ids,
        payload=payload,
    )


def _add_node(nodes: dict[str, dict[str, Any]], seed: _NodeSeed) -> None:
    existing = nodes.get(seed.node_id)
    next_node = {
        "id": seed.node_id,
        "type": seed.node_type,
        "label": seed.label,
        "source_evidence_ids": sorted(set(seed.source_evidence_ids)),
    }
    if existing is None:
        nodes[seed.node_id] = next_node
        return
    if existing["type"] != next_node["type"] or existing["label"] != next_node["label"]:
        raise ProcessDependencyGraphError(f"conflicting node definition for {seed.node_id}")
    existing["source_evidence_ids"] = sorted(set(existing["source_evidence_ids"]) | set(next_node["source_evidence_ids"]))


def _add_edge(edges: dict[tuple[str, str, str], dict[str, Any]], source: str, target: str, edge_type: str, evidence: str, source_evidence_ids: Iterable[str]) -> None:
    if source == target:
        raise ProcessDependencyGraphError(f"self dependency is not allowed for {source}")
    key = (source, target, edge_type)
    existing = edges.get(key)
    next_ids = set(_source_ids(source_evidence_ids))
    if existing is None:
        edges[key] = {
            "source": source,
            "target": target,
            "type": edge_type,
            "evidence": evidence,
            "source_evidence_ids": sorted(next_ids),
        }
        return
    existing["source_evidence_ids"] = sorted(set(existing["source_evidence_ids"]) | next_ids)


def _validate_graph(nodes: Sequence[Mapping[str, Any]], edges: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    node_ids = {str(node["id"]) for node in nodes}
    missing_refs = []
    for edge in edges:
        if edge["source"] not in node_ids:
            missing_refs.append({"edge": edge, "missing": edge["source"]})
        if edge["target"] not in node_ids:
            missing_refs.append({"edge": edge, "missing": edge["target"]})
    return {
        "status": "valid" if not missing_refs else "invalid",
        "node_count": len(nodes),
        "edge_count": len(edges),
        "missing_references": missing_refs,
    }


def _stage_for_item(item: Any, stage_aliases: Mapping[str, str]) -> str | None:
    if not isinstance(item, Mapping):
        return None
    stage_ref = item.get("stage") or item.get("process_stage")
    if stage_ref is None:
        return None
    return _resolve_stage_reference(stage_ref, stage_aliases)


def _resolve_stage_reference(reference: Any, stage_aliases: Mapping[str, str]) -> str:
    ref = _clean_text(reference, "stage reference")
    stage_id = stage_aliases.get(_alias(ref))
    if stage_id is None:
        raise ProcessDependencyGraphError(f"unknown stage dependency: {ref}")
    return stage_id


def _required_text(mapping: Mapping[str, Any], key: str) -> str:
    return _clean_text(mapping.get(key), key)


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _clean_text(value: Any, field_name: str) -> str:
    text = _optional_text(value)
    if text is None:
        raise ProcessDependencyGraphError(f"{field_name} is required")
    return text


def _source_ids(value: Any) -> tuple[str, ...]:
    return tuple(sorted({_clean_text(item, "source_evidence_ids") for item in _sequence(value)}))


def _sequence(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes)):
        return [value.decode("utf-8") if isinstance(value, bytes) else value]
    if isinstance(value, Sequence):
        return list(value)
    return [value]


def _stable_id(prefix: str, value: str) -> str:
    return f"{prefix}:{_alias(value)}"


def _alias(value: str) -> str:
    lowered = str(value).strip().lower()
    slug = _NODE_ID_RE.sub("-", lowered).strip("-")
    return slug or "unnamed"
