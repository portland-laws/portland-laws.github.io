"""Promotion eligibility checks for PP&D process models and guardrail bundles.

The gate is intentionally data-shape tolerant because promotion candidates are
assembled from multiple extraction and validation stages. A candidate may use
booleans, status strings, counts, or lists to describe unresolved blockers; the
normalization below converts those forms into deterministic blocker codes.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


PROMOTION_BLOCKER_CODES = (
    "citation_integrity",
    "source_freshness",
    "requirement_review_queue",
    "devhub_surface_drift",
    "unsupported_paths",
    "consequential_action_blockers",
)

_RESOLVED_STATUS_VALUES = {
    "clear",
    "cleared",
    "current",
    "fresh",
    "none",
    "pass",
    "passed",
    "resolved",
    "valid",
    "verified",
}

_UNRESOLVED_STATUS_VALUES = {
    "blocked",
    "dirty",
    "drifted",
    "expired",
    "fail",
    "failed",
    "invalid",
    "needs_review",
    "open",
    "pending",
    "stale",
    "unresolved",
}


@dataclass(frozen=True)
class PromotionBlocker:
    """A normalized reason a candidate cannot be marked promotable."""

    code: str
    message: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class PromotionGateResult:
    """Deterministic promotion decision for a single candidate."""

    candidate_id: str
    candidate_kind: str
    promotable: bool
    blockers: tuple[PromotionBlocker, ...]

    @property
    def blocker_codes(self) -> tuple[str, ...]:
        return tuple(blocker.code for blocker in self.blockers)


def load_promotion_fixture(path: Path | str) -> dict[str, Any]:
    """Load a committed promotion-gate fixture."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def evaluate_promotion_candidate(candidate: Mapping[str, Any]) -> PromotionGateResult:
    """Return whether a ProcessModel or GuardrailBundle may be promoted.

    A candidate is promotable only when every required validation domain is
    resolved. The incoming candidate's own ``promotable`` flag is treated as a
    requested state, not as authority to bypass the gate.
    """

    candidate_id = _string_value(
        candidate.get("process_id"),
        candidate.get("guardrail_bundle_id"),
        candidate.get("candidate_id"),
        fallback="unknown-candidate",
    )
    candidate_kind = _string_value(candidate.get("kind"), fallback="unknown")

    blockers = tuple(
        blocker
        for blocker in (
            _citation_integrity_blocker(candidate),
            _source_freshness_blocker(candidate),
            _requirement_review_queue_blocker(candidate),
            _devhub_surface_drift_blocker(candidate),
            _unsupported_paths_blocker(candidate),
            _consequential_action_blocker(candidate),
        )
        if blocker is not None
    )

    return PromotionGateResult(
        candidate_id=candidate_id,
        candidate_kind=candidate_kind,
        promotable=not blockers,
        blockers=blockers,
    )


def _citation_integrity_blocker(candidate: Mapping[str, Any]) -> PromotionBlocker | None:
    citation_integrity = _mapping(candidate.get("citation_integrity"))
    unresolved = _evidence_values(
        citation_integrity.get("unresolved"),
        citation_integrity.get("missing_citations"),
        citation_integrity.get("orphan_citations"),
        citation_integrity.get("broken_citation_spans"),
    )
    if unresolved or _status_is_unresolved(citation_integrity.get("status")):
        return PromotionBlocker(
            code="citation_integrity",
            message="Citation integrity has unresolved missing, orphaned, or broken evidence links.",
            evidence=unresolved,
        )
    return None


def _source_freshness_blocker(candidate: Mapping[str, Any]) -> PromotionBlocker | None:
    source_freshness = _mapping(candidate.get("source_freshness"))
    stale_sources = _evidence_values(
        source_freshness.get("stale_sources"),
        source_freshness.get("expired_sources"),
        source_freshness.get("unknown_sources"),
        source_freshness.get("unresolved"),
    )
    if stale_sources or _status_is_unresolved(source_freshness.get("status")):
        return PromotionBlocker(
            code="source_freshness",
            message="Source freshness has stale, expired, unknown, or unresolved source evidence.",
            evidence=stale_sources,
        )
    return None


