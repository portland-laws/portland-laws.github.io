"""Deterministic case-to-process gap reporting for PP&D fixtures.

The report combines fixture-shaped outputs from the user case store,
process bundle, document compliance, source freshness, and citation
integrity checks. It intentionally reports only prompts that need safe
human follow-up: missing, stale, ambiguous, or conflicting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

ACTION_BY_STATUS = {
    "missing": "Collect the missing fixture field or source-backed document before advancing the process.",
    "stale": "Refresh the cited public source fixture and re-run validation before relying on it.",
    "ambiguous": "Compare the fixture evidence and record the PP&D-safe interpretation before proceeding.",
    "conflicting": "Do not choose a winner automatically; preserve both fixture values and escalate for manual review.",
}

STATUS_ORDER = {
    "conflicting": 0,
    "missing": 1,
    "stale": 2,
    "ambiguous": 3,
}

SOURCE_NAMES = {
    "case_store": "user case store",
    "process_bundle": "process bundle",
    "document_compliance": "document compliance",
    "source_freshness": "source freshness",
    "citation_integrity": "citation integrity",
}

REQUIRED_FIELDS = {
    "case_store": ("case_id", "permit_type", "site_address"),
    "process_bundle": ("process_id", "required_documents", "milestones"),
}


@dataclass(frozen=True)
class Gap:
    prompt_id: str
    status: str
    source: str
    prompt: str
    evidence: tuple[str, ...]
    safe_next_action: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "prompt_id": self.prompt_id,
            "status": self.status,
            "source": self.source,
            "prompt": self.prompt,
            "evidence": list(self.evidence),
            "safe_next_action": self.safe_next_action,
        }


def build_case_process_gap_report(inputs: dict[str, Any]) -> dict[str, Any]:
    """Return only missing, stale, ambiguous, or conflicting prompts.

    The input is deliberately plain JSON data so tests and callers can use
    committed fixtures without importing crawler or DevHub automation code.
    """
    gaps: list[Gap] = []
    gaps.extend(_required_field_gaps(inputs))
    gaps.extend(_document_compliance_gaps(inputs.get("document_compliance", {})))
    gaps.extend(_source_freshness_gaps(inputs.get("source_freshness", {})))
    gaps.extend(_citation_integrity_gaps(inputs.get("citation_integrity", {})))
    gaps.extend(_explicit_prompt_gaps(inputs))

    unique = {_gap_key(gap): gap for gap in gaps}
    ordered = sorted(unique.values(), key=_sort_key)
    return {
        "case_id": _case_id(inputs),
        "gap_count": len(ordered),
        "gaps": [gap.as_dict() for gap in ordered],
    }


def _required_field_gaps(inputs: dict[str, Any]) -> list[Gap]:
    gaps: list[Gap] = []
    for section, fields in REQUIRED_FIELDS.items():
        values = inputs.get(section, {})
        for field in fields:
            value = values.get(field) if isinstance(values, dict) else None
            if _is_blank(value):
                gaps.append(
                    _gap(
                        prompt_id=f"{section}.{field}",
                        status="missing",
                        source=section,
                        prompt=f"Provide {field.replace('_', ' ')} for the {SOURCE_NAMES[section]}.",
                        evidence=[f"{section}.{field} is missing or blank"],
                    )
                )
    return gaps


def _document_compliance_gaps(section: Any) -> list[Gap]:
    gaps: list[Gap] = []
    documents = section.get("documents", []) if isinstance(section, dict) else []
    for doc in _dicts(documents):
        status = _normalized_status(doc.get("status"))
        if status not in ACTION_BY_STATUS:
            continue
        name = str(doc.get("name") or doc.get("id") or "document")
        gaps.append(
            _gap(
                prompt_id=f"document.{doc.get('id') or _slug(name)}",
                status=status,
                source="document_compliance",
                prompt=f"Resolve {name} document compliance status: {status}.",
                evidence=_evidence(doc, fallback=f"{name} status is {status}"),
            )
        )
    return gaps


def _source_freshness_gaps(section: Any) -> list[Gap]:
    gaps: list[Gap] = []
    sources = section.get("sources", []) if isinstance(section, dict) else []
    for source in _dicts(sources):
        status = _normalized_status(source.get("status"))
        if status not in {"stale", "missing", "ambiguous", "conflicting"}:
            continue
        label = str(source.get("label") or source.get("id") or "source")
        checked_at = source.get("checked_at") or "unknown check time"
        gaps.append(
            _gap(
                prompt_id=f"source.{source.get('id') or _slug(label)}",
                status=status,
                source="source_freshness",
                prompt=f"Refresh or verify source freshness for {label}.",
                evidence=_evidence(source, fallback=f"{label} is {status}; checked_at={checked_at}"),
            )
        )
    return gaps


def _citation_integrity_gaps(section: Any) -> list[Gap]:
    gaps: list[Gap] = []
    citations = section.get("citations", []) if isinstance(section, dict) else []
    for citation in _dicts(citations):
        status = _normalized_status(citation.get("status"))
        if status not in ACTION_BY_STATUS:
            continue
        label = str(citation.get("claim_id") or citation.get("id") or "citation")
        gaps.append(
            _gap(
                prompt_id=f"citation.{label}",
                status=status,
                source="citation_integrity",
                prompt=f"Repair citation integrity for {label}.",
                evidence=_evidence(citation, fallback=f"{label} citation status is {status}"),
            )
        )
    return gaps


def _explicit_prompt_gaps(inputs: dict[str, Any]) -> list[Gap]:
    gaps: list[Gap] = []
    for section_name in SOURCE_NAMES:
        section = inputs.get(section_name, {})
        prompts = section.get("prompts", []) if isinstance(section, dict) else []
        for prompt in _dicts(prompts):
            status = _normalized_status(prompt.get("status"))
            if status not in ACTION_BY_STATUS:
                continue
            prompt_id = str(prompt.get("id") or prompt.get("prompt_id") or _slug(str(prompt.get("prompt") or status)))
            gaps.append(
                _gap(
                    prompt_id=f"{section_name}.{prompt_id}",
                    status=status,
                    source=section_name,
                    prompt=str(prompt.get("prompt") or f"Resolve {status} prompt from {SOURCE_NAMES[section_name]}."),
                    evidence=_evidence(prompt, fallback=f"{SOURCE_NAMES[section_name]} prompt status is {status}"),
                )
            )
    return gaps


def _gap(prompt_id: str, status: str, source: str, prompt: str, evidence: Iterable[str]) -> Gap:
    return Gap(
        prompt_id=prompt_id,
        status=status,
        source=SOURCE_NAMES[source],
        prompt=prompt,
        evidence=tuple(str(item) for item in evidence if not _is_blank(item)),
        safe_next_action=ACTION_BY_STATUS[status],
    )


def _normalized_status(value: Any) -> str:
    return str(value or "").strip().lower()


def _evidence(item: dict[str, Any], fallback: str) -> list[str]:
    evidence = item.get("evidence")
    if isinstance(evidence, list):
        return [str(value) for value in evidence if not _is_blank(value)] or [fallback]
    if isinstance(evidence, str) and evidence.strip():
        return [evidence]
    detail = item.get("detail") or item.get("reason")
    return [str(detail)] if not _is_blank(detail) else [fallback]


def _dicts(values: Any) -> Iterable[dict[str, Any]]:
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, dict)]


def _is_blank(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _case_id(inputs: dict[str, Any]) -> str | None:
    case_store = inputs.get("case_store", {})
    if isinstance(case_store, dict) and not _is_blank(case_store.get("case_id")):
        return str(case_store["case_id"])
    return None


def _gap_key(gap: Gap) -> tuple[str, str, str]:
    return (gap.prompt_id, gap.status, gap.source)


def _sort_key(gap: Gap) -> tuple[int, str, str]:
    return (STATUS_ORDER[gap.status], gap.source, gap.prompt_id)


def _slug(value: str) -> str:
    cleaned = []
    previous_dash = False
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
            previous_dash = False
        elif not previous_dash:
            cleaned.append("-")
            previous_dash = True
    return "".join(cleaned).strip("-") or "item"
