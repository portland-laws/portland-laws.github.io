from __future__ import annotations

import json
from pathlib import Path

import pytest

from ppd.logic.process_dependency_normalizer import (
    ProcessDependencyGraphError,
    normalize_process_dependency_graph,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "process_dependency_normalizer"


def _load_fixture(name: str) -> dict:
    with (FIXTURE_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_normalizes_fixture_process_graph_deterministically() -> None:
    process_model = _load_fixture("minimal_process_model.json")

    first = normalize_process_dependency_graph(process_model)
    second = normalize_process_dependency_graph(process_model)

    assert first == second
    assert first["process_id"] == "fixture-minimal-devhub-request"
    assert first["permit_type"] == "fixture permit type"
    assert first["validation"] == {
        "status": "valid",
        "node_count": 7,
        "edge_count": 8,
        "missing_references": [],
    }

    node_ids = {node["id"] for node in first["nodes"]}
    assert node_ids == {
        "document:energy-form",
        "document:site-plan-pdf",
        "fact:owner-contact",
        "fact:project-address",
        "stage:documents",
        "stage:draft-entry",
        "stage:research",
    }

    edge_keys = {(edge["source"], edge["target"], edge["type"]) for edge in first["edges"]}
    assert edge_keys == {
        ("document:energy-form", "stage:documents", "required_document"),
        ("document:site-plan-pdf", "stage:documents", "required_document"),
        ("fact:owner-contact", "stage:draft-entry", "required_fact"),
        ("fact:project-address", "stage:documents", "required_fact"),
        ("stage:documents", "stage:draft-entry", "explicit_dependency"),
        ("stage:documents", "stage:draft-entry", "stage_order"),
        ("stage:research", "stage:documents", "explicit_dependency"),
        ("stage:research", "stage:documents", "stage_order"),
    }


def test_does_not_attach_top_level_requirements_without_explicit_stage() -> None:
    graph = normalize_process_dependency_graph(
        {
            "process_id": "no-inferred-stage",
            "stages": ["first stage"],
            "required_user_facts": ["unattached fact"],
            "required_documents": ["unattached document"],
        }
    )

    assert {node["id"] for node in graph["nodes"]} == {
        "document:unattached-document",
        "fact:unattached-fact",
        "stage:first-stage",
    }
    assert graph["edges"] == []
    assert graph["validation"]["status"] == "valid"


def test_rejects_unknown_stage_dependency() -> None:
    with pytest.raises(ProcessDependencyGraphError, match="unknown stage dependency"):
        normalize_process_dependency_graph(
            {
                "process_id": "bad-dependency",
                "stages": [
                    {"stage_id": "known", "name": "known stage"},
                    {"stage_id": "later", "name": "later stage", "depends_on": ["missing"]},
                ],
            }
        )


def test_rejects_self_dependency() -> None:
    with pytest.raises(ProcessDependencyGraphError, match="self dependency"):
        normalize_process_dependency_graph(
            {
                "process_id": "self-dependency",
                "stages": [
                    {"stage_id": "same", "name": "same stage", "depends_on": ["same"]},
                ],
            }
        )
