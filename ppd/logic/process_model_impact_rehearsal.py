"""Fixture-first process-model impact rehearsal packet helpers.

This module is intentionally side-effect free. It does not compile guardrails,
promote bundles, crawl sources, or write process models; it only summarizes
fixture inputs for review.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


_ALLOWED_REVIEW_STATUSES = {"accepted_for_rehearsal", "needs_reviewer_followup"}
_BLOCKED_OPERATIONS = (
    "compile_guardrails",
    "promote_guardrail_bundle",
    "change_active_process_model",
    "write_process_model_fixture",
)
_STALE_STATUSES = {"stale", "stale_current", "current_stale", "outdated", "superseded"}
_PRIVATE_CASE_FACT_KEYS = {
    "private_case_fact",
    "private_case_facts",
    "case_private_facts",
    "private_user_fact",
    "private_user_facts",
    "known_private_facts",
}
_LIVE_EXECUTION_KEYS = {
    "compiler_executed",
    "crawler_executed",
    "live_compiler_execution",
    "live_crawler_execution",
    "live_crawl_executed",
    "ran_live_crawler",
    "ran_live_compiler",
    "live_execution_claimed",
    "compiled_live_guardrails",
}
_ACTIVE_MUTATION_KEYS = {
    "active_process_model_mutated",
    "active_process_models_changed",
    "active_process_model_changed",
    "process_model_mutation_active",
    "mutates_active_process_models",
    "change_active_process_model",
    "write_active_process_model",
}
_OUTCOME_GUARANTEE_KEYS = {
    "legal_outcome_guarantee",
    "permitting_outcome_guarantee",
    "permit_outcome_guarantee",
    "approval_guarantee",
    "issuance_guarantee",
}
_OUTCOME_GUARANTEE_PHRASES = (
    "guarantee approval",
    "guarantees approval",
    "guaranteed approval",
    "guarantee issuance",
    "guarantees issuance",
    "guaranteed issuance",
    "permit will be approved",
    "permit will issue",
    "will receive approval",
)


@dataclass(frozen=True)
class RehearsalInputError(ValueError):
    """Raised when a rehearsal fixture is missing required safe inputs."""

    message: str

    def __str__(self) -> str:
        return self.message


def load_json_fixture(path: str | Path) -> dict[str, Any]:
    """Load a JSON fixture object from disk."""

    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise RehearsalInputError("process-model impact rehearsal fixture must be a JSON object")
    return data


def build_process_model_impact_rehearsal_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic impact rehearsal packet from fixture inputs.

    The returned packet is derived only from the supplied mapping. The function
    deep-copies the input before processing and records pre/post fingerprints so
    reviewers can verify that process-model fixtures were not mutated.
    """

    source_packet = deepcopy(dict(packet))
    input_fingerprint = _stable_digest(source_packet)

    guardrail_packet = _require_mapping(source_packet, "guardrail_recompilation_rehearsal_packet")
    if guardrail_packet.get("compiled") is not False:
        raise RehearsalInputError("guardrail recompilation rehearsal input must declare compiled=false")
    if guardrail_packet.get("promoted") is not False:
        raise RehearsalInputError("guardrail recompilation rehearsal input must declare promoted=false")

    process_models = _require_list(source_packet, "process_model_fixtures")
    candidates = _require_list(source_packet, "reviewed_synthetic_requirement_candidates")
    process_index = _index_process_models(process_models)
    _validate_rehearsal_inputs(source_packet, guardrail_packet, process_index, candidates)
    guardrail_impacts = _index_guardrail_impacts(guardrail_packet.get("predicate_impacts", []))

    affected_processes = []
    unsupported_candidates = []
    for process_id in sorted(process_index):
        model = process_index[process_id]
        model_candidates = [
            candidate
            for candidate in candidates
            if isinstance(candidate, Mapping) and candidate.get("process_id") == process_id
        ]
        accepted_candidates = [
            candidate
            for candidate in model_candidates
            if candidate.get("review_status") in _ALLOWED_REVIEW_STATUSES
        ]
        rejected_candidates = [
            candidate
            for candidate in model_candidates
            if candidate.get("review_status") not in _ALLOWED_REVIEW_STATUSES
        ]
        unsupported_candidates.extend(_candidate_stub(candidate) for candidate in rejected_candidates)

        if not accepted_candidates:
            continue

        affected_processes.append(
            _build_process_impact(
                process_id=process_id,
                model=model,
                candidates=accepted_candidates,
                guardrail_impacts=guardrail_impacts,
            )
        )

    output = {
        "packet_id": str(source_packet.get("packet_id", "process-model-impact-rehearsal.synthetic")),
        "packet_type": "fixture_first_process_model_impact_rehearsal",
        "input_packet_refs": {
            "guardrail_recompilation_rehearsal_packet_id": str(guardrail_packet.get("packet_id", "")),
            "reviewed_requirement_candidate_count": len(candidates),
            "process_model_fixture_count": len(process_models),
        },
        "process_mutation_policy": {
            "fixture_only": True,
            "blocked_operations": list(_BLOCKED_OPERATIONS),
            "compiled": False,
            "promoted": False,
            "active_process_models_changed": False,
        },
        "affected_processes": affected_processes,
        "unsupported_requirement_candidates": sorted(
            unsupported_candidates,
            key=lambda item: (item["process_id"], item["requirement_id"]),
        ),
        "no_process_mutation_attestation": {
            "input_fingerprint_before": input_fingerprint,
            "input_fingerprint_after": _stable_digest(source_packet),
            "input_unchanged": input_fingerprint == _stable_digest(source_packet),
            "attestation": "rehearsal summarized fixture snapshots only; no compile, promotion, crawl, write, or active process-model mutation occurred",
        },
    }
    return output


