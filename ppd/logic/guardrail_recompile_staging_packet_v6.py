"""Fixture-first guardrail recompile staging packet v6.

This module intentionally consumes committed fixtures only. It does not crawl,
open DevHub, read private documents, upload, submit, certify, pay, schedule, or
activate guardrails.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PACKET_VERSION = "guardrail_recompile_staging_packet_v6"
QUEUE_VERSION = "process_model_refresh_impact_queue_v6"
INACTIVE_STATUS = "inactive_staged_only"

PROHIBITED_OPERATIONS = (
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
)

OFFLINE_VALIDATION_COMMANDS = (
    ("python3", "-m", "py_compile", "ppd/logic/guardrail_recompile_staging_packet_v6.py"),
    ("python3", "-m", "pytest", "ppd/tests/test_guardrail_recompile_staging_packet_v6.py"),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

PRESERVATION_CHECK_TYPES = (
    "exact_confirmation_preservation",
    "refused_action_preservation",
)

MUTATION_FLAGS = {
    "active_activation",
    "active_activation_claim",
    "active_bundle_mutation",
    "active_guardrail_bundle_mutation",
    "active_guardrail_mutation",
    "active_mutation",
    "active_mutation_claim",
    "activate_guardrails",
    "activation_claim",
    "guardrail_bundle_mutation_claim",
    "guardrail_mutation_claim",
    "guardrails_changed",
    "guardrail_bundles_changed",
    "mutation_claim",
    "mutates_active_guardrails",
    "updates_active_guardrails",
}

PRIVATE_KEY_FRAGMENTS = (
    "auth",
    "browser_state",
    "cookie",
    "credential",
    "har",
    "password",
    "private_artifact",
    "session",
    "storage_state",
    "trace",
)

FORBIDDEN_STRING_FRAGMENTS = (
    "activated guardrails",
    "active activation",
    "active guardrail mutation",
    "authenticated devhub",
    "completed official action",
    "crawl executed",
    "final payment completed",
    "guarantee approval",
    "legal guarantee",
    "live crawl",
    "live devhub",
    "official action completed",
    "opened devhub",
    "permit will be approved",
    "permitting guarantee",
    "scheduled inspection",
    "submitted permit",
    "uploaded correction",
)


@dataclass(frozen=True)
class GuardrailRecompileStagingPacketV6ValidationResult:
    valid: bool
    problems: tuple[str, ...]


class GuardrailRecompileStagingPacketV6ValidationError(ValueError):
    """Raised when a guardrail recompile staging packet v6 is invalid."""


def load_process_model_refresh_impact_queue_v6(fixture_path: str | Path) -> dict[str, Any]:
    """Load and validate a process model refresh impact queue v6 fixture."""
    path = Path(fixture_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("queue_version") != QUEUE_VERSION:
        raise ValueError(f"expected queue_version {QUEUE_VERSION!r}")
    if not isinstance(payload.get("items"), list):
        raise ValueError("process model refresh impact queue fixture must include an items list")
    return payload


def build_guardrail_recompile_staging_packet_v6(fixture_path: str | Path) -> dict[str, Any]:
    """Build an inactive staging packet from a queue fixture.

    The output is deterministic and contains only staging metadata. It is not an
    activation artifact and deliberately carries stop gates for stale evidence.
    """
    queue = load_process_model_refresh_impact_queue_v6(fixture_path)
    items = sorted(queue["items"], key=lambda item: item.get("refresh_impact_id", ""))

    candidates: list[dict[str, Any]] = []
    process_impact_references: list[dict[str, Any]] = []
    carry_forward_rows: list[dict[str, Any]] = []
    predicate_placeholders: list[dict[str, Any]] = []
    preservation_checks: list[dict[str, Any]] = []
    stale_evidence_stop_gates: list[dict[str, Any]] = []
    rollback_comparison_rows: list[dict[str, Any]] = []
    reviewer_signoff_placeholders: list[dict[str, Any]] = []

    for item in items:
        refresh_impact_id = _required_string(item, "refresh_impact_id")
        process_id = _required_string(item, "process_id")
        bundle_candidate_id = _required_string(item, "bundle_candidate_id")
        source_evidence_ids = sorted(_text_sequence(item.get("source_evidence_ids")))
        stale_evidence = sorted(_text_sequence(item.get("stale_evidence")))
        candidate_status = "blocked_stale_evidence" if stale_evidence else INACTIVE_STATUS

        process_impact_references.append(
            {
                "refresh_impact_id": refresh_impact_id,
                "process_id": process_id,
                "bundle_candidate_id": bundle_candidate_id,
                "source_evidence_ids": source_evidence_ids,
                "impact_status": "staged_for_inactive_recompile_review",
            }
        )

        candidates.append(
            {
                "refresh_impact_id": refresh_impact_id,
                "process_id": process_id,
                "permit_type": item.get("permit_type", "unknown"),
                "bundle_candidate_id": bundle_candidate_id,
                "current_guardrail_bundle_id": item.get("current_guardrail_bundle_id"),
                "activation_status": "inactive",
                "candidate_status": candidate_status,
                "source_evidence_ids": source_evidence_ids,
                "stale_evidence_ids": stale_evidence,
                "deterministic_predicate_refresh_placeholder_ids": sorted(
                    predicate.get("predicate_id")
                    for predicate in item.get("deterministic_predicates", [])
                    if predicate.get("predicate_id")
                ),
            }
        )

        for row in item.get("source_evidence_carry_forward", []):
            carry_forward_rows.append(
                {
                    "refresh_impact_id": refresh_impact_id,
                    "process_id": process_id,
                    "evidence_id": _required_string(row, "evidence_id"),
                    "source_id": row.get("source_id"),
                    "carry_forward_status": row.get("carry_forward_status", "pending_reviewer_check"),
                    "reason": row.get("reason", "fixture_staged_carry_forward"),
                }
            )

        for predicate in item.get("deterministic_predicates", []):
            predicate_placeholders.append(
                {
                    "refresh_impact_id": refresh_impact_id,
                    "process_id": process_id,
                    "predicate_id": _required_string(predicate, "predicate_id"),
                    "refresh_status": "placeholder_only",
                    "inputs": deepcopy(predicate.get("inputs", [])),
                    "expected_result": predicate.get("expected_result", "pending_fixture_confirmation"),
                }
            )

        preservation_checks.append(
            {
                "refresh_impact_id": refresh_impact_id,
                "process_id": process_id,
                "check_type": "exact_confirmation_preservation",
                "preserved_action_ids": sorted(_text_sequence(item.get("exact_confirmation_action_ids"))),
                "status": "placeholder_pending_review",
            }
        )
        preservation_checks.append(
            {
                "refresh_impact_id": refresh_impact_id,
                "process_id": process_id,
                "check_type": "refused_action_preservation",
                "preserved_action_ids": sorted(_text_sequence(item.get("refused_action_ids"))),
                "status": "placeholder_pending_review",
            }
        )

        if stale_evidence:
            stale_evidence_stop_gates.append(
                {
                    "refresh_impact_id": refresh_impact_id,
                    "process_id": process_id,
                    "gate": "stop_on_stale_evidence",
                    "stale_evidence_ids": stale_evidence,
                    "blocks_activation": True,
                    "resolution_placeholder": "reviewer_must_refresh_or_retire_evidence_before_activation",
                }
            )

        rollback_comparison_rows.append(
            {
                "refresh_impact_id": refresh_impact_id,
                "process_id": process_id,
                "baseline_guardrail_bundle_id": item.get("rollback_baseline_bundle_id"),
                "candidate_guardrail_bundle_id": bundle_candidate_id,
                "comparison_status": "placeholder_pending_offline_diff",
                "rollback_available": bool(item.get("rollback_baseline_bundle_id")),
            }
        )

        for role in item.get("reviewer_roles", []):
            reviewer_signoff_placeholders.append(
                {
                    "refresh_impact_id": refresh_impact_id,
                    "process_id": process_id,
                    "reviewer_role": role,
                    "signoff_status": "not_signed",
                    "signed_at": None,
                    "notes": "fixture_placeholder_only",
                }
            )

    packet = {
        "packet_version": PACKET_VERSION,
        "source_queue_version": queue["queue_version"],
        "generated_from_fixture": str(Path(fixture_path)),
        "activation_status": "inactive",
        "side_effect_policy": "offline_fixture_only",
        "prohibited_operations": list(PROHIBITED_OPERATIONS),
        "process_impact_references": sorted(process_impact_references, key=lambda row: row["refresh_impact_id"]),
        "inactive_guardrail_bundle_candidates": candidates,
        "source_evidence_carry_forward_rows": sorted(carry_forward_rows, key=lambda row: (row["refresh_impact_id"], row["evidence_id"])),
        "deterministic_predicate_refresh_placeholders": sorted(
            predicate_placeholders,
            key=lambda row: (row["refresh_impact_id"], row["predicate_id"]),
        ),
        "exact_confirmation_and_refused_action_preservation_checks": sorted(
            preservation_checks,
            key=lambda row: (row["refresh_impact_id"], row["check_type"]),
        ),
        "stale_evidence_stop_gates": sorted(stale_evidence_stop_gates, key=lambda row: row["refresh_impact_id"]),
        "rollback_comparison_rows": sorted(rollback_comparison_rows, key=lambda row: row["refresh_impact_id"]),
        "reviewer_signoff_placeholders": sorted(
            reviewer_signoff_placeholders,
            key=lambda row: (row["refresh_impact_id"], row["reviewer_role"]),
        ),
        "offline_validation_commands": [list(command) for command in OFFLINE_VALIDATION_COMMANDS],
    }
    require_valid_guardrail_recompile_staging_packet_v6(packet)
    return packet


def validate_guardrail_recompile_staging_packet_v6(
    packet: Mapping[str, Any],
) -> GuardrailRecompileStagingPacketV6ValidationResult:
    problems: list[str] = []
    if not isinstance(packet, Mapping):
        return GuardrailRecompileStagingPacketV6ValidationResult(False, ("packet must be an object",))

    if packet.get("packet_version") != PACKET_VERSION:
        problems.append(f"packet_version must be {PACKET_VERSION}")
    if packet.get("source_queue_version") != QUEUE_VERSION:
        problems.append(f"source_queue_version must be {QUEUE_VERSION}")
    if packet.get("activation_status") != "inactive":
        problems.append("activation_status must be inactive")
    if packet.get("side_effect_policy") != "offline_fixture_only":
        problems.append("side_effect_policy must be offline_fixture_only")
    if packet.get("prohibited_operations") != list(PROHIBITED_OPERATIONS):
        problems.append("prohibited_operations must exactly match the offline prohibited operation list")
    if packet.get("offline_validation_commands") != [list(command) for command in OFFLINE_VALIDATION_COMMANDS]:
        problems.append("offline_validation_commands must exactly match the staging packet validation commands")

    process_refs = _mapping_sequence(packet.get("process_impact_references"))
    candidates = _mapping_sequence(packet.get("inactive_guardrail_bundle_candidates"))
    carry_rows = _mapping_sequence(packet.get("source_evidence_carry_forward_rows"))
    predicate_rows = _mapping_sequence(packet.get("deterministic_predicate_refresh_placeholders"))
    preservation_rows = _mapping_sequence(packet.get("exact_confirmation_and_refused_action_preservation_checks"))
    stop_gates = _mapping_sequence(packet.get("stale_evidence_stop_gates"))
    rollback_rows = _mapping_sequence(packet.get("rollback_comparison_rows"))
    signoff_rows = _mapping_sequence(packet.get("reviewer_signoff_placeholders"))

    required_sections = {
        "process_impact_references": process_refs,
        "inactive_guardrail_bundle_candidates": candidates,
        "source_evidence_carry_forward_rows": carry_rows,
        "deterministic_predicate_refresh_placeholders": predicate_rows,
        "exact_confirmation_and_refused_action_preservation_checks": preservation_rows,
        "rollback_comparison_rows": rollback_rows,
        "reviewer_signoff_placeholders": signoff_rows,
    }
    for key, rows in required_sections.items():
        if not rows:
            problems.append(f"{key} must be non-empty")

    candidate_by_impact = {_text(row.get("refresh_impact_id")): row for row in candidates}
    impact_ids = sorted(candidate_by_impact)
    if not impact_ids:
        problems.append("inactive_guardrail_bundle_candidates must include at least one refresh impact")

    for index, candidate in enumerate(candidates):
        prefix = f"inactive_guardrail_bundle_candidates[{index}]"
        refresh_impact_id = _text(candidate.get("refresh_impact_id"))
        process_id = _text(candidate.get("process_id"))
        bundle_candidate_id = _text(candidate.get("bundle_candidate_id"))
        source_evidence_ids = _text_sequence(candidate.get("source_evidence_ids"))
        stale_evidence_ids = _text_sequence(candidate.get("stale_evidence_ids"))
        placeholder_ids = _text_sequence(candidate.get("deterministic_predicate_refresh_placeholder_ids"))
        if not refresh_impact_id:
            problems.append(f"{prefix}.refresh_impact_id must be present")
        if not process_id:
            problems.append(f"{prefix}.process_id must be present")
        if not bundle_candidate_id:
            problems.append(f"{prefix}.bundle_candidate_id must be present")
        if candidate.get("activation_status") != "inactive":
            problems.append(f"{prefix}.activation_status must be inactive")
        if candidate.get("candidate_status") not in {INACTIVE_STATUS, "blocked_stale_evidence"}:
            problems.append(f"{prefix}.candidate_status must be inactive staged or blocked stale evidence")
        if not source_evidence_ids:
            problems.append(f"{prefix}.source_evidence_ids must be non-empty")
        if not placeholder_ids:
            problems.append(f"{prefix}.deterministic_predicate_refresh_placeholder_ids must be non-empty")
        if stale_evidence_ids and candidate.get("candidate_status") != "blocked_stale_evidence":
            problems.append(f"{prefix}.candidate_status must block activation when stale evidence is present")

    process_ref_by_impact = {_text(row.get("refresh_impact_id")): row for row in process_refs}
    for impact_id, candidate in candidate_by_impact.items():
        process_ref = process_ref_by_impact.get(impact_id)
        if process_ref is None:
            problems.append(f"process_impact_references must include {impact_id}")
            continue
        if _text(process_ref.get("process_id")) != _text(candidate.get("process_id")):
            problems.append(f"process_impact_references[{impact_id}].process_id must match candidate")
        if _text(process_ref.get("bundle_candidate_id")) != _text(candidate.get("bundle_candidate_id")):
            problems.append(f"process_impact_references[{impact_id}].bundle_candidate_id must match candidate")
        if sorted(_text_sequence(process_ref.get("source_evidence_ids"))) != sorted(_text_sequence(candidate.get("source_evidence_ids"))):
            problems.append(f"process_impact_references[{impact_id}].source_evidence_ids must match candidate")
        if process_ref.get("impact_status") != "staged_for_inactive_recompile_review":
            problems.append(f"process_impact_references[{impact_id}].impact_status must be staged_for_inactive_recompile_review")

    _validate_carry_forward_rows(candidates, carry_rows, problems)
    _validate_predicate_rows(candidates, predicate_rows, problems)
    _validate_preservation_rows(candidates, preservation_rows, problems)
    _validate_stale_stop_gates(candidates, stop_gates, problems)
    _validate_rollback_rows(candidates, rollback_rows, problems)
    _validate_signoff_rows(candidates, signoff_rows, problems)
    _validate_no_forbidden_state(packet, problems)
    return GuardrailRecompileStagingPacketV6ValidationResult(not problems, tuple(problems))


def require_valid_guardrail_recompile_staging_packet_v6(packet: Mapping[str, Any]) -> None:
    result = validate_guardrail_recompile_staging_packet_v6(packet)
    if not result.valid:
        raise GuardrailRecompileStagingPacketV6ValidationError(
            "invalid guardrail recompile staging packet v6: " + "; ".join(result.problems)
        )


def _validate_carry_forward_rows(
    candidates: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    problems: list[str],
) -> None:
    row_keys = {(_text(row.get("refresh_impact_id")), _text(row.get("evidence_id"))) for row in rows}
    for index, row in enumerate(rows):
        prefix = f"source_evidence_carry_forward_rows[{index}]"
        for key in ("refresh_impact_id", "process_id", "evidence_id", "source_id", "carry_forward_status", "reason"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} must be present")
        if row.get("carry_forward_status") != "pending_reviewer_check":
            problems.append(f"{prefix}.carry_forward_status must be pending_reviewer_check")
    for candidate in candidates:
        impact_id = _text(candidate.get("refresh_impact_id"))
        for evidence_id in _text_sequence(candidate.get("source_evidence_ids")):
            if (impact_id, evidence_id) not in row_keys:
                problems.append(f"source_evidence_carry_forward_rows must include {impact_id}/{evidence_id}")


def _validate_predicate_rows(
    candidates: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    problems: list[str],
) -> None:
    row_keys = {(_text(row.get("refresh_impact_id")), _text(row.get("predicate_id"))) for row in rows}
    for index, row in enumerate(rows):
        prefix = f"deterministic_predicate_refresh_placeholders[{index}]"
        for key in ("refresh_impact_id", "process_id", "predicate_id", "refresh_status", "expected_result"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} must be present")
        if row.get("refresh_status") != "placeholder_only":
            problems.append(f"{prefix}.refresh_status must be placeholder_only")
        if not _text_sequence(row.get("inputs")):
            problems.append(f"{prefix}.inputs must be non-empty")
    for candidate in candidates:
        impact_id = _text(candidate.get("refresh_impact_id"))
        for predicate_id in _text_sequence(candidate.get("deterministic_predicate_refresh_placeholder_ids")):
            if (impact_id, predicate_id) not in row_keys:
                problems.append(f"deterministic_predicate_refresh_placeholders must include {impact_id}/{predicate_id}")


def _validate_preservation_rows(
    candidates: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    problems: list[str],
) -> None:
    rows_by_impact: dict[str, set[str]] = {}
    for index, row in enumerate(rows):
        prefix = f"exact_confirmation_and_refused_action_preservation_checks[{index}]"
        impact_id = _text(row.get("refresh_impact_id"))
        check_type = _text(row.get("check_type"))
        rows_by_impact.setdefault(impact_id, set()).add(check_type)
        for key in ("refresh_impact_id", "process_id", "check_type", "status"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} must be present")
        if check_type not in PRESERVATION_CHECK_TYPES:
            problems.append(f"{prefix}.check_type must be an exact-confirmation or refused-action preservation check")
        if row.get("status") != "placeholder_pending_review":
            problems.append(f"{prefix}.status must be placeholder_pending_review")
        if not _text_sequence(row.get("preserved_action_ids")):
            problems.append(f"{prefix}.preserved_action_ids must be non-empty")
    for candidate in candidates:
        impact_id = _text(candidate.get("refresh_impact_id"))
        missing = set(PRESERVATION_CHECK_TYPES) - rows_by_impact.get(impact_id, set())
        for check_type in sorted(missing):
            problems.append(f"exact_confirmation_and_refused_action_preservation_checks must include {impact_id}/{check_type}")


def _validate_stale_stop_gates(
    candidates: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    problems: list[str],
) -> None:
    row_by_impact = {_text(row.get("refresh_impact_id")): row for row in rows}
    for index, row in enumerate(rows):
        prefix = f"stale_evidence_stop_gates[{index}]"
        for key in ("refresh_impact_id", "process_id", "gate", "resolution_placeholder"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} must be present")
        if row.get("gate") != "stop_on_stale_evidence":
            problems.append(f"{prefix}.gate must be stop_on_stale_evidence")
        if row.get("blocks_activation") is not True:
            problems.append(f"{prefix}.blocks_activation must be true")
        if not _text_sequence(row.get("stale_evidence_ids")):
            problems.append(f"{prefix}.stale_evidence_ids must be non-empty")
    for candidate in candidates:
        impact_id = _text(candidate.get("refresh_impact_id"))
        stale_evidence_ids = _text_sequence(candidate.get("stale_evidence_ids"))
        if not stale_evidence_ids:
            continue
        gate = row_by_impact.get(impact_id)
        if gate is None:
            problems.append(f"stale_evidence_stop_gates must include {impact_id}")
        elif sorted(_text_sequence(gate.get("stale_evidence_ids"))) != sorted(stale_evidence_ids):
            problems.append(f"stale_evidence_stop_gates[{impact_id}].stale_evidence_ids must match candidate")


def _validate_rollback_rows(
    candidates: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    problems: list[str],
) -> None:
    row_by_impact = {_text(row.get("refresh_impact_id")): row for row in rows}
    for index, row in enumerate(rows):
        prefix = f"rollback_comparison_rows[{index}]"
        for key in ("refresh_impact_id", "process_id", "baseline_guardrail_bundle_id", "candidate_guardrail_bundle_id", "comparison_status"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} must be present")
        if row.get("comparison_status") != "placeholder_pending_offline_diff":
            problems.append(f"{prefix}.comparison_status must be placeholder_pending_offline_diff")
        if row.get("rollback_available") is not True:
            problems.append(f"{prefix}.rollback_available must be true")
    for candidate in candidates:
        impact_id = _text(candidate.get("refresh_impact_id"))
        row = row_by_impact.get(impact_id)
        if row is None:
            problems.append(f"rollback_comparison_rows must include {impact_id}")
        elif _text(row.get("candidate_guardrail_bundle_id")) != _text(candidate.get("bundle_candidate_id")):
            problems.append(f"rollback_comparison_rows[{impact_id}].candidate_guardrail_bundle_id must match candidate")


def _validate_signoff_rows(
    candidates: Sequence[Mapping[str, Any]],
    rows: Sequence[Mapping[str, Any]],
    problems: list[str],
) -> None:
    impacts_with_signoffs = {_text(row.get("refresh_impact_id")) for row in rows}
    for index, row in enumerate(rows):
        prefix = f"reviewer_signoff_placeholders[{index}]"
        for key in ("refresh_impact_id", "process_id", "reviewer_role", "signoff_status", "notes"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} must be present")
        if row.get("signoff_status") != "not_signed":
            problems.append(f"{prefix}.signoff_status must be not_signed")
        if row.get("signed_at") is not None:
            problems.append(f"{prefix}.signed_at must be null")
    for candidate in candidates:
        impact_id = _text(candidate.get("refresh_impact_id"))
        if impact_id not in impacts_with_signoffs:
            problems.append(f"reviewer_signoff_placeholders must include at least one row for {impact_id}")


def _validate_no_forbidden_state(value: Any, problems: list[str], path: str = "packet") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            normalized = key_text.lower().replace("-", "_").replace(" ", "_")
            child_path = f"{path}.{key_text}"
            if normalized in MUTATION_FLAGS and child is not False:
                problems.append(f"{child_path} must be false or absent")
            if any(fragment in normalized for fragment in PRIVATE_KEY_FRAGMENTS):
                problems.append(f"{child_path} must not include private/session/auth artifact keys")
            _validate_no_forbidden_state(child, problems, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _validate_no_forbidden_state(child, problems, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.lower()
        for fragment in FORBIDDEN_STRING_FRAGMENTS:
            if fragment in lowered:
                problems.append(f"{path} must not contain forbidden claim: {fragment}")


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"expected non-empty string field {key!r}")
    return value


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _text_sequence(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in (_text(item) for item in value) if item]


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
