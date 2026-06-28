"""Fixture-first inactive guardrail bundle promotion candidate v1.

This module consumes approved synthetic reviewer packet rows only and assembles
inactive candidate metadata for manual review. It does not activate guardrails,
open DevHub, crawl sources, store private artifacts, or perform official actions.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Any

PACKET_TYPE = "ppd.inactive_guardrail_bundle_promotion_candidate.v1"
PACKET_VERSION = "v1"
SOURCE_PACKET_TYPE = "ppd.synthetic_guardrail_reviewer_packet.v1"
APPROVED_DISPOSITION = "approved"
APPROVED_FOR = "inactive_guardrail_bundle_promotion_candidate_v1"
INACTIVE_STATUS = "inactive_candidate_only"

OFFLINE_VALIDATION_COMMANDS = [
    ["python3", "-m", "py_compile", "ppd/agent_readiness/inactive_guardrail_bundle_promotion_candidate_v1.py"],
    ["python3", "-m", "unittest", "ppd.tests.test_inactive_guardrail_bundle_promotion_candidate_v1"],
    ["python3", "ppd/daemon/ppd_daemon.py", "--self-test"],
]

_REQUIRED_PACKET_LISTS = (
    "consumed_approved_synthetic_reviewer_rows",
    "reviewer_approval_references",
    "inactive_bundle_metadata",
    "source_evidence_placeholder_references",
    "deterministic_predicate_inventory",
    "deontic_predicate_inventory",
    "temporal_predicate_inventory",
    "reversible_gate_inventory",
    "refused_gate_inventory",
    "exact_confirmation_gate_inventory",
    "agent_facing_explanation_inventory",
    "release_blocker_notes",
    "rollback_notes",
    "offline_validation_commands",
)

_REQUIRED_TRUE_FLAGS = (
    "fixture_first",
    "synthetic_reviewer_rows_only",
    "inactive_candidate_only",
    "metadata_only",
    "no_devhub_opened",
    "no_live_crawl",
    "no_private_artifacts",
    "no_official_actions",
    "no_guardrail_activation",
)

_REQUIRED_FALSE_FLAGS = (
    "active_guardrail_mutation",
    "active_prompt_mutation",
    "active_source_mutation",
    "active_requirement_mutation",
    "active_release_state_mutation",
    "active_devhub_surface_mutation",
    "opens_devhub",
    "runs_crawler",
    "stores_private_artifacts",
    "performs_official_actions",
    "activates_guardrails",
)

_FORBIDDEN_KEY_RE = re.compile(
    r"(^|_)(auth|browser|cookie|credential|downloaded|har|password|payment|private|raw|screenshot|session|storage_state|token|trace|upload_payload|warc)(_|$)",
    re.IGNORECASE,
)
_FORBIDDEN_VALUE_RE = re.compile(
    r"(auth state|browser state|cookie jar|credential|downloaded document|har file|private artifact|private fact|raw crawl|raw html|raw pdf|session state|storage state|trace file|warc payload|live crawl|live devhub|opened devhub|devhub observed|devhub claim|official action completed|guardrail activated|active guardrail activated)",
    re.IGNORECASE,
)
_CONSEQUENTIAL_OR_OUTCOME_RE = re.compile(
    r"(approval guaranteed|guaranteed approval|legal advice|legal guarantee|permitting guarantee|permit guaranteed|permit will be approved|permit will issue|submit payment|submitted payment|payment completed|submit permit|submitted permit|upload correction|correction uploaded|schedule inspection|inspection scheduled|cancel permit|withdraw permit|certify acknowledgement|official action completed)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class InactiveGuardrailBundlePromotionCandidateV1Result:
    valid: bool
    problems: tuple[str, ...]


class InactiveGuardrailBundlePromotionCandidateV1Error(ValueError):
    def __init__(self, problems: Iterable[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("invalid inactive guardrail bundle promotion candidate v1: " + "; ".join(self.problems))


def load_json(path: str | Path) -> dict[str, Any]:
    loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("fixture must contain a JSON object")
    return loaded


def build_inactive_guardrail_bundle_promotion_candidate_v1_from_fixture(path: str | Path) -> dict[str, Any]:
    return build_inactive_guardrail_bundle_promotion_candidate_v1(load_json(path))


def build_inactive_guardrail_bundle_promotion_candidate_v1(source_packet: Mapping[str, Any]) -> dict[str, Any]:
    rows = _approved_synthetic_rows(source_packet)

    consumed_rows: list[dict[str, Any]] = []
    reviewer_approvals: list[dict[str, Any]] = []
    metadata: list[dict[str, Any]] = []
    evidence_refs: list[dict[str, Any]] = []
    deterministic: list[dict[str, Any]] = []
    deontic: list[dict[str, Any]] = []
    temporal: list[dict[str, Any]] = []
    reversible: list[dict[str, Any]] = []
    refused: list[dict[str, Any]] = []
    exact: list[dict[str, Any]] = []
    explanations: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    rollback: list[dict[str, Any]] = []

    for sequence, row in enumerate(rows, start=1):
        row_id = _required_text(row, "row_id")
        bundle_id = _required_text(row, "guardrail_bundle_id")
        candidate_id = f"inactive-candidate-{_slug(bundle_id)}"
        approval_ref = f"reviewer-approval-{_slug(bundle_id)}"
        citations = _string_list(row.get("citations"))
        source_ids = _string_list(row.get("source_evidence_ids"))

        consumed_rows.append(
            {
                "row_id": row_id,
                "source_packet_id": _required_text(source_packet, "packet_id"),
                "reviewer_disposition": APPROVED_DISPOSITION,
                "approved_for": APPROVED_FOR,
                "synthetic_reviewer_packet_row": True,
                "guardrail_bundle_id": bundle_id,
                "citations": citations,
            }
        )
        reviewer_approvals.append(
            {
                "approval_ref": approval_ref,
                "candidate_id": candidate_id,
                "guardrail_bundle_id": bundle_id,
                "source_reviewer_row_ref": row_id,
                "approval_status": "approved_by_synthetic_reviewer_packet",
                "reviewer_approval_reference_required": True,
                "approval_source": "synthetic_reviewer_row",
                "activation_allowed": False,
            }
        )
        metadata.append(
            {
                "candidate_id": candidate_id,
                "sequence": sequence,
                "guardrail_bundle_id": bundle_id,
                "process_id": _required_text(row, "process_id"),
                "candidate_status": INACTIVE_STATUS,
                "activation_allowed": False,
                "source_reviewer_row_ref": row_id,
                "reviewer_approval_ref": approval_ref,
                "metadata_status": "assembled_from_approved_synthetic_reviewer_row",
                "source_evidence_placeholder_ref": f"evidence-placeholder-{_slug(bundle_id)}",
                "rollback_note_ref": f"rollback-note-{_slug(bundle_id)}",
                "release_blocker_note_ref": f"release-blocker-{_slug(bundle_id)}",
            }
        )
        evidence_refs.append(
            {
                "placeholder_id": f"evidence-placeholder-{_slug(bundle_id)}",
                "candidate_id": candidate_id,
                "guardrail_bundle_id": bundle_id,
                "source_evidence_ids": source_ids,
                "citation_placeholders": citations,
                "placeholder_status": "pending_source_evidence_review",
                "official_source_fetch_allowed": False,
            }
        )

        predicate_inventory = _required_mapping(row, "predicate_inventory")
        deterministic.extend(_predicate_rows(predicate_inventory, "deterministic", candidate_id, bundle_id, row_id))
        deontic.extend(_predicate_rows(predicate_inventory, "deontic", candidate_id, bundle_id, row_id))
        temporal.extend(_predicate_rows(predicate_inventory, "temporal", candidate_id, bundle_id, row_id))

        gate_inventory = _required_mapping(row, "gate_inventory")
        reversible.extend(_gate_rows(gate_inventory, "reversible", candidate_id, bundle_id, row_id))
        refused.extend(_gate_rows(gate_inventory, "refused", candidate_id, bundle_id, row_id))
        exact.extend(_gate_rows(gate_inventory, "exact_confirmation", candidate_id, bundle_id, row_id))

        explanations.extend(_explanation_rows(row, candidate_id, bundle_id, row_id))
        blockers.append(
            {
                "blocker_id": f"release-blocker-{_slug(bundle_id)}",
                "candidate_id": candidate_id,
                "guardrail_bundle_id": bundle_id,
                "blocker_status": "blocks_release_until_manual_review",
                "note": _required_text(row, "release_blocker_note"),
                "activation_allowed": False,
            }
        )
        rollback.append(
            {
                "rollback_note_id": f"rollback-note-{_slug(bundle_id)}",
                "candidate_id": candidate_id,
                "guardrail_bundle_id": bundle_id,
                "note": _required_text(row, "rollback_note"),
                "rollback_action": "discard_inactive_candidate_metadata_only",
                "active_state_changed": False,
            }
        )

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_version": PACKET_VERSION,
        "packet_id": "inactive-guardrail-bundle-promotion-candidate-v1",
        "source_packet_type": source_packet.get("packet_type"),
        "fixture_first": True,
        "synthetic_reviewer_rows_only": True,
        "inactive_candidate_only": True,
        "metadata_only": True,
        "no_devhub_opened": True,
        "no_live_crawl": True,
        "no_private_artifacts": True,
        "no_official_actions": True,
        "no_guardrail_activation": True,
        "active_guardrail_mutation": False,
        "active_prompt_mutation": False,
        "active_source_mutation": False,
        "active_requirement_mutation": False,
        "active_release_state_mutation": False,
        "active_devhub_surface_mutation": False,
        "opens_devhub": False,
        "runs_crawler": False,
        "stores_private_artifacts": False,
        "performs_official_actions": False,
        "activates_guardrails": False,
        "consumed_approved_synthetic_reviewer_rows": consumed_rows,
        "reviewer_approval_references": reviewer_approvals,
        "inactive_bundle_metadata": metadata,
        "source_evidence_placeholder_references": evidence_refs,
        "deterministic_predicate_inventory": deterministic,
        "deontic_predicate_inventory": deontic,
        "temporal_predicate_inventory": temporal,
        "reversible_gate_inventory": reversible,
        "refused_gate_inventory": refused,
        "exact_confirmation_gate_inventory": exact,
        "agent_facing_explanation_inventory": explanations,
        "release_blocker_notes": blockers,
        "rollback_notes": rollback,
        "offline_validation_commands": OFFLINE_VALIDATION_COMMANDS,
    }
    assert_valid_inactive_guardrail_bundle_promotion_candidate_v1(packet)
    return packet


def assert_valid_inactive_guardrail_bundle_promotion_candidate_v1(packet: Mapping[str, Any]) -> None:
    result = validate_inactive_guardrail_bundle_promotion_candidate_v1(packet)
    if not result.valid:
        raise InactiveGuardrailBundlePromotionCandidateV1Error(result.problems)


def validate_inactive_guardrail_bundle_promotion_candidate_v1(packet: Mapping[str, Any]) -> InactiveGuardrailBundlePromotionCandidateV1Result:
    if not isinstance(packet, Mapping):
        return InactiveGuardrailBundlePromotionCandidateV1Result(False, ("packet must be an object",))

    problems: list[str] = []
    if packet.get("packet_type") != PACKET_TYPE:
        problems.append(f"packet_type must be {PACKET_TYPE}")
    if packet.get("packet_version") != PACKET_VERSION:
        problems.append("packet_version must be v1")
    if packet.get("offline_validation_commands") != OFFLINE_VALIDATION_COMMANDS:
        problems.append("offline_validation_commands must exactly match the v1 offline validation command bundle")

    for key in _REQUIRED_TRUE_FLAGS:
        if packet.get(key) is not True:
            problems.append(f"{key} must be true")
    for key in _REQUIRED_FALSE_FLAGS:
        if packet.get(key) is not False:
            problems.append(f"{key} must be false")
    for key in _REQUIRED_PACKET_LISTS:
        if not _non_empty_sequence(packet.get(key)):
            problems.append(f"{key} must be a non-empty list")

    _validate_consumed_rows(packet.get("consumed_approved_synthetic_reviewer_rows"), problems)
    _validate_reviewer_approvals(packet.get("reviewer_approval_references"), problems)
    _validate_metadata(packet.get("inactive_bundle_metadata"), problems)
    _validate_evidence(packet.get("source_evidence_placeholder_references"), problems)
    _validate_predicates(packet.get("deterministic_predicate_inventory"), "deterministic", problems)
    _validate_predicates(packet.get("deontic_predicate_inventory"), "deontic", problems)
    _validate_predicates(packet.get("temporal_predicate_inventory"), "temporal", problems)
    _validate_gates(packet.get("reversible_gate_inventory"), "reversible", problems)
    _validate_gates(packet.get("refused_gate_inventory"), "refused", problems)
    _validate_gates(packet.get("exact_confirmation_gate_inventory"), "exact_confirmation", problems)
    _validate_explanations(packet.get("agent_facing_explanation_inventory"), problems)
    _validate_release_blockers(packet.get("release_blocker_notes"), problems)
    _validate_rollback(packet.get("rollback_notes"), problems)
    _validate_cross_refs(packet, problems)
    _validate_forbidden_payload(packet, problems)
    return InactiveGuardrailBundlePromotionCandidateV1Result(not problems, tuple(problems))


def _approved_synthetic_rows(source_packet: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    if source_packet.get("packet_type") != SOURCE_PACKET_TYPE:
        raise ValueError(f"source packet must be {SOURCE_PACKET_TYPE}")
    rows = _mapping_sequence(source_packet.get("reviewer_rows"))
    if not rows:
        raise ValueError("source packet reviewer_rows must be non-empty")

    approved_rows: list[Mapping[str, Any]] = []
    rejected_refs: list[str] = []
    for index, row in enumerate(rows):
        row_ref = _text(row.get("row_id")) or f"reviewer_rows[{index}]"
        if row.get("synthetic_reviewer_packet_row") is not True:
            rejected_refs.append(row_ref)
            continue
        if _text(row.get("reviewer_disposition")) != APPROVED_DISPOSITION:
            rejected_refs.append(row_ref)
            continue
        if _text(row.get("approved_for")) != APPROVED_FOR:
            rejected_refs.append(row_ref)
            continue
        approved_rows.append(row)
    if rejected_refs:
        raise ValueError("source packet includes unapproved or non-synthetic reviewer rows: " + ", ".join(rejected_refs))
    if not approved_rows:
        raise ValueError("source packet must contain at least one approved synthetic reviewer row")
    return approved_rows


def _predicate_rows(inventory: Mapping[str, Any], kind: str, candidate_id: str, bundle_id: str, row_id: str) -> list[dict[str, Any]]:
    rows = []
    for index, predicate in enumerate(_mapping_sequence(inventory.get(kind)), start=1):
        predicate_id = _required_text(predicate, "predicate_id")
        rows.append(
            {
                "inventory_id": f"{kind}-predicate-{_slug(bundle_id)}-{index}",
                "candidate_id": candidate_id,
                "guardrail_bundle_id": bundle_id,
                "source_reviewer_row_ref": row_id,
                "predicate_kind": kind,
                "predicate_id": predicate_id,
                "description": _required_text(predicate, "description"),
                "inventory_status": "inactive_metadata_only",
                "activation_allowed": False,
            }
        )
    if not rows:
        raise ValueError(f"predicate_inventory.{kind} must contain at least one predicate")
    return rows


def _gate_rows(inventory: Mapping[str, Any], kind: str, candidate_id: str, bundle_id: str, row_id: str) -> list[dict[str, Any]]:
    rows = []
    for index, gate in enumerate(_mapping_sequence(inventory.get(kind)), start=1):
        gate_id = _required_text(gate, "gate_id")
        rows.append(
            {
                "gate_inventory_id": f"{kind}-gate-{_slug(bundle_id)}-{index}",
                "candidate_id": candidate_id,
                "guardrail_bundle_id": bundle_id,
                "source_reviewer_row_ref": row_id,
                "gate_kind": kind,
                "gate_id": gate_id,
                "description": _required_text(gate, "description"),
                "gate_status": "inactive_metadata_only",
                "activation_allowed": False,
            }
        )
    if not rows:
        raise ValueError(f"gate_inventory.{kind} must contain at least one gate")
    return rows


def _explanation_rows(row: Mapping[str, Any], candidate_id: str, bundle_id: str, row_id: str) -> list[dict[str, Any]]:
    rows = []
    for index, explanation in enumerate(_mapping_sequence(row.get("agent_facing_explanations")), start=1):
        rows.append(
            {
                "explanation_id": f"agent-explanation-{_slug(bundle_id)}-{index}",
                "candidate_id": candidate_id,
                "guardrail_bundle_id": bundle_id,
                "source_reviewer_row_ref": row_id,
                "audience": _required_text(explanation, "audience"),
                "template": _required_text(explanation, "template"),
                "explanation_status": "inactive_metadata_only",
                "activation_allowed": False,
            }
        )
    if not rows:
        raise ValueError("agent_facing_explanations must contain at least one explanation")
    return rows


def _validate_consumed_rows(value: Any, problems: list[str]) -> None:
    seen: set[str] = set()
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"consumed_approved_synthetic_reviewer_rows[{index}]"
        row_id = _text(row.get("row_id"))
        if not row_id:
            problems.append(f"{prefix}.row_id is required")
        elif row_id in seen:
            problems.append(f"{prefix}.row_id must be unique")
        seen.add(row_id)
        if row.get("synthetic_reviewer_packet_row") is not True:
            problems.append(f"{prefix}.synthetic_reviewer_packet_row must be true")
        if row.get("reviewer_disposition") != APPROVED_DISPOSITION:
            problems.append(f"{prefix}.reviewer_disposition must be approved")
        if row.get("approved_for") != APPROVED_FOR:
            problems.append(f"{prefix}.approved_for must be {APPROVED_FOR}")
        if not _string_list(row.get("citations")):
            problems.append(f"{prefix}.citations must be non-empty")


def _validate_reviewer_approvals(value: Any, problems: list[str]) -> None:
    seen: set[str] = set()
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"reviewer_approval_references[{index}]"
        approval_ref = _text(row.get("approval_ref"))
        if not approval_ref:
            problems.append(f"{prefix}.approval_ref is required")
        elif approval_ref in seen:
            problems.append(f"{prefix}.approval_ref must be unique")
        seen.add(approval_ref)
        if row.get("approval_status") != "approved_by_synthetic_reviewer_packet":
            problems.append(f"{prefix}.approval_status must be approved_by_synthetic_reviewer_packet")
        if row.get("reviewer_approval_reference_required") is not True:
            problems.append(f"{prefix}.reviewer_approval_reference_required must be true")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        if row.get("approval_source") != "synthetic_reviewer_row":
            problems.append(f"{prefix}.approval_source must be synthetic_reviewer_row")
        for key in ("candidate_id", "guardrail_bundle_id", "source_reviewer_row_ref"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} is required")


def _validate_metadata(value: Any, problems: list[str]) -> None:
    expected = 1
    seen: set[str] = set()
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"inactive_bundle_metadata[{index}]"
        candidate_id = _text(row.get("candidate_id"))
        if not candidate_id:
            problems.append(f"{prefix}.candidate_id is required")
        elif candidate_id in seen:
            problems.append(f"{prefix}.candidate_id must be unique")
        seen.add(candidate_id)
        if row.get("sequence") != expected:
            problems.append(f"{prefix}.sequence must be {expected}")
        expected += 1
        if row.get("candidate_status") != INACTIVE_STATUS:
            problems.append(f"{prefix}.candidate_status must remain inactive_candidate_only")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        for key in (
            "guardrail_bundle_id",
            "process_id",
            "source_reviewer_row_ref",
            "reviewer_approval_ref",
            "source_evidence_placeholder_ref",
            "rollback_note_ref",
            "release_blocker_note_ref",
        ):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} is required")


def _validate_evidence(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"source_evidence_placeholder_references[{index}]"
        for key in ("placeholder_id", "candidate_id", "guardrail_bundle_id"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} is required")
        if not _string_list(row.get("source_evidence_ids")):
            problems.append(f"{prefix}.source_evidence_ids must be non-empty")
        if not _string_list(row.get("citation_placeholders")):
            problems.append(f"{prefix}.citation_placeholders must be non-empty")
        if row.get("placeholder_status") != "pending_source_evidence_review":
            problems.append(f"{prefix}.placeholder_status must be pending_source_evidence_review")
        if row.get("official_source_fetch_allowed") is not False:
            problems.append(f"{prefix}.official_source_fetch_allowed must be false")


def _validate_predicates(value: Any, kind: str, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"{kind}_predicate_inventory[{index}]"
        if row.get("predicate_kind") != kind:
            problems.append(f"{prefix}.predicate_kind must be {kind}")
        if row.get("inventory_status") != "inactive_metadata_only":
            problems.append(f"{prefix}.inventory_status must be inactive_metadata_only")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        for key in ("inventory_id", "candidate_id", "guardrail_bundle_id", "source_reviewer_row_ref", "predicate_id", "description"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} is required")


def _validate_gates(value: Any, kind: str, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"{kind}_gate_inventory[{index}]"
        if row.get("gate_kind") != kind:
            problems.append(f"{prefix}.gate_kind must be {kind}")
        if row.get("gate_status") != "inactive_metadata_only":
            problems.append(f"{prefix}.gate_status must be inactive_metadata_only")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        for key in ("gate_inventory_id", "candidate_id", "guardrail_bundle_id", "source_reviewer_row_ref", "gate_id", "description"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} is required")


def _validate_explanations(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"agent_facing_explanation_inventory[{index}]"
        if row.get("explanation_status") != "inactive_metadata_only":
            problems.append(f"{prefix}.explanation_status must be inactive_metadata_only")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        for key in ("explanation_id", "candidate_id", "guardrail_bundle_id", "source_reviewer_row_ref", "audience", "template"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} is required")


def _validate_release_blockers(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"release_blocker_notes[{index}]"
        if row.get("blocker_status") != "blocks_release_until_manual_review":
            problems.append(f"{prefix}.blocker_status must block release until manual review")
        if row.get("activation_allowed") is not False:
            problems.append(f"{prefix}.activation_allowed must be false")
        for key in ("blocker_id", "candidate_id", "guardrail_bundle_id", "note"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} is required")


def _validate_rollback(value: Any, problems: list[str]) -> None:
    for index, row in enumerate(_mapping_sequence(value)):
        prefix = f"rollback_notes[{index}]"
        if row.get("rollback_action") != "discard_inactive_candidate_metadata_only":
            problems.append(f"{prefix}.rollback_action must discard inactive metadata only")
        if row.get("active_state_changed") is not False:
            problems.append(f"{prefix}.active_state_changed must be false")
        for key in ("rollback_note_id", "candidate_id", "guardrail_bundle_id", "note"):
            if not _text(row.get(key)):
                problems.append(f"{prefix}.{key} is required")


def _validate_cross_refs(packet: Mapping[str, Any], problems: list[str]) -> None:
    consumed = {_text(row.get("row_id")) for row in _mapping_sequence(packet.get("consumed_approved_synthetic_reviewer_rows"))}
    candidates = {_text(row.get("candidate_id")) for row in _mapping_sequence(packet.get("inactive_bundle_metadata"))}
    approvals = {_text(row.get("approval_ref")) for row in _mapping_sequence(packet.get("reviewer_approval_references"))}
    evidence = {_text(row.get("placeholder_id")) for row in _mapping_sequence(packet.get("source_evidence_placeholder_references"))}
    rollbacks = {_text(row.get("rollback_note_id")) for row in _mapping_sequence(packet.get("rollback_notes"))}
    blockers = {_text(row.get("blocker_id")) for row in _mapping_sequence(packet.get("release_blocker_notes"))}

    for index, row in enumerate(_mapping_sequence(packet.get("inactive_bundle_metadata"))):
        prefix = f"inactive_bundle_metadata[{index}]"
        if _text(row.get("source_reviewer_row_ref")) not in consumed:
            problems.append(f"{prefix}.source_reviewer_row_ref must reference consumed rows")
        if _text(row.get("reviewer_approval_ref")) not in approvals:
            problems.append(f"{prefix}.reviewer_approval_ref must reference reviewer approval references")
        if _text(row.get("source_evidence_placeholder_ref")) not in evidence:
            problems.append(f"{prefix}.source_evidence_placeholder_ref must reference evidence placeholders")
        if _text(row.get("rollback_note_ref")) not in rollbacks:
            problems.append(f"{prefix}.rollback_note_ref must reference rollback notes")
        if _text(row.get("release_blocker_note_ref")) not in blockers:
            problems.append(f"{prefix}.release_blocker_note_ref must reference release blocker notes")

    for section in (
        "reviewer_approval_references",
        "source_evidence_placeholder_references",
        "deterministic_predicate_inventory",
        "deontic_predicate_inventory",
        "temporal_predicate_inventory",
        "reversible_gate_inventory",
        "refused_gate_inventory",
        "exact_confirmation_gate_inventory",
        "agent_facing_explanation_inventory",
        "release_blocker_notes",
        "rollback_notes",
    ):
        for index, row in enumerate(_mapping_sequence(packet.get(section))):
            candidate_id = _text(row.get("candidate_id"))
            if candidate_id and candidate_id not in candidates:
                problems.append(f"{section}[{index}].candidate_id must reference inactive_bundle_metadata")
            row_ref = _text(row.get("source_reviewer_row_ref"))
            if row_ref and row_ref not in consumed:
                problems.append(f"{section}[{index}].source_reviewer_row_ref must reference consumed rows")


def _validate_forbidden_payload(packet: Mapping[str, Any], problems: list[str]) -> None:
    allowed_keys = {"no_private_artifacts", "stores_private_artifacts", "source_evidence_placeholder_references"}
    for path, key, value in _walk(packet):
        normalized = key.lower().replace("-", "_")
        if normalized not in allowed_keys and _FORBIDDEN_KEY_RE.search(normalized) and _truthy(value):
            problems.append(f"{path} must not include private, live, raw, session, browser, downloaded, or payment artifacts")
        if normalized.startswith("active_") and "mutation" in normalized and _truthy(value):
            problems.append(f"{path} must not set active mutation flags")
        if isinstance(value, str):
            if _FORBIDDEN_VALUE_RE.search(value):
                problems.append(f"{path} must not reference private artifacts, live operations, raw captures, DevHub claims, or activation")
            if _CONSEQUENTIAL_OR_OUTCOME_RE.search(value):
                problems.append(f"{path} must not guarantee outcomes or authorize consequential actions")


def _required_mapping(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = data.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"{key} must be an object")
    return value


def _required_text(data: Mapping[str, Any], key: str) -> str:
    value = _text(data.get(key))
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _mapping_sequence(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _non_empty_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and bool(value)


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _truthy(value: Any) -> bool:
    if value is None or value is False or value == "":
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)) and not value:
        return False
    if isinstance(value, Mapping) and not value:
        return False
    return True


def _walk(value: Any, prefix: str = "packet", key: str = "packet") -> Iterable[tuple[str, str, Any]]:
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            child_key_text = str(child_key)
            child_path = f"{prefix}.{child_key_text}"
            yield child_path, child_key_text, child_value
            yield from _walk(child_value, child_path, child_key_text)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, child_value in enumerate(value):
            child_path = f"{prefix}[{index}]"
            yield child_path, key, child_value
            yield from _walk(child_value, child_path, key)


def _slug(value: str) -> str:
    cleaned = "".join(char.lower() if char.isalnum() else "-" for char in value)
    return "-".join(part for part in cleaned.split("-") if part) or "item"
