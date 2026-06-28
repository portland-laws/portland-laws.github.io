"""Fixture-first process model impact candidates for regenerated requirements.

This module consumes regenerated requirement candidate packets and produces a
review-only impact packet. It identifies which process model surfaces need human
review after obligations, file rules, deadlines, fees, or action gates change.
It does not emit replacement process model content and does not promote active
process models.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from copy import deepcopy
from dataclasses import dataclass
from typing import Any


PROCESS_MODEL_IMPACT_KINDS: set[str] = {
    "obligation",
    "file_rule",
    "deadline",
    "fee",
    "action_gate",
}

_ACTIVE_MODEL_CONTENT_KEYS: set[str] = {
    "active_process_model",
    "active_process_models",
    "active_process_model_patch",
    "replacement_process_model",
    "replacement_process_models",
    "promoted_process_model",
    "compiled_process_model",
    "process_model_promotion",
}


@dataclass(frozen=True)
class ProcessModelImpactFinding:
    code: str
    path: str
    message: str


class ProcessModelImpactCandidateError(ValueError):
    """Raised when an impact candidate input is malformed."""


def build_process_model_impact_candidate(regenerated_candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic review-only process model impact packet.

    The input is expected to be a regenerated requirement candidate fixture. Each
    requirement diff may include impact_hints with process_stage_ids,
    user_fact_ids, required_document_ids, unsupported_path_ids, and
    reviewer_prompt. The output contains only impact references and reviewer work,
    never replacement active process model content.
    """

    if not isinstance(regenerated_candidate, Mapping):
        raise ProcessModelImpactCandidateError("regenerated candidate must be an object")

    original = deepcopy(regenerated_candidate)
    requirement_diffs = _list(regenerated_candidate, "requirement_diffs")
    candidate_id = _text(regenerated_candidate.get("candidate_id")) or _text(regenerated_candidate.get("packet_id")) or "regenerated-requirement-candidate"

    affected_stages: dict[tuple[str, str], dict[str, Any]] = {}
    affected_facts: dict[tuple[str, str], dict[str, Any]] = {}
    affected_documents: dict[tuple[str, str], dict[str, Any]] = {}
    affected_paths: dict[tuple[str, str], dict[str, Any]] = {}
    reviewer_prompts: list[dict[str, Any]] = []
    diff_ids: list[str] = []

    for index, raw_diff in enumerate(requirement_diffs):
        if not isinstance(raw_diff, Mapping):
            raise ProcessModelImpactCandidateError(f"requirement_diffs[{index}] must be an object")
        diff_id = _diff_id(raw_diff, index)
        diff_ids.append(diff_id)
        impact_kind = _impact_kind(raw_diff)
        hints = _mapping(raw_diff, "impact_hints")
        process_ids = _strings(regenerated_candidate.get("affected_process_ids")) or _strings(hints.get("process_model_ids"))
        if not process_ids:
            process_ids = ["unknown-process-model-needs-review"]

        for process_id in process_ids:
            for stage_id in _strings(hints.get("process_stage_ids")):
                key = (process_id, stage_id)
                affected_stages.setdefault(
                    key,
                    {
                        "process_model_id": process_id,
                        "stage_id": stage_id,
                        "impact_kinds": [],
                        "source_requirement_diff_ids": [],
                    },
                )
                _append_unique(affected_stages[key]["impact_kinds"], impact_kind)
                _append_unique(affected_stages[key]["source_requirement_diff_ids"], diff_id)

            for fact_id in _strings(hints.get("user_fact_ids")):
                key = (process_id, fact_id)
                affected_facts.setdefault(
                    key,
                    {
                        "process_model_id": process_id,
                        "user_fact_id": fact_id,
                        "impact_kinds": [],
                        "source_requirement_diff_ids": [],
                    },
                )
                _append_unique(affected_facts[key]["impact_kinds"], impact_kind)
                _append_unique(affected_facts[key]["source_requirement_diff_ids"], diff_id)

            for document_id in _strings(hints.get("required_document_ids")):
                key = (process_id, document_id)
                affected_documents.setdefault(
                    key,
                    {
                        "process_model_id": process_id,
                        "required_document_id": document_id,
                        "impact_kinds": [],
                        "source_requirement_diff_ids": [],
                    },
                )
                _append_unique(affected_documents[key]["impact_kinds"], impact_kind)
                _append_unique(affected_documents[key]["source_requirement_diff_ids"], diff_id)

            for path_id in _strings(hints.get("unsupported_path_ids")):
                key = (process_id, path_id)
                affected_paths.setdefault(
                    key,
                    {
                        "process_model_id": process_id,
                        "unsupported_path_id": path_id,
                        "impact_kinds": [],
                        "source_requirement_diff_ids": [],
                    },
                )
                _append_unique(affected_paths[key]["impact_kinds"], impact_kind)
                _append_unique(affected_paths[key]["source_requirement_diff_ids"], diff_id)

        prompt = _text(hints.get("reviewer_prompt")) or f"Review process model impact for {diff_id}."
        reviewer_prompts.append(
            {
                "prompt_id": f"review-process-model-impact-{diff_id}",
                "source_requirement_diff_id": diff_id,
                "impact_kind": impact_kind,
                "prompt": prompt,
                "blocks_process_model_promotion": True,
                "status": "unresolved",
            }
        )

    packet = {
        "packet_type": "process_model_impact_candidate",
        "candidate_id": "process-model-impact-" + _stable_hash(regenerated_candidate),
        "candidate_status": "draft_requires_human_review",
        "candidate_mode": "fixture_first_review_only",
        "source_regenerated_requirement_candidate_id": candidate_id,
        "input_requirement_diff_ids": sorted(diff_ids),
        "affected_process_model_ids": sorted(set(_strings(regenerated_candidate.get("affected_process_ids")))),
        "does_not_replace_active_process_models": True,
        "active_process_model_mutated": False,
        "promotion": {"target": "candidate", "promote_to_active": False},
        "affected_process_stages": _sorted_values(affected_stages, "stage_id"),
        "affected_user_facts": _sorted_values(affected_facts, "user_fact_id"),
        "affected_required_documents": _sorted_values(affected_documents, "required_document_id"),
        "affected_unsupported_paths": _sorted_values(affected_paths, "unsupported_path_id"),
        "reviewer_prompts": sorted(reviewer_prompts, key=lambda item: item["prompt_id"]),
    }

    if regenerated_candidate != original:
        raise ProcessModelImpactCandidateError("regenerated requirement candidate input was mutated")
    return packet