def _requirement_review_queue_blocker(candidate: Mapping[str, Any]) -> PromotionBlocker | None:
    queue = _mapping(candidate.get("requirement_review_queue"))
    pending_items = _evidence_values(queue.get("pending"), queue.get("needs_review"), queue.get("unresolved"))
    pending_count = _int_value(queue.get("pending_count"))
    if pending_items or pending_count > 0 or _status_is_unresolved(queue.get("status")):
        evidence = pending_items or ((f"pending_count:{pending_count}",) if pending_count > 0 else ())
        return PromotionBlocker(
            code="requirement_review_queue",
            message="Requirement extraction or formalization still has human-review work queued.",
            evidence=evidence,
        )
    return None


def _devhub_surface_drift_blocker(candidate: Mapping[str, Any]) -> PromotionBlocker | None:
    drift = _mapping(candidate.get("devhub_surface_drift"))
    drifted_surfaces = _evidence_values(
        drift.get("drifted_surfaces"),
        drift.get("selector_mismatches"),
        drift.get("unresolved"),
    )
    if drifted_surfaces or _status_is_unresolved(drift.get("status")):
        return PromotionBlocker(
            code="devhub_surface_drift",
            message="Observed DevHub surface structure has unresolved drift from the candidate model.",
            evidence=drifted_surfaces,
        )
    return None


def _unsupported_paths_blocker(candidate: Mapping[str, Any]) -> PromotionBlocker | None:
    unsupported_paths = candidate.get("unsupported_paths")
    if isinstance(unsupported_paths, Mapping):
        unresolved = _evidence_values(
            unsupported_paths.get("unresolved"),
            unsupported_paths.get("untriaged"),
            unsupported_paths.get("missing_manual_handoff"),
        )
        if unresolved or _status_is_unresolved(unsupported_paths.get("status")):
            return PromotionBlocker(
                code="unsupported_paths",
                message="Unsupported process paths remain unresolved or lack a manual handoff policy.",
                evidence=unresolved,
            )
    elif unsupported_paths:
        unresolved = _evidence_values(unsupported_paths)
        return PromotionBlocker(
            code="unsupported_paths",
            message="Unsupported process paths remain unresolved or lack a manual handoff policy.",
            evidence=unresolved,
        )
    return None


def _consequential_action_blocker(candidate: Mapping[str, Any]) -> PromotionBlocker | None:
    blockers = candidate.get("consequential_action_blockers")
    if isinstance(blockers, Mapping):
        unresolved = _evidence_values(blockers.get("unresolved"), blockers.get("actions"), blockers.get("missing_gates"))
        if unresolved or _status_is_unresolved(blockers.get("status")):
            return PromotionBlocker(
                code="consequential_action_blockers",
                message="Consequential actions still lack exact-confirmation, attendance, or refusal gates.",
                evidence=unresolved,
            )
    elif blockers:
        unresolved = _evidence_values(blockers)
        return PromotionBlocker(
            code="consequential_action_blockers",
            message="Consequential actions still lack exact-confirmation, attendance, or refusal gates.",
            evidence=unresolved,
        )
    return None


def _mapping(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _string_value(*values: Any, fallback: str) -> str:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return fallback


def _int_value(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return 0


def _status_is_unresolved(value: Any) -> bool:
    if isinstance(value, bool):
        return not value
    if not isinstance(value, str):
        return False
    normalized = value.strip().lower()
    if normalized in _UNRESOLVED_STATUS_VALUES:
        return True
    if normalized in _RESOLVED_STATUS_VALUES:
        return False
    return normalized.startswith("unresolved") or normalized.startswith("pending")


def _evidence_values(*values: Any) -> tuple[str, ...]:
    evidence: list[str] = []
    for value in values:
        evidence.extend(_flatten_evidence(value))
    return tuple(dict.fromkeys(item for item in evidence if item))


def _flatten_evidence(value: Any) -> Iterable[str]:
    if value is None or value is False:
        return ()
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Mapping):
        value_id = value.get("id") or value.get("source_id") or value.get("requirement_id") or value.get("surface_id")
        if value_id is not None:
            return (str(value_id),)
        return tuple(str(key) for key, item in value.items() if item)
    if isinstance(value, Iterable):
        flattened: list[str] = []
        for item in value:
            flattened.extend(_flatten_evidence(item))
        return tuple(flattened)
    if value:
        return (str(value),)
    return ()
