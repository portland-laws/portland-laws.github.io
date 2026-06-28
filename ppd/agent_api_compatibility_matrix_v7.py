"""Fixture-first PP&D agent API compatibility matrix v7.

This module intentionally reads only the two committed v7 fixture files supplied by
its caller. It does not activate guardrails, open DevHub, crawl live sites, read
private documents, upload, submit, certify, pay, schedule, or make legal or
permitting guarantees.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MATRIX_VERSION = 7
SMOKE_REPLAY_FIXTURE = "post_promotion_smoke_replay_plan_v7.json"
RELEASE_PACKET_FIXTURE = "post_recompile_release_decision_packet_v7.json"
ALLOWED_FIXTURE_NAMES = frozenset({SMOKE_REPLAY_FIXTURE, RELEASE_PACKET_FIXTURE})


def _read_fixture(path: Path, expected_fixture_type: str) -> dict[str, Any]:
    if path.name not in ALLOWED_FIXTURE_NAMES:
        raise ValueError(f"unsupported fixture for matrix v7: {path.name}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"fixture must contain a JSON object: {path.name}")
    if payload.get("schema_version") != MATRIX_VERSION:
        raise ValueError(f"fixture must be schema_version 7: {path.name}")
    if payload.get("fixture_type") != expected_fixture_type:
        raise ValueError(
            f"fixture_type mismatch for {path.name}: expected {expected_fixture_type!r}"
        )
    return payload


def _list(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key, {})
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _unique_strings(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if not isinstance(value, str):
            raise ValueError("expected a list of strings")
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def build_agent_api_compatibility_matrix_v7(fixture_dir: Path) -> dict[str, Any]:
    """Build the v7 compatibility matrix from the two allowed fixture files."""

    smoke_replay = _read_fixture(
        fixture_dir / SMOKE_REPLAY_FIXTURE,
        "post_promotion_smoke_replay_plan_v7",
    )
    release_packet = _read_fixture(
        fixture_dir / RELEASE_PACKET_FIXTURE,
        "post_recompile_release_decision_packet_v7",
    )

    supported_queries = []
    for query in _list(smoke_replay, "supported_agent_queries"):
        if not isinstance(query, dict):
            raise ValueError("supported_agent_queries entries must be objects")
        supported_queries.append(
            {
                "query_id": query["query_id"],
                "agent_query": query["agent_query"],
                "support_status": query.get("support_status", "supported"),
                "evidence_sources": _unique_strings(query.get("evidence_sources", [])),
            }
        )

    blocked_action_classes = _unique_strings(
        _list(smoke_replay, "blocked_action_classes")
        + _list(release_packet, "blocked_action_classes")
    )

    reversible_boundaries = _dict(release_packet, "reversible_draft_and_preview_boundaries")
    release_validation = _list(release_packet, "offline_validation_commands")

    return {
        "matrix_version": MATRIX_VERSION,
        "input_fixtures": [SMOKE_REPLAY_FIXTURE, RELEASE_PACKET_FIXTURE],
        "fixture_only": True,
        "live_site_access": "prohibited",
        "devhub_activation": "prohibited",
        "private_document_access": "prohibited",
        "legal_or_permitting_guarantees": "prohibited",
        "supported_agent_queries": supported_queries,
        "blocked_action_classes": blocked_action_classes,
        "citation_explanation_behavior": _dict(
            release_packet, "citation_explanation_behavior"
        ),
        "stale_evidence_holds": _list(release_packet, "stale_evidence_holds"),
        "missing_information_prompts": _list(
            smoke_replay, "missing_information_prompts"
        ),
        "reversible_draft_boundaries": reversible_boundaries.get(
            "reversible_draft", []
        ),
        "local_pdf_preview_boundaries": reversible_boundaries.get(
            "local_pdf_preview", []
        ),
        "exact_confirmation_checkpoints": _list(
            release_packet, "exact_confirmation_checkpoints"
        ),
        "manual_handoff_surfaces": _list(release_packet, "manual_handoff_surfaces"),
        "rollback_visibility": _dict(release_packet, "rollback_visibility"),
        "offline_validation_commands": release_validation,
    }


__all__ = [
    "ALLOWED_FIXTURE_NAMES",
    "MATRIX_VERSION",
    "RELEASE_PACKET_FIXTURE",
    "SMOKE_REPLAY_FIXTURE",
    "build_agent_api_compatibility_matrix_v7",
]