def validate_process_model_impact_candidate(packet: Mapping[str, Any]) -> list[ProcessModelImpactFinding]:
    """Return validation findings for a process model impact candidate packet."""

    if not isinstance(packet, Mapping):
        return [ProcessModelImpactFinding("invalid_packet", "$", "Packet must be an object.")]

    findings: list[ProcessModelImpactFinding] = []
    _validate_review_only_candidate(packet, findings)
    _validate_impact_mappings(packet, findings)
    _validate_reviewer_prompts(packet, findings)
    return findings


def require_valid_process_model_impact_candidate(packet: Mapping[str, Any]) -> None:
    findings = validate_process_model_impact_candidate(packet)
    if findings:
        detail = "; ".join(f"{item.code} at {item.path}: {item.message}" for item in findings)
        raise ValueError(f"invalid process model impact candidate: {detail}")


def finding_codes(findings: Iterable[ProcessModelImpactFinding]) -> set[str]:
    return {finding.code for finding in findings}


def _validate_review_only_candidate(packet: Mapping[str, Any], findings: list[ProcessModelImpactFinding]) -> None:
    if packet.get("packet_type") != "process_model_impact_candidate":
        findings.append(ProcessModelImpactFinding("invalid_packet_type", "$.packet_type", "Packet type must be process_model_impact_candidate."))
    if packet.get("candidate_mode") != "fixture_first_review_only":
        findings.append(ProcessModelImpactFinding("not_fixture_first", "$.candidate_mode", "Impact candidates must be fixture-first and review-only."))
    if packet.get("candidate_status") != "draft_requires_human_review":
        findings.append(ProcessModelImpactFinding("missing_human_review_block", "$.candidate_status", "Impact candidates must remain draft_requires_human_review."))
    if packet.get("does_not_replace_active_process_models") is not True:
        findings.append(ProcessModelImpactFinding("active_process_model_replacement", "$.does_not_replace_active_process_models", "Candidate must explicitly preserve active process models."))
    if packet.get("active_process_model_mutated") is not False:
        findings.append(ProcessModelImpactFinding("active_process_model_mutation", "$.active_process_model_mutated", "Candidate must not mutate active process models."))

    promotion = packet.get("promotion")
    if isinstance(promotion, Mapping):
        target = _text(promotion.get("target")).lower()
        if target in {"active", "active_process_model", "current"} or promotion.get("promote_to_active") is True:
            findings.append(ProcessModelImpactFinding("active_process_model_promotion", "$.promotion", "Impact candidates must not promote active process models."))

    for path, value in _walk(packet):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0]
        if key in _ACTIVE_MODEL_CONTENT_KEYS and value not in (None, False, "", [], {}):
            findings.append(ProcessModelImpactFinding("active_process_model_replacement", path, "Candidate must not include replacement active process model content."))


