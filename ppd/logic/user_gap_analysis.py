"""Deterministic user gap analysis for PP&D permit assistance.

This module is intentionally side-effect free. It compares a process model with
user-provided case facts and document metadata, then reports missing inputs and
blocked actions. It never performs DevHub automation or any official action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

CONSEQUENTIAL_ACTION_KEYWORDS = (
    "acknowledge",
    "attach",
    "cancel",
    "certification",
    "certify",
    "inspection",
    "payment",
    "purchase",
    "schedule",
    "submit",
    "upload",
    "withdraw",
)

DEFAULT_SAFE_NEXT_ACTIONS = (
    "review_public_requirements",
    "ask_user_for_missing_facts",
    "ask_user_for_missing_documents",
    "prepare_reversible_draft_plan",
)


@dataclass(frozen=True)
class MatchedDocument:
    """A user document matched to a process document requirement."""

    requirement_id: str
    document_id: str
    label: str


@dataclass(frozen=True)
class BlockedAction:
    """A consequential or unsupported action that must remain human-gated."""

    action_id: str
    reason: str
    requires_exact_confirmation: bool = True
    requires_attendance: bool = True


@dataclass(frozen=True)
class UserGapAnalysisResult:
    """Structured result compatible with the PP&D UserGapAnalysis data product."""

    case_id: str
    process_id: str
    known_facts: dict[str, Any]
    matched_documents: list[MatchedDocument] = field(default_factory=list)
    missing_facts: list[str] = field(default_factory=list)
    missing_documents: list[str] = field(default_factory=list)
    stale_evidence: list[str] = field(default_factory=list)
    conflicting_evidence: list[str] = field(default_factory=list)
    required_confirmations: list[str] = field(default_factory=list)
    blocked_actions: list[BlockedAction] = field(default_factory=list)
    next_safe_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "process_id": self.process_id,
            "known_facts": dict(self.known_facts),
            "matched_documents": [document.__dict__ for document in self.matched_documents],
            "missing_facts": list(self.missing_facts),
            "missing_documents": list(self.missing_documents),
            "stale_evidence": list(self.stale_evidence),
            "conflicting_evidence": list(self.conflicting_evidence),
            "required_confirmations": list(self.required_confirmations),
            "blocked_actions": [action.__dict__ for action in self.blocked_actions],
            "next_safe_actions": list(self.next_safe_actions),
        }


def analyze_user_gaps(
    *,
    case_id: str,
    process_model: Mapping[str, Any],
    known_facts: Mapping[str, Any] | None = None,
    user_documents: Sequence[Mapping[str, Any]] | None = None,
    requested_actions: Sequence[str] | None = None,
) -> UserGapAnalysisResult:
    """Compare a PP&D process model to user-supplied facts and documents.

    The function is deliberately conservative: consequential upload,
    certification, submission, payment, and inspection actions are always
    returned as blocked actions even when facts and documents are otherwise
    complete.
    """

    facts = dict(known_facts or {})
    documents = list(user_documents or [])
    actions = list(requested_actions or process_model.get("requested_actions", ()))

    process_id = str(process_model.get("process_id") or "unknown_process")
    missing_facts = _missing_required_facts(process_model, facts)
    matched_documents, missing_documents = _match_required_documents(process_model, documents)
    stale_evidence = _stale_evidence(facts, documents)
    conflicting_evidence = _conflicting_evidence(facts)
    blocked_actions = _blocked_actions(process_model, actions)
    required_confirmations = sorted({action.action_id for action in blocked_actions})
    next_safe_actions = _next_safe_actions(missing_facts, missing_documents)

    return UserGapAnalysisResult(
        case_id=case_id,
        process_id=process_id,
        known_facts=facts,
        matched_documents=matched_documents,
        missing_facts=missing_facts,
        missing_documents=missing_documents,
        stale_evidence=stale_evidence,
        conflicting_evidence=conflicting_evidence,
        required_confirmations=required_confirmations,
        blocked_actions=blocked_actions,
        next_safe_actions=next_safe_actions,
    )


def _missing_required_facts(process_model: Mapping[str, Any], known_facts: Mapping[str, Any]) -> list[str]:
    required_facts = process_model.get("required_user_facts", ())
    missing: list[str] = []
    for fact in required_facts:
        fact_id = _item_id(fact)
        if not fact_id:
            continue
        value = known_facts.get(fact_id)
        if value is None or value == "" or value == []:
            missing.append(fact_id)
    return sorted(missing)


def _match_required_documents(
    process_model: Mapping[str, Any], user_documents: Sequence[Mapping[str, Any]]
) -> tuple[list[MatchedDocument], list[str]]:
    documents_by_type: dict[str, Mapping[str, Any]] = {}
    documents_by_label: dict[str, Mapping[str, Any]] = {}
    for document in user_documents:
        document_type = str(document.get("document_type") or "").strip().lower()
        label = str(document.get("label") or document.get("title") or "").strip().lower()
        if document_type:
            documents_by_type[document_type] = document
        if label:
            documents_by_label[label] = document

    matched: list[MatchedDocument] = []
    missing: list[str] = []
    for requirement in process_model.get("required_documents", ()): 
        requirement_id = _item_id(requirement)
        label = str(requirement.get("label") or requirement_id) if isinstance(requirement, Mapping) else requirement_id
        accepted_types = _accepted_document_types(requirement)
        found = _find_document(accepted_types, label, documents_by_type, documents_by_label)
        if found is None:
            missing.append(requirement_id)
            continue
        matched.append(
            MatchedDocument(
                requirement_id=requirement_id,
                document_id=str(found.get("document_id") or found.get("id") or "unknown_document"),
                label=str(found.get("label") or found.get("title") or label),
            )
        )
    return matched, sorted(missing)


def _accepted_document_types(requirement: Any) -> list[str]:
    if isinstance(requirement, str):
        return [requirement.strip().lower()]
    if not isinstance(requirement, Mapping):
        return []
    raw_types = requirement.get("accepted_document_types") or requirement.get("document_types")
    if isinstance(raw_types, str):
        return [raw_types.strip().lower()]
    if raw_types:
        return [str(value).strip().lower() for value in raw_types if str(value).strip()]
    requirement_id = _item_id(requirement)
    return [requirement_id.strip().lower()] if requirement_id else []


def _find_document(
    accepted_types: Sequence[str],
    label: str,
    documents_by_type: Mapping[str, Mapping[str, Any]],
    documents_by_label: Mapping[str, Mapping[str, Any]],
) -> Mapping[str, Any] | None:
    for document_type in accepted_types:
        if document_type in documents_by_type:
            return documents_by_type[document_type]
    normalized_label = label.strip().lower()
    if normalized_label in documents_by_label:
        return documents_by_label[normalized_label]
    return None


def _stale_evidence(known_facts: Mapping[str, Any], user_documents: Sequence[Mapping[str, Any]]) -> list[str]:
    stale: list[str] = []
    for fact_id, value in known_facts.items():
        if isinstance(value, Mapping) and value.get("freshness_status") == "stale":
            stale.append(str(fact_id))
    for document in user_documents:
        if document.get("freshness_status") == "stale":
            stale.append(str(document.get("document_id") or document.get("id") or "unknown_document"))
    return sorted(stale)


def _conflicting_evidence(known_facts: Mapping[str, Any]) -> list[str]:
    conflicts: list[str] = []
    for fact_id, value in known_facts.items():
        if isinstance(value, Mapping) and value.get("conflict") is True:
            conflicts.append(str(fact_id))
    return sorted(conflicts)


def _blocked_actions(process_model: Mapping[str, Any], requested_actions: Sequence[str]) -> list[BlockedAction]:
    process_actions = [str(action) for action in process_model.get("blocked_actions", ())]
    action_ids = sorted(set(process_actions + [str(action) for action in requested_actions]))
    blocked: list[BlockedAction] = []
    for action_id in action_ids:
        if _is_consequential_action(action_id):
            blocked.append(
                BlockedAction(
                    action_id=action_id,
                    reason="Consequential PP&D action requires attended user review and exact confirmation.",
                )
            )
    return blocked


def _is_consequential_action(action_id: str) -> bool:
    normalized = action_id.replace("-", "_").lower()
    return any(keyword in normalized for keyword in CONSEQUENTIAL_ACTION_KEYWORDS)


def _next_safe_actions(missing_facts: Sequence[str], missing_documents: Sequence[str]) -> list[str]:
    safe_actions = ["review_public_requirements"]
    if missing_facts:
        safe_actions.append("ask_user_for_missing_facts")
    if missing_documents:
        safe_actions.append("ask_user_for_missing_documents")
    if not missing_facts and not missing_documents:
        safe_actions.append("prepare_reversible_draft_plan")
    return safe_actions


def _item_id(item: Any) -> str:
    if isinstance(item, str):
        return item
    if not isinstance(item, Mapping):
        return ""
    return str(item.get("fact_id") or item.get("document_id") or item.get("requirement_id") or item.get("id") or "")
