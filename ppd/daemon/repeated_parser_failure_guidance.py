"""Prompt guidance for repeated parser failures in PP&D domain tasks.

This module is intentionally small and deterministic. It gives the PP&D daemon a
single reusable prompt fragment for the case where a domain task has already
failed repeatedly because a generated Python or TypeScript proposal could not be
parsed or compiled.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


PARSER_FAILURE_MARKERS = (
    "SyntaxError",
    "py_compile",
    "TS1005",
    "TS1109",
    "TS1128",
)

CONTRACT_REUSE_GUIDANCE = "\n".join(
    (
        "Repeated parser or compile failures have been seen for this PP&D domain task.",
        "Before proposing a new module, inspect and reuse the committed PP&D contracts that already cover this domain.",
        "Do not introduce a similarly named replacement contract unless the task explicitly requires a shared contract extension.",
        "Prefer a smaller syntax-valid proposal that imports existing contracts, adds a narrow validator or fixture, and avoids broad rewrites.",
        "If a new module is still necessary, explain why no existing committed PP&D contract can represent the fixture or behavior.",
    )
)


@dataclass(frozen=True)
class ParserFailureSummary:
    """Compact repeated-parser-failure signal for prompt construction."""

    parser_failure_count: int
    matched_markers: tuple[str, ...]

    @property
    def requires_contract_reuse_guidance(self) -> bool:
        return self.parser_failure_count >= 2 and bool(self.matched_markers)


def summarize_parser_failures(failure_contexts: Iterable[str]) -> ParserFailureSummary:
    """Count parser-like failures and return the markers that were observed."""

    count = 0
    matched: list[str] = []
    seen: set[str] = set()

    for context in failure_contexts:
        for marker in PARSER_FAILURE_MARKERS:
            if marker in context:
                count += 1
                if marker not in seen:
                    seen.add(marker)
                    matched.append(marker)
                break

    return ParserFailureSummary(parser_failure_count=count, matched_markers=tuple(matched))


def render_contract_reuse_guidance(failure_contexts: Iterable[str]) -> str:
    """Return daemon prompt guidance when repeated parser failures warrant it."""

    summary = summarize_parser_failures(failure_contexts)
    if not summary.requires_contract_reuse_guidance:
        return ""

    marker_text = ", ".join(summary.matched_markers)
    return f"{CONTRACT_REUSE_GUIDANCE}\nObserved parser markers: {marker_text}."
