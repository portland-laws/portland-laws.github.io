"""Validation for PP&D process model impact candidate packets.

Impact candidate packets are review artifacts. They may describe how a regenerated
requirement set could affect a process model, but they must not update the active
process model or claim production readiness.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


PRODUCTION_READY_LABELS = {
    "production-ready",
    "production_ready",
    "ready-for-production",
    "ready_for_production",
    "approved-for-production",
    "approved_for_production",
    "prod-ready",
    "prod_ready",
}

SUPPORTED_PATH_STATUSES = {
    "supported",
    "devhub_supported",
    "automatable",
    "reversible_draft",
    "safe_read_only",
}

UNSUPPORTED_PATH_STATUSES = {
    "unsupported",
    "manual_handoff",
    "manual-only",
    "manual_only",
    "requires_human",
    "not_supported",
}

MUTATION_FIELDS = (
    "active_process_model_mutation",
    "mutates_active_process_model",
    "active_process_model_patch",
    "active_process_model_updates",
    "process_model_writeback",
    "process_model_mutations",
)

PRIVATE_FACT_FIELDS = (
    "private_case_facts",
    "private_case_fact_ids",
    "case_specific_facts",
    "user_case_facts",
    "private_user_values",
)


@dataclass(frozen=True)
class PacketValidationIssue:
    code: str
    message: str
    path: str


@dataclass(frozen=True)
class PacketValidationResult:
    ok: bool
    issues: tuple[PacketValidationIssue, ...]

    def issue_codes(self) -> tuple[str, ...]:
        return tuple(issue.code for issue in self.issues)


def validate_process_model_impact_candidate_packet(packet: Mapping[str, Any]) -> PacketValidationResult:
    """Return validation issues for a process model impact candidate packet."""

    issues: list[PacketValidationIssue] = []
    _validate_regenerated_requirement_links(packet, issues)
    _validate_stage_changes(packet, issues)
    _validate_private_case_facts(packet, issues)
    _validate_unsupported_path_downgrades(packet, issues)
    _validate_reviewer_prompts(packet, issues)
    _validate_labels(packet, issues)
    _validate_active_model_mutation(packet, issues)
    return PacketValidationResult(ok=not issues, issues=tuple(issues))


def _validate_regenerated_requirement_links(
    packet: Mapping[str, Any], issues: list[PacketValidationIssue]
) -> None:
    links = _sequence(packet.get("regenerated_requirement_links"))
    changed_requirement_ids = _string_set(packet.get("changed_requirement_ids"))
    if changed_requirement_ids and not links:
        issues.append(
            PacketValidationIssue(
                "missing_regenerated_requirement_link",
                "changed requirements must link each original requirement to its regenerated requirement",
                "regenerated_requirement_links",
            )
        )
        return

    linked_originals: set[str] = set()
    for index, link in enumerate(links):
        if not isinstance(link, Mapping):
            issues.append(
                PacketValidationIssue(
                    "missing_regenerated_requirement_link",
                    "each regenerated requirement link must be an object",
                    f"regenerated_requirement_links[{index}]",
                )
            )
            continue
        original_id = _text(link.get("requirement_id") or link.get("original_requirement_id"))
        regenerated_id = _text(link.get("regenerated_requirement_id"))
        evidence_ids = _string_set(link.get("evidence_ids") or link.get("citation_ids"))
        if not original_id or not regenerated_id or not evidence_ids:
            issues.append(
                PacketValidationIssue(
                    "missing_regenerated_requirement_link",
                    "regenerated requirement links require original id, regenerated id, and evidence ids",
                    f"regenerated_requirement_links[{index}]",
                )
            )
        if original_id:
            linked_originals.add(original_id)

    for requirement_id in sorted(changed_requirement_ids - linked_originals):
        issues.append(
            PacketValidationIssue(
                "missing_regenerated_requirement_link",
                f"changed requirement {requirement_id} has no regenerated requirement link",
                "changed_requirement_ids",
            )
        )


def _validate_stage_changes(packet: Mapping[str, Any], issues: list[PacketValidationIssue]) -> None:
    for index, change in enumerate(_sequence(packet.get("stage_changes"))):
        if not isinstance(change, Mapping):
            issues.append(
                PacketValidationIssue(
                    "uncited_stage_change",
                    "stage changes must be objects with citation ids",
                    f"stage_changes[{index}]",
                )
            )
            continue
        citations = _string_set(change.get("citation_ids") or change.get("evidence_ids"))
        if not citations:
            issues.append(
                PacketValidationIssue(
                    "uncited_stage_change",
                    "stage changes require source citations",
                    f"stage_changes[{index}]",
                )
            )


def _validate_private_case_facts(packet: Mapping[str, Any], issues: list[PacketValidationIssue]) -> None:
    for field in PRIVATE_FACT_FIELDS:
        value = packet.get(field)
        if _has_payload(value):
            issues.append(
                PacketValidationIssue(
                    "private_case_fact_present",
                    "impact candidate packets must not include private or user-specific case facts",
                    field,
                )
            )


def _validate_unsupported_path_downgrades(
    packet: Mapping[str, Any], issues: list[PacketValidationIssue]
) -> None:
    for index, change in enumerate(_sequence(packet.get("unsupported_path_changes"))):
        if not isinstance(change, Mapping):
            continue
        from_status = _normalized(change.get("from_status") or change.get("previous_status"))
        to_status = _normalized(change.get("to_status") or change.get("proposed_status"))
        explicit_downgrade = bool(change.get("downgrades_unsupported_path"))
        removes_handoff = bool(change.get("removes_manual_handoff"))
        if (
            explicit_downgrade
            or removes_handoff
            or (from_status in UNSUPPORTED_PATH_STATUSES and to_status in SUPPORTED_PATH_STATUSES)
        ):
            issues.append(
                PacketValidationIssue(
                    "unsupported_path_downgrade",
                    "candidate packets may not downgrade unsupported/manual paths to supported automation",
                    f"unsupported_path_changes[{index}]",
                )
            )


def _validate_reviewer_prompts(packet: Mapping[str, Any], issues: list[PacketValidationIssue]) -> None:
    prompts = _sequence(packet.get("reviewer_prompts"))
    if not prompts:
        issues.append(
            PacketValidationIssue(
                "missing_reviewer_prompt",
                "candidate packets require reviewer prompts before any promotion decision",
                "reviewer_prompts",
            )
        )
        return
    for index, prompt in enumerate(prompts):
        if isinstance(prompt, str):
            text = prompt.strip()
        elif isinstance(prompt, Mapping):
            text = _text(prompt.get("prompt") or prompt.get("question"))
        else:
            text = ""
        if not text:
            issues.append(
                PacketValidationIssue(
                    "missing_reviewer_prompt",
                    "reviewer prompts must contain a non-empty prompt or question",
                    f"reviewer_prompts[{index}]",
                )
            )


def _validate_labels(packet: Mapping[str, Any], issues: list[PacketValidationIssue]) -> None:
    labels = {_normalized(label) for label in _sequence(packet.get("labels"))}
    labels.update(_normalized(label) for label in _sequence(packet.get("status_labels")))
    disposition = _normalized(packet.get("readiness_label") or packet.get("promotion_label"))
    if disposition:
        labels.add(disposition)
    forbidden = sorted(label for label in labels if label in PRODUCTION_READY_LABELS)
    for label in forbidden:
        issues.append(
            PacketValidationIssue(
                "production_ready_label",
                f"candidate packet must not use production-ready label {label}",
                "labels",
            )
        )


def _validate_active_model_mutation(packet: Mapping[str, Any], issues: list[PacketValidationIssue]) -> None:
    for field in MUTATION_FIELDS:
        value = packet.get(field)
        if value is True or _has_payload(value):
            issues.append(
                PacketValidationIssue(
                    "active_process_model_mutation",
                    "candidate packets must not mutate the active process model",
                    field,
                )
            )


def _sequence(value: Any) -> tuple[Any, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return value
    if isinstance(value, list):
        return tuple(value)
    return (value,)


def _string_set(value: Any) -> set[str]:
    return {_text(item) for item in _sequence(value) if _text(item)}


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalized(value: Any) -> str:
    return _text(value).lower().replace(" ", "_")


def _has_payload(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return bool(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray, str)):
        return bool(value)
    return True
