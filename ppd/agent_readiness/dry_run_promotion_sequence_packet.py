from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ppd.agent_readiness.offline_release_decision_packet import validate_offline_release_decision_packet

PACKET_TYPE = "ppd.dry_run_promotion_sequence_packet.v1"

_FORBIDDEN_TRUE_KEYS = {
    "active_mutation",
    "active_promotion",
    "active_promotion_enabled",
    "commit_to_registry",
    "live_promotion",
    "live_promotion_claim",
    "manifest_promotion_active",
    "mutate_guardrail_bundle",
    "mutate_guardrails",
    "mutate_manifest",
    "mutate_manifests",
    "mutate_process_model",
    "mutate_process_models",
    "mutate_registry",
    "mutate_registries",
    "performs_promotion",
    "production_promotion_enabled",
    "promote_to_active",
    "promote_to_live",
    "promotes_release",
    "promotion_enabled",
    "release_promoted",
    "uses_live_network",
    "write_active_guardrails",
    "write_active_manifest",
    "write_active_process_model",
    "write_active_registry",
    "writes_active_state",
}

_LIVE_PROMOTION_KEYS = {
    "active_promotion_claim",
    "live_promotion_claim",
    "production_promotion_claim",
    "promotion_claim",
    "release_claim",
}

_PRIVATE_OR_RUNTIME_RE = re.compile(
    r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/root/)|(^/tmp/)|(^/var/folders/)|"
    r"(auth[_-]?state|browser[_-]?state|cookie|credential|download[_-]?(path|url|ref)?|har|password|"
    r"private[_-]?path|raw[_-]?(archive|body|crawl|download|html)|session[_-]?state|screenshot|secret|"
    r"storage[_-]?state|token|trace\.zip|warc|\.warc(\.gz)?)",
    re.IGNORECASE,
)

_LIVE_PROMOTION_CLAIM_RE = re.compile(
    r"\b(live promotion enabled|production promotion enabled|promoted to active|active promotion enabled|release promoted)\b",
    re.IGNORECASE,
)

_NO_ACTIVE_STATE_EFFECTS = {
    "writes_active_registries": False,
    "writes_active_manifests": False,
    "writes_active_requirements": False,
    "writes_active_process_models": False,
    "writes_active_guardrails": False,
    "writes_source_indexes": False,
    "writes_agent_consumer_state": False,
    "promotes_release": False,
    "uses_live_network": False,
}


@dataclass(frozen=True)
class DryRunPromotionSequenceValidationResult:
    valid: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "problems": list(self.problems)}


