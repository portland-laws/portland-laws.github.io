"""Deterministic PP&D requirement-to-guardrail compiler.

This module intentionally compiles curated extraction fixtures, not live
website state. It preserves evidence so downstream agents can explain why a
guardrail exists before taking any DevHub action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


class GuardrailCompilerError(ValueError):
    """Raised when a requirement fixture cannot be compiled safely."""


@dataclass(frozen=True)
class SourceEvidence:
    source_id: str
    source_url: str
    anchor_id: str
    captured_at: str
    excerpt: str

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "SourceEvidence":
        missing = [
            key
            for key in ("source_id", "source_url", "anchor_id", "captured_at", "excerpt")
            if not str(raw.get(key, "")).strip()
        ]
        if missing:
            raise GuardrailCompilerError(f"evidence missing required fields: {', '.join(missing)}")
        return cls(
            source_id=str(raw["source_id"]),
            source_url=str(raw["source_url"]),
            anchor_id=str(raw["anchor_id"]),
            captured_at=str(raw["captured_at"]),
            excerpt=str(raw["excerpt"]),
        )


@dataclass(frozen=True)
class DeterministicPredicate:
    id: str
    expression: str
    subject: str
    action: str
    object: str
    conditions: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class DeonticRule:
    id: str
    modality: str
    subject: str
    action: str
    object: str
    condition_expression: str
    formula: str


@dataclass(frozen=True)
class TemporalRule:
    id: str
    relation: str
    trigger: str
    expression: str


@dataclass(frozen=True)
class RequirementGuardrail:
    requirement_id: str
    requirement_type: str
    natural_language: str
    predicate: DeterministicPredicate
    deontic_rule: DeonticRule | None
    temporal_rule: TemporalRule | None
    evidence: tuple[SourceEvidence, ...]
    confidence: float
    formalization_status: str


@dataclass(frozen=True)
class CompiledGuardrailSet:
    fixture_id: str
    guardrails: tuple[RequirementGuardrail, ...]
    support_map: dict[str, tuple[SourceEvidence, ...]]

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.fixture_id.strip():
            errors.append("fixture_id is required")
        if not self.guardrails:
            errors.append("at least one guardrail is required")

        seen: set[str] = set()
        for guardrail in self.guardrails:
            if guardrail.requirement_id in seen:
                errors.append(f"duplicate guardrail id: {guardrail.requirement_id}")
            seen.add(guardrail.requirement_id)
            if not guardrail.evidence:
                errors.append(f"{guardrail.requirement_id} has no evidence")
            if guardrail.requirement_id not in self.support_map:
                errors.append(f"{guardrail.requirement_id} missing support map entry")
            if guardrail.confidence < 0 or guardrail.confidence > 1:
                errors.append(f"{guardrail.requirement_id} confidence must be between 0 and 1")
            if guardrail.requirement_type in {"obligation", "action_gate"} and guardrail.deontic_rule is None:
                errors.append(f"{guardrail.requirement_id} requires a deontic rule")
            if guardrail.requirement_type in {"deadline", "precondition"} and guardrail.temporal_rule is None:
                errors.append(f"{guardrail.requirement_id} requires a temporal rule")

        return errors


DEONTIC_MODALITIES = {
    "action_gate": "prohibited_without_confirmation",
    "deadline": "required_before",
    "exception": "excepted",
    "obligation": "obligated",
    "precondition": "required_precondition",
}


def compile_requirement_fixture(fixture: Mapping[str, Any]) -> CompiledGuardrailSet:
    fixture_id = str(fixture.get("fixture_id", "")).strip()
    if not fixture_id:
        raise GuardrailCompilerError("fixture_id is required")

    requirements = fixture.get("expected_requirements")
    if not isinstance(requirements, list) or not requirements:
        raise GuardrailCompilerError("expected_requirements must be a non-empty list")

    guardrails = tuple(_compile_requirement(requirement) for requirement in requirements)
    compiled = CompiledGuardrailSet(
        fixture_id=fixture_id,
        guardrails=guardrails,
        support_map={guardrail.requirement_id: guardrail.evidence for guardrail in guardrails},
    )
    errors = compiled.validate()
    if errors:
        raise GuardrailCompilerError("; ".join(errors))
    return compiled


def _compile_requirement(raw: Mapping[str, Any]) -> RequirementGuardrail:
    requirement_id = _required_text(raw, "requirement_id")
    requirement_type = _required_text(raw, "type")
    subject = _required_text(raw, "subject")
    action = _required_text(raw, "action")
    obj = _required_text(raw, "object")
    natural_language = _required_text(raw, "natural_language")
    temporal_scope = _required_text(raw, "deadline_or_temporal_scope")
    conditions = tuple(str(condition) for condition in raw.get("conditions", ()))
    evidence = tuple(SourceEvidence.from_mapping(item) for item in raw.get("evidence", ()))
    if not evidence:
        raise GuardrailCompilerError(f"{requirement_id} must include evidence")

    formula = str(raw.get("expected_formula_hint", "")).strip() or _fallback_formula(
        requirement_type,
        subject,
        action,
        obj,
        conditions,
    )
    predicate = DeterministicPredicate(
        id=f"pred-{requirement_id}",
        expression=formula,
        subject=subject,
        action=action,
        object=obj,
        conditions=conditions,
    )
    deontic_rule = _compile_deontic_rule(requirement_id, requirement_type, subject, action, obj, conditions, formula)
    temporal_rule = _compile_temporal_rule(requirement_id, temporal_scope)

    return RequirementGuardrail(
        requirement_id=requirement_id,
        requirement_type=requirement_type,
        natural_language=natural_language,
        predicate=predicate,
        deontic_rule=deontic_rule,
        temporal_rule=temporal_rule,
        evidence=evidence,
        confidence=float(raw.get("confidence", 0)),
        formalization_status=str(raw.get("formalization_status", "draft")),
    )


def _compile_deontic_rule(
    requirement_id: str,
    requirement_type: str,
    subject: str,
    action: str,
    obj: str,
    conditions: tuple[str, ...],
    formula: str,
) -> DeonticRule | None:
    modality = DEONTIC_MODALITIES.get(requirement_type)
    if modality is None:
        return None
    condition_expression = " AND ".join(conditions) if conditions else "true"
    return DeonticRule(
        id=f"deontic-{requirement_id}",
        modality=modality,
        subject=subject,
        action=action,
        object=obj,
        condition_expression=condition_expression,
        formula=formula,
    )


def _compile_temporal_rule(requirement_id: str, temporal_scope: str) -> TemporalRule | None:
    relation, trigger = _parse_temporal_scope(temporal_scope)
    if relation == "during":
        return None
    return TemporalRule(
        id=f"temporal-{requirement_id}",
        relation=relation,
        trigger=trigger,
        expression=temporal_scope,
    )


def _parse_temporal_scope(value: str) -> tuple[str, str]:
    text = value.strip()
    for relation in ("before", "after", "during"):
        prefix = f"{relation}("
        if text.startswith(prefix) and text.endswith(")"):
            return relation, text[len(prefix) : -1]
    return "scope", text


def _fallback_formula(
    requirement_type: str,
    subject: str,
    action: str,
    obj: str,
    conditions: tuple[str, ...],
) -> str:
    condition_text = ", ".join(conditions) if conditions else "true"
    return f"{requirement_type.upper()}({subject}, {action}({obj}), if({condition_text}))"


def _required_text(raw: Mapping[str, Any], key: str) -> str:
    value = str(raw.get(key, "")).strip()
    if not value:
        raise GuardrailCompilerError(f"requirement missing required field: {key}")
    return value
