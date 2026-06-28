"""Fixture-first PP&D readiness report validation.

The validator is intentionally narrow and deterministic. It checks that an
offline case bundle carries enough cited evidence to support a readiness report
without permitting consequential official actions to slip through as safe next
steps.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set

CONSEQUENTIAL_ACTION_TYPES = {
    "certify",
    "submit",
    "upload",
    "pay",
    "schedule",
    "cancel",
}


def validate_readiness_bundle(bundle: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a fail-closed readiness validation report for one case bundle."""

    diagnostics: List[Dict[str, str]] = []

    sources = _index_by(bundle.get("sources", []), "source_id", diagnostics, "sources")
    evidence = _index_by(bundle.get("evidence", []), "evidence_id", diagnostics, "evidence")

    _validate_sources(sources, diagnostics)
    _validate_evidence(evidence, sources, diagnostics)
    _validate_requirements(bundle.get("requirements", []), evidence, diagnostics)
    _validate_process_order(bundle.get("process_model", {}), diagnostics)
    _validate_gap_analysis(bundle.get("user_gap_analysis", {}), evidence, diagnostics)
    _validate_evidence_packs(bundle.get("evidence_packs", []), evidence, diagnostics)
    _validate_question_plan(bundle.get("question_plan", []), evidence, diagnostics)
    _validate_handoff_packets(bundle.get("handoff_packets", []), evidence, diagnostics)

    return {
        "case_id": str(bundle.get("case_id", "")),
        "ready": not diagnostics,
        "diagnostics": diagnostics,
        "checked_sections": [
            "source_freshness",
            "citation_integrity",
            "process_dependency_ordering",
            "user_gap_analysis",
            "next_safe_actions",
            "evidence_packs",
            "question_planning",
            "handoff_packets",
        ],
    }


def _index_by(
    rows: Any,
    key: str,
    diagnostics: List[Dict[str, str]],
    section: str,
) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(rows, list):
        diagnostics.append(_diagnostic(section, "invalid_section", f"{section} must be a list"))
        return {}

    indexed: Dict[str, Mapping[str, Any]] = {}
    for position, row in enumerate(rows):
        if not isinstance(row, Mapping):
            diagnostics.append(
                _diagnostic(section, "invalid_item", f"{section}[{position}] must be an object")
            )
            continue
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            diagnostics.append(
                _diagnostic(section, "missing_identifier", f"{section}[{position}] is missing {key}")
            )
            continue
        indexed[value] = row
    return indexed


def _validate_sources(
    sources: Mapping[str, Mapping[str, Any]], diagnostics: List[Dict[str, str]]
) -> None:
    for source_id, source in sources.items():
        if source.get("freshness_status") != "fresh":
            diagnostics.append(
                _diagnostic("sources", "stale_source", f"source {source_id} is not fresh")
            )
        for field in ("canonical_url", "last_verified_at", "owning_surface"):
            if not source.get(field):
                diagnostics.append(
                    _diagnostic("sources", "incomplete_source", f"source {source_id} is missing {field}")
                )


def _validate_evidence(
    evidence: Mapping[str, Mapping[str, Any]],
    sources: Mapping[str, Mapping[str, Any]],
    diagnostics: List[Dict[str, str]],
) -> None:
    for evidence_id, item in evidence.items():
        source_id = item.get("source_id")
        if source_id not in sources:
            diagnostics.append(
                _diagnostic("evidence", "unknown_source", f"evidence {evidence_id} references unknown source {source_id}")
            )
        if not item.get("citation"):
            diagnostics.append(
                _diagnostic("evidence", "missing_citation", f"evidence {evidence_id} has no citation")
            )
        if not item.get("quote"):
            diagnostics.append(
                _diagnostic("evidence", "missing_quote", f"evidence {evidence_id} has no supporting quote")
            )


def _validate_requirements(
    requirements: Any,
    evidence: Mapping[str, Mapping[str, Any]],
    diagnostics: List[Dict[str, str]],
) -> None:
    if not isinstance(requirements, list) or not requirements:
        diagnostics.append(_diagnostic("requirements", "missing_requirements", "requirements must be a non-empty list"))
        return

    for requirement in requirements:
        requirement_id = str(requirement.get("requirement_id", "")) if isinstance(requirement, Mapping) else ""
        if not isinstance(requirement, Mapping):
            diagnostics.append(_diagnostic("requirements", "invalid_requirement", "requirement must be an object"))
            continue
        _require_existing_evidence(
            requirement.get("source_evidence_ids", []),
            evidence,
            diagnostics,
            "requirements",
            requirement_id,
        )


def _validate_process_order(process_model: Any, diagnostics: List[Dict[str, str]]) -> None:
    if not isinstance(process_model, Mapping):
        diagnostics.append(_diagnostic("process_model", "invalid_process_model", "process_model must be an object"))
        return

    stages = process_model.get("stages", [])
    if not isinstance(stages, list) or not stages:
        diagnostics.append(_diagnostic("process_model", "missing_stages", "process_model.stages must be non-empty"))
        return

    seen: Set[str] = set()
    for stage in stages:
        if not isinstance(stage, Mapping):
            diagnostics.append(_diagnostic("process_model", "invalid_stage", "stage must be an object"))
            continue
        stage_id = str(stage.get("stage_id", ""))
        dependencies = stage.get("depends_on", [])
        if not isinstance(dependencies, list):
            diagnostics.append(
                _diagnostic("process_model", "invalid_dependencies", f"stage {stage_id} dependencies must be a list")
            )
            dependencies = []
        for dependency in dependencies:
            if dependency not in seen:
                diagnostics.append(
                    _diagnostic("process_model", "dependency_order_violation", f"stage {stage_id} depends on later or missing stage {dependency}")
                )
        if stage_id:
            seen.add(stage_id)


