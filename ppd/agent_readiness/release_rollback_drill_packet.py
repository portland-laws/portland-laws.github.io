from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ppd.agent_readiness.post_release_monitoring_plan_validation import validate_post_release_monitoring_plan
from ppd.agent_readiness.promotion_audit_log_candidate_packet import (
    validate_operator_promotion_approval_packet,
    validate_promotion_audit_log_candidate_packet,
)

PACKET_TYPE = "ppd.release_rollback_drill_packet.v1"

_FORBIDDEN_TRUE_KEYS = {
    "active_rollback",
    "active_rollback_started",
    "applies_rollback",
    "artifact_mutation_enabled",
    "cron_enabled",
    "invokes_crawlers",
    "invokes_devhub",
    "invokes_processors",
    "mutates_agent_state",
    "mutates_guardrails",
    "mutates_manifests",
    "mutates_process_models",
    "mutates_registries",
    "mutates_release_notes",
    "mutates_requirements",
    "mutates_schedules",
    "promotes_artifacts",
    "promotes_release",
    "rollback_executed",
    "schedule_active",
    "schedule_enabled",
    "uses_live_network",
    "writes_active_state",
    "writes_agent_state",
    "writes_guardrails",
    "writes_manifests",
    "writes_process_models",
    "writes_registries",
    "writes_release_notes",
    "writes_requirements",
    "writes_schedules",
}

_PRIVATE_OR_RUNTIME_RE = re.compile(
    r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/root/)|(^/tmp/)|"
    r"(auth[_-]?state|browser[_-]?state|cookie|credential|download[_-]?(path|url|ref)?|har|password|"
    r"private[_-]?path|raw[_-]?(archive|body|crawl|download|html)|session[_-]?state|screenshot|secret|"
    r"storage[_-]?state|token|trace\.zip|warc|\.warc(\.gz)?)",
    re.IGNORECASE,
)

_LIVE_OR_MUTATION_RE = re.compile(
    r"\b(active rollback executed|rollback executed|rolled back active|wrote active|updated active|"
    r"mutated registry|mutated manifest|published release notes|scheduled monitor|live devhub|live crawl|"
    r"submitted to devhub|uploaded to devhub|paid fees|scheduled inspection)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ReleaseRollbackDrillValidationResult:
    valid: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "problems": list(self.problems)}


