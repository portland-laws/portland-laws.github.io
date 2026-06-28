"""Fixture-first PP&D release acceptance review packets.

The packet assembled here is a review artifact only. It consumes already-loaded
fixture packets and produces acceptance checklist metadata without publishing a
release, launching automation, or mutating registries, manifests, requirements,
process models, guardrails, prompts, release notes, schedules, or agent state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence


PACKET_TYPE = "ppd.fixture_first_release_acceptance_review_packet.v1"

_REQUIRED_INPUTS = (
    "source_registry_schedule_update_candidate",
    "requirement_rerun_work_queue_packet",
    "process_model_impact_review_packet",
    "devhub_surface_registry_reviewer_approval_packet",
    "agent_prompt_regression_dry_run_packet",
    "release_rollback_drill_outcome_review_packet",
)

_NO_MUTATION_ATTESTATIONS = (
    "no_publication_performed",
    "no_registry_mutation",
    "no_manifest_mutation",
    "no_requirement_mutation",
    "no_process_model_mutation",
    "no_guardrail_mutation",
    "no_prompt_mutation",
    "no_release_notes_mutation",
    "no_schedule_mutation",
    "no_agent_state_mutation",
    "no_artifact_mutation",
)


@dataclass(frozen=True)
class ReleaseAcceptanceReviewValidationResult:
    valid: bool
    problems: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "problems": list(self.problems)}


class ReleaseAcceptanceReviewPacketError(ValueError):
    """Raised when a release acceptance review packet is incomplete."""


def build_release_acceptance_review_packet(inputs: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic fixture-first release acceptance review packet."""

    source_packets = {name: _mapping(inputs.get(name)) for name in _REQUIRED_INPUTS}
    missing = [name for name, packet in source_packets.items() if not packet]
    if missing:
        raise ReleaseAcceptanceReviewPacketError("missing required source packets: " + ", ".join(missing))

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_id": str(inputs.get("packet_id") or "fixture-first-release-acceptance-review-packet"),
        "fixture_first": True,
        "review_status": "pending_reviewer_acceptance",
        "consumed_packets": _consumed_packets(source_packets),
        "go_no_go_checklist_items": _go_no_go_checklist_items(source_packets),
        "open_blocker_dispositions": _open_blocker_dispositions(source_packets),
        "reviewer_owner_signoff_slots": _reviewer_owner_signoff_slots(source_packets),
        "validation_rerun_expectations": _validation_rerun_expectations(source_packets),
        "no_publication_no_artifact_mutation_attestations": _no_mutation_attestations(source_packets),
        "release_effects": {
            "publishes_release": False,
            "mutates_registries": False,
            "mutates_manifests": False,
            "mutates_requirements": False,
            "mutates_process_models": False,
            "mutates_guardrails": False,
            "mutates_prompts": False,
            "mutates_release_notes": False,
            "mutates_schedules": False,
            "mutates_agent_state": False,
            "mutates_artifacts": False,
            "uses_live_network": False,
            "launches_devhub": False,
            "invokes_llm_consumers": False,
            "invokes_processors": False,
        },
    }
    assert_valid_release_acceptance_review_packet(packet)
    return packet