def _validate_rehearsal_inputs(
    source_packet: Mapping[str, Any],
    guardrail_packet: Mapping[str, Any],
    process_index: Mapping[str, Mapping[str, Any]],
    candidates: list[Any],
) -> None:
    _reject_private_case_facts(source_packet)
    _reject_live_execution_claims(source_packet)
    _reject_outcome_guarantees(source_packet)
    _reject_active_process_model_mutation(source_packet)
    _reject_unacknowledged_stale_current_evidence(source_packet)

    candidate_requirement_ids: set[str] = set()
    accepted_requirement_ids: set[str] = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, Mapping):
            raise RehearsalInputError("reviewed requirement candidates must be objects")
        process_id = str(candidate.get("process_id", ""))
        requirement_id = str(candidate.get("requirement_id", candidate.get("candidate_id", "")))
        review_status = str(candidate.get("review_status", ""))
        if not process_id or process_id not in process_index:
            raise RehearsalInputError(f"candidate[{index}] references unknown process_id {process_id!r}")
        if not requirement_id:
            raise RehearsalInputError(f"candidate[{index}] missing requirement_id")
        candidate_requirement_ids.add(requirement_id)
        if review_status in _ALLOWED_REVIEW_STATUSES:
            accepted_requirement_ids.add(requirement_id)
            _validate_accepted_candidate(candidate, process_index[process_id], index)

    predicate_impacts = guardrail_packet.get("predicate_impacts", [])
    if not isinstance(predicate_impacts, list):
        raise RehearsalInputError("guardrail predicate_impacts must be a list")
    requirement_to_process = {
        str(candidate.get("requirement_id", candidate.get("candidate_id", ""))): str(candidate.get("process_id", ""))
        for candidate in candidates
        if isinstance(candidate, Mapping)
    }
    for index, impact in enumerate(predicate_impacts):
        if not isinstance(impact, Mapping):
            raise RehearsalInputError("guardrail predicate impact entries must be objects")
        requirement_id = str(impact.get("requirement_id", ""))
        if requirement_id not in candidate_requirement_ids:
            raise RehearsalInputError(f"predicate_impacts[{index}] references unknown requirement_id {requirement_id!r}")
        if requirement_id not in accepted_requirement_ids:
            continue
        process_id = requirement_to_process[requirement_id]
        _validate_guardrail_impact(impact, process_index[process_id], index)


def _validate_accepted_candidate(candidate: Mapping[str, Any], model: Mapping[str, Any], index: int) -> None:
    requirement_id = str(candidate.get("requirement_id", candidate.get("candidate_id", "")))
    reviewer_owner = str(candidate.get("reviewer_owner", "")).strip()
    if not reviewer_owner or reviewer_owner == "unassigned":
        raise RehearsalInputError(f"candidate[{index}] missing reviewer_owner for {requirement_id}")
    citations = _string_list(candidate.get("source_evidence_ids", []))
    if not citations:
        raise RehearsalInputError(f"candidate[{index}] impact for {requirement_id} requires source_evidence_ids")
    stage = str(candidate.get("process_stage", "")).strip()
    if not stage:
        raise RehearsalInputError(f"candidate[{index}] impact for {requirement_id} missing process_stage")
    if stage not in set(_string_list(model.get("stages", []))):
        raise RehearsalInputError(f"candidate[{index}] references unknown process_stage {stage!r}")
    for impact_index, impact in enumerate(candidate.get("document_rule_impacts", [])):
        if not isinstance(impact, Mapping):
            raise RehearsalInputError(f"candidate[{index}].document_rule_impacts[{impact_index}] must be an object")
        document = str(impact.get("document", impact.get("name", impact.get("document_type", "")))).strip()
        rule = str(impact.get("rule", impact.get("note", ""))).strip()
        if not document or not rule:
            raise RehearsalInputError(f"candidate[{index}].document_rule_impacts[{impact_index}] requires document and rule")
        if not citations:
            raise RehearsalInputError(f"candidate[{index}].document_rule_impacts[{impact_index}] requires citations")