def build_dry_run_promotion_sequence_packet(offline_release_decision_packet: Mapping[str, Any]) -> dict[str, Any]:
    """Build an ordered synthetic promotion sequence from an offline decision packet."""

    _raise_if_unsafe(offline_release_decision_packet)
    decision_validation = validate_offline_release_decision_packet(offline_release_decision_packet)
    if not decision_validation.valid:
        raise ValueError("invalid_source_offline_release_decision_packet: " + "; ".join(decision_validation.problems))

    packet_id = str(offline_release_decision_packet.get("packet_id") or "offline-release-decision-packet")
    source_packet_id = str(offline_release_decision_packet.get("source_packet_id") or packet_id)
    recommendations = _mapping_sequence(offline_release_decision_packet.get("recommendations"))
    blockers = _mapping_sequence(offline_release_decision_packet.get("unresolved_blocker_summaries"))
    command_refs = _mapping_sequence(offline_release_decision_packet.get("validation_command_references"))
    signoffs = _mapping_sequence(offline_release_decision_packet.get("operator_signoff_requests"))
    checkpoints = _mapping_sequence(offline_release_decision_packet.get("rollback_checkpoints"))
    attestations = _mapping_sequence(offline_release_decision_packet.get("no_promotion_attestations"))

    reviewer_owners = _reviewer_owners(signoffs)
    artifact_ids = _affected_artifact_ids(offline_release_decision_packet)
    evidence_ids = _packet_evidence_ids(offline_release_decision_packet)
    abort_conditions = _abort_conditions(blockers, command_refs, attestations)
    status = "blocked" if any(condition["severity"] == "blocking" for condition in abort_conditions) else "ready_for_operator_review"
    rollback_order = _rollback_order(checkpoints, artifact_ids, evidence_ids)

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_id": f"dry-run-sequence-for-{packet_id}",
        "fixture_only": True,
        "source_packet_type": "ppd.offline_release_decision_packet.v1",
        "source_packet_id": packet_id,
        "source_readiness_packet_id": source_packet_id,
        "sequence_status": status,
        "recommendation_decisions": [str(item.get("decision")) for item in recommendations if item.get("decision")],
        "prerequisite_validation_evidence": _prerequisite_validation_evidence(
            decision_packet_id=packet_id,
            blockers=blockers,
            command_refs=command_refs,
            signoffs=signoffs,
            checkpoints=checkpoints,
            attestations=attestations,
            evidence_ids=evidence_ids,
        ),
        "affected_artifact_ids": artifact_ids,
        "reviewer_owners": reviewer_owners,
        "ordered_synthetic_promotion_steps": _ordered_steps(
            artifact_ids=artifact_ids,
            evidence_ids=evidence_ids,
            reviewer_owners=reviewer_owners,
            abort_conditions=abort_conditions,
            rollback_order=rollback_order,
            blocked=status == "blocked",
        ),
        "rollback_order": rollback_order,
        "abort_conditions": abort_conditions,
        "active_state_effects": dict(_NO_ACTIVE_STATE_EFFECTS),
    }
    assert_valid_dry_run_promotion_sequence_packet(packet)
    return packet


