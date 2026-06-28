from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from ppd.agent_readiness.dry_run_promotion_sequence_packet import validate_dry_run_promotion_sequence_packet
from ppd.agent_readiness.operator_signoff import validate_operator_signoff_readiness_packet

PACKET_TYPE = "ppd.promotion_audit_log_candidate_packet.v1"
APPROVAL_PACKET_TYPE = "ppd.operator_promotion_approval_packet.v1"

_FALSE_POLICY_KEYS = {
    "writes_operational_audit_log",
    "appends_audit_ledger",
    "promotes_artifacts",
    "writes_active_state",
    "uses_live_network",
    "invokes_devhub",
    "invokes_crawlers",
    "invokes_processors",
    "reads_private_case_files",
}

_REQUIRED_ENTRY_LISTS = (
    "cited_prerequisites",
    "affected_artifact_refs",
    "reviewer_owner_fields",
    "rollback_links",
    "retention_notes",
    "source_evidence_ids",
)

_PRIVATE_OR_RUNTIME_RE = re.compile(
    r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/root/)|(^/tmp/)|(^/var/folders/)|"
    r"(auth[_-]?state|browser[_-]?state|cookie|credential|download[_-]?(path|url|ref)?|har|password|"
    r"private[_-]?path|raw[_-]?(archive|body|crawl|download|html)|session[_-]?state|screenshot|secret|"
    r"storage[_-]?state|token|trace\.zip|warc|\.warc(\.gz)?)",
    re.IGNORECASE,
)

_RAW_REFERENCE_RE = re.compile(
    r"\b(raw crawl|raw download|raw archive|raw html|raw body|downloaded document|archive output|warc|crawl output)\b",
    re.IGNORECASE,
)

_MUTATION_FLAG_KEYS = {
    "writes_operational_audit_log",
    "appends_audit_ledger",
    "promotes_artifacts",
    "promotes_release",
    "writes_active_state",
    "uses_live_network",
    "invokes_devhub",
    "invokes_crawlers",
    "invokes_processors",
    "active_artifact_mutation",
    "artifact_mutation_active",
    "artifacts_mutated",
    "mutates_artifacts",
    "writes_artifacts",
    "updates_active_artifacts",
}

_LIVE_CLAIM_RE = re.compile(
    r"\b(promoted to active|release promoted|operational audit log written|audit log written|write audit log|"
    r"wrote audit log|appended to audit ledger|logged to active ledger|ledger entry written|submitted to devhub|"
    r"uploaded to devhub|paid fees|scheduled inspection|certified application)\b",
    re.IGNORECASE,
)

_OUTCOME_GUARANTEE_RE = re.compile(
    r"\b(guarantee[sd]? (permit|approval|issuance|inspection|legal|permitting)|approval guaranteed|"
    r"permit (will|shall) be (approved|issued)|inspection (will|shall) pass|legally compliant|legal advice|"
    r"permitting outcome guaranteed|certain approval|assured approval)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class PromotionAuditLogCandidateValidationResult:
    valid: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "problems": list(self.problems)}


def build_promotion_audit_log_candidate_packet(
    dry_run_promotion_sequence_packet: Mapping[str, Any],
    operator_promotion_approval_packet: Mapping[str, Any],
) -> dict[str, Any]:
    """Build deterministic audit-entry candidates without writing an operational audit log."""

    _require_valid_sources(dry_run_promotion_sequence_packet, operator_promotion_approval_packet)
    dry_run_packet_id = _packet_id(dry_run_promotion_sequence_packet, "dry-run-promotion-sequence-packet")
    approval_packet_id = _packet_id(operator_promotion_approval_packet, "operator-promotion-approval-packet")
    entries = _audit_entries(dry_run_promotion_sequence_packet, operator_promotion_approval_packet)
    packet = {
        "packet_type": PACKET_TYPE,
        "packet_id": "fixture-first-promotion-audit-log-candidate-packet",
        "fixture_only": True,
        "candidate_status": "candidate_entries_not_written",
        "source_packet_ids": {
            "dry_run_promotion_sequence_packet": dry_run_packet_id,
            "operator_promotion_approval_packet": approval_packet_id,
        },
        "audit_log_policy": {
            "fixtures_only": True,
            "writes_operational_audit_log": False,
            "appends_audit_ledger": False,
            "promotes_artifacts": False,
            "writes_active_state": False,
            "uses_live_network": False,
            "invokes_devhub": False,
            "invokes_crawlers": False,
            "invokes_processors": False,
            "reads_private_case_files": False,
        },
        "audit_entry_candidates": entries,
        "packet_retention_notes": [
            {
                "retention_note_id": "retain-candidate-with-fixtures",
                "summary": "Retain this packet as committed fixture metadata only; it is not an operational audit log and does not append to any ledger.",
                "source_evidence_ids": _packet_evidence_ids(dry_run_promotion_sequence_packet, operator_promotion_approval_packet),
            }
        ],
    }
    assert_valid_promotion_audit_log_candidate_packet(packet)
    return packet


