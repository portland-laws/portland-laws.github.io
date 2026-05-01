"""Small diagnostic helpers for PP&D supervisor repair hints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SYNTAX_MARKERS = (
    "syntaxerror",
    "failed py_compile",
    "py_compile",
    "invalid syntax",
    "unterminated string literal",
)


@dataclass(frozen=True)
class SupervisorDiagnostic:
    kind: str
    severity: str
    hint: str
    recommended_action: str


def proposal_text(proposal: dict[str, Any]) -> str:
    parts: list[str] = []
    parts.extend(str(error) for error in proposal.get("errors", []) or [])
    for result in proposal.get("validation_results", []) or []:
        if not isinstance(result, dict):
            continue
        parts.append(str(result.get("stdout", "")))
        parts.append(str(result.get("stderr", "")))
    return "\n".join(parts).lower()


def is_python_syntax_failure(proposal: dict[str, Any]) -> bool:
    if str(proposal.get("failure_kind") or "") != "validation":
        return False
    text = proposal_text(proposal)
    return any(marker in text for marker in SYNTAX_MARKERS) and ".py" in text


def classify_repeated_python_syntax_failures(
    proposals: list[dict[str, Any]],
    *,
    repeated_threshold: int = 2,
) -> SupervisorDiagnostic:
    syntax_failures = [proposal for proposal in proposals if is_python_syntax_failure(proposal)]
    if len(syntax_failures) >= repeated_threshold:
        return SupervisorDiagnostic(
            kind="syntactic_validity_repair_hint",
            severity="warning",
            hint="Repeated Python SyntaxError validation failures indicate the daemon needs a smaller syntax-valid proposal.",
            recommended_action="Patch daemon prompt/preflight or ask for fewer files before retrying the domain task.",
        )
    return SupervisorDiagnostic(
        kind="no_repair_hint",
        severity="info",
        hint="Recent failures do not meet the repeated Python syntax failure threshold.",
        recommended_action="Continue observing normal daemon progress.",
    )
