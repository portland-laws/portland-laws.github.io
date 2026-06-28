from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURE_VERSION = "guardrail_bundle_recompile_candidate_v5"
PACKET_VERSION = "guardrail_recompile_reviewer_packet_v5"
_ALLOWED_FIXTURE_PARTS = ("ppd", "tests", "fixtures")


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{label} must be a list")
    return value


def _is_committed_fixture_path(path: Path) -> bool:
    parts = path.as_posix().split("/")
    for index in range(0, len(parts) - len(_ALLOWED_FIXTURE_PARTS) + 1):
        if tuple(parts[index : index + len(_ALLOWED_FIXTURE_PARTS)]) == _ALLOWED_FIXTURE_PARTS:
            return True
    return False


def load_guardrail_bundle_recompile_candidate_v5(path: str | Path) -> dict[str, Any]:
    fixture_path = Path(path)
    if not _is_committed_fixture_path(fixture_path):
        raise ValueError("guardrail reviewer packet v5 only consumes committed ppd/tests/fixtures inputs")

    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    candidate = _require_mapping(payload, "candidate fixture")
    if candidate.get("fixture_version") != FIXTURE_VERSION:
        raise ValueError(f"fixture_version must be {FIXTURE_VERSION}")
    return candidate


def build_guardrail_recompile_reviewer_packet_v5(candidate: dict[str, Any]) -> dict[str, Any]:
    candidate = _require_mapping(candidate, "candidate fixture")
    if candidate.get("fixture_version") != FIXTURE_VERSION:
        raise ValueError(f"fixture_version must be {FIXTURE_VERSION}")

    bundle_id = str(candidate.get("bundle_id", ""))
    if not bundle_id:
        raise ValueError("bundle_id is required")

    predicate_rows = []
    for row in _require_list(candidate.get("predicate_candidates", []), "predicate_candidates"):
        item = _require_mapping(row, "predicate row")
        predicate_rows.append(
            {
                "predicate_id": item.get("predicate_id"),
                "jurisdiction": item.get("jurisdiction"),
                "permit_stage": item.get("permit_stage"),
                "predicate_text": item.get("predicate_text"),
                "process_impact_evidence_refs": list(item.get("process_impact_evidence_refs", [])),
                "requirement_evidence_refs": list(item.get("requirement_evidence_refs", [])),
                "reviewer_decision": "TODO: approve | hold | reject",
                "reviewer_notes": "TODO",
            }
        )

    packet = {
        "packet_version": PACKET_VERSION,
        "source_fixture_version": FIXTURE_VERSION,
        "bundle_id": bundle_id,
        "mode": "fixture_first_offline_review_only",
        "prohibited_actions": [
            "activate_guardrails",
            "open_devhub",
            "read_private_documents",
            "upload",
            "submit",
            "certify",
            "pay",
            "schedule",
            "make_legal_or_permitting_guarantees",
        ],
        "predicate_rows": predicate_rows,
        "evidence_references": {
            "process_impact": list(candidate.get("process_impact_evidence", [])),
            "requirements": list(candidate.get("requirement_evidence", [])),
        },
        "stale_source_holds": list(candidate.get("stale_source_holds", [])),
        "exact_confirmation_checkpoints": list(candidate.get("exact_confirmation_checkpoints", [])),
        "refused_actions": list(candidate.get("refused_actions", [])),
        "source_freshness_caveats": list(candidate.get("source_freshness_caveats", [])),
        "rollback_owner_placeholders": list(candidate.get("rollback_owner_placeholders", [])),
        "reviewer_decision_placeholders": [
            {
                "decision": "TODO: approve | hold | reject",
                "decider": "TODO: reviewer name",
                "decided_at": "TODO: ISO-8601 timestamp",
                "rationale": "TODO",
            }
        ],
        "offline_validation_commands": list(candidate.get("offline_validation_commands", [])),
    }
    return packet


def build_packet_from_fixture(path: str | Path) -> dict[str, Any]:
    return build_guardrail_recompile_reviewer_packet_v5(
        load_guardrail_bundle_recompile_candidate_v5(path)
    )