def _validate_impact_mappings(packet: Mapping[str, Any], findings: list[ProcessModelImpactFinding]) -> None:
    diff_ids = set(_strings(packet.get("input_requirement_diff_ids")))
    if not diff_ids:
        findings.append(ProcessModelImpactFinding("missing_requirement_diffs", "$.input_requirement_diff_ids", "Impact candidate must reference regenerated requirement diffs."))

    group_specs = (
        ("affected_process_stages", "stage_id"),
        ("affected_user_facts", "user_fact_id"),
        ("affected_required_documents", "required_document_id"),
        ("affected_unsupported_paths", "unsupported_path_id"),
    )
    mapped_diff_ids: set[str] = set()
    seen_kinds: set[str] = set()

    for group_name, identity_key in group_specs:
        group = packet.get(group_name)
        if not isinstance(group, list) or not group:
            findings.append(ProcessModelImpactFinding("missing_impact_group", f"$.{group_name}", f"Candidate must include non-empty {group_name}."))
            continue
        for index, item in enumerate(group):
            path = f"$.{group_name}[{index}]"
            if not isinstance(item, Mapping):
                findings.append(ProcessModelImpactFinding("invalid_impact_mapping", path, "Impact mappings must be objects."))
                continue
            for key in ("process_model_id", identity_key):
                if not _text(item.get(key)):
                    findings.append(ProcessModelImpactFinding("invalid_impact_mapping", f"{path}.{key}", f"Impact mapping must include {key}."))
            item_diff_ids = set(_strings(item.get("source_requirement_diff_ids")))
            if not item_diff_ids:
                findings.append(ProcessModelImpactFinding("uncited_impact_mapping", f"{path}.source_requirement_diff_ids", "Impact mapping must cite requirement diffs."))
            elif diff_ids and not item_diff_ids.issubset(diff_ids):
                findings.append(ProcessModelImpactFinding("unknown_requirement_diff", f"{path}.source_requirement_diff_ids", "Impact mapping references a diff outside input_requirement_diff_ids."))
            mapped_diff_ids.update(item_diff_ids)
            kinds = set(_strings(item.get("impact_kinds")))
            if not kinds:
                findings.append(ProcessModelImpactFinding("missing_impact_kind", f"{path}.impact_kinds", "Impact mapping must include impact kinds."))
            unknown = kinds - PROCESS_MODEL_IMPACT_KINDS
            if unknown:
                findings.append(ProcessModelImpactFinding("unsupported_impact_kind", f"{path}.impact_kinds", "Impact mapping includes unsupported impact kinds."))
            seen_kinds.update(kinds)

    missing = diff_ids - mapped_diff_ids
    if missing:
        findings.append(ProcessModelImpactFinding("unmapped_requirement_diff", "$.input_requirement_diff_ids", "Every requirement diff must appear in at least one impact mapping."))

    missing_kinds = PROCESS_MODEL_IMPACT_KINDS - seen_kinds
    if missing_kinds:
        findings.append(ProcessModelImpactFinding("missing_required_impact_kind", "$", "Candidate must cover obligation, file_rule, deadline, fee, and action_gate impacts."))


