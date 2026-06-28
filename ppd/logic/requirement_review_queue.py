"""Deterministic review queue for extracted PP&D requirement nodes.

The queue is intentionally fixture-friendly and side-effect free.  It accepts
plain dictionaries so extraction tests can validate review behavior without
requiring live crawls, authenticated automation, or changes to shared contracts.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Any, Iterable, Mapping, Sequence


LOW_CONFIDENCE = "low_confidence"
OCR_DERIVED_EVIDENCE = "ocr_derived_evidence"
STALE_SOURCE = "stale_source"
MISSING_FORMALIZATION = "missing_formalization"
HUMAN_REVIEW_REQUIRED = "human_review_required"

BLOCKER_PRECEDENCE: tuple[str, ...] = (
    LOW_CONFIDENCE,
    OCR_DERIVED_EVIDENCE,
    STALE_SOURCE,
    MISSING_FORMALIZATION,
    HUMAN_REVIEW_REQUIRED,
)

PROMOTABLE_FORMALIZATION_STATUSES = frozenset({"formalized", "compiled", "ready"})
CLEAR_HUMAN_REVIEW_STATUSES = frozenset({"approved", "not_required", "complete", "cleared"})
REVIEW_HUMAN_REVIEW_STATUSES = frozenset({
    "required",
    "needs_review",
    "pending",
    "blocked",
    "rejected",
    "unreviewed",
})
STALE_FRESHNESS_STATUSES = frozenset({"stale", "expired", "unknown", "missing"})
OCR_MARKERS = frozenset({"ocr", "ocr_only", "ocr_derived", "image_ocr"})


@dataclass(frozen=True)
class RequirementReviewItem:
    """A requirement that must be reviewed before guardrail promotion."""

    requirement_id: str
    blocker_codes: tuple[str, ...]
    source_evidence_ids: tuple[str, ...]
    subject: str
    action: str
    object: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "blocker_codes": list(self.blocker_codes),
            "source_evidence_ids": list(self.source_evidence_ids),
            "subject": self.subject,
            "action": self.action,
            "object": self.object,
        }


def load_requirement_nodes(fixture_path: Path | str) -> list[dict[str, Any]]:
    """Load RequirementNode dictionaries from a fixture JSON file."""

    path = Path(fixture_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, Mapping):
        nodes = payload.get("requirement_nodes", [])
    else:
        nodes = payload
    if not isinstance(nodes, list):
        raise ValueError("requirement fixture must contain a list of requirement nodes")
    return [dict(node) for node in nodes if isinstance(node, Mapping)]


def build_requirement_review_queue(
    requirement_nodes: Iterable[Mapping[str, Any]],
    *,
    confidence_threshold: float = 0.75,
    stale_source_ids: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Return deterministic review items for requirements blocked from promotion."""

    stale_sources = {str(source_id) for source_id in stale_source_ids}
    items: list[RequirementReviewItem] = []
    for node in requirement_nodes:
        blockers = _blocker_codes(
            node,
            confidence_threshold=confidence_threshold,
            stale_source_ids=stale_sources,
        )
        if blockers:
            items.append(
                RequirementReviewItem(
                    requirement_id=_text(node.get("requirement_id")),
                    blocker_codes=tuple(blockers),
                    source_evidence_ids=_text_tuple(node.get("source_evidence_ids")),
                    subject=_text(node.get("subject")),
                    action=_text(node.get("action")),
                    object=_text(node.get("object")),
                )
            )

    return [item.as_dict() for item in sorted(items, key=lambda item: item.requirement_id)]


