"""Fixture-first human review queue packets for PP&D readiness digests."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any, Iterable, Mapping

from .e2e_digest import validate_e2e_readiness_digest


_REVIEW_SPECS: tuple[dict[str, Any], ...] = (
    {
        "category": "source_freshness",
        "title": "Confirm public source freshness before relying on the digest",
        "packet_keys": ("public_source_packet", "extraction_packet"),
        "review_prompt": "Check source dates, capture metadata, and freshness status without refreshing live services.",
    },
    {
        "category": "requirement_confidence",
        "title": "Confirm extracted requirement confidence and cited process coverage",
        "packet_keys": ("extraction_packet", "process_model_packet", "user_gap_packet"),
        "review_prompt": "Review requirement confidence, missing facts, and cited process-stage support before draft planning.",
    },
    {
        "category": "guardrail_predicates",
        "title": "Confirm deterministic guardrail predicates remain blocked where required",
        "packet_keys": ("guardrail_packet",),
        "review_prompt": "Review predicate evidence, refused-action gates, and exact-confirmation requirements.",
    },
    {
        "category": "devhub_surface_evidence",
        "title": "Confirm DevHub surface evidence is redacted and attended-only",
        "packet_keys": ("devhub_preflight_packet",),
        "review_prompt": "Check selector confidence, surface evidence, attendance requirements, and absence of private session artifacts.",
    },
    {
        "category": "payment_upload_boundaries",
        "title": "Confirm payment and upload boundaries are not promoted",
        "packet_keys": ("local_preview_packet", "guardrail_packet", "journal_packet"),
        "review_prompt": "Verify upload staging, fee/payment review, and official-record actions stay blocked pending exact user confirmation.",
    },
    {
        "category": "operator_signoff",
        "title": "Collect operator signoff before any live or official workflow",
        "packet_keys": ("user_gap_packet", "devhub_preflight_packet", "journal_packet", "post_action_packet"),
        "review_prompt": "Confirm a human operator reviewed blockers, missing confirmations, and post-action constraints.",
    },
)


class HumanReviewQueuePacketError(ValueError):
    """Raised when a PP&D human review queue packet is unsafe."""

    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid PP&D human review queue packet: " + "; ".join(self.problems))


def load_human_review_queue_expected_fixture(path: str | Path) -> dict[str, Any]:
    """Load a committed expected queue packet fixture."""

    fixture_path = Path(path)
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise HumanReviewQueuePacketError(["human review queue fixture root must be an object"])
    return raw


def build_human_review_queue_packet(digest: Mapping[str, Any]) -> dict[str, Any]:
    """Build ordered human review items from an end-to-end readiness digest."""

    source_digest = deepcopy(dict(digest))
    problems = validate_e2e_readiness_digest(source_digest)
    problems.extend(_digest_packet_link_problems(source_digest))
    if problems:
        raise HumanReviewQueuePacketError(problems)

    packet_links = _packet_links_by_key(source_digest)
    blocking_reasons = _blocking_reasons(source_digest)
    review_items = [
        _review_item(order=index + 1, spec=spec, packet_links=packet_links, blocking_reasons=blocking_reasons)
        for index, spec in enumerate(_REVIEW_SPECS)
    ]

    packet = {
        "packet_type": "ppd.human_review_queue.v1",
        "fixture_first": True,
        "live_services_called": False,
        "official_readiness": False,
        "production_ready": False,
        "case_id": str(source_digest["case_id"]),
        "process_id": str(source_digest["process_id"]),
        "digest_type": str(source_digest["digest_type"]),
        "digest_status": str(source_digest["synthetic_case_status"]),
        "review_status": "human_review_required",
        "blocked_from_production": True,
        "source_evidence_ids": sorted(str(item) for item in source_digest["source_evidence_ids"]),
        "review_items": review_items,
    }

    packet_problems = validate_human_review_queue_packet(packet)
    if packet_problems:
        raise HumanReviewQueuePacketError(packet_problems)
    return packet


def validate_human_review_queue_packet(packet: Mapping[str, Any]) -> list[str]:
    """Validate that a review queue is deterministic and never production-ready."""

    problems: list[str] = []
    if packet.get("packet_type") != "ppd.human_review_queue.v1":
        problems.append("packet_type must be ppd.human_review_queue.v1")
    if packet.get("fixture_first") is not True:
        problems.append("human review queue must be fixture_first")
    if packet.get("live_services_called") is not False:
        problems.append("human review queue must confirm live_services_called is false")
    if packet.get("official_readiness") is not False:
        problems.append("human review queue must not mark official_readiness")
    if packet.get("production_ready") is not False:
        problems.append("human review queue must not mark production_ready")
    if packet.get("blocked_from_production") is not True:
        problems.append("human review queue must be blocked_from_production")
    if not _non_empty_text(packet.get("case_id")):
        problems.append("human review queue is missing case_id")
    if not _non_empty_text(packet.get("process_id")):
        problems.append("human review queue is missing process_id")
    if packet.get("review_status") != "human_review_required":
        problems.append("human review queue review_status must be human_review_required")

    evidence_ids = packet.get("source_evidence_ids")
    if not isinstance(evidence_ids, list) or not evidence_ids or not all(_non_empty_text(item) for item in evidence_ids):
        problems.append("human review queue must include source_evidence_ids")

    items = packet.get("review_items")
    if not isinstance(items, list):
        problems.append("human review queue must include review_items")
        return problems
    if len(items) != len(_REVIEW_SPECS):
        problems.append("human review queue must include exactly six review items")

    expected_categories = [spec["category"] for spec in _REVIEW_SPECS]
    actual_categories: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            problems.append(f"review_items[{index}] must be an object")
            continue
        actual_categories.append(str(item.get("category") or ""))
        expected_order = index + 1
        if item.get("order") != expected_order:
            problems.append(f"review_items[{index}] must have order {expected_order}")
        if item.get("production_ready") is not False:
            problems.append(f"review_items[{index}] must not mark production_ready")
        if item.get("status") != "human_review_required":
            problems.append(f"review_items[{index}] status must be human_review_required")
        if not _non_empty_text(item.get("review_item_id")):
            problems.append(f"review_items[{index}] is missing review_item_id")
        if not _non_empty_text(item.get("title")):
            problems.append(f"review_items[{index}] is missing title")
        if not _non_empty_text(item.get("review_prompt")):
            problems.append(f"review_items[{index}] is missing review_prompt")
        refs = item.get("source_evidence_ids")
        if not isinstance(refs, list) or not refs or not all(_non_empty_text(ref) for ref in refs):
            problems.append(f"review_items[{index}] must cite source_evidence_ids")
        if _has_production_ready_status(item):
            problems.append(f"review_items[{index}] contains production-ready status")

    if actual_categories != expected_categories:
        problems.append("human review queue categories are not in the required order")
    if _has_production_ready_status(packet):
        problems.append("human review queue contains production-ready status")
    return problems


def _digest_packet_link_problems(digest: Mapping[str, Any]) -> list[str]:
    packet_links = digest.get("packet_links")
    if not isinstance(packet_links, list):
        return ["digest must include packet_links"]
    linked_keys = {link.get("packet_key") for link in packet_links if isinstance(link, Mapping)}
    problems: list[str] = []
    for spec in _REVIEW_SPECS:
        for packet_key in spec["packet_keys"]:
            if packet_key not in linked_keys:
                problems.append(f"digest is missing packet link for human review category {spec['category']}: {packet_key}")
    return problems


def _packet_links_by_key(digest: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    links: dict[str, Mapping[str, Any]] = {}
    for link in digest.get("packet_links", []):
        if isinstance(link, Mapping) and isinstance(link.get("packet_key"), str):
            links[str(link["packet_key"])] = link
    return links


def _blocking_reasons(digest: Mapping[str, Any]) -> dict[str, list[str]]:
    reasons: dict[str, list[str]] = {}
    for reason in digest.get("blocking_reasons", []):
        if not isinstance(reason, Mapping):
            continue
        packet_key = reason.get("packet_key")
        text = reason.get("reason")
        if isinstance(packet_key, str) and isinstance(text, str) and text:
            reasons.setdefault(packet_key, []).append(text)
    return reasons


def _review_item(
    *,
    order: int,
    spec: Mapping[str, Any],
    packet_links: Mapping[str, Mapping[str, Any]],
    blocking_reasons: Mapping[str, list[str]],
) -> dict[str, Any]:
    packet_keys = tuple(str(key) for key in spec["packet_keys"])
    evidence_ids: set[str] = set()
    statuses: list[dict[str, str]] = []
    blockers: list[dict[str, str]] = []

    for packet_key in packet_keys:
        link = packet_links[packet_key]
        statuses.append({"packet_key": packet_key, "status": str(link.get("status") or "fixture_validated")})
        refs = link.get("source_evidence_ids")
        if isinstance(refs, list):
            evidence_ids.update(str(ref) for ref in refs if isinstance(ref, str) and ref)
        for reason in blocking_reasons.get(packet_key, []):
            blockers.append({"packet_key": packet_key, "reason": reason})

    return {
        "review_item_id": f"human-review-{order:02d}-{spec['category']}",
        "order": order,
        "category": str(spec["category"]),
        "title": str(spec["title"]),
        "status": "human_review_required",
        "production_ready": False,
        "packet_keys": list(packet_keys),
        "packet_statuses": statuses,
        "blocking_reasons": blockers,
        "source_evidence_ids": sorted(evidence_ids),
        "review_prompt": str(spec["review_prompt"]),
    }


def _has_production_ready_status(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_lower = str(key).lower()
            if key_lower == "production_ready" and child is True:
                return True
            if key_lower in {"status", "review_status", "readiness_status"} and isinstance(child, str):
                if child.strip().lower() in {"production_ready", "ready_for_production", "approved_for_production"}:
                    return True
            if _has_production_ready_status(child):
                return True
    elif isinstance(value, list):
        return any(_has_production_ready_status(item) for item in value)
    return False


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