def validate_dry_run_promotion_sequence_packet(packet: Mapping[str, Any]) -> DryRunPromotionSequenceValidationResult:
    problems: list[str] = []
    try:
        _raise_if_unsafe(packet)
    except ValueError as exc:
        problems.append(str(exc))

    if packet.get("packet_type") != PACKET_TYPE:
        problems.append("packet_type must be ppd.dry_run_promotion_sequence_packet.v1")
    if packet.get("fixture_only") is not True:
        problems.append("fixture_only must be true")
    if packet.get("source_packet_type") != "ppd.offline_release_decision_packet.v1":
        problems.append("source_packet_type must reference the offline release decision packet")

    required_lists = (
        "prerequisite_validation_evidence",
        "affected_artifact_ids",
        "reviewer_owners",
        "ordered_synthetic_promotion_steps",
        "rollback_order",
        "abort_conditions",
    )
    for key in required_lists:
        if not isinstance(packet.get(key), list) or not packet.get(key):
            problems.append(f"{key} must be a non-empty list")

    prerequisites = _mapping_sequence(packet.get("prerequisite_validation_evidence"))
    packet_artifact_ids = _string_set(packet.get("affected_artifact_ids"))
    reviewer_owners = _mapping_sequence(packet.get("reviewer_owners"))
    reviewer_owner_ids = {str(owner.get("owner_id")) for owner in reviewer_owners if owner.get("owner_id")}
    steps = _mapping_sequence(packet.get("ordered_synthetic_promotion_steps"))
    rollback_items = _mapping_sequence(packet.get("rollback_order"))
    rollback_ids = {str(item.get("rollback_id")) for item in rollback_items if item.get("rollback_id")}
    abort_conditions = _mapping_sequence(packet.get("abort_conditions"))
    abort_condition_ids = {str(condition.get("condition_id")) for condition in abort_conditions if condition.get("condition_id")}

    prerequisite_evidence_ids: set[str] = set()
    for index, prerequisite in enumerate(prerequisites):
        if not prerequisite.get("prerequisite_id"):
            problems.append(f"prerequisite_validation_evidence[{index}] lacks prerequisite_id")
        if not prerequisite.get("status"):
            problems.append(f"prerequisite_validation_evidence[{index}] lacks status")
        evidence_ids = _evidence_ids(prerequisite)
        if not evidence_ids:
            problems.append(f"prerequisite_validation_evidence[{index}] lacks evidence_ids")
        prerequisite_evidence_ids.update(evidence_ids)

    if not prerequisite_evidence_ids:
        problems.append("prerequisite_validation_evidence must cite at least one evidence id")
    if not packet_artifact_ids:
        problems.append("affected_artifact_ids must contain at least one artifact id")

    for index, owner in enumerate(reviewer_owners):
        if not owner.get("owner_id"):
            problems.append(f"reviewer_owners[{index}] lacks owner_id")
        if not owner.get("role"):
            problems.append(f"reviewer_owners[{index}] lacks role")
        if not owner.get("signoff_request_id"):
            problems.append(f"reviewer_owners[{index}] lacks signoff_request_id")
        if not _evidence_ids(owner):
            problems.append(f"reviewer_owners[{index}] lacks source_evidence_ids")

    actual_sequence = [_safe_int(step.get("sequence")) for step in steps]
    if actual_sequence != list(range(1, len(steps) + 1)):
        problems.append("ordered_synthetic_promotion_steps must use contiguous one-based sequence numbers")

    artifacts_cited_by_steps: set[str] = set()
    rollback_ids_cited_by_steps: set[str] = set()
    abort_ids_cited_by_steps: set[str] = set()
    for index, step in enumerate(steps):
        if step.get("synthetic_only") is not True:
            problems.append(f"ordered_synthetic_promotion_steps[{index}] must be synthetic_only")
        if step.get("writes_active_state") is not False:
            problems.append(f"ordered_synthetic_promotion_steps[{index}] must not write active state")

        step_evidence_ids = _string_set(step.get("prerequisite_evidence_ids"))
        if not step_evidence_ids:
            problems.append(f"ordered_synthetic_promotion_steps[{index}] lacks prerequisite_evidence_ids")
        elif prerequisite_evidence_ids and not step_evidence_ids.issubset(prerequisite_evidence_ids):
            problems.append(f"ordered_synthetic_promotion_steps[{index}] cites unknown prerequisite evidence ids")

        step_artifact_ids = _string_set(step.get("affected_artifact_ids"))
        artifacts_cited_by_steps.update(step_artifact_ids)
        if not step_artifact_ids:
            problems.append(f"ordered_synthetic_promotion_steps[{index}] lacks affected_artifact_ids")
        elif packet_artifact_ids and not step_artifact_ids.issubset(packet_artifact_ids):
            problems.append(f"ordered_synthetic_promotion_steps[{index}] cites affected_artifact_ids outside packet scope")

        reviewer_owner = step.get("reviewer_owner")
        if not reviewer_owner:
            problems.append(f"ordered_synthetic_promotion_steps[{index}] lacks reviewer_owner")
        elif reviewer_owner_ids and str(reviewer_owner) not in reviewer_owner_ids:
            problems.append(f"ordered_synthetic_promotion_steps[{index}] reviewer_owner is not declared in reviewer_owners")

        step_abort_ids = _string_set(step.get("abort_condition_ids"))
        abort_ids_cited_by_steps.update(step_abort_ids)
        if not step_abort_ids:
            problems.append(f"ordered_synthetic_promotion_steps[{index}] lacks abort_condition_ids")
        elif abort_condition_ids and not step_abort_ids.issubset(abort_condition_ids):
            problems.append(f"ordered_synthetic_promotion_steps[{index}] cites unknown abort_condition_ids")

        rollback_action_id = step.get("rollback_action_id") or step.get("rollback_id")
        if not rollback_action_id:
            problems.append(f"ordered_synthetic_promotion_steps[{index}] lacks rollback_action_id")
        else:
            rollback_ids_cited_by_steps.add(str(rollback_action_id))
            if rollback_ids and str(rollback_action_id) not in rollback_ids:
                problems.append(f"ordered_synthetic_promotion_steps[{index}] rollback_action_id is not declared in rollback_order")

    missing_step_artifacts = packet_artifact_ids.difference(artifacts_cited_by_steps)
    if missing_step_artifacts:
        problems.append("affected_artifact_ids must be cited by ordered_synthetic_promotion_steps: " + ", ".join(sorted(missing_step_artifacts)))

    for key, expected in _NO_ACTIVE_STATE_EFFECTS.items():
        effects = packet.get("active_state_effects") if isinstance(packet.get("active_state_effects"), Mapping) else {}
        if effects.get(key) is not expected:
            problems.append(f"active_state_effects.{key} must be false")

    for index, condition in enumerate(abort_conditions):
        if not condition.get("condition_id"):
            problems.append(f"abort_conditions[{index}] lacks condition_id")
        if condition.get("abort_when") in (None, ""):
            problems.append(f"abort_conditions[{index}] lacks abort_when")
        if not condition.get("owner"):
            problems.append(f"abort_conditions[{index}] lacks owner")
        if not condition.get("severity"):
            problems.append(f"abort_conditions[{index}] lacks severity")

    if abort_condition_ids and not abort_condition_ids.issubset(abort_ids_cited_by_steps):
        missing_abort_ids = abort_condition_ids.difference(abort_ids_cited_by_steps)
        problems.append("abort_conditions must be cited by ordered_synthetic_promotion_steps: " + ", ".join(sorted(missing_abort_ids)))

    rollback_sequence = [_safe_int(rollback.get("sequence")) for rollback in rollback_items]
    if rollback_sequence != list(range(1, len(rollback_items) + 1)):
        problems.append("rollback_order must use contiguous one-based sequence numbers")

    artifacts_cited_by_rollback: set[str] = set()
    rollback_evidence_ids: set[str] = set()
    for index, rollback in enumerate(rollback_items):
        if rollback.get("writes_active_state") is not False:
            problems.append(f"rollback_order[{index}] must not write active state")
        if not rollback.get("rollback_id"):
            problems.append(f"rollback_order[{index}] lacks rollback_id")
        if not rollback.get("rollback_action"):
            problems.append(f"rollback_order[{index}] lacks rollback_action")
        item_artifact_ids = _string_set(rollback.get("affected_artifact_ids"))
        if not item_artifact_ids:
            problems.append(f"rollback_order[{index}] lacks affected_artifact_ids")
        elif packet_artifact_ids and not item_artifact_ids.issubset(packet_artifact_ids):
            problems.append(f"rollback_order[{index}] cites affected_artifact_ids outside packet scope")
        artifacts_cited_by_rollback.update(item_artifact_ids)
        item_evidence_ids = _evidence_ids(rollback)
        if not item_evidence_ids:
            problems.append(f"rollback_order[{index}] lacks evidence_ids")
        rollback_evidence_ids.update(item_evidence_ids)

    missing_rollback_artifacts = packet_artifact_ids.difference(artifacts_cited_by_rollback)
    if missing_rollback_artifacts:
        problems.append("affected_artifact_ids must be rollbackable: " + ", ".join(sorted(missing_rollback_artifacts)))
    if rollback_ids_cited_by_steps and not rollback_ids_cited_by_steps.issubset(rollback_ids):
        missing_rollback_ids = rollback_ids_cited_by_steps.difference(rollback_ids)
        problems.append("ordered_synthetic_promotion_steps cite missing rollback actions: " + ", ".join(sorted(missing_rollback_ids)))
    if prerequisite_evidence_ids and rollback_evidence_ids and not rollback_evidence_ids.issubset(prerequisite_evidence_ids):
        problems.append("rollback_order evidence_ids must be cited by prerequisite_validation_evidence")

    return DryRunPromotionSequenceValidationResult(valid=not problems, problems=tuple(_dedupe(problems)))


