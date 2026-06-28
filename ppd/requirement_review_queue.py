"""Fixture-first human review queue packets for PP&D candidate requirements.

This module intentionally does not run requirement extraction. It consumes already
structured, synthetic public document records plus source freshness badges and
builds a commit-safe packet for human review.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional


FRESHNESS_ADJUSTMENTS = {
    "fresh": 0.08,
    "current": 0.08,
    "monitor": 0.02,
    "unknown": -0.06,
    "stale": -0.14,
    "expired": -0.18,
}

REVIEWER_OWNER_BY_TYPE = {
    "action_gate": "ppd-guardrails-reviewer",
    "deadline": "ppd-process-reviewer",
    "document_requirement": "ppd-document-reviewer",
    "fee_trigger": "ppd-fee-reviewer",
    "license_requirement": "ppd-license-reviewer",
    "obligation": "ppd-requirements-reviewer",
    "precondition": "ppd-process-reviewer",
    "prohibition": "ppd-guardrails-reviewer",
}

ALLOWED_REQUIREMENT_TYPES = set(REVIEWER_OWNER_BY_TYPE)
RAW_TEXT_KEYS = {
    "body",
    "body_text",
    "content",
    "html",
    "markdown",
    "page_text",
    "raw",
    "raw_html",
    "raw_source_text",
    "text",
    "transcript",
}


@dataclass(frozen=True)
class ReviewQueuePacket:
    """Commit-safe packet containing only cited candidate requirement nodes."""

    packet_id: str
    generated_from_fixture: bool
    extraction_executed: bool
    requirements_changed: bool
    raw_source_text_stored: bool
    source_evidence_freshness_badges: List[Dict[str, Any]]
    candidate_requirement_nodes: List[Dict[str, Any]]
    deferred_formalization_notes: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "packet_id": self.packet_id,
            "generated_from_fixture": self.generated_from_fixture,
            "extraction_executed": self.extraction_executed,
            "requirements_changed": self.requirements_changed,
            "raw_source_text_stored": self.raw_source_text_stored,
            "source_evidence_freshness_badges": deepcopy(self.source_evidence_freshness_badges),
            "candidate_requirement_nodes": deepcopy(self.candidate_requirement_nodes),
            "deferred_formalization_notes": deepcopy(self.deferred_formalization_notes),
        }


def load_review_queue_fixture(path: Path) -> Dict[str, Any]:
    """Load and validate a deterministic synthetic review queue fixture."""

    data = json.loads(path.read_text(encoding="utf-8"))
    _assert_no_raw_source_text(data)
    return data


def build_human_review_queue_packet(fixture: Mapping[str, Any]) -> Dict[str, Any]:
    """Build cited candidate requirement nodes from synthetic structured records.

    The input is expected to contain source freshness badges and normalized public
    document records. Candidate requirements must already be represented as
    structured hints; this function does not inspect or extract raw source text.
    """

    _assert_no_raw_source_text(fixture)
    evidence_by_id = _index_evidence_badges(fixture.get("source_evidence_freshness_badges", []))
    documents = fixture.get("synthetic_public_document_records", [])
    if not isinstance(documents, list):
        raise ValueError("synthetic_public_document_records must be a list")

    candidates: List[Dict[str, Any]] = []
    deferred_notes: List[Dict[str, Any]] = []

    for document in documents:
        _assert_document_shape(document)
        hints = document.get("candidate_requirement_hints", [])
        if not isinstance(hints, list):
            raise ValueError("candidate_requirement_hints must be a list")
        for hint in hints:
            candidate = _candidate_from_hint(document, hint, evidence_by_id)
            candidates.append(candidate)
            deferred_notes.append(_deferred_note_for(candidate))

    candidates.sort(key=lambda item: item["requirement_id"])
    deferred_notes.sort(key=lambda item: item["requirement_id"])

    packet = ReviewQueuePacket(
        packet_id=_stable_packet_id(candidates),
        generated_from_fixture=True,
        extraction_executed=False,
        requirements_changed=False,
        raw_source_text_stored=False,
        source_evidence_freshness_badges=_public_badges(evidence_by_id.values()),
        candidate_requirement_nodes=candidates,
        deferred_formalization_notes=deferred_notes,
    )
    return packet.to_dict()


def _candidate_from_hint(
    document: Mapping[str, Any],
    hint: Mapping[str, Any],
    evidence_by_id: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    if not isinstance(hint, Mapping):
        raise ValueError("candidate requirement hints must be objects")

    requirement_type = str(hint.get("requirement_type", "")).strip()
    if requirement_type not in ALLOWED_REQUIREMENT_TYPES:
        raise ValueError(f"unsupported requirement_type: {requirement_type}")

    evidence_ids = [str(value) for value in hint.get("source_evidence_ids", [])]
    citations = [_citation_for(evidence_by_id[evidence_id]) for evidence_id in evidence_ids if evidence_id in evidence_by_id]
    confidence = _confidence_score(document, hint, citations, evidence_by_id)
    confidence_band = _confidence_band(confidence)
    review_reasons = _review_reasons(hint, citations, evidence_by_id, confidence_band)

    return {
        "requirement_id": _stable_requirement_id(document, hint),
        "requirement_type": requirement_type,
        "subject": _clean_scalar(hint.get("subject")),
        "action": _clean_scalar(hint.get("action")),
        "object": _clean_scalar(hint.get("object")),
        "conditions": _clean_list(hint.get("conditions", [])),
        "deadline_or_temporal_scope": _clean_scalar(hint.get("deadline_or_temporal_scope")),
        "permit_types": _clean_list(hint.get("permit_types", [])),
        "process_stage": _clean_scalar(hint.get("process_stage")),
        "source_evidence_ids": evidence_ids,
        "citations": citations,
        "confidence": confidence,
        "confidence_band": confidence_band,
        "human_review_status": "queued",
        "review_reasons": review_reasons,
        "reviewer_owner": REVIEWER_OWNER_BY_TYPE[requirement_type],
        "formalization_status": "deferred_pending_human_review",
        "deferred_formalization_note": _note_text(requirement_type, review_reasons),
    }


def _index_evidence_badges(badges: Any) -> Dict[str, Dict[str, Any]]:
    if not isinstance(badges, list):
        raise ValueError("source_evidence_freshness_badges must be a list")

    indexed: Dict[str, Dict[str, Any]] = {}
    for badge in badges:
        if not isinstance(badge, Mapping):
            raise ValueError("source evidence freshness badges must be objects")
        evidence_id = _clean_scalar(badge.get("source_evidence_id"))
        if not evidence_id:
            raise ValueError("source evidence badge missing source_evidence_id")
        indexed[evidence_id] = {
            "source_evidence_id": evidence_id,
            "source_id": _clean_scalar(badge.get("source_id")),
            "canonical_url": _clean_scalar(badge.get("canonical_url")),
            "freshness_status": _clean_scalar(badge.get("freshness_status")) or "unknown",
            "freshness_badge": _clean_scalar(badge.get("freshness_badge")) or "unknown",
            "last_verified_at": _clean_scalar(badge.get("last_verified_at")),
            "content_hash": _clean_scalar(badge.get("content_hash")),
            "location_ref": _clean_scalar(badge.get("location_ref")),
        }
    return indexed


def _citation_for(evidence: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "source_evidence_id": evidence["source_evidence_id"],
        "source_id": evidence.get("source_id", ""),
        "canonical_url": evidence.get("canonical_url", ""),
        "freshness_status": evidence.get("freshness_status", "unknown"),
        "freshness_badge": evidence.get("freshness_badge", "unknown"),
        "last_verified_at": evidence.get("last_verified_at", ""),
        "content_hash": evidence.get("content_hash", ""),
        "location_ref": evidence.get("location_ref", ""),
    }


def _confidence_score(
    document: Mapping[str, Any],
    hint: Mapping[str, Any],
    citations: List[Dict[str, Any]],
    evidence_by_id: Mapping[str, Mapping[str, Any]],
) -> float:
    base = float(hint.get("candidate_confidence", document.get("extraction_confidence", 0.5)))
    score = base
    score += min(len(citations), 3) * 0.03

    for evidence_id in hint.get("source_evidence_ids", []):
        evidence = evidence_by_id.get(str(evidence_id))
        if evidence is None:
            score -= 0.12
            continue
        freshness = str(evidence.get("freshness_status", "unknown")).lower()
        score += FRESHNESS_ADJUSTMENTS.get(freshness, -0.04)

    if hint.get("requires_inference") is True:
        score -= 0.08
    if not citations:
        score -= 0.18

    bounded = max(0.0, min(1.0, score))
    return round(bounded, 2)


def _confidence_band(score: float) -> str:
    if score >= 0.82:
        return "high"
    if score >= 0.62:
        return "medium"
    return "low"


def _review_reasons(
    hint: Mapping[str, Any],
    citations: List[Dict[str, Any]],
    evidence_by_id: Mapping[str, Mapping[str, Any]],
    confidence_band: str,
) -> List[str]:
    reasons: List[str] = []
    evidence_ids = [str(value) for value in hint.get("source_evidence_ids", [])]

    if not citations:
        reasons.append("missing cited evidence")

    for evidence_id in evidence_ids:
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None:
            reasons.append(f"unresolved source evidence id {evidence_id}")
            continue
        freshness = str(evidence.get("freshness_status", "unknown")).lower()
        if freshness in {"stale", "expired"}:
            reasons.append(f"source evidence {evidence_id} has {freshness} freshness badge")
        elif freshness == "unknown":
            reasons.append(f"source evidence {evidence_id} has unknown freshness")

    if hint.get("requires_inference") is True:
        reasons.append("candidate requires human interpretation before formalization")
    if confidence_band == "low":
        reasons.append("candidate confidence is low")
    if not reasons:
        reasons.append("confirm cited candidate before formalization")

    return sorted(set(reasons))


def _deferred_note_for(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "requirement_id": candidate["requirement_id"],
        "formalization_status": "deferred_pending_human_review",
        "reviewer_owner": candidate["reviewer_owner"],
        "note": candidate["deferred_formalization_note"],
    }


def _note_text(requirement_type: str, review_reasons: Iterable[str]) -> str:
    reason_text = "; ".join(review_reasons)
    return (
        f"Do not compile this {requirement_type} candidate into guardrails until a human reviewer "
        f"accepts the citation mapping and resolves: {reason_text}."
    )


def _stable_packet_id(candidates: List[Mapping[str, Any]]) -> str:
    payload = json.dumps([candidate["requirement_id"] for candidate in candidates], sort_keys=True)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"ppd-review-queue-{digest}"


def _stable_requirement_id(document: Mapping[str, Any], hint: Mapping[str, Any]) -> str:
    explicit = hint.get("requirement_id")
    if explicit:
        return _clean_scalar(explicit)
    payload = {
        "document_id": document.get("document_id"),
        "requirement_type": hint.get("requirement_type"),
        "subject": hint.get("subject"),
        "action": hint.get("action"),
        "object": hint.get("object"),
        "process_stage": hint.get("process_stage"),
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return f"candidate-requirement-{digest}"


def _public_badges(badges: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return sorted((_citation_for(badge) for badge in badges), key=lambda item: item["source_evidence_id"])


def _assert_document_shape(document: Mapping[str, Any]) -> None:
    if not isinstance(document, Mapping):
        raise ValueError("synthetic public document records must be objects")
    if not _clean_scalar(document.get("document_id")):
        raise ValueError("document record missing document_id")
    if not _clean_scalar(document.get("source_id")):
        raise ValueError("document record missing source_id")


def _assert_no_raw_source_text(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            key_text = str(key)
            if key_text in RAW_TEXT_KEYS:
                raise ValueError(f"raw source text field is not allowed at {path}.{key_text}")
            _assert_no_raw_source_text(nested, f"{path}.{key_text}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _assert_no_raw_source_text(nested, f"{path}[{index}]")


def _clean_scalar(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_list(value: Any) -> List[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        return [_clean_scalar(value)]
    return [_clean_scalar(item) for item in value if _clean_scalar(item)]
