"""Deterministic citation integrity validation for committed PP&D fixtures.

The validator is intentionally small: it checks only citation/source/span
relationships that can be proven from local JSON fixtures. It does not fetch
network content and it rejects authenticated/private evidence in commit-safe
outputs.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

PUBLIC_PRIVACY_VALUES = {"public", "public_record", "public_website", "commit_safe_public"}
PRIVATE_SOURCE_TYPES = {"devhub_authenticated", "authenticated", "private_authenticated"}
PRIVATE_PRIVACY_VALUES = {"private", "authenticated", "private_authenticated", "restricted", "credentialed"}


@dataclass(frozen=True)
class CitationFailure:
    """A deterministic citation validation failure."""

    code: str
    message: str
    citation_id: str
    source_id: Optional[str] = None
    span_id: Optional[str] = None

    def as_dict(self) -> Dict[str, Optional[str]]:
        return {
            "code": self.code,
            "message": self.message,
            "citation_id": self.citation_id,
            "source_id": self.source_id,
            "span_id": self.span_id,
        }


class CitationIntegrityError(ValueError):
    """Raised when one or more citation integrity checks fail."""

    def __init__(self, failures: Sequence[CitationFailure]) -> None:
        self.failures = list(failures)
        super().__init__("; ".join(f"{failure.code}:{failure.citation_id}" for failure in self.failures))


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _items(payload: Any, keys: Sequence[str]) -> List[Mapping[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, Mapping)]
    if isinstance(payload, Mapping):
        for key in keys:
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, Mapping)]
        return [payload]
    return []


def _string(value: Any) -> Optional[str]:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def _citation_id(item: Mapping[str, Any], fallback: str) -> str:
    for key in ("citation_id", "evidence_id", "requirement_id", "id"):
        value = _string(item.get(key))
        if value:
            return value
    return fallback


def _source_records(source_payload: Any) -> Dict[str, Mapping[str, Any]]:
    records: Dict[str, Mapping[str, Any]] = {}
    for item in _items(source_payload, ("sources", "source_registry", "records")):
        source_id = _string(item.get("source_id"))
        if source_id:
            records[source_id] = item
    return records


def _span_records(document_payload: Any) -> Dict[Tuple[str, str], Mapping[str, Any]]:
    spans: Dict[Tuple[str, str], Mapping[str, Any]] = {}
    for document in _items(document_payload, ("documents", "document_records", "records")):
        document_source_id = _string(document.get("source_id"))
        for span in document.get("citation_spans", []) or []:
            if not isinstance(span, Mapping):
                continue
            span_id = _string(span.get("span_id") or span.get("id") or span.get("citation_span_id"))
            source_id = _string(span.get("source_id")) or document_source_id
            if span_id and source_id:
                spans[(source_id, span_id)] = span
    return spans


def _private_source(record: Mapping[str, Any]) -> bool:
    source_type = (_string(record.get("source_type")) or "").lower()
    privacy = (_string(record.get("privacy_classification")) or "").lower()
    auth_scope = (_string(record.get("auth_scope")) or "").lower()
    if source_type in PRIVATE_SOURCE_TYPES:
        return True
    if privacy in PRIVATE_PRIVACY_VALUES:
        return True
    if auth_scope and auth_scope not in {"public", "anonymous"}:
        return True
    if privacy and privacy not in PUBLIC_PRIVACY_VALUES:
        return True
    return False


def _reference_from_string(value: str) -> Tuple[Optional[str], Optional[str]]:
    if "#" in value:
        source_id, span_id = value.split("#", 1)
        return _string(source_id), _string(span_id)
    return None, _string(value)


def _citation_references(item: Mapping[str, Any]) -> List[Tuple[str, Optional[str], Optional[str]]]:
    citation_id = _citation_id(item, "citation")
    references: List[Tuple[str, Optional[str], Optional[str]]] = []

    direct_source = _string(item.get("source_id"))
    direct_span = _string(item.get("span_id") or item.get("citation_span_id"))
    if direct_source or direct_span:
        references.append((citation_id, direct_source, direct_span))

    for key in ("source_evidence_ids", "evidence_ids", "citation_ids"):
        values = item.get(key)
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list):
            continue
        for index, value in enumerate(values):
            ref_id = f"{citation_id}.{key}[{index}]"
            if isinstance(value, str):
                source_id, span_id = _reference_from_string(value)
                references.append((ref_id, source_id, span_id))
            elif isinstance(value, Mapping):
                references.append((
                    _citation_id(value, ref_id),
                    _string(value.get("source_id")),
                    _string(value.get("span_id") or value.get("citation_span_id")),
                ))

    citations = item.get("citations")
    if isinstance(citations, list):
        for index, citation in enumerate(citations):
            if isinstance(citation, Mapping):
                references.append((
                    _citation_id(citation, f"{citation_id}.citations[{index}]"),
                    _string(citation.get("source_id")),
                    _string(citation.get("span_id") or citation.get("citation_span_id")),
                ))

    return references


def validate_citation_integrity(source_payload: Any, document_payload: Any, citation_payload: Any) -> List[CitationFailure]:
    """Return deterministic citation integrity failures for local fixture data."""
    sources = _source_records(source_payload)
    spans = _span_records(document_payload)
    failures: List[CitationFailure] = []

    citation_items = _items(citation_payload, ("citations", "requirements", "requirement_nodes", "evidence", "records"))
    for index, item in enumerate(citation_items):
        references = _citation_references(item)
        if not references:
            citation_id = _citation_id(item, f"citation[{index}]")
            failures.append(CitationFailure(
                code="missing_span",
                message="Citation does not identify a source_id and span_id pair.",
                citation_id=citation_id,
            ))
            continue

        for citation_id, source_id, span_id in references:
            if not source_id or source_id not in sources:
                failures.append(CitationFailure(
                    code="stale_source_id",
                    message="Citation references a source_id that is not present in the committed source registry fixture.",
                    citation_id=citation_id,
                    source_id=source_id,
                    span_id=span_id,
                ))
                continue

            if _private_source(sources[source_id]):
                failures.append(CitationFailure(
                    code="private_authenticated_evidence",
                    message="Citation references authenticated or private evidence that cannot be committed as PP&D fixture evidence.",
                    citation_id=citation_id,
                    source_id=source_id,
                    span_id=span_id,
                ))

            if not span_id or (source_id, span_id) not in spans:
                failures.append(CitationFailure(
                    code="missing_span",
                    message="Citation references a span_id that is not present for the source in committed document fixtures.",
                    citation_id=citation_id,
                    source_id=source_id,
                    span_id=span_id,
                ))

    return failures


def validate_citation_integrity_files(source_registry_path: Path, document_records_path: Path, citations_path: Path) -> List[CitationFailure]:
    return validate_citation_integrity(
        _load_json(source_registry_path),
        _load_json(document_records_path),
        _load_json(citations_path),
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate PP&D citation/source/span fixture integrity.")
    parser.add_argument("source_registry", type=Path)
    parser.add_argument("document_records", type=Path)
    parser.add_argument("citations", type=Path)
    args = parser.parse_args(argv)

    failures = validate_citation_integrity_files(args.source_registry, args.document_records, args.citations)
    result = {"ok": not failures, "failures": [failure.as_dict() for failure in failures]}
    print(json.dumps(result, sort_keys=True, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