def build_release_rollback_drill_packet(
    promotion_audit_log_candidate: Mapping[str, Any],
    operator_promotion_approval_packet: Mapping[str, Any],
    post_release_monitoring_plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a cited rollback drill packet without applying rollback actions."""

    _require_valid_inputs(promotion_audit_log_candidate, operator_promotion_approval_packet, post_release_monitoring_plan)
    packet = {
        "packet_type": PACKET_TYPE,
        "packet_id": "fixture-first-release-rollback-drill-packet",
        "fixture_only": True,
        "drill_status": "rollback_rehearsal_packet_only",
        "source_packet_ids": {
            "promotion_audit_log_candidate": _packet_id(promotion_audit_log_candidate),
            "operator_promotion_approval_packet": _packet_id(operator_promotion_approval_packet),
            "post_release_monitoring_plan": _packet_id(post_release_monitoring_plan, "post-release-monitoring-plan"),
        },
        "rollback_boundary": {
            "active_rollback": False,
            "rollback_executed": False,
            "mutates_registries": False,
            "mutates_manifests": False,
            "mutates_requirements": False,
            "mutates_process_models": False,
            "mutates_guardrails": False,
            "mutates_release_notes": False,
            "mutates_schedules": False,
            "mutates_agent_state": False,
            "uses_live_network": False,
            "invokes_devhub": False,
            "invokes_crawlers": False,
            "invokes_processors": False,
        },
        "rollback_decision_points": _rollback_decision_points(
            promotion_audit_log_candidate, operator_promotion_approval_packet
        ),
        "affected_artifact_references": _affected_artifact_references(promotion_audit_log_candidate),
        "reviewer_owner_fields": _reviewer_owner_fields(operator_promotion_approval_packet),
        "smoke_test_rerun_checklist": _smoke_test_rerun_checklist(post_release_monitoring_plan),
        "no_active_rollback_attestations": _no_active_rollback_attestations(
            promotion_audit_log_candidate, operator_promotion_approval_packet, post_release_monitoring_plan
        ),
    }
    assert_valid_release_rollback_drill_packet(packet)
    return packet


def validate_release_rollback_drill_packet(packet: Mapping[str, Any]) -> ReleaseRollbackDrillValidationResult:
    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append("packet_type must be ppd.release_rollback_drill_packet.v1")
    if packet.get("fixture_only") is not True:
        problems.append("fixture_only must be true")
    if packet.get("drill_status") != "rollback_rehearsal_packet_only":
        problems.append("drill_status must keep rollback as rehearsal metadata only")

    source_packet_ids = packet.get("source_packet_ids") if isinstance(packet.get("source_packet_ids"), Mapping) else {}
    for key in ("promotion_audit_log_candidate", "operator_promotion_approval_packet", "post_release_monitoring_plan"):
        if not source_packet_ids.get(key):
            problems.append(f"source_packet_ids.{key} is required")

    boundary = packet.get("rollback_boundary") if isinstance(packet.get("rollback_boundary"), Mapping) else {}
    if boundary.get("active_rollback") is not False:
        problems.append("rollback_boundary.active_rollback must be false")
    if boundary.get("rollback_executed") is not False:
        problems.append("rollback_boundary.rollback_executed must be false")
    for key in sorted(_FORBIDDEN_TRUE_KEYS):
        if key in boundary and boundary.get(key) is not False:
            problems.append(f"rollback_boundary.{key} must be false")

    decision_points = _mapping_sequence(packet.get("rollback_decision_points"))
    if not decision_points:
        problems.append("rollback_decision_points must be a non-empty list")
    for index, item in enumerate(decision_points):
        if not item.get("decision_point_id"):
            problems.append(f"rollback_decision_points[{index}] lacks decision_point_id")
        if not item.get("decision_owner"):
            problems.append(f"rollback_decision_points[{index}] lacks decision_owner")
        if not item.get("rollback_condition"):
            problems.append(f"rollback_decision_points[{index}] lacks rollback_condition")
        if item.get("active_rollback") is not False:
            problems.append(f"rollback_decision_points[{index}] must not activate rollback")
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"rollback_decision_points[{index}] lacks source_evidence_ids")

    artifact_refs = _mapping_sequence(packet.get("affected_artifact_references"))
    if not artifact_refs:
        problems.append("affected_artifact_references must be a non-empty list")
    for index, item in enumerate(artifact_refs):
        if not item.get("artifact_id"):
            problems.append(f"affected_artifact_references[{index}] lacks artifact_id")
        if item.get("active_artifact_mutation") is not False:
            problems.append(f"affected_artifact_references[{index}] must not mutate active artifacts")
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"affected_artifact_references[{index}] lacks source_evidence_ids")

    owners = _mapping_sequence(packet.get("reviewer_owner_fields"))
    if not owners:
        problems.append("reviewer_owner_fields must be a non-empty list")
    for index, item in enumerate(owners):
        if not item.get("reviewer_owner_id"):
            problems.append(f"reviewer_owner_fields[{index}] lacks reviewer_owner_id")
        if not item.get("reviewer_role"):
            problems.append(f"reviewer_owner_fields[{index}] lacks reviewer_role")
        if not item.get("approval_status"):
            problems.append(f"reviewer_owner_fields[{index}] lacks approval_status")
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"reviewer_owner_fields[{index}] lacks source_evidence_ids")

    smoke_tests = _mapping_sequence(packet.get("smoke_test_rerun_checklist"))
    if not smoke_tests:
        problems.append("smoke_test_rerun_checklist must be a non-empty list")
    for index, item in enumerate(smoke_tests):
        if not item.get("smoke_test_id"):
            problems.append(f"smoke_test_rerun_checklist[{index}] lacks smoke_test_id")
        if not item.get("reviewer_owner"):
            problems.append(f"smoke_test_rerun_checklist[{index}] lacks reviewer_owner")
        if not item.get("rerun_trigger"):
            problems.append(f"smoke_test_rerun_checklist[{index}] lacks rerun_trigger")
        if not item.get("escalation_note"):
            problems.append(f"smoke_test_rerun_checklist[{index}] lacks escalation_note")
        if item.get("schedule_enabled") is not False:
            problems.append(f"smoke_test_rerun_checklist[{index}] must keep schedules disabled")
        if item.get("writes_active_state") is not False:
            problems.append(f"smoke_test_rerun_checklist[{index}] must not write active state")
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"smoke_test_rerun_checklist[{index}] lacks source_evidence_ids")

    attestations = _mapping_sequence(packet.get("no_active_rollback_attestations"))
    if not attestations:
        problems.append("no_active_rollback_attestations must be a non-empty list")
    for index, item in enumerate(attestations):
        if item.get("attested") is not True:
            problems.append(f"no_active_rollback_attestations[{index}] must be attested")
        if item.get("active_rollback") is not False:
            problems.append(f"no_active_rollback_attestations[{index}] must keep active_rollback false")
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"no_active_rollback_attestations[{index}] lacks source_evidence_ids")

    problems.extend(_recursive_safety_problems(packet))
    return ReleaseRollbackDrillValidationResult(valid=not problems, problems=tuple(_dedupe(problems)))


def assert_valid_release_rollback_drill_packet(packet: Mapping[str, Any]) -> None:
    result = validate_release_rollback_drill_packet(packet)
    if not result.valid:
        raise ValueError("invalid_release_rollback_drill_packet: " + "; ".join(result.problems))


def _require_valid_inputs(audit_packet: Mapping[str, Any], approval_packet: Mapping[str, Any], monitoring_plan: Mapping[str, Any]) -> None:
    audit_result = validate_promotion_audit_log_candidate_packet(audit_packet)
    if not audit_result.valid:
        raise ValueError("invalid_source_promotion_audit_log_candidate: " + "; ".join(audit_result.problems))
    approval_result = validate_operator_promotion_approval_packet(approval_packet)
    if not approval_result.valid:
        raise ValueError("invalid_source_operator_promotion_approval_packet: " + "; ".join(approval_result.problems))
    monitoring_result = validate_post_release_monitoring_plan(monitoring_plan)
    if not monitoring_result.ready:
        raise ValueError("invalid_source_post_release_monitoring_plan: " + "; ".join(monitoring_result.problems))


def _rollback_decision_points(audit_packet: Mapping[str, Any], approval_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    owner = _primary_owner(approval_packet)
    points: list[dict[str, Any]] = []
    for entry in _mapping_sequence(audit_packet.get("audit_entry_candidates")):
        entry_id = str(entry.get("audit_entry_id") or "audit-entry")
        evidence_ids = _evidence_ids(entry) or _packet_evidence_ids(audit_packet)
        rollback_links = _mapping_sequence(entry.get("rollback_links"))
        if rollback_links:
            for link in rollback_links:
                rollback_id = str(link.get("rollback_id") or "rollback")
                points.append(
                    {
                        "decision_point_id": f"decision.{entry_id}.{rollback_id}",
                        "source_audit_entry_id": entry_id,
                        "rollback_link_id": rollback_id,
                        "rollback_condition": str(link.get("rollback_action") or "Abort and keep active PP&D state unchanged."),
                        "decision_owner": owner.get("reviewer_owner_id"),
                        "reviewer_role": owner.get("reviewer_role"),
                        "active_rollback": False,
                        "decision_status": "pending_human_review",
                        "source_evidence_ids": _dedupe(evidence_ids + _evidence_ids(link) + _evidence_ids(owner)),
                    }
                )
    return points


def _affected_artifact_references(audit_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in _mapping_sequence(audit_packet.get("audit_entry_candidates")):
        entry_id = str(entry.get("audit_entry_id") or "audit-entry")
        for artifact in _mapping_sequence(entry.get("affected_artifact_refs")):
            artifact_id = str(artifact.get("artifact_id") or "artifact")
            key = f"{entry_id}:{artifact_id}"
            if key in seen:
                continue
            seen.add(key)
            refs.append(
                {
                    "artifact_id": artifact_id,
                    "artifact_role": str(artifact.get("artifact_role") or "candidate_or_fixture_reference"),
                    "source_audit_entry_id": entry_id,
                    "reference_status": "affected_candidate_reference_only",
                    "active_artifact_mutation": False,
                    "source_evidence_ids": _dedupe(_evidence_ids(artifact) + _evidence_ids(entry)),
                }
            )
    return refs


def _reviewer_owner_fields(approval_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for signoff in _mapping_sequence(approval_packet.get("reviewer_signoffs")):
        fields.append(
            {
                "reviewer_owner_id": str(signoff.get("reviewer_id") or "ppd-release-operator"),
                "reviewer_role": str(signoff.get("reviewer_role") or "ppd_release_operator"),
                "approval_id": str(signoff.get("approval_id") or approval_packet.get("packet_id") or "operator-approval"),
                "approval_status": str(approval_packet.get("approval_status") or "approved_for_fixture_audit_candidate"),
                "signed_at": str(signoff.get("signed_at") or "1970-01-01T00:00:00Z"),
                "rollback_review_status": "pending_human_review",
                "source_evidence_ids": _dedupe(_evidence_ids(signoff) + _packet_evidence_ids(approval_packet)),
            }
        )
    return fields


def _smoke_test_rerun_checklist(monitoring_plan: Mapping[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for check in _mapping_sequence(monitoring_plan.get("monitoring_checks")):
        check_id = str(check.get("check_id") or "post-release-check")
        checks.append(
            {
                "smoke_test_id": f"rerun.{check_id}",
                "source_monitoring_check_id": check_id,
                "description": str(check.get("description") or "Rerun the cited post-release monitoring check before any rollback decision."),
                "reviewer_owner": str(check.get("reviewer_owner") or check.get("reviewer_owner_id") or "ppd-release-operator"),
                "rerun_trigger": "rollback_decision_review",
                "escalation_note": str(check.get("escalation_note") or "Escalate failed rerun results before any active rollback is considered."),
                "alert_threshold": check.get("alert_threshold") or check.get("threshold") or {},
                "schedule_enabled": False,
                "writes_active_state": False,
                "source_evidence_ids": _evidence_ids(check) or _packet_evidence_ids(monitoring_plan),
            }
        )
    return checks


def _no_active_rollback_attestations(*packets: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "attestation_id": f"no-active-rollback.{_packet_id(packet, 'packet')}",
            "source_packet_id": _packet_id(packet, "packet"),
            "attested": True,
            "active_rollback": False,
            "summary": "Consumed as committed fixture metadata only; no active rollback, release mutation, schedule activation, live crawl, DevHub action, or agent-state write is authorized.",
            "source_evidence_ids": _packet_evidence_ids(packet),
        }
        for packet in packets
    ]


def _primary_owner(approval_packet: Mapping[str, Any]) -> dict[str, Any]:
    fields = _reviewer_owner_fields(approval_packet)
    if fields:
        return fields[0]
    return {
        "reviewer_owner_id": "ppd-release-operator",
        "reviewer_role": "ppd_release_operator",
        "source_evidence_ids": _packet_evidence_ids(approval_packet),
    }


def _packet_id(packet: Mapping[str, Any], fallback: str = "packet") -> str:
    return str(packet.get("packet_id") or packet.get("plan_id") or fallback)


def _packet_evidence_ids(*packets: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for packet in packets:
        for _, child in _walk(packet):
            if isinstance(child, Mapping):
                values.extend(_evidence_ids(child))
    return _dedupe(values) or ["release-rollback-drill-fixture-evidence"]


def _evidence_ids(item: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for key in ("source_evidence_ids", "evidence_ids", "prerequisite_evidence_ids"):
        values.extend(_string_list(item.get(key)))
    return _dedupe(values)


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value else []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [str(item) for item in value if str(item)]
    return []


def _recursive_safety_problems(value: Any) -> list[str]:
    problems: list[str] = []
    for path, child in _walk(value):
        leaf = _path_leaf(path)
        if isinstance(child, bool) and child is True and leaf in _FORBIDDEN_TRUE_KEYS:
            problems.append(f"rollback drill mutation or live-operation flag must not be true at {path}")
        if isinstance(child, str):
            if _PRIVATE_OR_RUNTIME_RE.search(child):
                problems.append(f"private, runtime, raw, or downloaded artifact reference is not allowed at {path}")
            if _LIVE_OR_MUTATION_RE.search(child):
                problems.append(f"active rollback, live operation, or mutation claim is not allowed at {path}")
    return problems


def _walk(value: Any, path: str = "") -> list[tuple[str, Any]]:
    rows = [(path or "$", value)]
    if isinstance(value, Mapping):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else str(key)
            rows.extend(_walk(child, child_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child in enumerate(value):
            child_path = f"{path}.{index}" if path else str(index)
            rows.extend(_walk(child, child_path))
    return rows


def _path_leaf(path: str) -> str:
    parts = [part for part in path.rstrip(".").split(".") if part and not part.isdigit()]
    return parts[-1] if parts else ""


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
