"""Deterministic guardrail explanation packet rendering for PP&D fixtures.

The renderer is intentionally small and fixture-oriented. It accepts already-loaded
fixture dictionaries for guardrails, next safe actions, evidence packs, and
question plans. It validates that every cited evidence id exists before producing
an agent-facing explanation packet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


class GuardrailExplanationError(ValueError):
    """Base error for explanation packet rendering failures."""


class MissingCitationError(GuardrailExplanationError):
    """Raised when a rendered packet would rely on unavailable evidence."""


@dataclass(frozen=True)
class Citation:
    """A normalized evidence citation."""

    evidence_id: str
    source_id: str
    title: str
    url: str
    quote: str

    def as_dict(self) -> dict[str, str]:
        return {
            "evidence_id": self.evidence_id,
            "source_id": self.source_id,
            "title": self.title,
            "url": self.url,
            "quote": self.quote,
        }


def render_guardrail_explanation_packet(
    *,
    guardrail: Mapping[str, Any],
    next_safe_action: Mapping[str, Any],
    evidence_pack: Mapping[str, Any],
    question_plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Render a deterministic explanation packet from PP&D fixture dictionaries.

    The function fails closed: if a guardrail rule, action, or question cites an
    evidence id that is absent from the evidence pack, it raises
    MissingCitationError instead of returning a partial packet.
    """

    evidence_by_id = _index_evidence(evidence_pack)
    cited_ids = _collect_citation_ids(guardrail, next_safe_action, question_plan)
    _require_citations(cited_ids, evidence_by_id)

    return {
        "packet_type": "ppd.guardrail_explanation_packet",
        "schema_version": "1.0",
        "guardrail_bundle_id": _string_value(guardrail, "guardrail_bundle_id"),
        "process_id": _string_value(guardrail, "process_id"),
        "status": "ready",
        "summary": _string_value(guardrail, "summary", default="Guardrails require cited evidence before action."),
        "blocked_actions": _render_blocked_actions(guardrail, evidence_by_id),
        "next_safe_actions": _render_next_safe_actions(next_safe_action, evidence_by_id),
        "questions": _render_questions(question_plan, evidence_by_id),
        "citations": [_citation_for(evidence_by_id[evidence_id]).as_dict() for evidence_id in sorted(cited_ids)],
    }