def validate_release_acceptance_review_packet(packet: Mapping[str, Any]) -> ReleaseAcceptanceReviewValidationResult:
    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append("packet_type must be ppd.fixture_first_release_acceptance_review_packet.v1")
    if packet.get("fixture_first") is not True:
        problems.append("fixture_first must be true")

    consumed = _mapping(packet.get("consumed_packets"))
    for name in _REQUIRED_INPUTS:
        item = _mapping(consumed.get(name))
        if not item.get("packet_id"):
            problems.append(f"consumed_packets.{name}.packet_id is required")
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"consumed_packets.{name}.source_evidence_ids is required")

    for index, item in enumerate(_mapping_sequence(packet.get("go_no_go_checklist_items"))):
        if not item.get("checklist_item_id"):
            problems.append(f"go_no_go_checklist_items[{index}].checklist_item_id is required")
        if item.get("go_no_go") not in {"go_pending_signoff", "no_go_until_resolved"}:
            problems.append(f"go_no_go_checklist_items[{index}].go_no_go is invalid")
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"go_no_go_checklist_items[{index}].source_evidence_ids is required")

    for index, item in enumerate(_mapping_sequence(packet.get("open_blocker_dispositions"))):
        if not item.get("blocker_id"):
            problems.append(f"open_blocker_dispositions[{index}].blocker_id is required")
        if not item.get("disposition"):
            problems.append(f"open_blocker_dispositions[{index}].disposition is required")
        if not item.get("owner"):
            problems.append(f"open_blocker_dispositions[{index}].owner is required")
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"open_blocker_dispositions[{index}].source_evidence_ids is required")

    for index, item in enumerate(_mapping_sequence(packet.get("reviewer_owner_signoff_slots"))):
        if not item.get("reviewer_role"):
            problems.append(f"reviewer_owner_signoff_slots[{index}].reviewer_role is required")
        if not item.get("owner"):
            problems.append(f"reviewer_owner_signoff_slots[{index}].owner is required")
        if item.get("status") != "pending":
            problems.append(f"reviewer_owner_signoff_slots[{index}].status must be pending")
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"reviewer_owner_signoff_slots[{index}].source_evidence_ids is required")

    for index, item in enumerate(_mapping_sequence(packet.get("validation_rerun_expectations"))):
        if not item.get("validation_id"):
            problems.append(f"validation_rerun_expectations[{index}].validation_id is required")
        if not item.get("command"):
            problems.append(f"validation_rerun_expectations[{index}].command is required")
        if item.get("writes_active_artifacts") is not False:
            problems.append(f"validation_rerun_expectations[{index}].writes_active_artifacts must be false")
        if not _string_list(item.get("source_evidence_ids")):
            problems.append(f"validation_rerun_expectations[{index}].source_evidence_ids is required")

    attestations = _mapping(packet.get("no_publication_no_artifact_mutation_attestations"))
    for key in _NO_MUTATION_ATTESTATIONS:
        if attestations.get(key) is not True:
            problems.append(f"no_publication_no_artifact_mutation_attestations.{key} must be true")

    effects = _mapping(packet.get("release_effects"))
    for key, value in effects.items():
        if value is not False:
            problems.append(f"release_effects.{key} must be false")

    if not _mapping_sequence(packet.get("go_no_go_checklist_items")):
        problems.append("go_no_go_checklist_items must be non-empty")
    if not _mapping_sequence(packet.get("open_blocker_dispositions")):
        problems.append("open_blocker_dispositions must be non-empty")
    if not _mapping_sequence(packet.get("reviewer_owner_signoff_slots")):
        problems.append("reviewer_owner_signoff_slots must be non-empty")
    if not _mapping_sequence(packet.get("validation_rerun_expectations")):
        problems.append("validation_rerun_expectations must be non-empty")

    return ReleaseAcceptanceReviewValidationResult(valid=not problems, problems=tuple(dict.fromkeys(problems)))


def assert_valid_release_acceptance_review_packet(packet: Mapping[str, Any]) -> None:
    result = validate_release_acceptance_review_packet(packet)
    if not result.valid:
        raise ReleaseAcceptanceReviewPacketError("invalid release acceptance review packet: " + "; ".join(result.problems))


def _consumed_packets(source_packets: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        name: {
            "packet_id": _packet_id(packet, name),
            "consumed_for": _consumed_for(name),
            "source_evidence_ids": _evidence_ids(packet, name),
        }
        for name, packet in source_packets.items()
    }


