"""Fixture-first reviewer packet builder for guardrail recompile staging packet v6.

This module is intentionally offline-only. It accepts committed staging packet
fixtures and turns them into deterministic reviewer material without activating
any guardrail bundle or contacting PP&D, DevHub, private documents, or external
services.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

STAGING_PACKET_VERSION = "guardrail_recompile_staging_packet_v6"
REVIEWER_PACKET_VERSION = "guardrail_recompile_reviewer_packet_v6"
INACTIVE_STATUS = "inactive"

_ALLOWED_OFFLINE_COMMANDS = (
    ("python3", "-m", "unittest"),
    ("python3", "-m", "py_compile"),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

_DISALLOWED_COMMAND_TERMS = {
    "curl",
    "wget",
    "playwright",
    "npm",
    "npx",
    "devhub",
    "upload",
    "submit",
    "pay",
    "schedule",
    "certify",
}


class ReviewerPacketError(ValueError):
    """Raised when a staging fixture cannot produce an offline reviewer packet."""


@dataclass(frozen=True)
class ReviewerPacketInput:
    """Loaded staging fixture with source-path metadata for reviewer traceability."""

    fixture_path: Path
    packet: Mapping[str, Any]


def load_fixture_packet(path: str | Path) -> ReviewerPacketInput:
    """Load one committed staging packet fixture from disk."""

    fixture_path = Path(path)
    with fixture_path.open("r", encoding="utf-8") as handle:
        packet = json.load(handle)
    if not isinstance(packet, dict):
        raise ReviewerPacketError("staging fixture must contain a JSON object")
    return ReviewerPacketInput(fixture_path=fixture_path, packet=packet)


def build_reviewer_packet(source: ReviewerPacketInput | Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic reviewer packet from one staging packet v6 fixture."""

    if isinstance(source, ReviewerPacketInput):
        packet = source.packet
        fixture_ref = source.fixture_path.as_posix()
    else:
        packet = source
        fixture_ref = ""

    _require_staging_v6(packet)
    _require_inactive_guardrails(packet)

    guardrails = _sequence(packet, "guardrails")
    evidence = _evidence_by_id(packet)
    predicates = _sequence(packet, "deterministic_predicates")
    confirmations = _sequence(packet, "exact_confirmations")
    refused_actions = _sequence(packet, "refused_actions")
    stale_evidence = _sequence(packet, "stale_evidence")
    offline_commands = _validated_offline_commands(_sequence(packet, "offline_validation_commands"))

    comparison_rows = [_comparison_row(item, evidence) for item in guardrails]
    source_checks = [_source_continuity_check(item, evidence) for item in guardrails]

    return {
        "packet_version": REVIEWER_PACKET_VERSION,
        "source_staging_packet_version": STAGING_PACKET_VERSION,
        "source_fixture": fixture_ref,
        "source_packet_id": _string(packet, "packet_id"),
        "guardrail_activation_status": INACTIVE_STATUS,
        "inactive_guardrail_status_notes": _inactive_status_notes(guardrails),
        "reviewer_comparison_rows": comparison_rows,
        "source_evidence_continuity_checks": source_checks,
        "deterministic_predicate_review_prompts": [_predicate_prompt(item) for item in predicates],
        "exact_confirmation_preservation_summary": _preservation_summary(
            confirmations,
            "confirmation_id",
            "exact_confirmation",
        ),
        "refused_action_preservation_summary": _preservation_summary(
            refused_actions,
            "refusal_id",
            "refused_action",
        ),
        "stale_evidence_hold_propagation": [_stale_hold(item) for item in stale_evidence],
        "rollback_checkpoint_placeholders": _rollback_placeholders(guardrails),
        "signoff_owner_placeholders": _signoff_placeholders(guardrails),
        "offline_validation_commands": offline_commands,
        "prohibited_actions": [
            "activate_guardrails",
            "crawl_live_sites",
            "open_devhub",
            "read_private_documents",
            "upload",
            "submit",
            "certify",
            "pay",
            "schedule",
            "make_legal_or_permitting_guarantees",
        ],
    }


def build_reviewer_packet_from_fixture(path: str | Path) -> dict[str, Any]:
    """Convenience wrapper used by tests and offline validation scripts."""

    return build_reviewer_packet(load_fixture_packet(path))


def _require_staging_v6(packet: Mapping[str, Any]) -> None:
    version = packet.get("packet_version")
    if version != STAGING_PACKET_VERSION:
        raise ReviewerPacketError(
            f"expected {STAGING_PACKET_VERSION!r}, received {version!r}"
        )


def _require_inactive_guardrails(packet: Mapping[str, Any]) -> None:
    for guardrail in _sequence(packet, "guardrails"):
        guardrail_id = _string(guardrail, "guardrail_id")
        status = _string(guardrail, "activation_status")
        if status != INACTIVE_STATUS:
            raise ReviewerPacketError(
                f"guardrail {guardrail_id!r} must remain inactive in reviewer packet v6"
            )


