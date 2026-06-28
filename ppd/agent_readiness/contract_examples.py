"""Fixture-first PP&D agent readiness contract examples.

This module turns reviewed guardrail and source-registry promotion fixtures into
stable synthetic API examples for agent-facing PP&D readiness responses. It is
side-effect free and never calls an LLM, DevHub, a browser, or network service.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping


EXAMPLE_RESPONSE_TYPES = (
    "missing_fact_prompt",
    "stale_evidence_warning",
    "allowed_local_preview",
    "refused_consequential_action",
    "manual_handoff_response",
)

_PRIVATE_OR_LIVE_KEYS = {
    "access_token",
    "auth_state",
    "body",
    "card_number",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "cvv",
    "downloaded_document",
    "email",
    "field_value",
    "har",
    "html",
    "local_path",
    "page_text",
    "password",
    "payment_details",
    "phone",
    "private_value",
    "raw_body",
    "raw_crawl_output",
    "raw_html",
    "raw_text",
    "raw_value",
    "refresh_token",
    "screenshot",
    "secret",
    "session_cookie",
    "session_state",
    "ssn",
    "token",
    "trace",
    "user_input",
    "value",
}

_CONSEQUENTIAL_CLASSES = {
    "cancellation",
    "certification",
    "financial",
    "inspection_scheduling",
    "payment",
    "scheduling",
    "submission",
    "upload",
    "upload_to_official_record",
}


class AgentReadinessContractExamplesError(ValueError):
    """Raised when synthetic readiness examples violate the fixture contract."""

    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid agent readiness contract examples: " + "; ".join(self.problems))


def load_agent_readiness_contract_examples_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed fixture and build the deterministic examples packet."""

    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise AgentReadinessContractExamplesError(["fixture must be a JSON object"])
    return build_agent_readiness_contract_examples_packet(raw)


def build_agent_readiness_contract_examples_packet(fixture: Mapping[str, Any]) -> dict[str, Any]:
    """Build stable synthetic API examples from reviewed promotion fixtures."""

    source_promotion = deepcopy(_required_mapping(fixture, "reviewed_source_registry_promotion"))
    guardrail_promotion = deepcopy(_required_mapping(fixture, "reviewed_guardrail_promotion"))
    examples = deepcopy(_required_list(fixture, "synthetic_api_examples"))
    evidence = _evidence_by_id(source_promotion.get("source_evidence"))

    problems = _input_problems(source_promotion, guardrail_promotion, examples, evidence)
    if problems:
        raise AgentReadinessContractExamplesError(problems)

    normalized_examples = [_normalize_example(example, evidence) for example in examples if isinstance(example, Mapping)]
    packet = {
        "packet_type": "ppd.agent_readiness_contract_examples.v1",
        "fixture_first": True,
        "synthetic": True,
        "llm_called": False,
        "devhub_called": False,
        "live_services_called": False,
        "metadata_only": True,
        "source_registry_promotion_id": source_promotion["promotion_id"],
        "guardrail_promotion_id": guardrail_promotion["promotion_id"],
        "case_id": str(fixture.get("case_id") or ""),
        "process_id": str(guardrail_promotion.get("process_id") or ""),
        "response_order": list(EXAMPLE_RESPONSE_TYPES),
        "promotion_inputs": {
            "source_registry_status": source_promotion.get("review_status"),
            "guardrail_status": guardrail_promotion.get("review_status"),
            "no_raw_body_persisted": source_promotion.get("no_raw_body_persisted"),
            "source_evidence_ids": sorted(evidence),
            "guardrail_bundle_id": guardrail_promotion.get("guardrail_bundle_id"),
        },
        "api_examples": normalized_examples,
    }

    packet_problems = validate_agent_readiness_contract_examples_packet(packet)
    if packet_problems:
        raise AgentReadinessContractExamplesError(packet_problems)
    return packet