def validate_promotion_audit_log_candidate_packet(packet: Mapping[str, Any]) -> PromotionAuditLogCandidateValidationResult:
    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append("packet_type must be ppd.promotion_audit_log_candidate_packet.v1")
    if packet.get("fixture_only") is not True:
        problems.append("fixture_only must be true")
    if packet.get("candidate_status") != "candidate_entries_not_written":
        problems.append("candidate_status must keep audit entries unwritten")

    source_packet_ids = packet.get("source_packet_ids") if isinstance(packet.get("source_packet_ids"), Mapping) else {}
    for key in ("dry_run_promotion_sequence_packet", "operator_promotion_approval_packet"):
        if not source_packet_ids.get(key):
            problems.append(f"source_packet_ids.{key} is required")

    policy = packet.get("audit_log_policy") if isinstance(packet.get("audit_log_policy"), Mapping) else {}
    if policy.get("fixtures_only") is not True:
        problems.append("audit_log_policy.fixtures_only must be true")
    for key in sorted(_FALSE_POLICY_KEYS):
        if policy.get(key) is not False:
            problems.append(f"audit_log_policy.{key} must be false")

    entries = _mapping_sequence(packet.get("audit_entry_candidates"))
    if not entries:
        problems.append("audit_entry_candidates must be a non-empty list")
    expected_sequence = list(range(1, len(entries) + 1))
    actual_sequence = [_safe_int(entry.get("sequence")) for entry in entries]
    if actual_sequence != expected_sequence:
        problems.append("audit_entry_candidates must use contiguous one-based sequence numbers")

    cited_entry_ids: set[str] = set()
    for index, entry in enumerate(entries):
        if not entry.get("audit_entry_id"):
            problems.append(f"audit_entry_candidates[{index}] lacks audit_entry_id")
        else:
            cited_entry_ids.add(str(entry.get("audit_entry_id")))
        if entry.get("synthetic_only") is not True:
            problems.append(f"audit_entry_candidates[{index}] must be synthetic_only")
        if entry.get("writes_operational_audit_log") is not False:
            problems.append(f"audit_entry_candidates[{index}] must not write an operational audit log")
        if entry.get("promotes_artifacts") is not False:
            problems.append(f"audit_entry_candidates[{index}] must not promote artifacts")
        for key in _REQUIRED_ENTRY_LISTS:
            if not isinstance(entry.get(key), list) or not entry.get(key):
                problems.append(f"audit_entry_candidates[{index}].{key} must be a non-empty list")
        if not _string_list(entry.get("source_evidence_ids")):
            problems.append(f"audit_entry_candidates[{index}] is uncited")
        for item_key in ("cited_prerequisites", "affected_artifact_refs", "rollback_links", "retention_notes"):
            for item_index, item in enumerate(_mapping_sequence(entry.get(item_key))):
                if not _string_list(item.get("source_evidence_ids")):
                    problems.append(f"audit_entry_candidates[{index}].{item_key}[{item_index}] lacks source_evidence_ids")
        for owner in _mapping_sequence(entry.get("reviewer_owner_fields")):
            if not owner.get("reviewer_owner_id"):
                problems.append(f"audit_entry_candidates[{index}] has reviewer owner without reviewer_owner_id")
            if not owner.get("approval_status"):
                problems.append(f"audit_entry_candidates[{index}] has reviewer owner without approval_status")
            if not _string_list(owner.get("source_evidence_ids")):
                problems.append(f"audit_entry_candidates[{index}] has uncited reviewer owner")

    for index, note in enumerate(_mapping_sequence(packet.get("packet_retention_notes"))):
        if not note.get("retention_note_id"):
            problems.append(f"packet_retention_notes[{index}] lacks retention_note_id")
        if not _string_list(note.get("source_evidence_ids")):
            problems.append(f"packet_retention_notes[{index}] lacks source_evidence_ids")

    problems.extend(_recursive_safety_problems(packet))
    return PromotionAuditLogCandidateValidationResult(valid=not problems, problems=tuple(_dedupe(problems)))


