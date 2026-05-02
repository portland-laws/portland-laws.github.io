"""Syntax-first diagnostics for repeated malformed Python proposal failures."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

DIAGNOSTIC_KIND = "syntax_first_retry_stop"
MALFORMED_COMPARISON_SYNTAX = "malformed_python_comparison_syntax"
RETRY_SCOPE = "same_target_task"

_MALFORMED_SNIPPETS = (
    "confidence 1",
    "confidence 1.0",
    "return 0.0 list[str]",
)


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _entry_task_id(entry: Mapping[str, Any]) -> str:
    for key in ("task_id", "target_task_id", "selected_task"):
        value = _as_text(entry.get(key)).strip()
        if value:
            return value
    return ""


def _entry_text(entry: Mapping[str, Any]) -> str:
    parts = []
    for key in ("summary", "error", "errors", "validation", "stderr", "message", "proposal_excerpt"):
        text = _as_text(entry.get(key)).strip()
        if text:
            parts.append(text)
    return "\n".join(parts)


def _matched_snippets(text: str) -> tuple[str, ...]:
    return tuple(snippet for snippet in _MALFORMED_SNIPPETS if snippet in text)


def is_malformed_python_comparison_syntax(entry: Mapping[str, Any]) -> bool:
    """Return True when a failed proposal contains the targeted syntax pattern."""
    text = _entry_text(entry)
    if "SyntaxError" not in text:
        return False
    return bool(_matched_snippets(text))


def classify_repeated_malformed_comparison_syntax(
    failures: Sequence[Mapping[str, Any]],
    target_task_id: str,
    minimum_repetitions: int = 3,
) -> dict[str, Any]:
    """Classify repeated malformed Python syntax failures for one daemon task.

    The diagnostic is intentionally narrow: it only stops retries when the same
    target task has repeated Python SyntaxError failures containing the known
    malformed comparison or annotation-like fragments seen in proposal output.
    """
    task_id = target_task_id.strip()
    matching_entries = []
    matched_fragments: list[str] = []

    for entry in failures:
        if _entry_task_id(entry) != task_id:
            continue
        if not is_malformed_python_comparison_syntax(entry):
            continue
        matching_entries.append(entry)
        for fragment in _matched_snippets(_entry_text(entry)):
            if fragment not in matched_fragments:
                matched_fragments.append(fragment)

    should_stop = len(matching_entries) >= minimum_repetitions
    return {
        "kind": DIAGNOSTIC_KIND,
        "syntax_family": MALFORMED_COMPARISON_SYNTAX,
        "retry_scope": RETRY_SCOPE,
        "target_task_id": task_id,
        "minimum_repetitions": minimum_repetitions,
        "matched_repetitions": len(matching_entries),
        "matched_fragments": matched_fragments,
        "should_stop_retry": should_stop,
        "recommended_next_step": "return a smaller syntax-valid repair proposal for the same task" if should_stop else "continue normal validation",
    }


def classify_fixture_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Classify a JSON fixture payload used by PP&D daemon tests."""
    target_task_id = _as_text(payload.get("target_task_id")).strip()
    failures = payload.get("failures", ())
    if not isinstance(failures, Sequence) or isinstance(failures, (str, bytes)):
        failures = ()
    mapped_failures = [entry for entry in failures if isinstance(entry, Mapping)]
    minimum_repetitions = payload.get("minimum_repetitions", 3)
    if not isinstance(minimum_repetitions, int):
        minimum_repetitions = 3
    return classify_repeated_malformed_comparison_syntax(
        mapped_failures,
        target_task_id,
        minimum_repetitions=minimum_repetitions,
    )