def validate_agent_readiness_contract_examples_packet(packet: Mapping[str, Any]) -> list[str]:
    """Validate the assembled synthetic readiness examples packet."""

    problems: list[str] = []
    if packet.get("packet_type") != "ppd.agent_readiness_contract_examples.v1":
        problems.append("packet_type must be ppd.agent_readiness_contract_examples.v1")
    for key in ("fixture_first", "synthetic", "metadata_only"):
        if packet.get(key) is not True:
            problems.append(f"{key} must be true")
    for key in ("llm_called", "devhub_called", "live_services_called"):
        if packet.get(key) is not False:
            problems.append(f"{key} must be false")
    if packet.get("response_order") != list(EXAMPLE_RESPONSE_TYPES):
        problems.append("response_order must expose the five readiness example types")

    promotion_inputs = packet.get("promotion_inputs")
    if not isinstance(promotion_inputs, Mapping):
        problems.append("promotion_inputs must be an object")
    else:
        if promotion_inputs.get("source_registry_status") != "reviewed_promotable":
            problems.append("source registry promotion must be reviewed_promotable")
        if promotion_inputs.get("guardrail_status") != "reviewed_promotable":
            problems.append("guardrail promotion must be reviewed_promotable")
        if promotion_inputs.get("no_raw_body_persisted") is not True:
            problems.append("source registry promotion must preserve no_raw_body_persisted=true")

    examples = packet.get("api_examples")
    if not isinstance(examples, list):
        problems.append("api_examples must be a list")
        examples = []
    response_types = [example.get("response_type") for example in examples if isinstance(example, Mapping)]
    if response_types != list(EXAMPLE_RESPONSE_TYPES):
        problems.append("api_examples must appear in deterministic response_order")

    for index, example in enumerate(examples):
        if not isinstance(example, Mapping):
            problems.append(f"api_examples[{index}] must be an object")
            continue
        problems.extend(_example_problems(example, f"api_examples[{index}]"))

    problems.extend(_unsafe_key_problems(packet))
    return _dedupe(problems)


def _input_problems(
    source_promotion: Mapping[str, Any],
    guardrail_promotion: Mapping[str, Any],
    examples: list[Any],
    evidence: Mapping[str, Mapping[str, Any]],
) -> list[str]:
    problems: list[str] = []
    for path, promotion in (
        ("reviewed_source_registry_promotion", source_promotion),
        ("reviewed_guardrail_promotion", guardrail_promotion),
    ):
        if not _non_empty_text(promotion.get("promotion_id")):
            problems.append(f"{path}.promotion_id is required")
        if promotion.get("review_status") != "reviewed_promotable":
            problems.append(f"{path}.review_status must be reviewed_promotable")
        if promotion.get("llm_called") is not False:
            problems.append(f"{path}.llm_called must be false")
        if promotion.get("devhub_called") is not False:
            problems.append(f"{path}.devhub_called must be false")
    if source_promotion.get("no_raw_body_persisted") is not True:
        problems.append("reviewed_source_registry_promotion.no_raw_body_persisted must be true")
    if not _non_empty_text(guardrail_promotion.get("guardrail_bundle_id")):
        problems.append("reviewed_guardrail_promotion.guardrail_bundle_id is required")
    if not _non_empty_text(guardrail_promotion.get("process_id")):
        problems.append("reviewed_guardrail_promotion.process_id is required")

    if len(examples) != len(EXAMPLE_RESPONSE_TYPES):
        problems.append("synthetic_api_examples must include exactly five examples")
    response_types = [item.get("response_type") for item in examples if isinstance(item, Mapping)]
    if response_types != list(EXAMPLE_RESPONSE_TYPES):
        problems.append("synthetic_api_examples must be ordered by EXAMPLE_RESPONSE_TYPES")

    for index, example in enumerate(examples):
        if not isinstance(example, Mapping):
            problems.append(f"synthetic_api_examples[{index}] must be an object")
            continue
        for evidence_id in _string_list(example.get("source_evidence_ids")):
            if evidence_id not in evidence:
                problems.append(f"synthetic_api_examples[{index}] cites unknown source evidence {evidence_id}")
        if example.get("response_type") == "stale_evidence_warning":
            stale_ids = set(_string_list(example.get("stale_evidence_ids")))
            if not stale_ids:
                problems.append("stale_evidence_warning must declare stale_evidence_ids")
            for evidence_id in stale_ids:
                if evidence_id not in evidence:
                    problems.append(f"stale_evidence_warning cites unknown stale evidence {evidence_id}")
                elif evidence[evidence_id].get("freshness_status") != "stale":
                    problems.append(f"stale evidence {evidence_id} must have freshness_status=stale")
    problems.extend(_unsafe_key_problems(source_promotion, "reviewed_source_registry_promotion"))
    problems.extend(_unsafe_key_problems(guardrail_promotion, "reviewed_guardrail_promotion"))
    problems.extend(_unsafe_key_problems({"synthetic_api_examples": examples}))
    return _dedupe(problems)