def _validate_guardrail_impact(impact: Mapping[str, Any], model: Mapping[str, Any], index: int) -> None:
    requirement_id = str(impact.get("requirement_id", ""))
    citations = _string_list(impact.get("citation_ids", []))
    if not citations:
        raise RehearsalInputError(f"predicate_impacts[{index}] for {requirement_id} requires citation_ids")
    affected_stage = str(impact.get("affected_stage", "")).strip()
    if not affected_stage:
        raise RehearsalInputError(f"predicate_impacts[{index}] for {requirement_id} missing affected_stage")
    if affected_stage not in set(_string_list(model.get("stages", []))):
        raise RehearsalInputError(f"predicate_impacts[{index}] references unknown affected_stage {affected_stage!r}")
    for field in ("document_rules_added", "document_rules_changed"):
        rules = impact.get(field, [])
        if not isinstance(rules, list):
            raise RehearsalInputError(f"predicate_impacts[{index}].{field} must be a list")
        for rule_index, rule in enumerate(rules):
            if not isinstance(rule, Mapping):
                raise RehearsalInputError(f"predicate_impacts[{index}].{field}[{rule_index}] must be an object")
            document = str(rule.get("document", rule.get("name", rule.get("document_type", "")))).strip()
            text = str(rule.get("rule", rule.get("note", ""))).strip()
            if not document or not text:
                raise RehearsalInputError(f"predicate_impacts[{index}].{field}[{rule_index}] requires document and rule")
            if not citations:
                raise RehearsalInputError(f"predicate_impacts[{index}].{field}[{rule_index}] requires citations")


def _reject_private_case_facts(value: Any) -> None:
    for path, key, child in _walk_keyed_values(value):
        normalized = key.lower()
        if normalized in _PRIVATE_CASE_FACT_KEYS and _truthy_or_nonempty(child):
            raise RehearsalInputError(f"private case facts are not allowed in rehearsal packets at {path}")
        if normalized == "privacy_classification" and str(child).lower() in {"private", "personal", "case_private"}:
            raise RehearsalInputError(f"private case facts are not allowed in rehearsal packets at {path}")


def _reject_live_execution_claims(value: Any) -> None:
    for path, key, child in _walk_keyed_values(value):
        normalized = key.lower()
        if normalized in _LIVE_EXECUTION_KEYS and child is True:
            raise RehearsalInputError(f"live compiler or crawler execution claims are not allowed at {path}")
        if isinstance(child, str):
            lowered = child.lower().replace("-", "_")
            if "live_crawler" in lowered or "live_compiler" in lowered:
                raise RehearsalInputError(f"live compiler or crawler execution claims are not allowed at {path}")


def _reject_outcome_guarantees(value: Any) -> None:
    for path, key, child in _walk_keyed_values(value):
        normalized = key.lower()
        if normalized in _OUTCOME_GUARANTEE_KEYS and _truthy_or_nonempty(child):
            raise RehearsalInputError(f"legal or permitting outcome guarantees are not allowed at {path}")
        if isinstance(child, str):
            lowered = child.lower()
            if any(phrase in lowered for phrase in _OUTCOME_GUARANTEE_PHRASES):
                raise RehearsalInputError(f"legal or permitting outcome guarantees are not allowed at {path}")


def _reject_active_process_model_mutation(value: Any) -> None:
    for path, key, child in _walk_keyed_values(value):
        normalized = key.lower()
        if normalized in _ACTIVE_MUTATION_KEYS and child is True:
            raise RehearsalInputError(f"active process-model mutation flags are not allowed at {path}")


