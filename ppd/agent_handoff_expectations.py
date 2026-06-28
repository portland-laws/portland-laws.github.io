"""Validation for PP&D agent handoff transcript expectation matrices.

The validator is intentionally schema-tolerant because expectation matrices are
handoff artifacts produced by multiple supervisors. It checks for safety signals
that must never appear in committed PP&D expectations, regardless of the exact
column names used by a matrix producer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import re
from typing import Any, Iterable, Mapping, Sequence


_CITATION_KEYS = (
    "citation",
    "citations",
    "source_citation",
    "source_citations",
    "source_evidence_id",
    "source_evidence_ids",
    "evidence",
    "evidence_ids",
    "source_ids",
)

_EXPECTED_RESPONSE_KEYS = (
    "expected_response",
    "expected_agent_response",
    "expected_answer",
    "expected_text",
    "response",
)

_MANUAL_HANDOFF_TERMS = (
    "manual handoff",
    "human handoff",
    "attended handoff",
    "user handoff",
    "requires attendance",
    "requires user attendance",
    "manual only",
    "human must",
    "user must",
)

_MANUAL_TRIGGER_TERMS = (
    "mfa",
    "captcha",
    "account creation",
    "password recovery",
    "password reset",
    "payment",
    "submit payment",
    "certification",
    "certify",
    "official upload",
    "upload correction",
    "schedule inspection",
    "cancel inspection",
    "withdraw",
    "reactivation",
    "extension request",
)

_GUARANTEE_PATTERNS = (
    re.compile(r"\b(will|guarantee[sd]?|ensures?|certainly|definitely)\b.*\b(approve[sd]?|approval|permit|issuance|issued|pass(?:es)? inspection|legal(?:ly)? compliant|code compliant)\b", re.IGNORECASE),
    re.compile(r"\b(permit|application|inspection|plans?)\b.*\b(will|guarantee[sd]?|ensures?|certainly|definitely)\b.*\b(approve[sd]?|pass|be issued|succeed)\b", re.IGNORECASE),
    re.compile(r"\b(no risk|cannot be denied|must be approved|legally guaranteed)\b", re.IGNORECASE),
)

_PRIVATE_PATTERNS = (
    re.compile(r"/(?:home|Users)/[^\s'\"<>]+"),
    re.compile(r"[A-Za-z]:\\Users\\[^\s'\"<>]+"),
    re.compile(r"\b(?:password|passwd|secret|api[_-]?key|access[_-]?token|refresh[_-]?token|cookie|session[_-]?id)\b\s*[:=]", re.IGNORECASE),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
)

_LIVE_LLM_KEYS = (
    "allow_live_llm",
    "execute_live_llm",
    "live_llm_execution",
    "use_live_llm",
    "use_live_model",
    "run_live_model",
    "call_live_llm",
)

_CONSEQUENTIAL_TERMS = (
    "submit",
    "certify",
    "upload correction",
    "official upload",
    "purchase permit",
    "schedule inspection",
    "cancel",
    "withdraw",
    "request extension",
    "reactivate",
    "enter payment",
    "submit payment",
    "pay fee",
    "payment",
)

_SAFE_DOWNGRADE_TERMS = (
    "safe",
    "allowed",
    "allow",
    "reversible",
    "draft",
    "autonomous",
    "can proceed",
    "agent may",
)

_BLOCKED_TERMS = (
    "blocked",
    "refused",
    "prohibited",
    "manual",
    "consequential",
    "financial",
    "unsupported",
)

_AUTOMATION_CLAIM_PATTERN = re.compile(
    r"\b(devhub|dev hub)\b.*\b(automate|automatic|autonomously|without user|unattended|submit|certify|upload|pay|payment|schedule|cancel|bypass|mfa|captcha|login|sign in)\b|"
    r"\b(automate|automatic|autonomously|without user|unattended|submit|certify|upload|pay|payment|schedule|cancel|bypass|mfa|captcha|login|sign in)\b.*\b(devhub|dev hub)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class HandoffMatrixIssue:
    """A deterministic validation issue for a handoff expectation matrix."""

    code: str
    path: str
    message: str


def validate_handoff_expectation_matrix(matrix: Mapping[str, Any]) -> list[HandoffMatrixIssue]:
    """Return all safety issues found in a PP&D handoff expectation matrix."""

    issues: list[HandoffMatrixIssue] = []
    rows = _rows_from_matrix(matrix)
    sources_by_id = _sources_by_id(matrix.get("sources") or matrix.get("source_registry") or [])
    as_of = _parse_date(matrix.get("as_of") or matrix.get("verified_at") or matrix.get("matrix_date")) or date.today()
    max_age_days = _int_or_default(matrix.get("max_current_source_age_days"), 30)

    _validate_live_llm_flags(matrix, "$", issues)
    _validate_enabled_consequential_controls(matrix.get("controls") or matrix.get("action_controls") or [], "$.controls", issues)
    _validate_sources_currentness(sources_by_id.values(), as_of, max_age_days, issues)

    for index, row in enumerate(rows):
        path = f"$.expectations[{index}]"
        text = _flatten_text(row)
        expected_text = _expected_response_text(row)

        _validate_live_llm_flags(row, path, issues)
        _validate_enabled_consequential_controls(row.get("controls") or row.get("action_controls") or [], f"{path}.controls", issues)

        if expected_text and not _has_citation(row, sources_by_id):
            issues.append(HandoffMatrixIssue("uncited_expected_response", path, "Expected responses must cite public PP&D source evidence."))

        if _contains_guarantee(text):
            issues.append(HandoffMatrixIssue("outcome_guarantee", path, "Expected responses must not guarantee legal, permitting, inspection, or approval outcomes."))

        if _contains_private_value(text):
            issues.append(HandoffMatrixIssue("private_value_or_path", path, "Expectation matrices must not contain private values, credentials, or local private paths."))

        if _stale_source_marked_current(row, sources_by_id, as_of, max_age_days):
            issues.append(HandoffMatrixIssue("stale_source_marked_current", path, "A stale or old source is represented as current."))

        if _contains_blocked_action_downgrade(row, text):
            issues.append(HandoffMatrixIssue("blocked_action_downgrade", path, "Blocked, consequential, financial, or manual actions must not be downgraded to safe autonomous actions."))

        if _requires_manual_handoff(row, text) and not _mentions_manual_handoff(text):
            issues.append(HandoffMatrixIssue("missing_manual_handoff_expectation", path, "Manual-only or attended workflow triggers must include an explicit manual handoff expectation."))

        if _contains_devhub_automation_claim(text):
            issues.append(HandoffMatrixIssue("devhub_automation_claim", path, "Expectation matrices must not claim unattended DevHub automation for login or consequential controls."))

    return issues


def assert_valid_handoff_expectation_matrix(matrix: Mapping[str, Any]) -> None:
    """Raise ValueError when a handoff expectation matrix is unsafe."""

    issues = validate_handoff_expectation_matrix(matrix)
    if issues:
        detail = "; ".join(f"{issue.code} at {issue.path}: {issue.message}" for issue in issues)
        raise ValueError(detail)


def _rows_from_matrix(matrix: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    for key in ("expectations", "rows", "matrix", "cases", "examples"):
        value = matrix.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, Mapping)]
    return []


def _sources_by_id(sources: Any) -> dict[str, Mapping[str, Any]]:
    if not isinstance(sources, list):
        return {}
    result: dict[str, Mapping[str, Any]] = {}
    for source in sources:
        if not isinstance(source, Mapping):
            continue
        source_id = source.get("source_id") or source.get("id") or source.get("evidence_id")
        if source_id:
            result[str(source_id)] = source
    return result


def _validate_live_llm_flags(value: Mapping[str, Any], path: str, issues: list[HandoffMatrixIssue]) -> None:
    for key in _LIVE_LLM_KEYS:
        if value.get(key) is True:
            issues.append(HandoffMatrixIssue("live_llm_execution_flag", f"{path}.{key}", "Committed handoff expectation matrices must not enable live LLM execution."))


def _validate_enabled_consequential_controls(controls: Any, path: str, issues: list[HandoffMatrixIssue]) -> None:
    if not isinstance(controls, list):
        return
    for index, control in enumerate(controls):
        if not isinstance(control, Mapping) or control.get("enabled") is not True:
            continue
        text = _flatten_text(control).lower()
        action_type = str(control.get("action_type") or control.get("classification") or control.get("risk") or "").lower()
        if action_type in {"consequential", "financial", "official", "submission"} or any(term in text for term in _CONSEQUENTIAL_TERMS):
            issues.append(HandoffMatrixIssue("enabled_consequential_control", f"{path}[{index}]", "Consequential, official, or financial controls must not be enabled in committed expectations."))


def _validate_sources_currentness(sources: Iterable[Mapping[str, Any]], as_of: date, max_age_days: int, issues: list[HandoffMatrixIssue]) -> None:
    for source in sources:
        source_id = str(source.get("source_id") or source.get("id") or source.get("evidence_id") or "")
        if _source_marked_current(source) and _source_is_stale(source, as_of, max_age_days):
            issues.append(HandoffMatrixIssue("stale_source_marked_current", f"$.sources[{source_id}]", "Source registry entry is marked current but is stale by status or verification date."))


def _expected_response_text(row: Mapping[str, Any]) -> str:
    parts = []
    for key in _EXPECTED_RESPONSE_KEYS:
        value = row.get(key)
        if isinstance(value, str):
            parts.append(value)
    return "\n".join(parts).strip()


def _has_citation(row: Mapping[str, Any], sources_by_id: Mapping[str, Mapping[str, Any]]) -> bool:
    values: list[Any] = []
    for key in _CITATION_KEYS:
        if key in row:
            values.append(row[key])
    for value in values:
        for citation in _iter_scalar_values(value):
            if not citation:
                continue
            citation_text = str(citation).strip()
            if citation_text.startswith("http://") or citation_text.startswith("https://"):
                return True
            if citation_text in sources_by_id:
                return True
            if re.match(r"^[A-Za-z0-9_.:-]+$", citation_text):
                return True
    return False


def _flatten_text(value: Any) -> str:
    parts = [str(item) for item in _iter_scalar_values(value) if item is not None]
    return "\n".join(parts)


def _iter_scalar_values(value: Any) -> Iterable[Any]:
    if isinstance(value, Mapping):
        for nested in value.values():
            yield from _iter_scalar_values(nested)
    elif isinstance(value, list | tuple | set):
        for nested in value:
            yield from _iter_scalar_values(nested)
    elif isinstance(value, str | int | float | bool):
        yield value


def _contains_guarantee(text: str) -> bool:
    return any(pattern.search(text) for pattern in _GUARANTEE_PATTERNS)


def _contains_private_value(text: str) -> bool:
    return any(pattern.search(text) for pattern in _PRIVATE_PATTERNS)


def _stale_source_marked_current(row: Mapping[str, Any], sources_by_id: Mapping[str, Mapping[str, Any]], as_of: date, max_age_days: int) -> bool:
    row_sources = row.get("sources") or row.get("source_refs") or row.get("source_citations") or row.get("source_evidence_ids") or []
    for source_ref in _iter_scalar_values(row_sources):
        source = sources_by_id.get(str(source_ref))
        if source and _source_marked_current(source) and _source_is_stale(source, as_of, max_age_days):
            return True
    return _source_marked_current(row) and _source_is_stale(row, as_of, max_age_days)


def _source_marked_current(source: Mapping[str, Any]) -> bool:
    status = str(source.get("freshness_status") or source.get("status") or "").lower()
    return source.get("current") is True or source.get("is_current") is True or status == "current"


def _source_is_stale(source: Mapping[str, Any], as_of: date, max_age_days: int) -> bool:
    status = str(source.get("freshness_status") or source.get("status") or "").lower()
    if status in {"stale", "expired", "outdated"}:
        return True
    verified = _parse_date(source.get("last_verified_at") or source.get("verified_at") or source.get("last_seen_at"))
    if verified is None:
        return False
    return (as_of - verified).days > max_age_days


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).date() if value.tzinfo else value.date()
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).date()
    except ValueError:
        pass
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def _int_or_default(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _contains_blocked_action_downgrade(row: Mapping[str, Any], text: str) -> bool:
    lower = text.lower()
    declared_policy = str(row.get("action_policy") or row.get("policy") or row.get("classification") or row.get("risk") or "").lower()
    blocked = any(term in declared_policy for term in _BLOCKED_TERMS) or any(term in lower for term in _BLOCKED_TERMS)
    consequential = any(term in lower for term in _CONSEQUENTIAL_TERMS)
    downgraded = any(term in lower for term in _SAFE_DOWNGRADE_TERMS)
    return downgraded and (blocked or consequential)


def _requires_manual_handoff(row: Mapping[str, Any], text: str) -> bool:
    lower = text.lower()
    if row.get("requires_manual_handoff") is True or row.get("requires_attendance") is True:
        return True
    action_policy = str(row.get("action_policy") or row.get("policy") or row.get("classification") or "").lower()
    if "manual" in action_policy or "unsupported" in action_policy:
        return True
    return any(term in lower for term in _MANUAL_TRIGGER_TERMS)


def _mentions_manual_handoff(text: str) -> bool:
    lower = text.lower()
    return any(term in lower for term in _MANUAL_HANDOFF_TERMS)


def _contains_devhub_automation_claim(text: str) -> bool:
    return bool(_AUTOMATION_CLAIM_PATTERN.search(text))