def assert_valid_promotion_audit_log_candidate_packet(packet: Mapping[str, Any]) -> None:
    result = validate_promotion_audit_log_candidate_packet(packet)
    if not result.valid:
        raise ValueError("invalid_promotion_audit_log_candidate_packet: " + "; ".join(result.problems))


def validate_operator_promotion_approval_packet(packet: Mapping[str, Any]) -> PromotionAuditLogCandidateValidationResult:
    problems: list[str] = []
    signoff_result = validate_operator_signoff_readiness_packet(packet)
    if not signoff_result.ready:
        problems.extend(signoff_result.problems)
    if packet.get("packet_type") != APPROVAL_PACKET_TYPE:
        problems.append("operator approval packet_type must be ppd.operator_promotion_approval_packet.v1")
    if packet.get("fixture_only") is not True:
        problems.append("operator approval fixture_only must be true")
    if packet.get("approval_status") != "approved_for_fixture_audit_candidate":
        problems.append("operator approval status must be approved_for_fixture_audit_candidate")
    if str(packet.get("approval_scope") or "") != "fixture_audit_candidate_only":
        problems.append("operator approval scope must be fixture_audit_candidate_only")
    if not _mapping_sequence(packet.get("reviewer_signoffs")):
        problems.append("operator approval packet must include reviewer_signoffs")
    if not _string_list(packet.get("approved_source_packet_ids")):
        problems.append("operator approval packet must cite approved_source_packet_ids")
    problems.extend(_recursive_safety_problems(packet))
    return PromotionAuditLogCandidateValidationResult(valid=not problems, problems=tuple(_dedupe(problems)))


def _require_valid_sources(dry_run_packet: Mapping[str, Any], approval_packet: Mapping[str, Any]) -> None:
    dry_run_result = validate_dry_run_promotion_sequence_packet(dry_run_packet)
    if not dry_run_result.valid:
        raise ValueError("invalid_source_dry_run_promotion_sequence_packet: " + "; ".join(dry_run_result.problems))
    approval_result = validate_operator_promotion_approval_packet(approval_packet)
    if not approval_result.valid:
        raise ValueError("invalid_source_operator_promotion_approval_packet: " + "; ".join(approval_result.problems))
    approved_ids = set(_string_list(approval_packet.get("approved_source_packet_ids")))
    dry_run_packet_id = _packet_id(dry_run_packet, "dry-run-promotion-sequence-packet")
    if dry_run_packet_id not in approved_ids:
        raise ValueError("operator promotion approval packet must cite the dry-run promotion sequence packet")