def _reject_unacknowledged_stale_current_evidence(packet: Mapping[str, Any]) -> None:
    stale_paths = []
    for path, key, child in _walk_keyed_values(packet):
        normalized = key.lower()
        if normalized in {"freshness_status", "current_evidence_status", "source_freshness_status", "evidence_status"}:
            if str(child).lower() in _STALE_STATUSES and "current" in path.lower():
                stale_paths.append(path)
    if not stale_paths:
        return
    acknowledgement = packet.get("stale_current_evidence_acknowledgement")
    if isinstance(acknowledgement, Mapping):
        acknowledged = acknowledgement.get("acknowledged") is True
    else:
        acknowledged = packet.get("stale_current_evidence_acknowledged") is True
    if not acknowledged:
        raise RehearsalInputError("stale-current evidence requires explicit acknowledgement")


def _walk_keyed_values(value: Any, path: str = "$") -> list[tuple[str, str, Any]]:
    walked: list[tuple[str, str, Any]] = []
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            walked.append((child_path, key_text, child))
            walked.extend(_walk_keyed_values(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            walked.extend(_walk_keyed_values(child, f"{path}[{index}]"))
    return walked


def _truthy_or_nonempty(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return False


def _build_process_impact(
    *,
    process_id: str,
    model: Mapping[str, Any],
    candidates: list[Mapping[str, Any]],
    guardrail_impacts: Mapping[str, list[Mapping[str, Any]]],
) -> dict[str, Any]:
    cited_affected_stages: dict[str, dict[str, Any]] = {}
    fact_changes: dict[str, set[str]] = {"add": set(), "remove": set(), "review": set()}
    document_impacts: dict[str, dict[str, Any]] = {}
    unsupported_path_notes: list[dict[str, Any]] = []
    reviewer_owners: set[str] = set()

    for candidate in candidates:
        requirement_id = str(candidate.get("requirement_id", candidate.get("candidate_id", "")))
        stage = str(candidate.get("process_stage", "unspecified"))
        citations = _string_list(candidate.get("source_evidence_ids", []))
        reviewer = str(candidate.get("reviewer_owner", "unassigned"))
        reviewer_owners.add(reviewer)

        for guardrail_impact in guardrail_impacts.get(requirement_id, []):
            citations.extend(_string_list(guardrail_impact.get("citation_ids", [])))
            stage = str(guardrail_impact.get("affected_stage", stage))
            for fact in _string_list(guardrail_impact.get("required_facts_added", [])):
                fact_changes["add"].add(fact)
            for fact in _string_list(guardrail_impact.get("required_facts_removed", [])):
                fact_changes["remove"].add(fact)
            for rule in guardrail_impact.get("document_rules_added", []):
                _record_document_impact(document_impacts, requirement_id, rule, "add", citations)
            for rule in guardrail_impact.get("document_rules_changed", []):
                _record_document_impact(document_impacts, requirement_id, rule, "change", citations)
            for note in _string_list(guardrail_impact.get("unsupported_paths", [])):
                unsupported_path_notes.append(
                    {"requirement_id": requirement_id, "note": note, "citations": sorted(set(citations))}
                )

        for fact in _string_list(candidate.get("required_fact_changes", {}).get("add", [])):
            fact_changes["add"].add(fact)
        for fact in _string_list(candidate.get("required_fact_changes", {}).get("remove", [])):
            fact_changes["remove"].add(fact)
        for fact in _string_list(candidate.get("required_fact_changes", {}).get("review", [])):
            fact_changes["review"].add(fact)

        for impact in candidate.get("document_rule_impacts", []):
            _record_document_impact(
                document_impacts,
                requirement_id,
                impact,
                str(impact.get("impact_type", "review")) if isinstance(impact, Mapping) else "review",
                citations,
            )
        for note in _string_list(candidate.get("unsupported_path_notes", [])):
            unsupported_path_notes.append(
                {"requirement_id": requirement_id, "note": note, "citations": sorted(set(citations))}
            )

        stage_entry = cited_affected_stages.setdefault(
            stage,
            {"stage": stage, "requirement_ids": set(), "citations": set()},
        )
        stage_entry["requirement_ids"].add(requirement_id)
        stage_entry["citations"].update(citations)

    existing_facts = set(_string_list(model.get("required_user_facts", [])))
    existing_documents = set(_document_names(model.get("required_documents", [])))

    return {
        "process_id": process_id,
        "permit_type": str(model.get("permit_type", "synthetic")),
        "fixture_ref": str(model.get("fixture_ref", "embedded_synthetic_process_model")),
        "guardrail_bundle_id": str(model.get("guardrail_bundle_id", "")),
        "cited_affected_stages": _sorted_stage_entries(cited_affected_stages),
        "required_fact_changes": {
            "add": sorted(fact_changes["add"] - existing_facts),
            "remove": sorted(fact_changes["remove"]),
            "review": sorted(fact_changes["review"]),
            "already_required_by_fixture": sorted(fact_changes["add"] & existing_facts),
        },
        "document_rule_impacts": sorted(
            document_impacts.values(),
            key=lambda item: (item["document"], item["impact_type"], item["requirement_id"]),
        ),
        "existing_document_rules_referenced": sorted(existing_documents),
        "unsupported_path_notes": sorted(
            unsupported_path_notes,
            key=lambda item: (item["requirement_id"], item["note"]),
        ),
        "reviewer_owners": sorted(reviewer_owners),
        "no_process_mutation_attestation": {
            "fixture_ref": str(model.get("fixture_ref", "embedded_synthetic_process_model")),
            "active_process_model_changed": False,
            "fixture_written": False,
            "compiled": False,
            "promoted": False,
        },
    }


def _candidate_stub(candidate: Mapping[str, Any]) -> dict[str, str]:
    return {
        "process_id": str(candidate.get("process_id", "")),
        "requirement_id": str(candidate.get("requirement_id", candidate.get("candidate_id", ""))),
        "review_status": str(candidate.get("review_status", "missing_review_status")),
        "reason": "candidate was not approved for impact rehearsal",
    }


def _document_names(documents: Any) -> list[str]:
    names: list[str] = []
    if not isinstance(documents, list):
        return names
    for document in documents:
        if isinstance(document, Mapping):
            names.append(str(document.get("document", document.get("name", document.get("document_type", "")))))
        elif document is not None:
            names.append(str(document))
    return [name for name in names if name]


def _index_guardrail_impacts(raw_impacts: Any) -> dict[str, list[Mapping[str, Any]]]:
    indexed: dict[str, list[Mapping[str, Any]]] = {}
    if not isinstance(raw_impacts, list):
        raise RehearsalInputError("guardrail predicate_impacts must be a list")
    for impact in raw_impacts:
        if not isinstance(impact, Mapping):
            raise RehearsalInputError("guardrail predicate impact entries must be objects")
        requirement_id = str(impact.get("requirement_id", ""))
        if not requirement_id:
            raise RehearsalInputError("guardrail predicate impact entry missing requirement_id")
        indexed.setdefault(requirement_id, []).append(impact)
    return indexed


def _index_process_models(process_models: list[Any]) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for model in process_models:
        if not isinstance(model, Mapping):
            raise RehearsalInputError("process_model_fixtures entries must be objects")
        process_id = str(model.get("process_id", ""))
        if not process_id:
            raise RehearsalInputError("process model fixture missing process_id")
        if process_id in indexed:
            raise RehearsalInputError(f"duplicate process model fixture for {process_id}")
        indexed[process_id] = model
    return indexed


def _record_document_impact(
    impacts: dict[str, dict[str, Any]],
    requirement_id: str,
    impact: Any,
    impact_type: str,
    citations: list[str],
) -> None:
    if isinstance(impact, Mapping):
        document = str(impact.get("document", impact.get("name", impact.get("document_type", ""))))
        rule = str(impact.get("rule", impact.get("note", "")))
    else:
        document = str(impact)
        rule = "review document rule impact"
    if not document:
        raise RehearsalInputError("document rule impact missing document name")
    key = f"{requirement_id}\u241f{document}\u241f{impact_type}\u241f{rule}"
    impacts[key] = {
        "requirement_id": requirement_id,
        "document": document,
        "impact_type": impact_type,
        "rule": rule,
        "citations": sorted(set(citations)),
    }


def _require_list(packet: Mapping[str, Any], key: str) -> list[Any]:
    value = packet.get(key)
    if not isinstance(value, list):
        raise RehearsalInputError(f"{key} must be a list")
    return value


def _require_mapping(packet: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = packet.get(key)
    if not isinstance(value, Mapping):
        raise RehearsalInputError(f"{key} must be an object")
    return value


def _sorted_stage_entries(entries: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rendered = []
    for stage in sorted(entries):
        entry = entries[stage]
        rendered.append(
            {
                "stage": stage,
                "requirement_ids": sorted(entry["requirement_ids"]),
                "citations": sorted(entry["citations"]),
            }
        )
    return rendered


def _stable_digest(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise RehearsalInputError("expected a list of strings")
    return [str(item) for item in value if item is not None and str(item)]
