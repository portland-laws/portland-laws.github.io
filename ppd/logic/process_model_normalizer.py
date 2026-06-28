"""Deterministic PP&D process model normalization.

This module intentionally compiles only committed fixture/source evidence data into
small process model dictionaries. It does not crawl, infer from live pages, or
mint evidence ids.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


STANDARD_PROCESS_STAGES = (
    "pre-application research",
    "account setup or manual login",
    "property lookup",
    "permit type selection",
    "eligibility screening",
    "document preparation",
    "application data entry",
    "upload staging",
    "acknowledgement/certification review",
    "submission",
    "prescreen/intake",
    "fee payment",
    "plan review",
    "corrections/checksheets",
    "approval/issuance",
    "inspections",
    "closeout, cancellation, expiration, extension, or reactivation",
)

_STAGE_ORDER = {stage: index for index, stage in enumerate(STANDARD_PROCESS_STAGES)}


class ProcessModelNormalizationError(ValueError):
    """Raised when fixture data cannot be compiled into a safe model."""


def load_requirement_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed JSON requirement fixture."""

    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ProcessModelNormalizationError("requirement fixture must be a JSON object")
    return payload


def compile_process_model_from_fixture(path: str | Path) -> dict[str, Any]:
    """Compile a fixture into a normalized process model and guardrail bundle."""

    return normalize_process_model(load_requirement_fixture(path))