def assert_valid_dry_run_promotion_sequence_packet(packet: Mapping[str, Any]) -> None:
    result = validate_dry_run_promotion_sequence_packet(packet)
    if not result.valid:
        raise ValueError("invalid_dry_run_promotion_sequence_packet: " + "; ".join(result.problems))


def _prerequisite_validation_evidence(
    *,
    decision_packet_id: str,
    blockers: list[Mapping[str, Any]],
    command_refs: list[Mapping[str, Any]],
    signoffs: list[Mapping[str, Any]],
    checkpoints: list[Mapping[str, Any]],
    attestations: list[Mapping[str, Any]],
    evidence_ids: list[str],
) -> list[dict[str, Any]]:
    failed_commands = [str(ref.get("command_ref_id") or index) for index, ref in enumerate(command_refs) if int(ref.get("returncode") or 0) != 0]
    false_attestations = [str(item.get("attestation_id") or index) for index, item in enumerate(attestations) if item.get("value") is not True]
    return [
        {
            "prerequisite_id": "offline-decision-packet-validated",
            "status": "satisfied",
            "summary": "Source decision packet passed offline release decision validation.",
            "source_packet_id": decision_packet_id,
            "evidence_ids": evidence_ids,
        },
        {
            "prerequisite_id": "validation-command-results-reviewed",
            "status": "blocked" if failed_commands else "satisfied",
            "summary": "All cited validation command results must be passing before operator review can proceed.",
            "validation_command_ref_ids": [str(ref.get("command_ref_id") or index) for index, ref in enumerate(command_refs)],
            "failed_validation_command_ref_ids": failed_commands,
            "evidence_ids": _collect_evidence(command_refs) or evidence_ids,
        },
        {
            "prerequisite_id": "operator-signoffs-identified",
            "status": "pending_operator_review",
            "summary": "Reviewer owners are identified, but this fixture does not record approval or promote state.",
            "reviewer_owners": _reviewer_owners(signoffs),
            "evidence_ids": _collect_evidence(signoffs) or evidence_ids,
        },
        {
            "prerequisite_id": "release-blockers-reviewed",
            "status": "blocked" if blockers else "satisfied",
            "summary": "Unresolved blockers abort synthetic promotion review until reconciled.",
            "blocker_ids": [str(blocker.get("blocker_id") or index) for index, blocker in enumerate(blockers)],
            "evidence_ids": _collect_evidence(blockers) or evidence_ids,
        },
        {
            "prerequisite_id": "rollback-checkpoints-present",
            "status": "satisfied" if checkpoints else "blocked",
            "summary": "Rollback checkpoints must be available before any reviewer go claim.",
            "checkpoint_ids": [str(checkpoint.get("checkpoint_id") or index) for index, checkpoint in enumerate(checkpoints)],
            "evidence_ids": _collect_evidence(checkpoints) or evidence_ids,
        },
        {
            "prerequisite_id": "no-active-promotion-attested",
            "status": "blocked" if false_attestations else "satisfied",
            "summary": "No-promotion attestations must remain true for a fixture-only sequence.",
            "false_attestation_ids": false_attestations,
            "evidence_ids": evidence_ids,
        },
    ]


