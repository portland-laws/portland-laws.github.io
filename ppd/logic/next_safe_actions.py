"""Deterministic next-safe-actions aggregation for PP&D guardrails.

This module is deliberately side-effect free. It only combines already supplied
fixture data: a process model, a user gap analysis, and a guardrail bundle. It
never fetches live sources, reads authenticated DevHub data, or performs official
actions.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple


JsonObject = Dict[str, Any]


def load_fixture_bundle(fixture_path: Path) -> Tuple[JsonObject, JsonObject, JsonObject]:
    """Load process, gap-analysis, and guardrail fixtures.

    The fixture may be either a directory containing process_model.json,
    user_gap_analysis.json, and guardrail_bundle.json, or a single bundled JSON
    object with process_model, user_gap_analysis, and guardrail_bundle keys.
    """

    if fixture_path.is_file():
        return _bundle_parts(_load_json(fixture_path), fixture_path)

    bundled = fixture_path / "sample_gap_analysis.json"
    if bundled.exists():
        return _bundle_parts(_load_json(bundled), bundled)

    return (
        _load_json(fixture_path / "process_model.json"),
        _load_json(fixture_path / "user_gap_analysis.json"),
        _load_json(fixture_path / "guardrail_bundle.json"),
    )


def build_next_safe_actions(
    process_model: JsonObject,
    user_gap_analysis: JsonObject,
    guardrail_bundle: JsonObject,
) -> JsonObject:
    """Return cited missing questions, warnings, drafts, and blocked actions."""

    evidence_index = _index_evidence(process_model, guardrail_bundle)
    blocked_ids = {
        str(action.get("action_id"))
        for action in _objects(user_gap_analysis.get("blocked_actions"))
        if action.get("action_id")
    }
    refused_types = _predicate_types(guardrail_bundle.get("refused_action_predicates"))
    exact_confirmation_types = _predicate_types(
        guardrail_bundle.get("exact_confirmation_predicates")
    )
    reversible_types = _predicate_types(
        guardrail_bundle.get("reversible_action_predicates")
    )

    return {
        "case_id": user_gap_analysis.get("case_id"),
        "process_id": process_model.get("process_id"),
        "guardrail_bundle_id": guardrail_bundle.get("guardrail_bundle_id"),
        "missing_questions": _missing_questions(
            process_model, user_gap_analysis, evidence_index
        ),
        "evidence_warnings": _evidence_warnings(user_gap_analysis, evidence_index),
        "reversible_draft_actions": _reversible_draft_actions(
            user_gap_analysis,
            reversible_types,
            blocked_ids,
            evidence_index,
        ),
        "blocked_consequential_actions": _blocked_consequential_actions(
            user_gap_analysis,
            refused_types,
            exact_confirmation_types,
            evidence_index,
        ),
    }


def _bundle_parts(bundle: JsonObject, path: Path) -> Tuple[JsonObject, JsonObject, JsonObject]:
    keys = ("process_model", "user_gap_analysis", "guardrail_bundle")
    missing = [key for key in keys if not isinstance(bundle.get(key), dict)]
    if missing:
        raise ValueError("Expected bundled fixture at %s to contain %s" % (path, missing))
    return bundle["process_model"], bundle["user_gap_analysis"], bundle["guardrail_bundle"]


def _load_json(path: Path) -> JsonObject:
    with path.open("r", encoding="utf-8") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError("Expected object fixture at %s" % path)
    return loaded


def _objects(value: Any) -> Iterable[JsonObject]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _index_evidence(process_model: JsonObject, guardrail_bundle: JsonObject) -> JsonObject:
    evidence = {}
    for item in list(_objects(process_model.get("source_evidence"))) + list(
        _objects(guardrail_bundle.get("source_evidence"))
    ):
        evidence_id = item.get("evidence_id")
        if evidence_id:
            evidence[str(evidence_id)] = item
    return evidence


def _predicate_types(predicates: Any) -> Set[str]:
    result = set()
    for predicate in _objects(predicates):
        action_type = predicate.get("action_type")
        if action_type:
            result.add(str(action_type))
    return result


def _missing_questions(
    process_model: JsonObject,
    user_gap_analysis: JsonObject,
    evidence_index: JsonObject,
) -> List[JsonObject]:
    process_facts = {
        str(item.get("fact_id")): item
        for item in _objects(process_model.get("required_user_facts"))
        if item.get("fact_id")
    }
    process_documents = {
        str(item.get("document_id")): item
        for item in _objects(process_model.get("required_documents"))
        if item.get("document_id")
    }

    questions = []
    for missing in _objects(user_gap_analysis.get("missing_facts")):
        fact_id = str(missing.get("fact_id", ""))
        process_fact = process_facts.get(fact_id, {})
        questions.append(
            {
                "kind": "missing_fact",
                "id": fact_id,
                "question": missing.get("question") or process_fact.get("question"),
                "reason": missing.get("reason") or process_fact.get("reason"),
                "citations": _citations(_evidence_ids(missing, process_fact), evidence_index),
            }
        )

    for missing in _objects(user_gap_analysis.get("missing_documents")):
        document_id = str(missing.get("document_id", ""))
        process_document = process_documents.get(document_id, {})
        questions.append(
            {
                "kind": "missing_document",
                "id": document_id,
                "question": missing.get("question") or process_document.get("question"),
                "reason": missing.get("reason") or process_document.get("reason"),
                "citations": _citations(
                    _evidence_ids(missing, process_document), evidence_index
                ),
            }
        )
    return questions


def _evidence_warnings(
    user_gap_analysis: JsonObject,
    evidence_index: JsonObject,
) -> List[JsonObject]:
    warnings = []
    for stale in _objects(user_gap_analysis.get("stale_evidence")):
        warnings.append(
            {
                "kind": "stale_evidence",
                "id": stale.get("evidence_id"),
                "message": stale.get("message"),
                "severity": stale.get("severity", "warning"),
                "citations": _citations(_evidence_ids(stale), evidence_index),
            }
        )
    for conflict in _objects(user_gap_analysis.get("conflicting_evidence")):
        warnings.append(
            {
                "kind": "conflicting_evidence",
                "id": conflict.get("conflict_id"),
                "message": conflict.get("message"),
                "severity": conflict.get("severity", "warning"),
                "citations": _citations(_evidence_ids(conflict), evidence_index),
            }
        )
    return warnings


def _reversible_draft_actions(
    user_gap_analysis: JsonObject,
    reversible_types: Set[str],
    blocked_ids: Set[str],
    evidence_index: JsonObject,
) -> List[JsonObject]:
    actions = []
    for action in _objects(user_gap_analysis.get("next_safe_actions")):
        action_id = str(action.get("action_id", ""))
        action_type = str(action.get("action_type", ""))
        if action_id in blocked_ids or action_type not in reversible_types:
            continue
        actions.append(
            {
                "action_id": action_id,
                "action_type": action_type,
                "label": action.get("label"),
                "draft_only": True,
                "requires_user_confirmation_before_official_action": True,
                "citations": _citations(_evidence_ids(action), evidence_index),
            }
        )
    return actions


def _blocked_consequential_actions(
    user_gap_analysis: JsonObject,
    refused_types: Set[str],
    exact_confirmation_types: Set[str],
    evidence_index: JsonObject,
) -> List[JsonObject]:
    blocked = []
    seen = set()
    for action in _objects(user_gap_analysis.get("blocked_actions")):
        action_id = str(action.get("action_id", ""))
        seen.add(action_id)
        blocked.append(_blocked_action(action, "gap_analysis_block", evidence_index))

    for action in _objects(user_gap_analysis.get("next_safe_actions")):
        action_id = str(action.get("action_id", ""))
        action_type = str(action.get("action_type", ""))
        if action_id in seen:
            continue
        if action_type in refused_types:
            blocked.append(_blocked_action(action, "refused_by_guardrail", evidence_index))
        elif action_type in exact_confirmation_types:
            blocked.append(
                _blocked_action(action, "requires_exact_confirmation", evidence_index)
            )
    return blocked


def _blocked_action(action: JsonObject, reason_code: str, evidence_index: JsonObject) -> JsonObject:
    return {
        "action_id": action.get("action_id"),
        "action_type": action.get("action_type"),
        "label": action.get("label"),
        "reason_code": reason_code,
        "reason": action.get("reason"),
        "requires_attended_handoff": True,
        "citations": _citations(_evidence_ids(action), evidence_index),
    }


def _evidence_ids(*items: JsonObject) -> List[str]:
    evidence_ids = []
    for item in items:
        for key in ("source_evidence_ids", "evidence_ids"):
            value = item.get(key)
            if isinstance(value, list):
                evidence_ids.extend(str(entry) for entry in value)
        single = item.get("evidence_id")
        if single:
            evidence_ids.append(str(single))
    return list(dict.fromkeys(evidence_ids))


def _citations(evidence_ids: List[str], evidence_index: JsonObject) -> List[JsonObject]:
    citations = []
    for evidence_id in evidence_ids:
        source = evidence_index.get(evidence_id, {})
        citations.append(
            {
                "evidence_id": evidence_id,
                "source_id": source.get("source_id"),
                "url": source.get("url"),
                "title": source.get("title"),
                "quote": source.get("quote"),
            }
        )
    return citations