def normalize_process_model(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize source-backed requirement nodes into a process model bundle.

    The compiler accepts a compact fixture shape with top-level metadata and a
    ``requirements`` list. Every requirement must carry committed
    ``source_evidence_ids``; those ids are propagated into the model and
    guardrail bundle without alteration.
    """

    requirements = payload.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        raise ProcessModelNormalizationError("payload must include a non-empty requirements list")

    source_evidence = payload.get("source_evidence", [])
    committed_evidence_ids = _collect_committed_evidence_ids(source_evidence)
    normalized_requirements = [_normalize_requirement(node, committed_evidence_ids) for node in requirements]

    process_id = _required_text(payload, "process_id")
    permit_type = _required_text(payload, "permit_type")
    scope = _required_text(payload, "scope")
    bundle_id = _text(payload.get("guardrail_bundle_id")) or f"guardrails:{process_id}"

    all_evidence_ids = _sorted_unique(
        evidence_id
        for node in normalized_requirements
        for evidence_id in node["source_evidence_ids"]
    )

    stages = _normalize_stages(normalized_requirements)
    model = {
        "process_id": process_id,
        "permit_type": permit_type,
        "scope": scope,
        "eligibility_rules": _requirement_summaries(normalized_requirements, {"precondition", "license_requirement"}),
        "required_user_facts": _required_user_facts(normalized_requirements),
        "required_documents": _document_requirements(normalized_requirements),
        "file_rules": _condition_items(normalized_requirements, "file_rule"),
        "fees": _requirement_summaries(normalized_requirements, {"fee_trigger"}),
        "stages": stages,
        "deadlines": _requirement_summaries(normalized_requirements, {"deadline"}),
        "exceptions": _requirement_summaries(normalized_requirements, {"exception"}),
        "unsupported_paths": _unsupported_paths(normalized_requirements),
        "devhub_surface_refs": _devhub_surface_refs(normalized_requirements),
        "guardrail_bundle_id": bundle_id,
        "source_evidence_ids": all_evidence_ids,
    }

    guardrail_bundle = {
        "guardrail_bundle_id": bundle_id,
        "process_id": process_id,
        "source_evidence_ids": all_evidence_ids,
        "deterministic_predicates": _deterministic_predicates(normalized_requirements),
        "deontic_rules": _requirement_summaries(
            normalized_requirements,
            {"obligation", "prohibition", "permission", "precondition", "document_requirement"},
        ),
        "temporal_rules": _requirement_summaries(normalized_requirements, {"deadline"}),
        "reversible_action_predicates": _action_predicates(normalized_requirements, "reversible"),
        "exact_confirmation_predicates": _action_predicates(normalized_requirements, "exact_confirmation"),
        "refused_action_predicates": _action_predicates(normalized_requirements, "refused"),
        "explanation_templates": {
            "missing_fact": "Ask for the missing fact before drafting or advancing the permit workflow.",
            "missing_document": "Ask for the cited document before preparing upload or submission steps.",
            "blocked_action": "Stop before consequential action and require attended exact confirmation.",
        },
        "validation_status": "fixture_normalized",
    }

    return {
        "process_model": model,
        "guardrail_bundle": guardrail_bundle,
        "requirements": normalized_requirements,
    }


def _collect_committed_evidence_ids(source_evidence: Any) -> set[str]:
    if not isinstance(source_evidence, list) or not source_evidence:
        raise ProcessModelNormalizationError("payload must include committed source_evidence entries")
    evidence_ids: set[str] = set()
    for entry in source_evidence:
        if not isinstance(entry, dict):
            raise ProcessModelNormalizationError("source_evidence entries must be objects")
        evidence_id = _required_text(entry, "evidence_id")
        evidence_ids.add(evidence_id)
    return evidence_ids


def _normalize_requirement(node: Any, committed_evidence_ids: set[str]) -> dict[str, Any]:
    if not isinstance(node, dict):
        raise ProcessModelNormalizationError("requirement entries must be objects")

    requirement_id = _required_text(node, "requirement_id")
    requirement_type = _required_text(node, "requirement_type")
    source_evidence_ids = node.get("source_evidence_ids")
    if not isinstance(source_evidence_ids, list) or not source_evidence_ids:
        raise ProcessModelNormalizationError(f"{requirement_id} must include source_evidence_ids")

    normalized_evidence_ids = []
    for evidence_id in source_evidence_ids:
        evidence_text = _text(evidence_id)
        if not evidence_text:
            raise ProcessModelNormalizationError(f"{requirement_id} has an empty evidence id")
        if evidence_text not in committed_evidence_ids:
            raise ProcessModelNormalizationError(
                f"{requirement_id} references uncommitted evidence id {evidence_text}"
            )
        normalized_evidence_ids.append(evidence_text)

    conditions = node.get("conditions", {})
    if conditions is None:
        conditions = {}
    if not isinstance(conditions, dict):
        raise ProcessModelNormalizationError(f"{requirement_id} conditions must be an object")

    return {
        "requirement_id": requirement_id,
        "source_evidence_ids": _sorted_unique(normalized_evidence_ids),
        "requirement_type": requirement_type,
        "subject": _text(node.get("subject")),
        "action": _text(node.get("action")),
        "object": _text(node.get("object")),
        "conditions": _stable_jsonable(conditions),
        "deadline_or_temporal_scope": _text(node.get("deadline_or_temporal_scope")),
        "permit_types": _text_list(node.get("permit_types")),
        "process_stage": _text(node.get("process_stage")),
        "confidence": node.get("confidence", "fixture"),
        "human_review_status": _text(node.get("human_review_status")) or "fixture_reviewed",
        "formalization_status": _text(node.get("formalization_status")) or "normalized",
    }


def _normalize_stages(requirements: list[dict[str, Any]]) -> list[str]:
    observed = [_text(node.get("process_stage")) for node in requirements]
    unique = {stage for stage in observed if stage}
    return sorted(unique, key=lambda stage: (_STAGE_ORDER.get(stage, len(_STAGE_ORDER)), stage))


def _requirement_summaries(requirements: list[dict[str, Any]], types: set[str]) -> list[dict[str, Any]]:
    summaries = []
    for node in requirements:
        if node["requirement_type"] in types:
            summaries.append(_summary(node))
    return sorted(summaries, key=lambda item: item["requirement_id"])


def _summary(node: dict[str, Any]) -> dict[str, Any]:
    return {
        "requirement_id": node["requirement_id"],
        "requirement_type": node["requirement_type"],
        "subject": node["subject"],
        "action": node["action"],
        "object": node["object"],
        "process_stage": node["process_stage"],
        "source_evidence_ids": node["source_evidence_ids"],
    }


def _required_user_facts(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    facts = []
    for node in requirements:
        conditions = node["conditions"]
        for key in ("required_user_fact", "user_fact", "fact_key"):
            fact_key = _text(conditions.get(key))
            if fact_key:
                facts.append(
                    {
                        "fact_key": fact_key,
                        "label": _text(conditions.get("fact_label")) or node["object"] or fact_key,
                        "requirement_id": node["requirement_id"],
                        "process_stage": node["process_stage"],
                        "source_evidence_ids": node["source_evidence_ids"],
                    }
                )
    return sorted(facts, key=lambda item: (item["fact_key"], item["requirement_id"]))


def _document_requirements(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    documents = []
    for node in requirements:
        if node["requirement_type"] != "document_requirement":
            continue
        conditions = node["conditions"]
        document_key = _text(conditions.get("document_key")) or _slug(node["object"])
        documents.append(
            {
                "document_key": document_key,
                "label": _text(conditions.get("document_label")) or node["object"],
                "requirement_id": node["requirement_id"],
                "process_stage": node["process_stage"],
                "source_evidence_ids": node["source_evidence_ids"],
            }
        )
    return sorted(documents, key=lambda item: (item["document_key"], item["requirement_id"]))


def _condition_items(requirements: list[dict[str, Any]], condition_key: str) -> list[dict[str, Any]]:
    items = []
    for node in requirements:
        value = node["conditions"].get(condition_key)
        if value:
            items.append(
                {
                    condition_key: value,
                    "requirement_id": node["requirement_id"],
                    "source_evidence_ids": node["source_evidence_ids"],
                }
            )
    return sorted(items, key=lambda item: item["requirement_id"])


def _unsupported_paths(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    paths = []
    for node in requirements:
        value = _text(node["conditions"].get("unsupported_path"))
        if value or node["requirement_type"] == "prohibition":
            paths.append(
                {
                    "path": value or node["object"],
                    "requirement_id": node["requirement_id"],
                    "source_evidence_ids": node["source_evidence_ids"],
                }
            )
    return sorted(paths, key=lambda item: (item["path"], item["requirement_id"]))


def _devhub_surface_refs(requirements: list[dict[str, Any]]) -> list[str]:
    refs = []
    for node in requirements:
        value = node["conditions"].get("devhub_surface_ref")
        if isinstance(value, list):
            refs.extend(_text_list(value))
        elif _text(value):
            refs.append(_text(value))
    return _sorted_unique(refs)


def _deterministic_predicates(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    predicates = []
    for node in requirements:
        predicate = _text(node["conditions"].get("predicate"))
        if predicate:
            predicates.append(
                {
                    "predicate": predicate,
                    "requirement_id": node["requirement_id"],
                    "source_evidence_ids": node["source_evidence_ids"],
                }
            )
    return sorted(predicates, key=lambda item: (item["predicate"], item["requirement_id"]))


def _action_predicates(requirements: list[dict[str, Any]], gate: str) -> list[dict[str, Any]]:
    predicates = []
    for node in requirements:
        if node["requirement_type"] != "action_gate":
            continue
        if _text(node["conditions"].get("gate")) != gate:
            continue
        predicates.append(
            {
                "action": node["action"],
                "object": node["object"],
                "process_stage": node["process_stage"],
                "requirement_id": node["requirement_id"],
                "source_evidence_ids": node["source_evidence_ids"],
            }
        )
    return sorted(predicates, key=lambda item: (item["action"], item["object"], item["requirement_id"]))


def _stable_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _stable_jsonable(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_stable_jsonable(item) for item in value]
    return value


def _required_text(payload: dict[str, Any], key: str) -> str:
    value = _text(payload.get(key))
    if not value:
        raise ProcessModelNormalizationError(f"missing required field: {key}")
    return value


def _text(value: Any) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return " ".join(value.strip().split())


def _text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = [value]
    return [_text(item) for item in value if _text(item)]


def _sorted_unique(values: Iterable[str]) -> list[str]:
    return sorted({value for value in values if value})


def _slug(value: str) -> str:
    normalized = []
    previous_dash = False
    for char in value.lower():
        if char.isalnum():
            normalized.append(char)
            previous_dash = False
        elif not previous_dash:
            normalized.append("-")
            previous_dash = True
    return "".join(normalized).strip("-") or "document"