def _ordered_steps(
    *,
    artifact_ids: list[str],
    evidence_ids: list[str],
    reviewer_owners: list[dict[str, Any]],
    abort_conditions: list[dict[str, Any]],
    rollback_order: list[dict[str, Any]],
    blocked: bool,
) -> list[dict[str, Any]]:
    owner = reviewer_owners[0]["owner_id"] if reviewer_owners else "ppd-release-operator"
    condition_ids = [condition["condition_id"] for condition in abort_conditions]
    rollback_action_id = "discard-synthetic-sequence"
    if rollback_action_id not in {str(item.get("rollback_id")) for item in rollback_order}:
        rollback_action_id = str(rollback_order[0].get("rollback_id") if rollback_order else "stop-before-active-state")
    status = "aborted_until_blockers_clear" if blocked else "ready_for_review"
    labels = [
        ("load-offline-decision-packet", "Load the cited offline decision packet as read-only fixture input."),
        ("verify-prerequisites", "Review validation command evidence, no-promotion attestations, signoff owners, and rollback checkpoints."),
        ("enumerate-affected-artifacts", "List only candidate and fixture artifact identifiers affected by the synthetic review."),
        ("stage-synthetic-promotion-order", "Create ordered dry-run promotion steps without writing active PP&D state."),
        ("review-abort-conditions", "Stop the sequence when blockers, failed commands, missing signoffs, or active-write requests appear."),
        ("confirm-no-active-writes", "End the dry run with all active registries, manifests, requirements, process models, guardrails, source indexes, and consumer state unchanged."),
    ]
    return [
        {
            "sequence": index,
            "step_id": step_id,
            "description": description,
            "status": status,
            "synthetic_only": True,
            "writes_active_state": False,
            "prerequisite_evidence_ids": evidence_ids,
            "affected_artifact_ids": artifact_ids,
            "reviewer_owner": owner,
            "abort_condition_ids": condition_ids,
            "rollback_action_id": rollback_action_id,
        }
        for index, (step_id, description) in enumerate(labels, start=1)
    ]


