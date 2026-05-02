"""Diagnostics for repeated malformed Python proposals.

The PP&D daemon receives complete-file replacements from an LLM. When a target
task repeatedly returns Python that fails before runtime, the daemon should stop
that target as a syntax-first retry condition instead of continuing to ask for
larger replacements. This module is intentionally small and deterministic so it
can be used by supervisor repair tests without touching PP&D domain artifacts.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence


SYNTAX_FAILURE_MARKERS = (
    "syntaxerror",
    "py_compile",
    "ts1005",
    "ts1109",
    "ts1128",
)

MALFORMED_CONFIDENCE_COMPARISON_RE = re.compile(
    r"\b(?:if|elif|while|assert)\s+confidence\s+1(?:\.0)?\s*:",
    re.IGNORECASE,
)

MALFORMED_NUMERIC_RETURN_TYPE_RE = re.compile(
    r"\breturn\s+0(?:\.0)?\s+[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]\n]+\])?",
    re.IGNORECASE,
)


def _string_values(value: Any) -> list[str]:
    """Collect strings from nested proposal/result dictionaries."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        parts: list[str] = []
        for child in value.values():
            parts.extend(_string_values(child))
        return parts
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        parts = []
        for child in value:
            parts.extend(_string_values(child))
        return parts
    return []


def diagnostic_text(value: Any) -> str:
    return "\n".join(_string_values(value))


def syntax_failure_present(value: Any) -> bool:
    text = diagnostic_text(value).lower()
    return any(marker in text for marker in SYNTAX_FAILURE_MARKERS)


def malformed_python_signatures(value: Any) -> list[str]:
    """Return normalized malformed-syntax signatures seen in proposal text.

    The signatures intentionally collapse `confidence 1` and `confidence 1.0`
    to the same class because both represent the same missing-comparator bug.
    """
    text = diagnostic_text(value)
    signatures: list[str] = []
    if MALFORMED_CONFIDENCE_COMPARISON_RE.search(text):
        signatures.append("malformed-comparison:confidence-missing-operator")
    if MALFORMED_NUMERIC_RETURN_TYPE_RE.search(text):
        signatures.append("malformed-return:numeric-value-followed-by-type")
    return signatures


def classify_syntax_first_retry_stop(
    *,
    target_task: str,
    current_proposal: Mapping[str, Any],
    recent_failures: Sequence[Mapping[str, Any]],
    minimum_repetitions: int = 2,
) -> dict[str, Any]:
    """Classify whether a target task should stop after repeated syntax failures.

    Only failures for the same target task count. The current proposal must both
    include a known malformed Python signature and carry syntax-failure evidence
    such as `SyntaxError` or `py_compile` output.
    """
    current_signatures = malformed_python_signatures(current_proposal)
    if not current_signatures or not syntax_failure_present(current_proposal):
        return {
            "syntax_first_retry_stop": False,
            "target_task": target_task,
            "repeat_count": 0,
            "signatures": current_signatures,
            "reason": "current proposal does not match a known malformed Python syntax failure",
        }

    repeat_count = 1
    matching_prior_signatures: list[str] = []
    for failure in recent_failures:
        if str(failure.get("target_task", "")) != target_task:
            continue
        if not syntax_failure_present(failure):
            continue
        prior_signatures = malformed_python_signatures(failure)
        if not prior_signatures:
            continue
        repeat_count += 1
        matching_prior_signatures.extend(prior_signatures)

    all_signatures = sorted(set(current_signatures + matching_prior_signatures))
    should_stop = repeat_count >= minimum_repetitions
    return {
        "syntax_first_retry_stop": should_stop,
        "target_task": target_task,
        "repeat_count": repeat_count,
        "signatures": all_signatures,
        "reason": (
            "same target task repeatedly produced known malformed Python syntax"
            if should_stop
            else "known malformed Python syntax has not repeated for this target task"
        ),
    }
