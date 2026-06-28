"""User-facing guardrail explanations for PP&D predicates.

This module intentionally accepts plain dictionaries so deterministic fixtures can
exercise guardrail behavior without requiring live DevHub sessions or private
crawl artifacts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

_PRIVATE_KEYS = {
    "private_value",
    "private_values",
    "raw_authenticated_page_data",
    "authenticated_page_data",
    "session_state",
    "cookies",
    "token",
    "password",
    "payment_details",
    "local_private_file_path",
}


@dataclass(frozen=True)
class GuardrailExplanation:
    """A cited explanation that is safe to show to a user."""

    predicate_id: str
    explanation: str
    citations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "predicate_id": self.predicate_id,
            "explanation": self.explanation,
            "citations": list(self.citations),
        }


def render_guardrail_explanations(fixture: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Render blocked-action and missing-information explanations.

    The returned text uses only public labels, policy reasons, and citations from
    the fixture. Private predicate values and raw authenticated page data are
    excluded even when present in the source fixture.
    """

    source_index = _source_index(fixture.get("sources", []))
    blocked = [
        _render_blocked_action(predicate, source_index).as_dict()
        for predicate in fixture.get("blocked_action_predicates", [])
    ]
    missing = [
        _render_missing_information(predicate, source_index).as_dict()
        for predicate in fixture.get("missing_information_predicates", [])
    ]
    result = {"blocked_actions": blocked, "missing_information": missing}
    _assert_no_private_payload_leaked(result, fixture)
    return result


def _render_blocked_action(
    predicate: Mapping[str, Any], source_index: Mapping[str, Mapping[str, Any]]
) -> GuardrailExplanation:
    predicate_id = str(predicate.get("predicate_id", "blocked-action"))
    action_label = _safe_text(predicate.get("action_label", "this action"))
    reason = _safe_text(predicate.get("public_reason", "Official PP&D action requires user review."))
    next_step = _safe_text(
        predicate.get(
            "safe_next_step",
            "Review the cited guidance and wait for attended user confirmation before proceeding.",
        )
    )
    citations = _citations(predicate.get("evidence_ids", []), source_index)
    explanation = f"I cannot complete {action_label}. {reason} {next_step}"
    return GuardrailExplanation(predicate_id=predicate_id, explanation=explanation, citations=citations)


def _render_missing_information(
    predicate: Mapping[str, Any], source_index: Mapping[str, Mapping[str, Any]]
) -> GuardrailExplanation:
    predicate_id = str(predicate.get("predicate_id", "missing-information"))
    fact_label = _safe_text(predicate.get("fact_label", "a required fact"))
    reason = _safe_text(predicate.get("public_reason", "PP&D guidance requires this before the workflow can continue."))
    user_question = _safe_text(predicate.get("user_question", f"Please provide {fact_label}."))
    citations = _citations(predicate.get("evidence_ids", []), source_index)
    explanation = f"I need {fact_label} before continuing. {reason} {user_question}"
    return GuardrailExplanation(predicate_id=predicate_id, explanation=explanation, citations=citations)


def _source_index(sources: Any) -> dict[str, Mapping[str, Any]]:
    index: dict[str, Mapping[str, Any]] = {}
    if not isinstance(sources, Sequence) or isinstance(sources, (str, bytes)):
        return index
    for source in sources:
        if isinstance(source, Mapping) and source.get("source_id"):
            index[str(source["source_id"])] = source
    return index


def _citations(evidence_ids: Any, source_index: Mapping[str, Mapping[str, Any]]) -> tuple[str, ...]:
    if not isinstance(evidence_ids, Iterable) or isinstance(evidence_ids, (str, bytes)):
        return ()
    citations: list[str] = []
    for evidence_id in evidence_ids:
        source = source_index.get(str(evidence_id))
        if source is None:
            continue
        title = _safe_text(source.get("title", str(evidence_id)))
        url = _safe_text(source.get("url", ""))
        if url:
            citations.append(f"{title} ({url})")
        else:
            citations.append(title)
    return tuple(citations)


def _safe_text(value: Any) -> str:
    """Return display text without accepting nested private structures."""

    if isinstance(value, Mapping):
        allowed_parts = []
        for key, item in value.items():
            if str(key).lower() in _PRIVATE_KEYS:
                continue
            if isinstance(item, (str, int, float, bool)):
                allowed_parts.append(str(item))
        return " ".join(allowed_parts).strip()
    if isinstance(value, (list, tuple, set)):
        return " ".join(_safe_text(item) for item in value if not isinstance(item, Mapping)).strip()
    return str(value).strip()


def _assert_no_private_payload_leaked(rendered: Mapping[str, Any], fixture: Mapping[str, Any]) -> None:
    rendered_text = repr(rendered)
    for secret in _private_strings(fixture):
        if secret and secret in rendered_text:
            raise ValueError(f"guardrail explanation leaked private fixture value: {secret!r}")


def _private_strings(value: Any, parent_key: str = "") -> set[str]:
    parent_is_private = parent_key.lower() in _PRIVATE_KEYS
    if isinstance(value, Mapping):
        secrets: set[str] = set()
        for key, item in value.items():
            secrets.update(_private_strings(item, str(key)))
        return secrets
    if isinstance(value, (list, tuple, set)):
        secrets = set()
        for item in value:
            secrets.update(_private_strings(item, parent_key))
        return secrets
    if parent_is_private and isinstance(value, (str, int, float)):
        return {str(value)}
    return set()