def _rollback_order(checkpoints: list[Mapping[str, Any]], artifact_ids: list[str], evidence_ids: list[str]) -> list[dict[str, Any]]:
    rollback = [
        {
            "sequence": 1,
            "rollback_id": "stop-before-active-state",
            "rollback_action": "Abort before any active PP&D write boundary is reached.",
            "affected_artifact_ids": artifact_ids,
            "evidence_ids": evidence_ids,
            "writes_active_state": False,
        },
        {
            "sequence": 2,
            "rollback_id": "discard-synthetic-sequence",
            "rollback_action": "Discard synthetic promotion steps and retain the source decision packet unchanged.",
            "affected_artifact_ids": artifact_ids,
            "evidence_ids": evidence_ids,
            "writes_active_state": False,
        },
    ]
    for offset, checkpoint in enumerate(reversed(checkpoints), start=3):
        rollback.append(
            {
                "sequence": offset,
                "rollback_id": str(checkpoint.get("checkpoint_id") or f"rollback-checkpoint-{offset}"),
                "rollback_action": str(checkpoint.get("checkpoint") or "Keep active PP&D state unchanged."),
                "affected_artifact_ids": [str(checkpoint.get("candidate_id") or "synthetic-release-candidate")],
                "evidence_ids": _evidence_ids(checkpoint) or evidence_ids,
                "writes_active_state": False,
            }
        )
    return rollback