def _audit_entries(dry_run_packet: Mapping[str, Any], approval_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    prerequisites = _prerequisite_refs(dry_run_packet)
    artifact_refs = _artifact_refs(dry_run_packet)
    reviewer_fields = _reviewer_owner_fields(dry_run_packet, approval_packet)
    rollback_links = _rollback_links(dry_run_packet)
    approval_evidence = _packet_evidence_ids(approval_packet)
    entries: list[dict[str, Any]] = []
    for step in _mapping_sequence(dry_run_packet.get("ordered_synthetic_promotion_steps")):
        sequence = _safe_int(step.get("sequence"))
        step_id = str(step.get("step_id") or f"synthetic-step-{sequence}")
        step_evidence = _evidence_ids(step) or _packet_evidence_ids(dry_run_packet)
        entries.append(
            {
                "sequence": sequence,
                "audit_entry_id": f"audit-candidate-{sequence:02d}-{step_id}",
                "event_type": "synthetic_promotion_step_reviewed",
                "event_summary": str(step.get("description") or "Synthetic promotion step reviewed for audit candidate generation."),
                "synthetic_only": True,
                "writes_operational_audit_log": False,
                "promotes_artifacts": False,
                "source_step_id": step_id,
                "source_packet_refs": ["dry_run_promotion_sequence_packet", "operator_promotion_approval_packet"],
                "cited_prerequisites": prerequisites,
                "affected_artifact_refs": artifact_refs,
                "reviewer_owner_fields": reviewer_fields,
                "rollback_links": rollback_links,
                "retention_notes": [
                    {
                        "retention_note_id": f"retain-{step_id}",
                        "summary": "Retain as fixture audit-entry candidate metadata only; discard or regenerate before any operational audit-log process.",
                        "source_evidence_ids": _dedupe(step_evidence + approval_evidence),
                    }
                ],
                "source_evidence_ids": _dedupe(step_evidence + approval_evidence),
            }
        )
    return entries


def _prerequisite_refs(dry_run_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for item in _mapping_sequence(dry_run_packet.get("prerequisite_validation_evidence")):
        refs.append(
            {
                "prerequisite_id": str(item.get("prerequisite_id") or "prerequisite"),
                "status": str(item.get("status") or "unknown"),
                "source_evidence_ids": _evidence_ids(item),
            }
        )
    return refs


def _artifact_refs(dry_run_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    evidence_ids = _packet_evidence_ids(dry_run_packet)
    return [
        {
            "artifact_id": artifact_id,
            "artifact_role": "candidate_or_fixture_reference",
            "source_packet_ref": "dry_run_promotion_sequence_packet",
            "source_evidence_ids": evidence_ids,
        }
        for artifact_id in _string_list(dry_run_packet.get("affected_artifact_ids"))
    ]


def _reviewer_owner_fields(dry_run_packet: Mapping[str, Any], approval_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    signoffs = _mapping_sequence(approval_packet.get("reviewer_signoffs"))
    primary_signoff = signoffs[0] if signoffs else {}
    fields: list[dict[str, Any]] = []
    for owner in _mapping_sequence(dry_run_packet.get("reviewer_owners")):
        fields.append(
            {
                "reviewer_owner_id": str(owner.get("owner_id") or "ppd-release-operator"),
                "role": str(owner.get("role") or primary_signoff.get("reviewer_role") or "ppd_release_operator"),
                "signoff_request_id": str(owner.get("signoff_request_id") or "signoff-required"),
                "approval_id": str(primary_signoff.get("approval_id") or approval_packet.get("packet_id") or "operator-approval"),
                "approval_status": str(approval_packet.get("approval_status") or "approved_for_fixture_audit_candidate"),
                "approved_by_reviewer_id": str(primary_signoff.get("reviewer_id") or "operator-reviewer"),
                "signed_at": str(primary_signoff.get("signed_at") or approval_packet.get("approved_at") or "1970-01-01T00:00:00Z"),
                "source_evidence_ids": _dedupe(_evidence_ids(owner) + _evidence_ids(primary_signoff) + _packet_evidence_ids(approval_packet)),
            }
        )
    return fields


def _rollback_links(dry_run_packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for item in _mapping_sequence(dry_run_packet.get("rollback_order")):
        links.append(
            {
                "rollback_id": str(item.get("rollback_id") or "rollback"),
                "rollback_action": str(item.get("rollback_action") or "Keep active PP&D state unchanged."),
                "affected_artifact_ids": _string_list(item.get("affected_artifact_ids")),
                "source_evidence_ids": _evidence_ids(item),
            }
        )
    return links


def _recursive_safety_problems(value: Any) -> list[str]:
    problems: list[str] = []
    for path, child in _walk(value):
        if isinstance(child, str):
            if _PRIVATE_OR_RUNTIME_RE.search(child):
                problems.append(f"private or runtime artifact reference is not allowed at {path}")
            if _RAW_REFERENCE_RE.search(child):
                problems.append(f"raw crawl/download/archive reference is not allowed at {path}")
            if _LIVE_CLAIM_RE.search(child):
                problems.append(f"live execution or operational audit claim is not allowed at {path}")
            if _OUTCOME_GUARANTEE_RE.search(child):
                problems.append(f"legal or permitting outcome guarantee is not allowed at {path}")
        elif isinstance(child, bool):
            leaf = _path_leaf(path)
            if child is True and leaf in _MUTATION_FLAG_KEYS:
                problems.append(f"mutation or live-operation flag must not be true at {path}")
    return problems


def _packet_id(packet: Mapping[str, Any], fallback: str) -> str:
    return str(packet.get("packet_id") or packet.get("plan_id") or fallback)


def _packet_evidence_ids(*packets: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for packet in packets:
        for _, child in _walk(packet):
            if isinstance(child, Mapping):
                values.extend(_evidence_ids(child))
    return _dedupe(values) or ["promotion-audit-candidate-fixture-evidence"]


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


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


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