def _validate_reviewer_prompts(packet: Mapping[str, Any], findings: list[ProcessModelImpactFinding]) -> None:
    diff_ids = set(_strings(packet.get("input_requirement_diff_ids")))
    prompts = packet.get("reviewer_prompts")
    if not isinstance(prompts, list) or not prompts:
        findings.append(ProcessModelImpactFinding("missing_reviewer_prompts", "$.reviewer_prompts", "Candidate must include reviewer prompts."))
        return

    prompted_diff_ids: set[str] = set()
    for index, prompt in enumerate(prompts):
        path = f"$.reviewer_prompts[{index}]"
        if not isinstance(prompt, Mapping):
            findings.append(ProcessModelImpactFinding("invalid_reviewer_prompt", path, "Reviewer prompts must be objects."))
            continue
        diff_id = _text(prompt.get("source_requirement_diff_id"))
        if not diff_id:
            findings.append(ProcessModelImpactFinding("invalid_reviewer_prompt", f"{path}.source_requirement_diff_id", "Reviewer prompts must cite a requirement diff."))
        elif diff_ids and diff_id not in diff_ids:
            findings.append(ProcessModelImpactFinding("unknown_requirement_diff", f"{path}.source_requirement_diff_id", "Reviewer prompt references a diff outside input_requirement_diff_ids."))
        else:
            prompted_diff_ids.add(diff_id)
        if _text(prompt.get("impact_kind")) not in PROCESS_MODEL_IMPACT_KINDS:
            findings.append(ProcessModelImpactFinding("unsupported_impact_kind", f"{path}.impact_kind", "Reviewer prompt must include a supported impact kind."))
        if not _text(prompt.get("prompt")):
            findings.append(ProcessModelImpactFinding("invalid_reviewer_prompt", f"{path}.prompt", "Reviewer prompt text is required."))
        if prompt.get("blocks_process_model_promotion") is not True:
            findings.append(ProcessModelImpactFinding("review_prompt_does_not_block_promotion", f"{path}.blocks_process_model_promotion", "Reviewer prompts must block process model promotion."))
        if _text(prompt.get("status")) != "unresolved":
            findings.append(ProcessModelImpactFinding("resolved_reviewer_prompt", f"{path}.status", "Reviewer prompts must remain unresolved."))

    missing_prompted = diff_ids - prompted_diff_ids
    if missing_prompted:
        findings.append(ProcessModelImpactFinding("missing_reviewer_prompt_for_diff", "$.reviewer_prompts", "Every requirement diff must have a reviewer prompt."))


def _diff_id(diff: Mapping[str, Any], index: int) -> str:
    return _text(diff.get("diff_id")) or _text(diff.get("id")) or f"requirement-diff-{index}"


def _impact_kind(diff: Mapping[str, Any]) -> str:
    raw = _text(diff.get("impact_kind")) or _text(diff.get("requirement_type")) or _text(diff.get("type"))
    normalized = raw.lower().replace("-", "_")
    aliases = {
        "document_requirement": "file_rule",
        "file_naming_rule": "file_rule",
        "fee_trigger": "fee",
        "fees": "fee",
        "action_gate_requirement": "action_gate",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in PROCESS_MODEL_IMPACT_KINDS:
        raise ProcessModelImpactCandidateError(f"unsupported impact kind {raw!r}")
    return normalized


def _mapping(raw: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = raw.get(key)
    if not isinstance(value, Mapping):
        raise ProcessModelImpactCandidateError(f"{key} must be an object")
    return value


def _list(raw: Mapping[str, Any], key: str) -> list[Any]:
    value = raw.get(key)
    if not isinstance(value, list):
        raise ProcessModelImpactCandidateError(f"{key} must be a list")
    return value


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def _sorted_values(items: Mapping[tuple[str, str], dict[str, Any]], id_key: str) -> list[dict[str, Any]]:
    result = list(items.values())
    for item in result:
        item["impact_kinds"] = sorted(item["impact_kinds"])
        item["source_requirement_diff_ids"] = sorted(item["source_requirement_diff_ids"])
    return sorted(result, key=lambda item: (item["process_model_id"], item[id_key]))


def _stable_hash(value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, Mapping):
        for key, nested in value.items():
            yield from _walk(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _walk(nested, f"{path}[{index}]")


__all__ = [
    "ProcessModelImpactCandidateError",
    "ProcessModelImpactFinding",
    "build_process_model_impact_candidate",
    "finding_codes",
    "require_valid_process_model_impact_candidate",
    "validate_process_model_impact_candidate",
]
