"""Fixture-first requirement extraction delta packet v1.

This module intentionally consumes only caller-provided synthetic rows. It does not
crawl, download, OCR, open DevHub, or mutate any active PP&D requirement state.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

ALLOWED_DOCUMENT_TYPES = {"public_html", "public_pdf", "public_form"}
ALLOWED_CHANGE_TYPES = {"added", "changed", "removed"}
DEFAULT_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/requirement_extraction_delta_packet_v1.py"],
    ["python3", "-m", "py_compile", "ppd/tests/test_requirement_extraction_delta_packet_v1.py"],
    ["python3", "-m", "unittest", "ppd.tests.test_requirement_extraction_delta_packet_v1"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]


@dataclass(frozen=True)
class SyntheticDocumentRow:
    document_id: str
    source_id: str
    canonical_url: str
    title: str
    document_type: str
    change_type: str
    content_hash: str
    previous_content_hash: str | None
    stale_evidence_ids: tuple[str, ...]
    extracted_statements: tuple[dict[str, Any], ...]


def load_changed_document_rows(path: str | Path) -> list[dict[str, Any]]:
    """Load synthetic changed document rows from a committed fixture file."""
    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    rows = payload.get("changed_document_rows", payload)
    if not isinstance(rows, list):
        raise ValueError("changed document fixture must contain a list of rows")
    return rows


def build_requirement_extraction_delta_packet_v1(
    changed_document_rows: list[dict[str, Any]],
    *,
    packet_id: str = "requirement-extraction-delta-packet-v1-fixture",
    generated_at: str = "2026-05-31T00:00:00Z",
) -> dict[str, Any]:
    """Build a deterministic offline delta packet from synthetic document rows."""
    normalized_rows = [_normalize_row(row) for row in changed_document_rows]
    candidates: list[dict[str, Any]] = []
    evidence_refs: list[dict[str, Any]] = []
    confidence_rows: list[dict[str, Any]] = []
    human_review_rows: list[dict[str, Any]] = []
    stale_evidence_impacts: list[dict[str, Any]] = []

    for row in normalized_rows:
        operation = _candidate_operation(row.change_type)
        if row.stale_evidence_ids:
            stale_evidence_impacts.append(_build_stale_impact(row))

        if row.change_type == "removed" and not row.extracted_statements:
            candidate_id = _stable_id("candidate", row.document_id, row.content_hash, "removed")
            candidates.append(
                {
                    "candidate_id": candidate_id,
                    "operation": "remove",
                    "document_id": row.document_id,
                    "source_id": row.source_id,
                    "canonical_url": row.canonical_url,
                    "requirement_type": "unknown",
                    "subject": "previously extracted requirement",
                    "action": "remove stale requirement candidate",
                    "object": row.title,
                    "conditions": [],
                    "deadline_or_temporal_scope": None,
                    "permit_types": [],
                    "process_stage": None,
                    "source_evidence_ids": [],
                    "human_review_status": "needs_human_review",
                    "formalization_status": "candidate_only",
                }
            )
            confidence_rows.append(_confidence_row(candidate_id, 0.2, "removed row has no replacement evidence"))
            human_review_rows.append(_human_review_row(candidate_id, "needs_human_review", "removed public document row"))
            continue

        for index, statement in enumerate(row.extracted_statements):
            candidate_id = _stable_id("candidate", row.document_id, row.content_hash, str(index), operation)
            evidence_id = _stable_id("evidence", row.document_id, row.content_hash, str(index))
            evidence_refs.append(_evidence_ref(evidence_id, row, statement, index))
            candidates.append(_candidate(candidate_id, operation, row, statement, evidence_id))
            confidence_rows.append(_confidence_row(candidate_id, _confidence(statement), _confidence_reason(statement)))
            human_review_rows.append(_human_review_row(candidate_id, _review_status(statement), _review_reason(statement)))

    return {
        "packet_version": "requirement_extraction_delta_packet_v1",
        "packet_id": packet_id,
        "generated_at": generated_at,
        "source_mode": "synthetic_fixture_only",
        "side_effects": {
            "live_sources_extracted": False,
            "ocr_ran": False,
            "documents_downloaded": False,
            "devhub_opened": False,
            "active_requirements_mutated": False,
        },
        "changed_document_count": len(normalized_rows),
        "requirement_candidates": candidates,
        "source_evidence_refs": evidence_refs,
        "confidence_rows": confidence_rows,
        "human_review_rows": human_review_rows,
        "stale_evidence_impacts": stale_evidence_impacts,
        "validation_commands": DEFAULT_VALIDATION_COMMANDS,
    }


def _normalize_row(row: dict[str, Any]) -> SyntheticDocumentRow:
    required = ["document_id", "source_id", "canonical_url", "title", "document_type", "change_type", "content_hash"]
    for key in required:
        if not row.get(key):
            raise ValueError(f"missing required changed document row field: {key}")

    document_type = str(row["document_type"])
    if document_type not in ALLOWED_DOCUMENT_TYPES:
        raise ValueError(f"unsupported synthetic document_type: {document_type}")

    change_type = str(row["change_type"])
    if change_type not in ALLOWED_CHANGE_TYPES:
        raise ValueError(f"unsupported synthetic change_type: {change_type}")

    statements = row.get("extracted_statements", [])
    if not isinstance(statements, list):
        raise ValueError("extracted_statements must be a list")

    stale_ids = row.get("stale_evidence_ids", [])
    if not isinstance(stale_ids, list):
        raise ValueError("stale_evidence_ids must be a list")

    return SyntheticDocumentRow(
        document_id=str(row["document_id"]),
        source_id=str(row["source_id"]),
        canonical_url=str(row["canonical_url"]),
        title=str(row["title"]),
        document_type=document_type,
        change_type=change_type,
        content_hash=str(row["content_hash"]),
        previous_content_hash=str(row["previous_content_hash"]) if row.get("previous_content_hash") else None,
        stale_evidence_ids=tuple(str(value) for value in stale_ids),
        extracted_statements=tuple(dict(statement) for statement in statements),
    )


def _candidate_operation(change_type: str) -> str:
    if change_type == "added":
        return "add"
    if change_type == "changed":
        return "change"
    return "remove"


def _candidate(
    candidate_id: str,
    operation: str,
    row: SyntheticDocumentRow,
    statement: dict[str, Any],
    evidence_id: str,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "operation": operation,
        "document_id": row.document_id,
        "source_id": row.source_id,
        "canonical_url": row.canonical_url,
        "requirement_type": str(statement.get("requirement_type", "obligation")),
        "subject": str(statement.get("subject", "applicant")),
        "action": str(statement.get("action", "review requirement")),
        "object": str(statement.get("object", row.title)),
        "conditions": list(statement.get("conditions", [])),
        "deadline_or_temporal_scope": statement.get("deadline_or_temporal_scope"),
        "permit_types": list(statement.get("permit_types", [])),
        "process_stage": statement.get("process_stage"),
        "source_evidence_ids": [evidence_id],
        "human_review_status": _review_status(statement),
        "formalization_status": "candidate_only",
    }


def _evidence_ref(
    evidence_id: str,
    row: SyntheticDocumentRow,
    statement: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    return {
        "source_evidence_id": evidence_id,
        "document_id": row.document_id,
        "source_id": row.source_id,
        "canonical_url": row.canonical_url,
        "document_type": row.document_type,
        "title": row.title,
        "content_hash": row.content_hash,
        "previous_content_hash": row.previous_content_hash,
        "locator": statement.get("locator", f"synthetic_statement[{index}]"),
        "quote": str(statement.get("quote", "")),
        "extraction_method": "fixture_provided_statement",
    }


def _confidence_row(candidate_id: str, confidence: float, reason: str) -> dict[str, Any]:
    bounded = max(0.0, min(1.0, float(confidence)))
    return {
        "candidate_id": candidate_id,
        "confidence": bounded,
        "confidence_band": _confidence_band(bounded),
        "reason": reason,
    }


def _confidence(statement: dict[str, Any]) -> float:
    value = statement.get("confidence", 0.55)
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.55


def _confidence_band(value: float) -> str:
    if value >= 0.8:
        return "high"
    if value >= 0.55:
        return "medium"
    return "low"


def _confidence_reason(statement: dict[str, Any]) -> str:
    reason = statement.get("confidence_reason")
    if reason:
        return str(reason)
    if statement.get("quote"):
        return "synthetic fixture statement includes source quote"
    return "synthetic fixture statement lacks quote"


def _human_review_row(candidate_id: str, status: str, reason: str) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id,
        "human_review_status": status,
        "reason": reason,
    }


def _review_status(statement: dict[str, Any]) -> str:
    value = statement.get("human_review_status")
    if value in {"ready_for_review", "needs_human_review", "blocked"}:
        return str(value)
    if _confidence(statement) >= 0.8 and statement.get("quote"):
        return "ready_for_review"
    return "needs_human_review"


def _review_reason(statement: dict[str, Any]) -> str:
    reason = statement.get("human_review_reason")
    if reason:
        return str(reason)
    if _review_status(statement) == "ready_for_review":
        return "high-confidence synthetic statement with evidence quote"
    return "candidate requires PP&D reviewer confirmation before formalization"


def _build_stale_impact(row: SyntheticDocumentRow) -> dict[str, Any]:
    return {
        "document_id": row.document_id,
        "source_id": row.source_id,
        "canonical_url": row.canonical_url,
        "change_type": row.change_type,
        "previous_content_hash": row.previous_content_hash,
        "content_hash": row.content_hash,
        "stale_evidence_ids": list(row.stale_evidence_ids),
        "impact": "linked evidence must be re-reviewed before dependent requirements are trusted",
        "mutates_active_requirements": False,
    }


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"