def _abort_conditions(blockers: list[Mapping[str, Any]], command_refs: list[Mapping[str, Any]], attestations: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    conditions = [
        {
            "condition_id": "abort-on-active-state-write-request",
            "severity": "blocking",
            "abort_when": "Any step proposes writing active PP&D registries, manifests, requirements, process models, guardrails, source indexes, or agent consumer state.",
            "owner": "ppd-release-operator",
        },
        {
            "condition_id": "abort-on-missing-operator-signoff",
            "severity": "blocking",
            "abort_when": "A required reviewer owner is absent or has not completed attended review.",
            "owner": "ppd-release-operator",
        },
    ]
    for blocker in blockers:
        conditions.append(
            {
                "condition_id": f"abort-on-{blocker.get('blocker_id') or 'unresolved-blocker'}",
                "severity": "blocking",
                "abort_when": str(blocker.get("summary") or blocker.get("reason") or "Unresolved release blocker remains open."),
                "owner": "ppd-release-operator",
                "source_evidence_ids": _evidence_ids(blocker),
            }
        )
    for index, command_ref in enumerate(command_refs):
        if int(command_ref.get("returncode") or 0) != 0:
            conditions.append(
                {
                    "condition_id": f"abort-on-{command_ref.get('command_ref_id') or index}",
                    "severity": "blocking",
                    "abort_when": "A cited validation command did not pass.",
                    "owner": "validation-owner",
                    "source_evidence_ids": _evidence_ids(command_ref),
                }
            )
    for index, attestation in enumerate(attestations):
        if attestation.get("value") is not True:
            conditions.append(
                {
                    "condition_id": f"abort-on-{attestation.get('attestation_id') or index}",
                    "severity": "blocking",
                    "abort_when": "A no-promotion attestation is false or missing.",
                    "owner": "ppd-release-operator",
                }
            )
    return conditions


def _reviewer_owners(signoffs: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    owners: list[dict[str, Any]] = []
    for index, signoff in enumerate(signoffs):
        role = str(signoff.get("role") or "ppd_release_operator")
        owners.append(
            {
                "owner_id": role.replace("_", "-"),
                "role": role,
                "signoff_request_id": str(signoff.get("signoff_request_id") or signoff.get("signoff_id") or f"signoff-{index + 1}"),
                "required_before": "any_release_promotion_or_operator_go_claim",
                "source_evidence_ids": _evidence_ids(signoff),
            }
        )
    if not owners:
        owners.append(
            {
                "owner_id": "ppd-release-operator",
                "role": "ppd_release_operator",
                "signoff_request_id": "signoff-required",
                "required_before": "any_release_promotion_or_operator_go_claim",
                "source_evidence_ids": [],
            }
        )
    return owners


def _affected_artifact_ids(packet: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("packet_id", "source_packet_id", "source_readiness_packet_id"):
        if packet.get(key):
            values.append(str(packet[key]))
    for collection_key in (
        "recommendations",
        "unresolved_blocker_summaries",
        "operator_signoff_requests",
        "rollback_checkpoints",
        "validation_command_references",
    ):
        for item in _mapping_sequence(packet.get(collection_key)):
            for item_key in ("candidate_id", "command_ref_id", "recommendation_id", "checkpoint_id", "signoff_request_id"):
                if item.get(item_key):
                    values.append(str(item[item_key]))
    return _dedupe(values) or ["synthetic-release-candidate"]


def _packet_evidence_ids(packet: Mapping[str, Any]) -> list[str]:
    evidence: list[str] = []
    for key in (
        "recommendations",
        "unresolved_blocker_summaries",
        "operator_signoff_requests",
        "rollback_checkpoints",
        "validation_command_references",
    ):
        evidence.extend(_collect_evidence(_mapping_sequence(packet.get(key))))
    return _dedupe(evidence) or [str(packet.get("packet_id") or "offline-release-decision-packet")]


def _collect_evidence(items: Sequence[Mapping[str, Any]]) -> list[str]:
    evidence: list[str] = []
    for item in items:
        evidence.extend(_evidence_ids(item))
    return _dedupe(evidence)


def _evidence_ids(record: Mapping[str, Any]) -> list[str]:
    raw = record.get("source_evidence_ids") or record.get("validation_evidence_ids") or record.get("citation_ids") or record.get("evidence_ids") or []
    if isinstance(raw, str):
        return [raw] if raw else []
    if isinstance(raw, Sequence) and not isinstance(raw, (bytes, bytearray)):
        return [str(item) for item in raw if str(item)]
    return []


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _string_set(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value} if value else set()
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return {str(item) for item in value if str(item)}
    return set()


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _dedupe(values: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            deduped.append(value)
    return deduped


def _raise_if_unsafe(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).lower()
            child_path = f"{path}.{key}"
            if key_text in _FORBIDDEN_TRUE_KEYS and child is not False:
                if child not in (None, "", [], {}):
                    raise ValueError(f"active mutation or promotion flag must be false at {child_path}")
            if key_text in _LIVE_PROMOTION_KEYS and child not in (None, "", False, [], {}):
                raise ValueError(f"live promotion claims are not allowed at {child_path}")
            if _PRIVATE_OR_RUNTIME_RE.search(key_text):
                raise ValueError(f"raw archive/body/download or private reference field is not allowed at {child_path}")
            _raise_if_unsafe(child, child_path)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            _raise_if_unsafe(child, f"{path}[{index}]")
    elif isinstance(value, str):
        if _PRIVATE_OR_RUNTIME_RE.search(value):
            raise ValueError(f"raw archive/body/download or private reference is not allowed at {path}")
        if _LIVE_PROMOTION_CLAIM_RE.search(value):
            raise ValueError(f"live promotion claims are not allowed at {path}")
