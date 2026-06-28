"""Deterministic regression corpus helpers for PP&D agent prompt guardrails.

The corpus is fixture-first: it loads committed synthetic cases and validates
that agent missing-information prompts remain source-cited, offline, and free of
private case material. It intentionally does not call an LLM or inspect user
files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set


REQUIRED_SOURCE_IDS: Set[str] = {
    "offline-guardrail-consumer-smoke-test-plan",
    "agent-readiness-release-blocker-reconciliation-packet",
    "safe-next-action-user-handoff-checklist",
}

REQUIRED_PROMPT_CATEGORIES: Set[str] = {
    "missing_fact_question",
    "stale_evidence_prompt",
    "manual_handoff_prompt",
    "refused_consequential_action_prompt",
    "local_preview_only_expectation",
}

FORBIDDEN_TEXT_MARKERS: Sequence[str] = (
    "cookie",
    "credential",
    "password",
    "private case file",
    "private_case_file",
    "session storage",
    "auth state",
    "har file",
    "screenshot path",
    "trace.zip",
    "payment card",
    "ssn",
)


@dataclass(frozen=True)
class CorpusValidationResult:
    """Validation result for a committed prompt regression corpus fixture."""

    case_count: int
    source_ids: Set[str]
    prompt_categories: Set[str]
    errors: List[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def load_prompt_corpus(path: Path) -> Dict[str, Any]:
    """Load a prompt corpus fixture from disk without following external refs."""

    with path.open("r", encoding="utf-8") as fixture_file:
        data = json.load(fixture_file)
    if not isinstance(data, dict):
        raise ValueError("prompt corpus fixture must be a JSON object")
    return data


def validate_prompt_corpus(corpus: Mapping[str, Any]) -> CorpusValidationResult:
    """Validate offline regression coverage and citation hygiene."""

    errors: List[str] = []
    source_ids = _collect_source_ids(corpus.get("sources"))
    missing_sources = REQUIRED_SOURCE_IDS.difference(source_ids)
    if missing_sources:
        errors.append("missing required source ids: " + ", ".join(sorted(missing_sources)))

    cases = corpus.get("synthetic_user_cases")
    if not isinstance(cases, list) or not cases:
        errors.append("synthetic_user_cases must be a non-empty list")
        cases = []

    prompt_categories: Set[str] = set()
    case_ids: Set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append("case at index %d must be an object" % index)
            continue
        case_id = _string_value(case, "case_id")
        if not case_id:
            errors.append("case at index %d is missing case_id" % index)
        elif case_id in case_ids:
            errors.append("duplicate case_id: " + case_id)
        else:
            case_ids.add(case_id)

        if _has_forbidden_text(case):
            errors.append("case %s contains forbidden private or credential marker" % (case_id or index))

        _validate_case_citations(case, source_ids, errors, case_id or str(index))
        prompts = case.get("expected_prompts")
        if not isinstance(prompts, list) or not prompts:
            errors.append("case %s must include expected_prompts" % (case_id or index))
            continue
        for prompt_index, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                errors.append("case %s prompt %d must be an object" % (case_id or index, prompt_index))
                continue
            category = _string_value(prompt, "category")
            if not category:
                errors.append("case %s prompt %d is missing category" % (case_id or index, prompt_index))
            else:
                prompt_categories.add(category)
            text = _string_value(prompt, "text")
            if not text.endswith("?") and category in {"missing_fact_question", "stale_evidence_prompt", "manual_handoff_prompt"}:
                errors.append("case %s prompt %d should be phrased as a question" % (case_id or index, prompt_index))
            if category == "refused_consequential_action_prompt" and "cannot" not in text.lower():
                errors.append("case %s refusal prompt must explicitly say cannot" % (case_id or index))
            if category == "local_preview_only_expectation" and "local preview" not in text.lower():
                errors.append("case %s local-preview expectation must mention local preview" % (case_id or index))
            _validate_prompt_citations(prompt, source_ids, errors, case_id or str(index), prompt_index)

    missing_categories = REQUIRED_PROMPT_CATEGORIES.difference(prompt_categories)
    if missing_categories:
        errors.append("missing prompt categories: " + ", ".join(sorted(missing_categories)))

    if corpus.get("execution_policy") != "offline_fixture_only_no_llm_no_private_files":
        errors.append("execution_policy must be offline_fixture_only_no_llm_no_private_files")

    return CorpusValidationResult(
        case_count=len(cases),
        source_ids=source_ids,
        prompt_categories=prompt_categories,
        errors=errors,
    )


def expected_prompt_matrix(corpus: Mapping[str, Any]) -> Dict[str, List[str]]:
    """Return case id to expected prompt category mapping for regression tests."""

    matrix: Dict[str, List[str]] = {}
    cases = corpus.get("synthetic_user_cases")
    if not isinstance(cases, list):
        return matrix
    for case in cases:
        if not isinstance(case, dict):
            continue
        case_id = _string_value(case, "case_id")
        prompts = case.get("expected_prompts")
        if not case_id or not isinstance(prompts, list):
            continue
        matrix[case_id] = [
            prompt.get("category", "")
            for prompt in prompts
            if isinstance(prompt, dict) and isinstance(prompt.get("category"), str)
        ]
    return matrix


def _collect_source_ids(sources: Any) -> Set[str]:
    if not isinstance(sources, list):
        return set()
    return {
        source.get("source_id")
        for source in sources
        if isinstance(source, dict) and isinstance(source.get("source_id"), str)
    }


def _validate_case_citations(case: Mapping[str, Any], source_ids: Set[str], errors: List[str], case_id: str) -> None:
    citations = case.get("citations")
    if not isinstance(citations, list) or not citations:
        errors.append("case %s must include citations" % case_id)
        return
    _validate_citations(citations, source_ids, errors, "case %s" % case_id)


def _validate_prompt_citations(
    prompt: Mapping[str, Any],
    source_ids: Set[str],
    errors: List[str],
    case_id: str,
    prompt_index: int,
) -> None:
    citations = prompt.get("citations")
    if not isinstance(citations, list) or not citations:
        errors.append("case %s prompt %d must include citations" % (case_id, prompt_index))
        return
    _validate_citations(citations, source_ids, errors, "case %s prompt %d" % (case_id, prompt_index))


def _validate_citations(citations: Iterable[Any], source_ids: Set[str], errors: List[str], label: str) -> None:
    for citation in citations:
        if not isinstance(citation, dict):
            errors.append(label + " citation must be an object")
            continue
        source_id = citation.get("source_id")
        section = citation.get("section")
        if source_id not in source_ids:
            errors.append(label + " citation references unknown source_id: " + str(source_id))
        if not isinstance(section, str) or not section:
            errors.append(label + " citation must include a section")


def _string_value(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    return value if isinstance(value, str) else ""


def _has_forbidden_text(value: Any) -> bool:
    lowered = json.dumps(value, sort_keys=True).lower()
    return any(marker in lowered for marker in FORBIDDEN_TEXT_MARKERS)
