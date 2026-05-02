"""Prompt guidance for PP&D daemon syntax-preflight rollbacks.

This module is intentionally narrow: it detects parser/compiler failure context
and returns a compact instruction block that supervisors can include in daemon
prompts before retrying a failed proposal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


SYNTAX_FAILURE_MARKERS: tuple[str, ...] = (
    "SyntaxError",
    "py_compile",
    "TS1005",
    "TS1109",
    "TS1128",
)


@dataclass(frozen=True)
class SyntaxRollbackDiagnostics:
    """Compact diagnostics for a recent syntax-preflight rollback."""

    has_syntax_failure: bool
    matched_markers: tuple[str, ...]
    guidance: str


def diagnose_syntax_rollback(failure_context: Iterable[str]) -> SyntaxRollbackDiagnostics:
    """Return prompt guidance when recent failures show syntax-preflight errors."""

    context_text = "\n".join(str(item) for item in failure_context)
    matched_markers = tuple(marker for marker in SYNTAX_FAILURE_MARKERS if marker in context_text)
    has_syntax_failure = bool(matched_markers)
    guidance = syntax_recovery_prompt_guidance(matched_markers) if has_syntax_failure else ""
    return SyntaxRollbackDiagnostics(
        has_syntax_failure=has_syntax_failure,
        matched_markers=matched_markers,
        guidance=guidance,
    )


def syntax_recovery_prompt_guidance(matched_markers: Iterable[str]) -> str:
    """Build deterministic daemon prompt guidance for syntax recovery."""

    unique_markers = tuple(dict.fromkeys(str(marker) for marker in matched_markers if str(marker).strip()))
    marker_text = ", ".join(unique_markers) if unique_markers else "syntax-preflight failure"
    return (
        "Recent PP&D validation failed during syntax preflight "
        f"({marker_text}). Return a smaller recovery proposal: replace one file only, "
        "or replace one narrow test file plus one adjacent deterministic fixture when the "
        "fixture is required by that test. Do not rewrite broad shared contracts, including "
        "ppd/contracts/documents.py, unless the selected task explicitly requires that "
        "contract extension. Keep Python syntax Python-only, keep TypeScript syntax "
        "TypeScript-only, and ensure changed Python files pass py_compile before full "
        "validation."
    )


def _self_test() -> None:
    diagnostics = diagnose_syntax_rollback([
        "rollback failure_kind=syntax_preflight",
        "py_compile failed: SyntaxError: invalid syntax",
    ])
    assert diagnostics.has_syntax_failure
    assert diagnostics.matched_markers == ("SyntaxError", "py_compile")
    assert "one file only" in diagnostics.guidance
    assert "one narrow test file plus one adjacent deterministic fixture" in diagnostics.guidance
    assert "Do not rewrite broad shared contracts" in diagnostics.guidance

    clean = diagnose_syntax_rollback(["unit test assertion failed"])
    assert not clean.has_syntax_failure
    assert clean.matched_markers == ()
    assert clean.guidance == ""


if __name__ == "__main__":
    _self_test()
