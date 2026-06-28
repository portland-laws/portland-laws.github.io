"""Build fixture-first guardrail regeneration readiness packets.

The readiness packet is intentionally conservative: a reviewed invalidation packet
never promotes regenerated guardrails automatically. It turns each invalidated
source-to-guardrail link into blocked work, human review checkpoints, citation
refresh requirements, and cache invalidation evidence.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any


def build_regeneration_readiness_packet(invalidation_packet: dict[str, Any]) -> dict[str, Any]:
    """Return a deterministic no-promotion readiness packet.

    The input must be a reviewed source-to-guardrail invalidation packet for one
    permit process. The function performs no crawling and no live authentication.
    """

    packet = deepcopy(invalidation_packet)
    if packet.get("review_status") != "reviewed":
        raise ValueError("invalidation packet must have review_status='reviewed'")

    permit_process = packet.get("permit_process")
    if not isinstance(permit_process, dict) or not permit_process.get("process_id"):
        raise ValueError("invalidation packet must include one permit_process.process_id")

    invalidations = packet.get("invalidations")
    if not isinstance(invalidations, list) or not invalidations:
        raise ValueError("invalidation packet must include at least one invalidation")

    process_id = str(permit_process["process_id"])
    packet_id = str(packet.get("packet_id", f"reviewed-invalidation-{process_id}"))
    generated_at = str(packet.get("reviewed_at") or _utc_now())

    blocked_work_items = []
    citation_refresh_requirements = []
    cache_invalidation_evidence = []

    for index, invalidation in enumerate(sorted(invalidations, key=_invalidation_sort_key), start=1):
        guardrail_id = str(invalidation.get("guardrail_id") or f"guardrail-{index}")
        source_id = str(invalidation.get("source_id") or f"source-{index}")
        reason = str(invalidation.get("reason") or "reviewed source invalidation requires regeneration")
        citation_ids = [str(value) for value in invalidation.get("citation_ids", [])]
        cache_keys = [str(value) for value in invalidation.get("cache_keys", [])]

        blocked_work_items.append(
            {
                "work_item_id": f"regen-blocked-{process_id}-{index:02d}",
                "status": "blocked_pending_human_review",
                "permit_process_id": process_id,
                "guardrail_id": guardrail_id,
                "source_id": source_id,
                "blockers": [
                    "human_review_checkpoint_required",
                    "citation_refresh_required",
                    "cache_invalidation_evidence_required",
                    "promotion_disabled_for_fixture_packet",
                ],
                "reason": reason,
            }
        )

        citation_refresh_requirements.append(
            {
                "requirement_id": f"citation-refresh-{process_id}-{index:02d}",
                "guardrail_id": guardrail_id,
                "source_id": source_id,
                "citation_ids": citation_ids,
                "required_action": "refresh_against_reviewed_public_source_before_regeneration",
                "status": "required",
            }
        )

        cache_invalidation_evidence.append(
            {
                "evidence_id": f"cache-invalidation-{process_id}-{index:02d}",
                "guardrail_id": guardrail_id,
                "source_id": source_id,
                "cache_keys": cache_keys,
                "required_action": "record_cache_keys_invalidated_before_any_regeneration_attempt",
                "status": "required",
            }
        )

    return {
        "packet_type": "guardrail_regeneration_readiness",
        "packet_id": f"readiness-{packet_id}",
        "generated_at": generated_at,
        "source_invalidation_packet_id": packet_id,
        "fixture_first": True,
        "permit_process": {
            "process_id": process_id,
            "name": str(permit_process.get("name", "Synthetic permit process")),
            "synthetic": bool(permit_process.get("synthetic", True)),
        },
        "blocked_regeneration_work_items": blocked_work_items,
        "required_human_review_checkpoints": [
            {
                "checkpoint_id": f"human-review-{process_id}-01",
                "status": "required",
                "required_reviewer_role": "ppd_guardrail_reviewer",
                "scope": "confirm invalidated sources, refreshed citations, and cache invalidation evidence before regeneration",
            },
            {
                "checkpoint_id": f"human-review-{process_id}-02",
                "status": "required",
                "required_reviewer_role": "ppd_promotion_approver",
                "scope": "confirm regenerated guardrails remain blocked from promotion until a separate reviewed promotion packet exists",
            },
        ],
        "citation_refresh_requirements": citation_refresh_requirements,
        "cache_invalidation_evidence": cache_invalidation_evidence,
        "promotion_status": {
            "status": "no_promotion",
            "promotion_allowed": False,
            "reason": "fixture readiness packets only prepare blocked regeneration work and cannot promote guardrails",
        },
    }


def _invalidation_sort_key(invalidation: dict[str, Any]) -> tuple[str, str]:
    return (str(invalidation.get("guardrail_id", "")), str(invalidation.get("source_id", "")))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
