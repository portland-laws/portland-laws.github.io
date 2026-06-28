"""Validation for PP&D missing-information prompt regression corpora.

The regression corpus is an executable safety artifact. It must not contain
private case data, local paths, claims of live authenticated work, or enabled
controls for consequential DevHub actions. These checks are intentionally
string-based and deterministic so they can run in offline self-tests.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


CONSEQUENTIAL_CONTROL_KINDS = frozenset(
    {
        "payment",
        "pay",
        "upload",
        "submit",
        "submission",
        "schedule",
        "scheduling",
        "cancel",
        "cancellation",
        "certify",
        "certification",
        "acknowledgement",
        "acknowledgment",
    }
)

_PRIVATE_FACT_PATTERNS = (
    re.compile(r"\b\d{1,6}\s+[A-Z][A-Za-z0-9.'-]*(?:\s+[A-Z][A-Za-z0-9.'-]*){0,4}\s+(?:Ave|Avenue|Blvd|Boulevard|Ct|Court|Dr|Drive|Ln|Lane|Loop|Pl|Place|Rd|Road|St|Street|Way)\b"),
    re.compile(r"\b(?:permit|case|application|ivr)\s*(?:#|number|no\.)?\s*[:#]?\s*[A-Z]{1,4}[- ]?\d{4,}\b", re.IGNORECASE),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    re.compile(r"\b(?:owner|applicant|contractor|tenant|client)\s+(?:is|name is|named)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b"),
)

_LOCAL_PATH_PATTERNS = (
    re.compile(r"(?:^|\s)/(?:Users|home|private|tmp|var/folders)/[^\s]+"),
    re.compile(r"\b[A-Za-z]:\\\\(?:Users|Documents|Downloads|Temp|tmp)\\\\[^\s]+"),
    re.compile(r"\bfile://[^\s]+", re.IGNORECASE),
)

_OUTCOME_GUARANTEE_PATTERNS = (
    re.compile(r"\b(?:guarantee|promise|ensure)\b.{0,80}\b(?:approval|approved|issuance|issued|permit|inspection passes?)\b", re.IGNORECASE),
    re.compile(r"\b(?:will|must)\s+(?:be\s+)?(?:approved|issued|accepted|granted)\b", re.IGNORECASE),
    re.compile(r"\bno\s+risk\s+(?:of\s+)?(?:denial|rejection|correction|checksheets?)\b", re.IGNORECASE),
)

_RAW_ARTIFACT_PATTERNS = (
    re.compile(r"\b(?:raw\s+)?(?:crawl|crawler|download|downloaded|archive|warc|har|trace|screenshot)\b", re.IGNORECASE),
    re.compile(r"\b(?:archive_artifact_ref|raw_body|downloaded_document|crawl_output|browser_trace)\b", re.IGNORECASE),
)

_LIVE_EXECUTION_PATTERNS = (
    re.compile(r"\b(?:I|we|agent)\s+(?:logged\s+in|signed\s+in|clicked|submitted|uploaded|paid|scheduled|cancelled|canceled|certified)\b.{0,80}\b(?:DevHub|portal|application|permit|inspection|fee)\b", re.IGNORECASE),
    re.compile(r"\b(?:live|real)\s+(?:LLM|DevHub|browser|portal|account)\s+(?:run|execution|session|login|automation)\b", re.IGNORECASE),
    re.compile(r"\b(?:called|ran|queried)\s+(?:the\s+)?(?:live\s+)?(?:LLM|DevHub|Portland\s+DevHub)\b", re.IGNORECASE),
)

_REFUSAL_REQUIRED_PATTERNS = (
    *_PRIVATE_FACT_PATTERNS,
    *_LOCAL_PATH_PATTERNS,
    *_OUTCOME_GUARANTEE_PATTERNS,
    *_RAW_ARTIFACT_PATTERNS,
    *_LIVE_EXECUTION_PATTERNS,
)

_CITATION_MARKER_RE = re.compile(r"(?:\[[A-Za-z0-9_.:-]+\]|https://www\.portland\.gov/ppd/[^\s)]+|source_evidence_ids?|citation_ids?)", re.IGNORECASE)


@dataclass(frozen=True)
class CorpusValidationIssue:
    """A deterministic validation finding for one corpus entry."""

    case_id: str
    code: str
    message: str


def load_prompt_corpus(path: str | Path) -> Any:
    """Load a JSON regression corpus from disk."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_prompt_corpus_file(path: str | Path) -> list[CorpusValidationIssue]:
    """Validate a JSON regression corpus file."""

    return validate_prompt_corpus(load_prompt_corpus(path))


def validate_prompt_corpus(corpus: Any) -> list[CorpusValidationIssue]:
    """Validate every case in a missing-information prompt corpus.

    Supported corpus shapes are either a list of cases or a mapping containing a
    ``cases`` list. Individual cases may use ``prompt``, ``messages``,
    ``expected_refusal``, ``refusal_expected``, ``citations``,
    ``citation_ids``, ``source_evidence_ids``, and ``controls`` fields.
    """

    cases = _extract_cases(corpus)
    issues: list[CorpusValidationIssue] = []
    for index, case in enumerate(cases):
        issues.extend(_validate_case(case, index))
    return issues