def render_or_block_guardrail_explanation_packet(
    *,
    guardrail: Mapping[str, Any],
    next_safe_action: Mapping[str, Any],
    evidence_pack: Mapping[str, Any],
    question_plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Render a packet, returning a deterministic blocked packet on citation gaps."""

    try:
        return render_guardrail_explanation_packet(
            guardrail=guardrail,
            next_safe_action=next_safe_action,
            evidence_pack=evidence_pack,
            question_plan=question_plan,
        )
    except MissingCitationError as exc:
        return {
            "packet_type": "ppd.guardrail_explanation_packet",
            "schema_version": "1.0",
            "guardrail_bundle_id": _string_value(guardrail, "guardrail_bundle_id"),
            "process_id": _string_value(guardrail, "process_id"),
            "status": "blocked_missing_citations",
            "summary": "Explanation packet blocked because required citations are unavailable.",
            "blocked_reason": str(exc),
            "blocked_actions": [],
            "next_safe_actions": [],
            "questions": [],
            "citations": [],
        }


def _index_evidence(evidence_pack: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    items = _list_value(evidence_pack, "evidence") or _list_value(evidence_pack, "items")
    indexed: dict[str, Mapping[str, Any]] = {}
    for item in items:
        if not isinstance(item, Mapping):
            continue
        evidence_id = _string_value(item, "evidence_id") or _string_value(item, "id")
        if evidence_id:
            indexed[evidence_id] = item
    return dict(sorted(indexed.items()))


def _collect_citation_ids(*sections: Mapping[str, Any]) -> set[str]:
    citations: set[str] = set()
    for section in sections:
        citations.update(_walk_citation_ids(section))
    return citations


def _walk_citation_ids(value: Any) -> set[str]:
    if isinstance(value, Mapping):
        found: set[str] = set()
        for key, nested in value.items():
            if key in {"citation", "citation_id", "evidence_id", "source_evidence_id"}:
                if isinstance(nested, str) and nested.strip():
                    found.add(nested.strip())
            elif key in {"citations", "citation_ids", "evidence_ids", "source_evidence_ids"}:
                found.update(_string_list(nested))
            else:
                found.update(_walk_citation_ids(nested))
        return found
    if isinstance(value, list):
        found = set()
        for item in value:
            found.update(_walk_citation_ids(item))
        return found
    return set()


def _require_citations(cited_ids: Iterable[str], evidence_by_id: Mapping[str, Mapping[str, Any]]) -> None:
    missing = sorted(evidence_id for evidence_id in cited_ids if evidence_id not in evidence_by_id)
    if missing:
        raise MissingCitationError("missing evidence citations: " + ", ".join(missing))


def _render_blocked_actions(
    guardrail: Mapping[str, Any], evidence_by_id: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    rows = _list_value(guardrail, "blocked_actions") or _list_value(guardrail, "refused_action_predicates")
    return [_render_cited_row(row, evidence_by_id) for row in _sorted_rows(rows)]


def _render_next_safe_actions(
    next_safe_action: Mapping[str, Any], evidence_by_id: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    rows = _list_value(next_safe_action, "next_safe_actions") or _list_value(next_safe_action, "actions")
    return [_render_cited_row(row, evidence_by_id) for row in _sorted_rows(rows)]


def _render_questions(
    question_plan: Mapping[str, Any], evidence_by_id: Mapping[str, Mapping[str, Any]]
) -> list[dict[str, Any]]:
    rows = _list_value(question_plan, "questions") or _list_value(question_plan, "missing_information_questions")
    return [_render_cited_row(row, evidence_by_id) for row in _sorted_rows(rows)]


def _render_cited_row(row: Mapping[str, Any], evidence_by_id: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    citation_ids = sorted(_walk_citation_ids(row))
    rendered = {
        "id": _string_value(row, "id") or _string_value(row, "action_id") or _string_value(row, "question_id"),
        "label": _string_value(row, "label") or _string_value(row, "title") or _string_value(row, "question"),
        "explanation": _string_value(row, "explanation") or _string_value(row, "reason") or _string_value(row, "description"),
        "citation_ids": citation_ids,
        "citations": [_citation_for(evidence_by_id[evidence_id]).as_dict() for evidence_id in citation_ids],
    }
    return {key: value for key, value in rendered.items() if value not in ("", [], None)}


def _citation_for(evidence: Mapping[str, Any]) -> Citation:
    return Citation(
        evidence_id=_string_value(evidence, "evidence_id") or _string_value(evidence, "id"),
        source_id=_string_value(evidence, "source_id"),
        title=_string_value(evidence, "title"),
        url=_string_value(evidence, "url") or _string_value(evidence, "canonical_url"),
        quote=_string_value(evidence, "quote") or _string_value(evidence, "text") or _string_value(evidence, "snippet"),
    )


def _sorted_rows(rows: list[Any]) -> list[Mapping[str, Any]]:
    mapped = [row for row in rows if isinstance(row, Mapping)]
    return sorted(mapped, key=lambda row: (_string_value(row, "sort_key"), _string_value(row, "id"), _string_value(row, "label")))


def _list_value(row: Mapping[str, Any], key: str) -> list[Any]:
    value = row.get(key)
    return value if isinstance(value, list) else []


def _string_value(row: Mapping[str, Any], key: str, *, default: str = "") -> str:
    value = row.get(key)
    if value is None:
        return default
    return str(value).strip()


def _string_list(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value.strip()} if value.strip() else set()
    if isinstance(value, list):
        return {str(item).strip() for item in value if str(item).strip()}
    return set()