def _validate_gap_analysis(
    gap_analysis: Any,
    evidence: Mapping[str, Mapping[str, Any]],
    diagnostics: List[Dict[str, str]],
) -> None:
    if not isinstance(gap_analysis, Mapping):
        diagnostics.append(_diagnostic("user_gap_analysis", "invalid_gap_analysis", "user_gap_analysis must be an object"))
        return

    for field in ("missing_facts", "missing_documents", "blocked_actions", "next_safe_actions"):
        if not isinstance(gap_analysis.get(field), list):
            diagnostics.append(
                _diagnostic("user_gap_analysis", "invalid_gap_field", f"user_gap_analysis.{field} must be a list")
            )

    for action in gap_analysis.get("next_safe_actions", []):
        if not isinstance(action, Mapping):
            diagnostics.append(_diagnostic("next_safe_actions", "invalid_action", "next safe action must be an object"))
            continue
        action_id = str(action.get("action_id", ""))
        action_type = action.get("action_type")
        if action_type in CONSEQUENTIAL_ACTION_TYPES:
            diagnostics.append(
                _diagnostic("next_safe_actions", "consequential_action_not_safe", f"action {action_id} is consequential and cannot be next-safe")
            )
        _require_existing_evidence(
            action.get("source_evidence_ids", []),
            evidence,
            diagnostics,
            "next_safe_actions",
            action_id,
        )


def _validate_evidence_packs(
    packs: Any,
    evidence: Mapping[str, Mapping[str, Any]],
    diagnostics: List[Dict[str, str]],
) -> None:
    if not isinstance(packs, list) or not packs:
        diagnostics.append(_diagnostic("evidence_packs", "missing_evidence_packs", "evidence_packs must be non-empty"))
        return

    for pack in packs:
        if not isinstance(pack, Mapping):
            diagnostics.append(_diagnostic("evidence_packs", "invalid_pack", "evidence pack must be an object"))
            continue
        pack_id = str(pack.get("pack_id", ""))
        _require_existing_evidence(pack.get("evidence_ids", []), evidence, diagnostics, "evidence_packs", pack_id)


def _validate_question_plan(
    questions: Any,
    evidence: Mapping[str, Mapping[str, Any]],
    diagnostics: List[Dict[str, str]],
) -> None:
    if not isinstance(questions, list) or not questions:
        diagnostics.append(_diagnostic("question_plan", "missing_questions", "question_plan must be non-empty"))
        return

    for question in questions:
        if not isinstance(question, Mapping):
            diagnostics.append(_diagnostic("question_plan", "invalid_question", "question must be an object"))
            continue
        question_id = str(question.get("question_id", ""))
        if not question.get("asks_for"):
            diagnostics.append(
                _diagnostic("question_plan", "missing_question_target", f"question {question_id} does not identify the missing fact or document")
            )
        _require_existing_evidence(
            question.get("source_evidence_ids", []),
            evidence,
            diagnostics,
            "question_plan",
            question_id,
        )


def _validate_handoff_packets(
    packets: Any,
    evidence: Mapping[str, Mapping[str, Any]],
    diagnostics: List[Dict[str, str]],
) -> None:
    if not isinstance(packets, list) or not packets:
        diagnostics.append(_diagnostic("handoff_packets", "missing_handoff_packets", "handoff_packets must be non-empty"))
        return

    for packet in packets:
        if not isinstance(packet, Mapping):
            diagnostics.append(_diagnostic("handoff_packets", "invalid_packet", "handoff packet must be an object"))
            continue
        packet_id = str(packet.get("packet_id", ""))
        action_type = packet.get("action_type")
        if action_type in CONSEQUENTIAL_ACTION_TYPES:
            if packet.get("requires_attendance") is not True:
                diagnostics.append(
                    _diagnostic("handoff_packets", "missing_attendance_gate", f"packet {packet_id} lacks an attendance gate")
                )
            if packet.get("requires_exact_confirmation") is not True:
                diagnostics.append(
                    _diagnostic("handoff_packets", "missing_exact_confirmation", f"packet {packet_id} lacks exact confirmation")
                )
        _require_existing_evidence(
            packet.get("source_evidence_ids", []),
            evidence,
            diagnostics,
            "handoff_packets",
            packet_id,
        )


def _require_existing_evidence(
    evidence_ids: Any,
    evidence: Mapping[str, Mapping[str, Any]],
    diagnostics: List[Dict[str, str]],
    section: str,
    owner_id: str,
) -> None:
    if not isinstance(evidence_ids, list) or not evidence_ids:
        diagnostics.append(
            _diagnostic(section, "missing_citation", f"{owner_id} has no source evidence citations")
        )
        return
    for evidence_id in evidence_ids:
        if evidence_id not in evidence:
            diagnostics.append(
                _diagnostic(section, "unknown_citation", f"{owner_id} references unknown evidence {evidence_id}")
            )


def _diagnostic(section: str, code: str, message: str) -> Dict[str, str]:
    return {"section": section, "code": code, "message": message}
