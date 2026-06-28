"""Deterministic fixture-only evidence-pack assembly for PP&D tasks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


UTC = timezone.utc


@dataclass(frozen=True)
class FixtureDocument:
    id: str
    title: str
    url: str
    captured_at: datetime
    text: str

    @classmethod
    def from_mapping(cls, data: dict[str, Any], source: Path) -> "FixtureDocument":
        missing = [key for key in ("id", "title", "url", "captured_at", "text") if not data.get(key)]
        if missing:
            raise ValueError(f"{source} is missing required field(s): {', '.join(missing)}")
        captured_at = _parse_utc_datetime(str(data["captured_at"]), f"{source}:captured_at")
        return cls(
            id=str(data["id"]),
            title=str(data["title"]),
            url=str(data["url"]),
            captured_at=captured_at,
            text=str(data["text"]),
        )


def load_fixture_documents(fixture_dir: str | Path) -> list[FixtureDocument]:
    """Load committed fixture documents in stable path order."""
    root = Path(fixture_dir)
    if not root.is_dir():
        raise ValueError(f"fixture directory does not exist: {root}")

    documents: list[FixtureDocument] = []
    seen_ids: set[str] = set()
    for path in sorted(root.glob("*.json"), key=lambda item: item.name):
        with path.open("r", encoding="utf-8") as handle:
            document = FixtureDocument.from_mapping(json.load(handle), path)
        if document.id in seen_ids:
            raise ValueError(f"duplicate fixture document id: {document.id}")
        seen_ids.add(document.id)
        documents.append(document)

    if not documents:
        raise ValueError(f"fixture directory contains no JSON documents: {root}")
    return documents


def assemble_evidence_pack(
    fixture_dir: str | Path,
    *,
    generated_at: str | datetime = "2026-05-12T00:00:00Z",
    max_age_days: int = 180,
    claims: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a deterministic evidence pack from committed fixture JSON only."""
    generated = _coerce_utc_datetime(generated_at, "generated_at")
    documents = load_fixture_documents(fixture_dir)
    by_id = {document.id: document for document in documents}

    if claims is None:
        claim_rows = [_default_claim(document) for document in documents]
    else:
        claim_rows = [dict(claim) for claim in claims]

    packed_claims = [_validate_claim(claim, by_id) for claim in claim_rows]
    packed_claims.sort(key=lambda claim: claim["id"])

    return {
        "schema_version": "ppd.evidence_pack.v1",
        "generated_at": _format_utc(generated),
        "source_mode": "committed-fixtures-only",
        "freshness": {
            "max_age_days": max_age_days,
            "oldest_captured_at": _format_utc(min(document.captured_at for document in documents)),
            "newest_captured_at": _format_utc(max(document.captured_at for document in documents)),
            "is_stale": any((generated - document.captured_at).days > max_age_days for document in documents),
        },
        "documents": [
            {
                "id": document.id,
                "title": document.title,
                "url": document.url,
                "captured_at": _format_utc(document.captured_at),
            }
            for document in sorted(documents, key=lambda item: item.id)
        ],
        "claims": packed_claims,
    }


def _default_claim(document: FixtureDocument) -> dict[str, Any]:
    quote = _first_nonempty_line(document.text)
    return {
        "id": f"claim:{document.id}",
        "text": f"Fixture document '{document.title}' is available as evidence.",
        "citations": [{"document_id": document.id, "quote": quote}],
    }


def _validate_claim(claim: dict[str, Any], documents: dict[str, FixtureDocument]) -> dict[str, Any]:
    claim_id = str(claim.get("id") or "").strip()
    text = str(claim.get("text") or "").strip()
    citations = claim.get("citations")
    if not claim_id or not text:
        raise ValueError("each claim requires non-empty id and text")
    if not isinstance(citations, list) or not citations:
        raise ValueError(f"claim {claim_id} requires at least one citation")

    packed_citations: list[dict[str, str]] = []
    for citation in citations:
        if not isinstance(citation, dict):
            raise ValueError(f"claim {claim_id} has a non-object citation")
        document_id = str(citation.get("document_id") or "").strip()
        quote = str(citation.get("quote") or "").strip()
        if document_id not in documents:
            raise ValueError(f"claim {claim_id} cites unknown document: {document_id}")
        if not quote:
            raise ValueError(f"claim {claim_id} cites {document_id} without a quote")
        if quote not in documents[document_id].text:
            raise ValueError(f"claim {claim_id} quote is not present in {document_id}")
        packed_citations.append({"document_id": document_id, "quote": quote})

    packed_citations.sort(key=lambda citation: (citation["document_id"], citation["quote"]))
    return {"id": claim_id, "text": text, "citations": packed_citations}


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    raise ValueError("fixture document text must contain at least one non-empty line")


def _coerce_utc_datetime(value: str | datetime, field_name: str) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    return _parse_utc_datetime(value, field_name)


def _parse_utc_datetime(value: str, field_name: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _format_utc(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