def _go_no_go_checklist_items(source_packets: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "checklist_item_id": "registry-schedule-candidate-reviewed",
            "title": "Source registry schedule update candidate remains review-only",
            "go_no_go": "go_pending_signoff",
            "required_condition": "Candidate has cited adjustments and no active registry or schedule mutation.",
            "source_evidence_ids": _evidence_ids(source_packets["source_registry_schedule_update_candidate"], "source_registry_schedule_update_candidate"),
        },
        {
            "checklist_item_id": "requirement-rerun-queue-reviewed",
            "title": "Requirement rerun work queue is metadata-only",
            "go_no_go": "go_pending_signoff",
            "required_condition": "Rerun steps cite requirement, process, and guardrail references without live extraction.",
            "source_evidence_ids": _evidence_ids(source_packets["requirement_rerun_work_queue_packet"], "requirement_rerun_work_queue_packet"),
        },
        {
            "checklist_item_id": "process-impact-reviewed",
            "title": "Process-model impact review keeps blocked-action carryovers visible",
            "go_no_go": "go_pending_signoff",
            "required_condition": "Process-stage impacts and prompt implications are reviewer-owned and non-mutating.",
            "source_evidence_ids": _evidence_ids(source_packets["process_model_impact_review_packet"], "process_model_impact_review_packet"),
        },
        {
            "checklist_item_id": "devhub-surface-approval-reviewed",
            "title": "DevHub surface registry reviewer approval remains offline",
            "go_no_go": "go_pending_signoff",
            "required_condition": "Selector approvals, manual handoffs, and redaction attestations are cited before any surface promotion.",
            "source_evidence_ids": _evidence_ids(source_packets["devhub_surface_registry_reviewer_approval_packet"], "devhub_surface_registry_reviewer_approval_packet"),
        },
        {
            "checklist_item_id": "agent-prompt-regression-reviewed",
            "title": "Agent prompt regression dry run has rerun expectations",
            "go_no_go": "go_pending_signoff",
            "required_condition": "Prompt/refusal before-after outcomes are cited and require fixture-only reruns.",
            "source_evidence_ids": _evidence_ids(source_packets["agent_prompt_regression_dry_run_packet"], "agent_prompt_regression_dry_run_packet"),
        },
        {
            "checklist_item_id": "rollback-outcome-reviewed",
            "title": "Rollback drill outcome review carries no-publication guardrails",
            "go_no_go": "go_pending_signoff",
            "required_condition": "Rollback observations, thresholds, and artifact references are cited and review-only.",
            "source_evidence_ids": _evidence_ids(source_packets["release_rollback_drill_outcome_review_packet"], "release_rollback_drill_outcome_review_packet"),
        },
    ]


