"""Fixture-first release-consumer handoff packet compiler.

This module is deliberately deterministic and side-effect free. It accepts a
committed fixture describing release readiness inputs and compiles the consumer
handoff views that an agent reviewer needs before any promotion. It does not
invoke LLM consumers, browser automation, live DevHub sessions, crawlers, or
private case-file readers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

_REQUIRED_INPUT_SECTIONS = (
    "guardrail_consumer_integration_checklist",
    "agent_consumer_regression_rerun_plan",
    "post_promotion_smoke_test_plan",
    "release_notes_candidate",
)

_REQUIRED_ATTESTATIONS = (
    "fixture_first_inputs_only",
    "no_llm_consumers_invoked",
    "no_live_agent_execution",
    "no_private_case_files_read",
)

_OUTPUT_COLLECTIONS = (
    "readiness_notes",
    "expected_safe_action_envelopes",
    "missing_information_prompt_reminders",
    "refusal_examples",
    "reviewer_owners",
)


class HandoffPacketError(ValueError):
    """Raised when a release-consumer handoff fixture is incomplete or unsafe."""


def load_handoff_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed JSON fixture from disk."""

    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as fixture_file:
        payload = json.load(fixture_file)
    if not isinstance(payload, dict):
        raise HandoffPacketError("handoff fixture must contain a JSON object")
    return payload


def compile_handoff_packet(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Compile a deterministic consumer handoff packet from fixture inputs."""

    _validate_fixture_shape(fixture)
    citations = fixture["citations"]
    citation_ids = set(citations)
    inputs = fixture["inputs"]
    handoff = fixture["handoff"]

    _validate_input_sections(inputs, citation_ids)
    _validate_output_sections(handoff, citation_ids)

    attestations = _build_attestations(fixture)
    validation_summary = _build_validation_summary(inputs, handoff, citation_ids)

    return {
        "packet_id": fixture["packet_id"],
        "release_id": fixture["release_id"],
        "prepared_for": fixture["prepared_for"],
        "source_mode": "fixture_first",
        "citations": citations,
        "readiness_notes": handoff["readiness_notes"],
        "expected_safe_action_envelopes": handoff["expected_safe_action_envelopes"],
        "missing_information_prompt_reminders": handoff[
            "missing_information_prompt_reminders"
        ],
        "refusal_examples": handoff["refusal_examples"],
        "reviewer_owners": handoff["reviewer_owners"],
        "attestations": attestations,
        "validation_summary": validation_summary,
    }


def compile_handoff_packet_from_path(path: str | Path) -> dict[str, Any]:
    """Load and compile a release-consumer handoff fixture."""

    return compile_handoff_packet(load_handoff_fixture(path))


def _validate_fixture_shape(fixture: Mapping[str, Any]) -> None:
    for field in ("packet_id", "release_id", "prepared_for", "citations", "inputs", "handoff"):
        if field not in fixture:
            raise HandoffPacketError(f"missing fixture field: {field}")
    if not isinstance(fixture["citations"], dict) or not fixture["citations"]:
        raise HandoffPacketError("citations must be a non-empty object")
    if not isinstance(fixture["inputs"], dict):
        raise HandoffPacketError("inputs must be an object")
    if not isinstance(fixture["handoff"], dict):
        raise HandoffPacketError("handoff must be an object")


def _validate_input_sections(inputs: Mapping[str, Any], citation_ids: set[str]) -> None:
    for section_name in _REQUIRED_INPUT_SECTIONS:
        section = inputs.get(section_name)
        if not isinstance(section, list) or not section:
            raise HandoffPacketError(f"input section must be non-empty: {section_name}")
        for item in section:
            _validate_cited_item(section_name, item, citation_ids)


def _validate_output_sections(handoff: Mapping[str, Any], citation_ids: set[str]) -> None:
    for section_name in _OUTPUT_COLLECTIONS:
        section = handoff.get(section_name)
        if not isinstance(section, list) or not section:
            raise HandoffPacketError(f"handoff section must be non-empty: {section_name}")
        for item in section:
            _validate_cited_item(section_name, item, citation_ids)

    for envelope in handoff["expected_safe_action_envelopes"]:
        if "allowed_actions" not in envelope or "blocked_actions" not in envelope:
            raise HandoffPacketError("safe-action envelopes require allowed and blocked actions")
        if not envelope["blocked_actions"]:
            raise HandoffPacketError("safe-action envelopes must name blocked actions")

    for refusal in handoff["refusal_examples"]:
        if "user_request" not in refusal or "refusal_response" not in refusal:
            raise HandoffPacketError("refusal examples require request and response text")

    for owner in handoff["reviewer_owners"]:
        if "owner" not in owner or "review_scope" not in owner:
            raise HandoffPacketError("reviewer owners require owner and review_scope")


def _validate_cited_item(section_name: str, item: Any, citation_ids: set[str]) -> None:
    if not isinstance(item, dict):
        raise HandoffPacketError(f"{section_name} entries must be objects")
    item_citations = item.get("citation_ids")
    if not isinstance(item_citations, list) or not item_citations:
        raise HandoffPacketError(f"{section_name} entry missing citation_ids")
    unknown = sorted(set(item_citations) - citation_ids)
    if unknown:
        raise HandoffPacketError(
            f"{section_name} entry references unknown citations: {', '.join(unknown)}"
        )


def _build_attestations(fixture: Mapping[str, Any]) -> list[dict[str, Any]]:
    fixture_attestations = fixture.get("attestations", {})
    if not isinstance(fixture_attestations, dict):
        raise HandoffPacketError("attestations must be an object")

    compiled: list[dict[str, Any]] = []
    for attestation_id in _REQUIRED_ATTESTATIONS:
        value = fixture_attestations.get(attestation_id)
        if value is not True:
            raise HandoffPacketError(f"required attestation is not true: {attestation_id}")
        compiled.append(
            {
                "attestation_id": attestation_id,
                "status": "attested",
                "evidence": "committed fixture declares this constraint and compiler performs no live or private reads",
            }
        )
    return compiled


def _build_validation_summary(
    inputs: Mapping[str, Any], handoff: Mapping[str, Any], citation_ids: set[str]
) -> dict[str, Any]:
    source_item_count = sum(len(inputs[name]) for name in _REQUIRED_INPUT_SECTIONS)
    output_item_count = sum(len(handoff[name]) for name in _OUTPUT_COLLECTIONS)
    cited_output_ids = sorted(_iter_citation_ids(handoff[name] for name in _OUTPUT_COLLECTIONS))
    return {
        "required_input_sections_consumed": list(_REQUIRED_INPUT_SECTIONS),
        "source_item_count": source_item_count,
        "output_item_count": output_item_count,
        "citation_count": len(citation_ids),
        "cited_output_ids": cited_output_ids,
        "live_execution": False,
        "private_case_file_access": False,
        "llm_consumer_invocation": False,
    }


def _iter_citation_ids(sections: Iterable[Iterable[Mapping[str, Any]]]) -> Iterable[str]:
    for section in sections:
        for item in section:
            for citation_id in item.get("citation_ids", []):
                yield citation_id
