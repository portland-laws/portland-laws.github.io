"""Supervisor guidance for retrying after daemon syntax preflight failures.

The PP&D daemon asks the model for complete JSON file replacements. When a
proposal fails before validation because a Python or TypeScript file cannot be
parsed, the next prompt should become smaller and explicitly syntax-first.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


SYNTAX_ERROR_MARKERS = (
    "SyntaxError",
    "py_compile",
    "TS1005",
    "TS1109",
    "TS1128",
    "unterminated string literal",
    "invalid syntax",
)

FORBIDDEN_RETRY_SCOPES = (
    "live DevHub",
    "Playwright session",
    "authenticated automation",
    "broad contract rewrite",
    "domain implementation",
)


@dataclass(frozen=True)
class SyntaxRetryGuidance:
    """A narrow retry instruction produced after syntax preflight failures."""

    should_narrow: bool
    reason: str
    max_files: int
    required_preflight: tuple[str, ...]
    prompt_bullets: tuple[str, ...]


def has_syntax_failure(errors: Iterable[str]) -> bool:
    """Return True when daemon errors show parser or compiler syntax failure."""

    combined = "\n".join(str(error) for error in errors)
    return any(marker in combined for marker in SYNTAX_ERROR_MARKERS)


def build_syntax_retry_guidance(errors: Iterable[str]) -> SyntaxRetryGuidance:
    """Build deterministic prompt guidance for the next daemon LLM round."""

    syntax_failure = has_syntax_failure(errors)
    if not syntax_failure:
        return SyntaxRetryGuidance(
            should_narrow=False,
            reason="no syntax preflight marker detected",
            max_files=4,
            required_preflight=(),
            prompt_bullets=(),
        )

    return SyntaxRetryGuidance(
        should_narrow=True,
        reason="syntax preflight failed before validation",
        max_files=2,
        required_preflight=(
            "python3 -m py_compile ",
            "JSON parse check for each changed fixture file",
        ),
        prompt_bullets=(
            "Return exactly one JSON object with complete file replacements only.",
            "Limit the retry to one or two files that directly repair the syntax failure.",
            "Prefer quoted sentinel values such as '[REDACTED:empty-before]' over multiline string literals in assertions.",
            "Do not rewrite broad fixture contracts, daemon contracts, or unrelated validators during a syntax retry.",
            "Do not launch Playwright, touch live DevHub, use private sessions, upload, submit, pay, certify, cancel, schedule inspections, automate MFA, or automate CAPTCHA.",
        ),
    )


def render_syntax_retry_prompt(errors: Iterable[str]) -> str:
    """Render concise supervisor text for the next syntax-first retry."""

    guidance = build_syntax_retry_guidance(errors)
    if not guidance.should_narrow:
        return "No syntax-first retry guidance is needed."

    lines = [
        "Syntax preflight failed before validation; make the next daemon round syntax-first.",
        f"Maximum replacement files: {guidance.max_files}.",
        "Required preflight:",
    ]
    lines.extend(f"- {item}" for item in guidance.required_preflight)
    lines.append("Retry guardrails:")
    lines.extend(f"- {item}" for item in guidance.prompt_bullets)
    return "\n".join(lines)
