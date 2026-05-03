"""Daemon-only diagnostics for parser-clean LLM failures.

The helpers in this module intentionally keep only compact metadata derived from
raw model output. They must not persist full raw LLM responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable, Mapping, Sequence

_MAX_SNIPPET_CHARS = 120
_PRIVATE_MARKERS = (
    "auth-state",
    "auth_state",
    "storage-state",
    "storage_state",
    "trace.zip",
    ".har",
    "cookie",
    "screenshot",
    "downloaded document",
    "raw crawl output",
)


@dataclass(frozen=True)
class ParserCleanDiagnostic:
    """Compact diagnostic payload safe for daemon ledgers."""

    target_task: str
    failure_kind: str
    compact_raw_response_summary: str
    next_action_hint: str

    def to_dict(self) -> dict[str, str]:
        return {
            "target_task": self.target_task,
            "failure_kind": self.failure_kind,
            "compact_raw_response_summary": self.compact_raw_response_summary,
            "next_action_hint": self.next_action_hint,
        }


def build_parser_clean_diagnostic(
    *,
    target_task: str,
    raw_response: str | Sequence[str] | None = None,
    raw_responses: Sequence[str] | None = None,
    error: BaseException | str | None = None,
) -> dict[str, str]:
    """Return a compact parser-clean diagnostic without storing raw output.

    ``raw_response`` accepts either a single string or a sequence so callers can
    pass repeated failed LLM attempts directly. ``raw_responses`` is accepted as
    an explicit synonym for clarity at call sites.
    """

    attempts = _coerce_attempts(raw_responses if raw_responses is not None else raw_response)
    failure_kind = _classify_failure(attempts, error)
    diagnostic = ParserCleanDiagnostic(
        target_task=target_task,
        failure_kind=failure_kind,
        compact_raw_response_summary=_summarize_attempts(attempts),
        next_action_hint=_next_action_hint(failure_kind),
    )
    return diagnostic.to_dict()


def _coerce_attempts(raw: str | Sequence[str] | None) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    return [item if isinstance(item, str) else repr(item) for item in raw]


def _classify_failure(attempts: Sequence[str], error: BaseException | str | None) -> str:
    error_text = "" if error is None else str(error).lower()
    if "json" in error_text or any(not _looks_like_json_object(attempt) for attempt in attempts):
        return "non_json_llm_output"
    if "runtime" in error_text or "exception" in error_text:
        return "runtime_failure"
    return "parser_clean_failure"


def _looks_like_json_object(value: str) -> bool:
    stripped = value.strip()
    return stripped.startswith("{") and stripped.endswith("}")


def _summarize_attempts(attempts: Sequence[str]) -> str:
    if not attempts:
        return "attempts=0 chars=0 sha256=empty snippet=''"

    total_chars = sum(len(attempt) for attempt in attempts)
    digest = sha256("\n---attempt---\n".join(attempts).encode("utf-8")).hexdigest()[:12]
    unique_count = len(set(attempts))
    first_snippet = _compact_snippet(attempts[0])
    repeat_note = " repeated=true" if len(attempts) > 1 and unique_count == 1 else " repeated=false"
    return (
        f"attempts={len(attempts)} unique={unique_count} chars={total_chars} "
        f"sha256={digest}{repeat_note} snippet='{first_snippet}'"
    )


def _compact_snippet(value: str) -> str:
    compact = " ".join(value.split())
    compact = _redact_private_markers(compact)
    if len(compact) > _MAX_SNIPPET_CHARS:
        compact = compact[: _MAX_SNIPPET_CHARS - 3] + "..."
    return compact.replace("'", "\\'")


def _redact_private_markers(value: str) -> str:
    redacted = value
    lowered = redacted.lower()
    for marker in _PRIVATE_MARKERS:
        while marker in lowered:
            index = lowered.index(marker)
            redacted = redacted[:index] + "[private-marker-omitted]" + redacted[index + len(marker) :]
            lowered = redacted.lower()
    return redacted


def _next_action_hint(failure_kind: str) -> str:
    hints: Mapping[str, str] = {
        "non_json_llm_output": "Retry with a JSON-only instruction and a minimal schema; do not persist the raw response.",
        "runtime_failure": "Retry once after isolating the parser-clean runtime exception path.",
        "parser_clean_failure": "Inspect parser-clean validation and retry with the smallest deterministic fixture.",
    }
    return hints.get(failure_kind, hints["parser_clean_failure"])