def assert_valid_prompt_corpus(corpus: Any) -> None:
    """Raise ``ValueError`` when a corpus contains any unsafe entry."""

    issues = validate_prompt_corpus(corpus)
    if issues:
        rendered = "; ".join(f"{issue.case_id}:{issue.code}" for issue in issues)
        raise ValueError(f"invalid missing-information prompt corpus: {rendered}")


def _extract_cases(corpus: Any) -> Sequence[Mapping[str, Any]]:
    if isinstance(corpus, list):
        return [_as_mapping(case) for case in corpus]
    if isinstance(corpus, Mapping):
        raw_cases = corpus.get("cases")
        if isinstance(raw_cases, list):
            return [_as_mapping(case) for case in raw_cases]
    raise TypeError("prompt corpus must be a list or a mapping with a cases list")


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError("prompt corpus cases must be JSON objects")
    return value


def _validate_case(case: Mapping[str, Any], index: int) -> list[CorpusValidationIssue]:
    case_id = str(case.get("id") or case.get("case_id") or f"case-{index}")
    text = _case_text(case)
    issues: list[CorpusValidationIssue] = []

    if not _has_citation(case, text):
        issues.append(CorpusValidationIssue(case_id, "missing_citation", "prompt case must include source citations"))

    for code, message, patterns in (
        ("private_case_fact", "prompt case includes private case facts", _PRIVATE_FACT_PATTERNS),
        ("local_private_path", "prompt case includes a local private path", _LOCAL_PATH_PATTERNS),
        ("outcome_guarantee", "prompt case guarantees a legal or permitting outcome", _OUTCOME_GUARANTEE_PATTERNS),
        ("raw_artifact_reference", "prompt case references raw crawl, download, or archive artifacts", _RAW_ARTIFACT_PATTERNS),
        ("live_execution_claim", "prompt case claims live LLM or DevHub execution", _LIVE_EXECUTION_PATTERNS),
    ):
        if _matches_any(text, patterns):
            issues.append(CorpusValidationIssue(case_id, code, message))

    refusal_required = _matches_any(text, _REFUSAL_REQUIRED_PATTERNS) or _has_enabled_consequential_control(case)
    if refusal_required and not _expects_refusal(case):
        issues.append(CorpusValidationIssue(case_id, "missing_refusal_expectation", "unsafe prompt case must expect refusal"))

    if _has_enabled_consequential_control(case):
        issues.append(CorpusValidationIssue(case_id, "enabled_consequential_control", "payment, upload, submission, scheduling, cancellation, and certification controls must not be enabled"))

    return issues


def _case_text(case: Mapping[str, Any]) -> str:
    parts: list[str] = []
    for key in ("prompt", "input", "user_prompt", "expected", "expected_response", "notes"):
        value = case.get(key)
        if isinstance(value, str):
            parts.append(value)
    messages = case.get("messages")
    if isinstance(messages, list):
        for message in messages:
            if isinstance(message, Mapping) and isinstance(message.get("content"), str):
                parts.append(message["content"])
            elif isinstance(message, str):
                parts.append(message)
    return "\n".join(parts)


def _has_citation(case: Mapping[str, Any], text: str) -> bool:
    for key in ("citations", "citation_ids", "source_evidence_ids", "source_ids"):
        value = case.get(key)
        if isinstance(value, list) and value:
            return True
    return bool(_CITATION_MARKER_RE.search(text))


def _expects_refusal(case: Mapping[str, Any]) -> bool:
    for key in ("expected_refusal", "refusal_expected", "must_refuse"):
        if case.get(key) is True:
            return True
    expectation = case.get("expectation") or case.get("expected_behavior")
    return isinstance(expectation, str) and "refus" in expectation.lower()


def _has_enabled_consequential_control(case: Mapping[str, Any]) -> bool:
    controls = case.get("controls") or case.get("ui_controls") or case.get("actions") or []
    if not isinstance(controls, list):
        return False
    return any(_control_is_enabled_consequential(control) for control in controls)


def _control_is_enabled_consequential(control: Any) -> bool:
    if isinstance(control, str):
        text = control.lower()
        return "enabled" in text and any(kind in text for kind in CONSEQUENTIAL_CONTROL_KINDS)
    if not isinstance(control, Mapping):
        return False
    enabled = control.get("enabled", control.get("is_enabled", control.get("available")))
    if enabled is not True:
        return False
    kind_text = " ".join(
        str(control.get(key, ""))
        for key in ("kind", "type", "name", "label", "action", "control_id")
    ).lower()
    return any(kind in kind_text for kind in CONSEQUENTIAL_CONTROL_KINDS)


def _matches_any(text: str, patterns: Iterable[re.Pattern[str]]) -> bool:
    return any(pattern.search(text) for pattern in patterns)
