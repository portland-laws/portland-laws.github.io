"""Diagnostics for repeated daemon syntax-preflight failures.

This module is intentionally narrow: it formats diagnostic records only. It does
not rank, filter, or otherwise affect worker task selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


SMALLER_NEXT_ATTEMPT_GUIDANCE = (
    "Return a smaller next attempt that only includes the files needed for a "
    "syntax-valid implementation or repair. Keep Python and TypeScript syntax "
    "separate, and run the reported validation command before proposing the "
    "next change."
)


@dataclass(frozen=True)
class SyntaxPreflightFailure:
    """Commit-safe summary of one syntax-preflight failure."""

    target_task: str
    failing_file: str
    validation_command: tuple[str, ...]
    summary: str = ""


def _failure_key(failure: SyntaxPreflightFailure) -> tuple[str, str, tuple[str, ...]]:
    return (failure.target_task, failure.failing_file, failure.validation_command)


def repeated_syntax_preflight_diagnostics(
    failures: Iterable[SyntaxPreflightFailure],
    *,
    repeat_threshold: int = 2,
) -> list[dict[str, object]]:
    """Return diagnostics for repeated syntax-preflight failures.

    The output is deterministic and contains only daemon diagnostic metadata.
    It deliberately omits any worker selection fields so callers can append these
    records to logs without changing scheduling semantics.
    """

    if repeat_threshold < 2:
        raise ValueError("repeat_threshold must be at least 2")

    grouped: dict[tuple[str, str, tuple[str, ...]], list[SyntaxPreflightFailure]] = {}
    for failure in failures:
        grouped.setdefault(_failure_key(failure), []).append(failure)

    diagnostics: list[dict[str, object]] = []
    for key in sorted(grouped):
        entries = grouped[key]
        if len(entries) < repeat_threshold:
            continue

        target_task, failing_file, validation_command = key
        diagnostics.append(
            {
                "kind": "repeated_syntax_preflight_failure",
                "target_task": target_task,
                "failing_file": failing_file,
                "validation_command": list(validation_command),
                "failure_count": len(entries),
                "latest_summary": entries[-1].summary,
                "guidance": SMALLER_NEXT_ATTEMPT_GUIDANCE,
            }
        )

    return diagnostics
