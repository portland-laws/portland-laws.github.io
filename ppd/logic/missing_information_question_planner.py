"""Deterministic missing-information question planning for PP&D workflows.

This module is intentionally offline and side-effect free. It consumes already
compiled process and gap-analysis data, then produces the smallest safe set of
questions needed before reversible local drafting can continue.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


FORBIDDEN_WORKFLOW_KEYWORDS = (
    "live crawl",
    "crawl",
    "devhub",
    "document upload",
    "upload",
    "payment",
    "pay fee",
    "submit",
    "submission",
    "certify",
    "certification",
    "schedule",
    "scheduling",
    "cancel",
    "cancellation",
    "account creation",
    "create account",
    "captcha",
    "mfa",
    "multi-factor",
)

QUESTION_PRIORITY = {
    "missing_fact": 10,
    "missing_document": 20,
    "stale_evidence": 30,
    "conflicting_evidence": 40,
}


@dataclass(frozen=True)
class PlannedQuestion:
    """A single safe question for the user."""

    question_id: str
    category: str
    prompt: str
    answer_type: str = "text"
    required: bool = True
    reason: str = "Required before preparing a reversible local draft."
    source_requirement_ids: tuple[str, ...] = field(default_factory=tuple)
    blocks_reversible_drafting: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "category": self.category,
            "prompt": self.prompt,
            "answer_type": self.answer_type,
            "required": self.required,
            "reason": self.reason,
            "source_requirement_ids": list(self.source_requirement_ids),
            "blocks_reversible_drafting": self.blocks_reversible_drafting,
        }


@dataclass(frozen=True)
class QuestionPlan:
    """A minimal, side-effect-free missing-information plan."""

    case_id: str
    process_id: str
    questions: tuple[PlannedQuestion, ...]
    blocked_actions: tuple[str, ...]
    next_safe_actions: tuple[str, ...]
    refused_capabilities: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "process_id": self.process_id,
            "questions": [question.to_dict() for question in self.questions],
            "blocked_actions": list(self.blocked_actions),
            "next_safe_actions": list(self.next_safe_actions),
            "refused_capabilities": list(self.refused_capabilities),
        }


def plan_missing_information_questions(
    process_model: Mapping[str, Any],
    user_gap_analysis: Mapping[str, Any],
) -> QuestionPlan:
    """Build a deterministic minimal question plan from known PP&D gaps.

    The planner never crawls, opens DevHub, uploads documents, enters payment
    details, submits, certifies, schedules, cancels, creates accounts, or handles
    CAPTCHA/MFA. Inputs must be previously collected public-source models and
    user-provided case facts.
    """

    case_id = str(user_gap_analysis.get("case_id") or "unknown-case")
    process_id = str(
        user_gap_analysis.get("process_id")
        or process_model.get("process_id")
        or "unknown-process"
    )

    raw_blocked_actions = _as_list(user_gap_analysis.get("blocked_actions"))
    blocked_actions = tuple(_dedupe_preserve_order(_stringify_items(raw_blocked_actions)))
    refused_capabilities = tuple(_detect_refused_capabilities(blocked_actions))

    questions: list[PlannedQuestion] = []
    questions.extend(_questions_for_missing_facts(process_model, user_gap_analysis))
    questions.extend(_questions_for_missing_documents(user_gap_analysis))
    questions.extend(_questions_for_stale_evidence(user_gap_analysis))
    questions.extend(_questions_for_conflicting_evidence(user_gap_analysis))

    minimal_questions = tuple(_dedupe_questions(questions))
    next_safe_actions = _next_safe_actions(minimal_questions)

    return QuestionPlan(
        case_id=case_id,
        process_id=process_id,
        questions=minimal_questions,
        blocked_actions=blocked_actions,
        next_safe_actions=next_safe_actions,
        refused_capabilities=refused_capabilities,
    )


def _questions_for_missing_facts(
    process_model: Mapping[str, Any],
    user_gap_analysis: Mapping[str, Any],
) -> list[PlannedQuestion]:
    required_fact_specs = _index_by_key(
        _as_list(process_model.get("required_user_facts")),
        key_names=("fact_id", "key", "name"),
    )
    questions: list[PlannedQuestion] = []

    for item in _as_list(user_gap_analysis.get("missing_facts")):
        key = _item_key(item)
        spec = required_fact_specs.get(key, {}) if key else {}
        label = _label(item, spec)
        prompt = _prompt_from_item(item, spec) or f"What is the {label}?"
        questions.append(
            PlannedQuestion(
                question_id=_question_id("missing_fact", key or label),
                category="missing_fact",
                prompt=prompt,
                answer_type=str(_first_present(item, spec, names=("answer_type", "type")) or "text"),
                reason=str(
                    _first_present(item, spec, names=("reason", "description"))
                    or "This fact is required by the selected PP&D process model."
                ),
                source_requirement_ids=tuple(_source_requirement_ids(item, spec)),
            )
        )

    return questions


def _questions_for_missing_documents(user_gap_analysis: Mapping[str, Any]) -> list[PlannedQuestion]:
    questions: list[PlannedQuestion] = []
    for item in _as_list(user_gap_analysis.get("missing_documents")):
        key = _item_key(item) or _label(item, {})
        label = _label(item, {})
        prompt = _prompt_from_item(item, {}) or (
            f"Do you have the required document '{label}', and what is its current status?"
        )
        questions.append(
            PlannedQuestion(
                question_id=_question_id("missing_document", key),
                category="missing_document",
                prompt=prompt,
                answer_type="document_status",
                reason=str(
                    _mapping(item).get("reason")
                    or "The selected PP&D process model requires this document before drafting can be treated as complete."
                ),
                source_requirement_ids=tuple(_source_requirement_ids(item, {})),
            )
        )
    return questions


def _questions_for_stale_evidence(user_gap_analysis: Mapping[str, Any]) -> list[PlannedQuestion]:
    questions: list[PlannedQuestion] = []
    for item in _as_list(user_gap_analysis.get("stale_evidence")):
        key = _item_key(item) or _label(item, {})
        label = _label(item, {})
        prompt = _prompt_from_item(item, {}) or f"Is the current value for {label} still accurate?"
        questions.append(
            PlannedQuestion(
                question_id=_question_id("stale_evidence", key),
                category="stale_evidence",
                prompt=prompt,
                answer_type="confirmation_or_update",
                reason=str(_mapping(item).get("reason") or "Existing evidence is stale and must be confirmed before reuse."),
                source_requirement_ids=tuple(_source_requirement_ids(item, {})),
            )
        )
    return questions


def _questions_for_conflicting_evidence(user_gap_analysis: Mapping[str, Any]) -> list[PlannedQuestion]:
    questions: list[PlannedQuestion] = []
    for item in _as_list(user_gap_analysis.get("conflicting_evidence")):
        key = _item_key(item) or _label(item, {})
        label = _label(item, {})
        prompt = _prompt_from_item(item, {}) or f"Which value should be used for {label}?"
        questions.append(
            PlannedQuestion(
                question_id=_question_id("conflicting_evidence", key),
                category="conflicting_evidence",
                prompt=prompt,
                answer_type="choose_or_explain",
                reason=str(_mapping(item).get("reason") or "Conflicting evidence must be resolved before drafting."),
                source_requirement_ids=tuple(_source_requirement_ids(item, {})),
            )
        )
    return questions


def _next_safe_actions(questions: Sequence[PlannedQuestion]) -> tuple[str, ...]:
    if questions:
        return ("ask_planned_missing_information_questions", "update_local_gap_analysis_from_user_answers")
    return ("prepare_reversible_local_draft_plan",)


def _detect_refused_capabilities(actions: Sequence[str]) -> list[str]:
    refused: list[str] = []
    for action in actions:
        lowered = action.lower()
        for keyword in FORBIDDEN_WORKFLOW_KEYWORDS:
            if keyword in lowered:
                refused.append(keyword)
    return _dedupe_preserve_order(refused)


def _dedupe_questions(questions: Sequence[PlannedQuestion]) -> list[PlannedQuestion]:
    by_key: dict[tuple[str, str], PlannedQuestion] = {}
    for question in sorted(
        questions,
        key=lambda item: (QUESTION_PRIORITY.get(item.category, 100), item.question_id),
    ):
        key = (question.category, question.question_id)
        if key not in by_key:
            by_key[key] = question
    return list(by_key.values())


def _index_by_key(items: Sequence[Any], key_names: Sequence[str]) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for item in items:
        mapping = _mapping(item)
        for name in key_names:
            value = mapping.get(name)
            if value:
                indexed[str(value)] = mapping
                break
    return indexed


def _item_key(item: Any) -> str:
    mapping = _mapping(item)
    for name in ("fact_id", "document_id", "evidence_id", "key", "name", "id"):
        value = mapping.get(name)
        if value:
            return str(value)
    if isinstance(item, str):
        return item
    return ""


def _label(item: Any, spec: Mapping[str, Any]) -> str:
    for source in (_mapping(item), spec):
        for name in ("label", "title", "name", "fact_id", "document_id", "key", "id"):
            value = source.get(name)
            if value:
                return str(value).replace("_", " ")
    if isinstance(item, str):
        return item.replace("_", " ")
    return "requested information"


def _prompt_from_item(item: Any, spec: Mapping[str, Any]) -> str:
    for source in (_mapping(item), spec):
        value = source.get("question") or source.get("prompt")
        if value:
            return str(value)
    return ""


def _source_requirement_ids(item: Any, spec: Mapping[str, Any]) -> list[str]:
    values: list[Any] = []
    for source in (_mapping(item), spec):
        values.extend(_as_list(source.get("source_requirement_ids")))
        values.extend(_as_list(source.get("requirement_ids")))
        requirement_id = source.get("requirement_id")
        if requirement_id:
            values.append(requirement_id)
    return _dedupe_preserve_order(_stringify_items(values))


def _first_present(item: Any, spec: Mapping[str, Any], names: Sequence[str]) -> Any:
    for source in (_mapping(item), spec):
        for name in names:
            if source.get(name) is not None:
                return source[name]
    return None


def _mapping(item: Any) -> Mapping[str, Any]:
    if isinstance(item, Mapping):
        return item
    return {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _stringify_items(items: Sequence[Any]) -> list[str]:
    return [str(item) for item in items if item is not None and str(item)]


def _dedupe_preserve_order(items: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _question_id(category: str, key: str) -> str:
    normalized = "_".join(str(key).strip().lower().replace("-", "_").split())
    normalized = "".join(char for char in normalized if char.isalnum() or char == "_")
    return f"{category}:{normalized or 'item'}"