def promotable_requirement_nodes(
    requirement_nodes: Iterable[Mapping[str, Any]],
    *,
    confidence_threshold: float = 0.75,
    stale_source_ids: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Return nodes that are clear to enter guardrail bundle compilation."""

    stale_sources = {str(source_id) for source_id in stale_source_ids}
    promoted: list[dict[str, Any]] = []
    for node in requirement_nodes:
        blockers = _blocker_codes(
            node,
            confidence_threshold=confidence_threshold,
            stale_source_ids=stale_sources,
        )
        if not blockers:
            promoted.append(dict(node))
    return sorted(promoted, key=lambda node: _text(node.get("requirement_id")))


def partition_requirements_for_guardrails(
    requirement_nodes: Iterable[Mapping[str, Any]],
    *,
    confidence_threshold: float = 0.75,
    stale_source_ids: Iterable[str] = (),
) -> dict[str, list[dict[str, Any]]]:
    """Split extracted requirements into review queue and promotable nodes."""

    nodes = [dict(node) for node in requirement_nodes]
    return {
        "review_queue": build_requirement_review_queue(
            nodes,
            confidence_threshold=confidence_threshold,
            stale_source_ids=stale_source_ids,
        ),
        "promotable_requirement_nodes": promotable_requirement_nodes(
            nodes,
            confidence_threshold=confidence_threshold,
            stale_source_ids=stale_source_ids,
        ),
    }


def _blocker_codes(
    node: Mapping[str, Any],
    *,
    confidence_threshold: float,
    stale_source_ids: set[str],
) -> list[str]:
    found: set[str] = set()

    confidence = node.get("confidence")
    if not _is_confident(confidence, confidence_threshold):
        found.add(LOW_CONFIDENCE)

    if _has_ocr_evidence(node):
        found.add(OCR_DERIVED_EVIDENCE)

    if _has_stale_source(node, stale_source_ids):
        found.add(STALE_SOURCE)

    formalization_status = _normalized(node.get("formalization_status"))
    if formalization_status not in PROMOTABLE_FORMALIZATION_STATUSES:
        found.add(MISSING_FORMALIZATION)

    if _requires_human_review(node):
        found.add(HUMAN_REVIEW_REQUIRED)

    return [code for code in BLOCKER_PRECEDENCE if code in found]


def _is_confident(value: Any, threshold: float) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return False
    if not isinstance(value, (int, float)):
        return False
    return float(value) >= threshold


def _has_ocr_evidence(node: Mapping[str, Any]) -> bool:
    for key in ("evidence_derivation", "evidence_quality", "extraction_method"):
        if _normalized(node.get(key)) in OCR_MARKERS:
            return True
    for evidence in _evidence_records(node):
        for key in ("derivation", "quality", "extraction_method", "source_method"):
            if _normalized(evidence.get(key)) in OCR_MARKERS:
                return True
    return False


def _has_stale_source(node: Mapping[str, Any], stale_source_ids: set[str]) -> bool:
    if _normalized(node.get("source_freshness_status")) in STALE_FRESHNESS_STATUSES:
        return True
    source_id = _text(node.get("source_id"))
    if source_id and source_id in stale_source_ids:
        return True
    for source_id in _text_tuple(node.get("source_ids")):
        if source_id in stale_source_ids:
            return True
    for evidence in _evidence_records(node):
        if _normalized(evidence.get("freshness_status")) in STALE_FRESHNESS_STATUSES:
            return True
        evidence_source_id = _text(evidence.get("source_id"))
        if evidence_source_id and evidence_source_id in stale_source_ids:
            return True
    return False


def _requires_human_review(node: Mapping[str, Any]) -> bool:
    if node.get("requires_human_review") is True:
        return True
    status = _normalized(node.get("human_review_status"))
    if status in REVIEW_HUMAN_REVIEW_STATUSES:
        return True
    if status and status not in CLEAR_HUMAN_REVIEW_STATUSES:
        return True
    return False


def _evidence_records(node: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    records = node.get("evidence_records", [])
    if not isinstance(records, Sequence) or isinstance(records, (str, bytes)):
        return ()
    return tuple(record for record in records if isinstance(record, Mapping))


def _normalized(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def _text(value: Any) -> str:
    return str(value or "").strip()


def _text_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, Sequence):
        return (str(value),)
    return tuple(str(item) for item in value if str(item).strip())