def _comparison_row(guardrail: Mapping[str, Any], evidence: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    evidence_ids = _string_list(guardrail, "source_evidence_ids")
    missing_evidence = [item for item in evidence_ids if item not in evidence]
    return {
        "guardrail_id": _string(guardrail, "guardrail_id"),
        "process_id": _string(guardrail, "process_id"),
        "staged_rule_hash": _string(guardrail, "staged_rule_hash"),
        "previous_rule_hash": _string(guardrail, "previous_rule_hash"),
        "review_disposition": "review_required",
        "activation_status": _string(guardrail, "activation_status"),
        "source_evidence_ids": evidence_ids,
        "missing_source_evidence_ids": missing_evidence,
        "comparison_note": _string(guardrail, "comparison_note"),
    }


def _source_continuity_check(guardrail: Mapping[str, Any], evidence: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    evidence_ids = _string_list(guardrail, "source_evidence_ids")
    present = [item for item in evidence_ids if item in evidence]
    stale = [item for item in present if evidence[item].get("freshness_status") == "stale"]
    return {
        "guardrail_id": _string(guardrail, "guardrail_id"),
        "expected_source_evidence_ids": evidence_ids,
        "present_source_evidence_ids": present,
        "stale_source_evidence_ids": stale,
        "continuity_status": "blocked_by_missing_evidence" if len(present) != len(evidence_ids) else "continuous",
        "requires_human_review": bool(stale) or len(present) != len(evidence_ids),
    }


def _predicate_prompt(predicate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "predicate_id": _string(predicate, "predicate_id"),
        "prompt": (
            "Review the deterministic predicate against the staged source evidence. "
            "Confirm only whether the predicate is preserved, narrowed, stale-held, or refused; "
            "do not activate it."
        ),
        "predicate_text": _string(predicate, "predicate_text"),
        "expected_review_answers": ["preserved", "narrowed", "stale-held", "refused"],
    }


def _preservation_summary(items: Sequence[Mapping[str, Any]], id_field: str, kind: str) -> dict[str, Any]:
    ids = [_string(item, id_field) for item in items]
    return {
        "summary_kind": kind,
        "preserved_count": len(ids),
        "preserved_ids": ids,
        "review_note": "Exact wording and refusal boundaries are preserved from staging fixtures only.",
    }


def _stale_hold(item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "source_evidence_id": _string(item, "source_evidence_id"),
        "hold_reason": _string(item, "hold_reason"),
        "propagated_to_guardrail_ids": _string_list(item, "guardrail_ids"),
        "reviewer_action": "keep_hold_until_fresh_source_fixture_is_committed",
    }


def _rollback_placeholders(guardrails: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "guardrail_id": _string(item, "guardrail_id"),
            "rollback_checkpoint_id": "TBD_BY_REVIEWER",
            "rollback_checkpoint_note": "Placeholder only; no rollback is executed by this packet.",
        }
        for item in guardrails
    ]


def _signoff_placeholders(guardrails: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "guardrail_id": _string(item, "guardrail_id"),
            "signoff_owner": "TBD_BY_REVIEWER",
            "signoff_status": "not_signed_off",
        }
        for item in guardrails
    ]


def _inactive_status_notes(guardrails: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    return [
        {
            "guardrail_id": _string(item, "guardrail_id"),
            "activation_status": INACTIVE_STATUS,
            "note": "Reviewer packet assembly preserves inactive staging status and does not activate guardrails.",
        }
        for item in guardrails
    ]


def _validated_offline_commands(commands: Sequence[Mapping[str, Any]]) -> list[list[str]]:
    validated: list[list[str]] = []
    for command in commands:
        argv = command.get("argv")
        if not isinstance(argv, list) or not all(isinstance(part, str) for part in argv):
            raise ReviewerPacketError("offline validation command argv must be a list of strings")
        lowered = {part.lower() for part in argv}
        if lowered & _DISALLOWED_COMMAND_TERMS:
            raise ReviewerPacketError(f"disallowed non-offline validation command: {argv!r}")
        if not any(tuple(argv[: len(prefix)]) == prefix for prefix in _ALLOWED_OFFLINE_COMMANDS):
            raise ReviewerPacketError(f"unsupported offline validation command: {argv!r}")
        validated.append(list(argv))
    return validated


def _evidence_by_id(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    evidence: dict[str, Mapping[str, Any]] = {}
    for item in _sequence(packet, "source_evidence"):
        evidence[_string(item, "source_evidence_id")] = item
    return evidence


def _sequence(mapping: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    value = mapping.get(key)
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise ReviewerPacketError(f"{key} must be a list of objects")
    return value


def _string(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ReviewerPacketError(f"{key} must be a non-empty string")
    return value


def _string_list(mapping: Mapping[str, Any], key: str) -> list[str]:
    value = mapping.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise ReviewerPacketError(f"{key} must be a list of non-empty strings")
    return list(value)
