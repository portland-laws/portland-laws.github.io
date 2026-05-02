"""Fixture-only missing-information response planning for PP&D agents.

This module converts unresolved PP&D facts, required document placeholders,
stale evidence flags, and default stop gates into user-facing questions. It is
intentionally deterministic and does not perform live crawling, DevHub access,
file upload, submission, payment, certification, cancellation, or inspection
scheduling.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


FORBIDDEN_QUESTION_TERMS = (
    "submit",
    "submission",
    "upload",
    "pay",
    "payment",
    "certify",
    "certification",
    "cancel",
    "cancellation",
    "schedule inspection",
    "inspection scheduling",
)

QUESTION_TYPES = {
    "unresolved_fact",
    "required_document_placeholder",
    "stale_evidence",
    "default_stop_gate",
}


@dataclass(frozen=True)
class MissingInformationQuestion:
    """A deterministic user-facing question derived from fixture state."""

    question_id: str
    question_type: str
    prompt: str
    source_item_id: str
    evidence_ids: tuple[str, ...]
    stop_gate: bool = False

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.question_id.strip():
            errors.append("question_id is required")
        if self.question_type not in QUESTION_TYPES:
            errors.append(f"question {self.question_id} has unsupported type {self.question_type}")
        if not self.prompt.strip().endswith("?"):
            errors.append(f"question {self.question_id} prompt must be a user-facing question")
        if not self.source_item_id.strip():
            errors.append(f"question {self.question_id} source_item_id is required")
        if not self.evidence_ids:
            errors.append(f"question {self.question_id} requires at least one evidence id")
        lowered = self.prompt.lower()
        for term in FORBIDDEN_QUESTION_TERMS:
            if term in lowered:
                errors.append(f"question {self.question_id} contains forbidden suggestion term {term}")
        return errors


def build_missing_information_questions(plan: Mapping[str, Any]) -> list[MissingInformationQuestion]:
    """Build deterministic questions from a missing-information response fixture."""

    evidence_ids = _evidence_ids(plan)
    questions: list[MissingInformationQuestion] = []

    for fact in _sequence(plan.get("unresolvedFacts")):
        fact_id = _text(fact.get("id"))
        label = _text(fact.get("label")) or fact_id.replace("_", " ")
        questions.append(
            MissingInformationQuestion(
                question_id=f"ask_{fact_id}",
                question_type="unresolved_fact",
                prompt=f"What is the {label} for this PP&D request?",
                source_item_id=fact_id,
                evidence_ids=_item_evidence_ids(fact, evidence_ids),
            )
        )

    for document in _sequence(plan.get("requiredDocumentPlaceholders")):
        document_id = _text(document.get("id"))
        label = _text(document.get("label")) or document_id.replace("_", " ")
        questions.append(
            MissingInformationQuestion(
                question_id=f"ask_{document_id}",
                question_type="required_document_placeholder",
                prompt=f"Which prepared document should be tracked for the required {label}?",
                source_item_id=document_id,
                evidence_ids=_item_evidence_ids(document, evidence_ids),
            )
        )

    for stale in _sequence(plan.get("staleEvidenceFlags")):
        stale_id = _text(stale.get("id"))
        label = _text(stale.get("label")) or stale_id.replace("_", " ")
        captured_at = _text(stale.get("capturedAt")) or "the recorded capture date"
        questions.append(
            MissingInformationQuestion(
                question_id=f"ask_{stale_id}",
                question_type="stale_evidence",
                prompt=f"Should we treat the {label} guidance captured at {captured_at} as needing PP&D source review before relying on it?",
                source_item_id=stale_id,
                evidence_ids=_item_evidence_ids(stale, evidence_ids),
            )
        )

    for gate in _sequence(plan.get("defaultStopGates")):
        gate_id = _text(gate.get("id"))
        label = _text(gate.get("label")) or gate_id.replace("_", " ")
        questions.append(
            MissingInformationQuestion(
                question_id=f"ask_{gate_id}",
                question_type="default_stop_gate",
                prompt=f"Do you want the agent to pause and ask again before any {label} step is discussed for this case?",
                source_item_id=gate_id,
                evidence_ids=_item_evidence_ids(gate, evidence_ids),
                stop_gate=True,
            )
        )

    return questions


def validate_missing_information_response_plan(plan: Mapping[str, Any]) -> list[str]:
    """Validate the fixture and its derived user-facing questions."""

    errors: list[str] = []
    if int(plan.get("schemaVersion", 0)) != 1:
        errors.append("schemaVersion must be 1")
    if _text(plan.get("mode")) != "fixture_only":
        errors.append("mode must be fixture_only")
    if not _text(plan.get("planId")):
        errors.append("planId is required")

    source_ids = _evidence_ids(plan)
    if not source_ids:
        errors.append("at least one public evidence source is required")

    category_to_field = {
        "unresolved_fact": "unresolvedFacts",
        "required_document_placeholder": "requiredDocumentPlaceholders",
        "stale_evidence": "staleEvidenceFlags",
        "default_stop_gate": "defaultStopGates",
    }
    for category, field_name in category_to_field.items():
        if not _sequence(plan.get(field_name)):
            errors.append(f"{field_name} requires at least one fixture item for {category}")

    questions = build_missing_information_questions(plan)
    seen_question_ids: set[str] = set()
    covered_types: set[str] = set()
    for question in questions:
        if question.question_id in seen_question_ids:
            errors.append(f"duplicate question id {question.question_id}")
        seen_question_ids.add(question.question_id)
        covered_types.add(question.question_type)
        errors.extend(question.validate())
        for evidence_id in question.evidence_ids:
            if evidence_id not in source_ids:
                errors.append(f"question {question.question_id} references unknown evidence id {evidence_id}")

    missing_types = QUESTION_TYPES.difference(covered_types)
    for question_type in sorted(missing_types):
        errors.append(f"missing derived question for {question_type}")

    for action in _sequence(plan.get("prohibitedAgentSuggestions")):
        term = _text(action)
        if term and term.lower() not in FORBIDDEN_QUESTION_TERMS:
            errors.append(f"unsupported prohibited suggestion term {term}")

    return errors


def _evidence_ids(plan: Mapping[str, Any]) -> set[str]:
    evidence_ids: set[str] = set()
    for evidence in _sequence(plan.get("publicEvidence")):
        evidence_id = _text(evidence.get("id"))
        if evidence_id:
            evidence_ids.add(evidence_id)
    return evidence_ids


def _item_evidence_ids(item: Mapping[str, Any], known_evidence_ids: set[str]) -> tuple[str, ...]:
    ids = tuple(_text(value) for value in _sequence(item.get("evidenceIds")) if _text(value))
    if ids:
        return ids
    return tuple(sorted(known_evidence_ids))[:1]


def _sequence(value: Any) -> Sequence[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return value
    return ()


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