def _open_blocker_dispositions(source_packets: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    dispositions: list[dict[str, Any]] = []
    for name, packet in source_packets.items():
        for index, blocker in enumerate(_candidate_blockers(packet)):
            dispositions.append(
                {
                    "blocker_id": str(blocker.get("blocker_id") or blocker.get("id") or f"{name}-blocker-{index + 1}"),
                    "source_packet_id": _packet_id(packet, name),
                    "summary": str(blocker.get("summary") or blocker.get("description") or blocker.get("reason") or "Reviewer disposition required before release acceptance."),
                    "disposition": str(blocker.get("disposition") or "open_pending_reviewer_resolution"),
                    "owner": _owner_from_packet(packet, f"{name}-review-owner"),
                    "source_evidence_ids": _evidence_ids(blocker, name) or _evidence_ids(packet, name),
                }
            )
    if dispositions:
        return dispositions
    return [
        {
            "blocker_id": "release-acceptance-reviewer-signoff-required",
            "source_packet_id": "fixture-first-release-acceptance-review-packet",
            "summary": "Release acceptance remains open until all reviewer-owner signoff slots are completed.",
            "disposition": "open_pending_reviewer_signoff",
            "owner": "ppd-release-acceptance-owner",
            "source_evidence_ids": ["release_acceptance_review#reviewer_owner_signoff_slots"],
        }
    ]


def _reviewer_owner_signoff_slots(source_packets: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    roles = (
        ("source_registry_schedule_update_candidate", "source registry schedule reviewer"),
        ("requirement_rerun_work_queue_packet", "requirement rerun reviewer"),
        ("process_model_impact_review_packet", "process-model impact reviewer"),
        ("devhub_surface_registry_reviewer_approval_packet", "DevHub surface registry reviewer"),
        ("agent_prompt_regression_dry_run_packet", "agent prompt regression reviewer"),
        ("release_rollback_drill_outcome_review_packet", "rollback outcome reviewer"),
    )
    slots: list[dict[str, Any]] = []
    for name, role in roles:
        packet = source_packets[name]
        slots.append(
            {
                "signoff_slot_id": f"signoff-{name.replace('_', '-')}",
                "reviewer_role": role,
                "owner": _owner_from_packet(packet, f"ppd-{name.replace('_', '-')}-owner"),
                "status": "pending",
                "acceptance_effect": "review_packet_only_no_publication",
                "source_evidence_ids": _evidence_ids(packet, name),
            }
        )
    return slots


def _validation_rerun_expectations(source_packets: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    evidence = _evidence_ids(source_packets["agent_prompt_regression_dry_run_packet"], "agent_prompt_regression_dry_run_packet")
    return [
        {
            "validation_id": "ppd-daemon-self-test",
            "command": ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
            "expected_result": "pass_before_release_acceptance",
            "writes_active_artifacts": False,
            "source_evidence_ids": evidence,
        },
        {
            "validation_id": "ppd-unit-fixture-suite",
            "command": ["python3", "-m", "unittest", "discover", "-s", "ppd/tests", "-p", "test_*.py"],
            "expected_result": "pass_before_release_acceptance",
            "writes_active_artifacts": False,
            "source_evidence_ids": evidence,
        },
        {
            "validation_id": "ppd-typescript-syntax-check",
            "command": ["npx", "tsc", "--noEmit"],
            "expected_result": "pass_for_committed_ppd_typescript_contracts",
            "writes_active_artifacts": False,
            "source_evidence_ids": ["release_acceptance_review#validation_rerun_expectations"],
        },
    ]


def _no_mutation_attestations(source_packets: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    attestations = {key: True for key in _NO_MUTATION_ATTESTATIONS}
    attestations["source_evidence_ids"] = sorted(
        {evidence for name, packet in source_packets.items() for evidence in _evidence_ids(packet, name)}
    )
    return attestations


def _candidate_blockers(packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    blockers: list[Mapping[str, Any]] = []
    for key in ("open_blockers", "release_blockers", "unresolved_blockers", "follow_up_work_items", "blocked_action_carryovers"):
        blockers.extend(_mapping_sequence(packet.get(key)))
    return blockers


def _consumed_for(name: str) -> list[str]:
    return {
        "source_registry_schedule_update_candidate": ["registry and schedule review gate"],
        "requirement_rerun_work_queue_packet": ["requirement rerun validation gate"],
        "process_model_impact_review_packet": ["process impact and blocked-action gate"],
        "devhub_surface_registry_reviewer_approval_packet": ["DevHub selector approval and redaction gate"],
        "agent_prompt_regression_dry_run_packet": ["agent prompt regression rerun gate"],
        "release_rollback_drill_outcome_review_packet": ["rollback outcome and no-publication gate"],
    }[name]


def _packet_id(packet: Mapping[str, Any], fallback: str) -> str:
    value = packet.get("packet_id") or packet.get("id") or fallback
    return str(value)


def _owner_from_packet(packet: Mapping[str, Any], fallback: str) -> str:
    for key in ("reviewer_owner", "review_owner", "owner", "assigned_owner", "primary_reviewer"):
        value = packet.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for key in ("reviewer_owner_fields", "reviewer_owners", "reviewer_signoff_slots", "reviewer_owner_fields"):
        for value in _walk_values(packet.get(key)):
            if isinstance(value, str) and value.strip():
                return value.strip()
    return fallback


def _evidence_ids(packet: Mapping[str, Any], fallback: str) -> list[str]:
    values: list[str] = []
    for key in ("source_evidence_ids", "citations", "citation_refs", "evidence_refs", "source_refs", "citation"):
        values.extend(_string_list(packet.get(key)))
    if values:
        return _ordered_unique(values)
    packet_id = _packet_id(packet, fallback)
    return [f"{packet_id}#fixture-review"]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [item for item in value if isinstance(item, Mapping)]
    return []


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        result: list[str] = []
        for item in value:
            result.extend(_string_list(item))
        return result
    return []


def _walk_values(value: Any) -> Iterable[Any]:
    yield value
    if isinstance(value, Mapping):
        for child in value.values():
            yield from _walk_values(child)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            yield from _walk_values(child)


def _ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