def _normalize_example(example: Mapping[str, Any], evidence: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    response_type = str(example.get("response_type") or "")
    source_ids = _string_list(example.get("source_evidence_ids"))
    normalized = {
        "response_id": str(example.get("response_id") or ""),
        "response_type": response_type,
        "status": str(example.get("status") or ""),
        "agent_message": str(example.get("agent_message") or ""),
        "llm_called": False,
        "devhub_called": False,
        "citations": [_citation(evidence[evidence_id]) for evidence_id in source_ids],
    }
    for key in (
        "prompt_fields",
        "stale_evidence_ids",
        "allowed_actions",
        "refused_actions",
        "manual_handoff_actions",
        "blocked_actions",
        "next_safe_actions",
    ):
        if key in example:
            normalized[key] = deepcopy(example[key])
    return normalized


def _example_problems(example: Mapping[str, Any], path: str) -> list[str]:
    problems: list[str] = []
    response_type = str(example.get("response_type") or "")
    if response_type not in EXAMPLE_RESPONSE_TYPES:
        problems.append(f"{path}.response_type is unsupported")
    for key in ("response_id", "status", "agent_message"):
        if not _non_empty_text(example.get(key)):
            problems.append(f"{path}.{key} is required")
    if example.get("llm_called") is not False:
        problems.append(f"{path}.llm_called must be false")
    if example.get("devhub_called") is not False:
        problems.append(f"{path}.devhub_called must be false")
    citations = example.get("citations")
    if not isinstance(citations, list) or not citations:
        problems.append(f"{path}.citations must be a non-empty list")
    else:
        for citation_index, citation in enumerate(citations):
            problems.extend(_citation_problems(citation, f"{path}.citations[{citation_index}]"))

    if response_type == "allowed_local_preview":
        for action in _mapping_items(example.get("allowed_actions")):
            action_path = f"{path}.allowed_actions"
            if action.get("allowed") is not True:
                problems.append(f"{action_path} entries must be allowed")
            if action.get("classification") not in {"local_preview", "read_only", "reversible_draft"}:
                problems.append(f"{action_path} entries must be local preview or reversible metadata actions")
            if action.get("devhub_called") is not False:
                problems.append(f"{action_path} entries must not call DevHub")
    if response_type == "refused_consequential_action":
        refused = _mapping_items(example.get("refused_actions"))
        if not refused:
            problems.append(f"{path}.refused_actions must be non-empty")
        for action in refused:
            if action.get("classification") not in _CONSEQUENTIAL_CLASSES:
                problems.append(f"{path}.refused_actions entries must be consequential")
            if action.get("status") != "refused":
                problems.append(f"{path}.refused_actions entries must be refused")
            if action.get("requires_exact_confirmation") is not True:
                problems.append(f"{path}.refused_actions entries must require exact confirmation")
            if action.get("requires_manual_handoff") is not True:
                problems.append(f"{path}.refused_actions entries must require manual handoff")
    if response_type == "manual_handoff_response":
        handoffs = _mapping_items(example.get("manual_handoff_actions"))
        if not handoffs:
            problems.append(f"{path}.manual_handoff_actions must be non-empty")
        for action in handoffs:
            if action.get("requires_user_attendance") is not True:
                problems.append(f"{path}.manual_handoff_actions entries must require user attendance")
            if action.get("automation_paused") is not True:
                problems.append(f"{path}.manual_handoff_actions entries must pause automation")
    if response_type == "stale_evidence_warning":
        if not _string_list(example.get("stale_evidence_ids")):
            problems.append(f"{path}.stale_evidence_ids must be non-empty")
        if str(example.get("status") or "") != "blocked_until_refresh":
            problems.append(f"{path}.status must be blocked_until_refresh")
    return problems


def _citation_problems(citation: Any, path: str) -> list[str]:
    if not isinstance(citation, Mapping):
        return [f"{path} must be an object"]
    problems: list[str] = []
    for key in ("evidence_id", "canonical_url", "source_type", "freshness_status", "review_status"):
        if not _non_empty_text(citation.get(key)):
            problems.append(f"{path}.{key} is required")
    canonical_url = str(citation.get("canonical_url") or "")
    if canonical_url and not canonical_url.startswith("https://www.portland.gov/ppd/"):
        problems.append(f"{path}.canonical_url must be an official PP&D URL")
    if citation.get("review_status") != "reviewed_promotable":
        problems.append(f"{path}.review_status must be reviewed_promotable")
    if citation.get("no_raw_body_persisted") is not True:
        problems.append(f"{path}.no_raw_body_persisted must be true")
    return problems


def _citation(record: Mapping[str, Any]) -> dict[str, str | bool]:
    return {
        "evidence_id": str(record.get("evidence_id") or ""),
        "title": str(record.get("title") or ""),
        "canonical_url": str(record.get("canonical_url") or ""),
        "source_type": str(record.get("source_type") or ""),
        "last_verified_at": str(record.get("last_verified_at") or ""),
        "freshness_status": str(record.get("freshness_status") or ""),
        "review_status": str(record.get("review_status") or ""),
        "no_raw_body_persisted": bool(record.get("no_raw_body_persisted")),
    }


def _evidence_by_id(source_evidence: Any) -> dict[str, Mapping[str, Any]]:
    if not isinstance(source_evidence, list):
        raise AgentReadinessContractExamplesError(["source_evidence must be a list"])
    indexed: dict[str, Mapping[str, Any]] = {}
    for item in source_evidence:
        if not isinstance(item, Mapping):
            continue
        evidence_id = str(item.get("evidence_id") or "")
        if evidence_id:
            indexed[evidence_id] = item
    if not indexed:
        raise AgentReadinessContractExamplesError(["source_evidence must include cited records"])
    return indexed


def _required_mapping(fixture: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    item = fixture.get(key)
    if not isinstance(item, Mapping):
        raise AgentReadinessContractExamplesError([f"fixture is missing {key}"])
    return item


def _required_list(fixture: Mapping[str, Any], key: str) -> list[Any]:
    item = fixture.get(key)
    if not isinstance(item, list):
        raise AgentReadinessContractExamplesError([f"fixture is missing {key}"])
    return item


def _mapping_items(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _unsafe_key_problems(value: Any, path: str = "packet") -> list[str]:
    problems: list[str] = []
    if isinstance(value, Mapping):
        for key, nested in value.items():
            nested_path = f"{path}.{key}"
            if str(key).lower() in _PRIVATE_OR_LIVE_KEYS:
                problems.append(f"{nested_path} is a private or live artifact field")
            problems.extend(_unsafe_key_problems(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            problems.extend(_unsafe_key_problems(nested, f"{path}[{index}]"))
    elif isinstance(value, str):
        lowered = value.lower()
        if "file://" in lowered or "/home/" in lowered or "\\users\\" in lowered:
            problems.append(f"{path} contains a private local path")
    return problems


def _dedupe(problems: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for problem in problems:
        if problem not in seen:
            seen.add(problem)
            deduped.append(problem)
    return deduped
