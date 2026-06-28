"""Fixture-first requirement regeneration promotion decision packets.

The packet built here is a metadata-only decision artifact. It consumes the
reviewer acknowledgement packet, regenerated requirement candidate, process
model impact candidate, guardrail recompilation rehearsal, and regenerated agent
regression matrix, then records reviewer-selected promote/defer decisions.

It never emits replacement active requirement, process model, or guardrail bundle
content. Downstream activation remains blocked for a separate promotion step.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from typing import Any


PROMOTION_DECISIONS = {"promote", "defer"}
_REQUIRED_PREREQUISITE_COMPONENTS = {
    "reviewer_acknowledgement_packet",
    "regenerated_requirement_candidate",
    "process_model_impact_candidate",
    "guardrail_recompilation_rehearsal",
    "regenerated_agent_regression_matrix",
}
_ACTIVE_CONTENT_KEYS = {
    "active_requirement",
    "active_requirements",
    "active_requirement_patch",
    "replacement_requirement",
    "replacement_requirements",
    "promoted_requirement",
    "active_process_model",
    "active_process_models",
    "active_process_model_patch",
    "replacement_process_model",
    "replacement_process_models",
    "promoted_process_model",
    "compiled_process_model",
    "active_guardrail_bundle",
    "active_guardrail_bundles",
    "active_guardrail_bundle_patch",
    "replacement_guardrail_bundle",
    "replacement_guardrail_bundles",
    "promoted_guardrail_bundle",
    "compiled_guardrail_bundle",
}
_PRIVATE_KEY_PARTS = {
    "auth_state",
    "authorization",
    "case_fact_value",
    "credential",
    "cookie",
    "password",
    "payment_detail",
    "private_case_fact",
    "private_path",
    "secret",
    "session_state",
    "token",
    "trace",
    "user_case_fact",
}
_RAW_REFERENCE_KEY_PARTS = {
    "crawl_output",
    "downloaded_document",
    "har",
    "raw_body",
    "raw_crawl",
    "raw_document",
    "raw_html",
    "raw_pdf",
    "screenshot",
    "trace_file",
    "warc",
}
_LIVE_EXECUTION_KEYS = {
    "call_llm",
    "calls_llm",
    "execute_live_devhub",
    "launch_devhub",
    "launches_devhub",
    "open_browser",
    "playwright_enabled",
    "use_live_llm",
    "uses_authenticated_session",
    "writes_private_artifacts",
}
_DOWNSTREAM_ACTIVATION_KEYS = {
    "activate_downstream",
    "activation_allowed",
    "activation_enabled",
    "apply_to_active",
    "direct_activation",
    "downstream_activation_enabled",
    "enable_downstream_activation",
    "mutates_active_artifacts",
    "promote_to_active",
    "production_promotion_enabled",
}
_ACTIVE_MUTATION_KEYS = {
    "active_guardrail_bundle_mutated",
    "active_process_model_mutated",
    "active_requirement_mutated",
    "mutates_active_guardrail_bundles",
    "mutates_active_process_models",
    "mutates_active_requirements",
}
_PRODUCTION_READY_LABELS = {
    "production_enabled",
    "production-ready",
    "production_ready",
    "ready_for_production",
}
_STALE_SOURCE_STATUSES = {
    "changed",
    "expired",
    "needs_review",
    "outdated",
    "stale",
    "stale_source",
}
_ACCEPTED_DECISIONS = {
    "accept",
    "accepted",
    "accepted_for_regeneration",
    "approved",
    "promote",
}


@dataclass(frozen=True)
class RequirementRegenerationPromotionDecisionFinding:
    code: str
    path: str
    message: str


class RequirementRegenerationPromotionDecisionPacketError(ValueError):
    """Raised when a promotion decision packet is malformed or unsafe."""


def load_json_object(path: str) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise RequirementRegenerationPromotionDecisionPacketError(f"expected JSON object in {path}")
    return data


def build_requirement_regeneration_promotion_decision_packet(packet_input: Mapping[str, Any]) -> dict[str, Any]:
    """Build a deterministic metadata-only promote/defer decision packet."""

    if not isinstance(packet_input, Mapping):
        raise RequirementRegenerationPromotionDecisionPacketError("packet input must be an object")
    _reject_unsafe_inputs(packet_input)

    acknowledgement_packet = _mapping(packet_input, "reviewer_acknowledgement_packet")
    regenerated_candidate = _mapping(packet_input, "regenerated_requirement_candidate")
    impact_candidate = _mapping(packet_input, "process_model_impact_candidate")
    rehearsal = _mapping(packet_input, "guardrail_recompilation_rehearsal")
    regression_matrix = _mapping(packet_input, "regenerated_agent_regression_matrix")
    reviewer_decisions = list(_sequence_of_mappings(packet_input.get("reviewer_promotion_decisions")))

    originals = (
        deepcopy(acknowledgement_packet),
        deepcopy(regenerated_candidate),
        deepcopy(impact_candidate),
        deepcopy(rehearsal),
        deepcopy(regression_matrix),
    )

    acknowledgement_complete = _acknowledgement_complete(acknowledgement_packet)
    regression_issues = _regression_matrix_issues(regression_matrix)
    rehearsal_disabled = _rehearsal_disabled(rehearsal)
    candidate_ids = _candidate_artifact_ids(
        acknowledgement_packet,
        regenerated_candidate,
        impact_candidate,
        rehearsal,
        regression_matrix,
    )
    citation_scope = _citation_refresh_scope(acknowledgement_packet, regenerated_candidate, reviewer_decisions)
    change_audit = _change_citation_audit(regenerated_candidate, impact_candidate)
    rollback_notes = _rollback_notes(rehearsal, regenerated_candidate, impact_candidate)
    decisions = _promotion_decisions(
        reviewer_decisions,
        acknowledgement_complete=acknowledgement_complete,
        regression_issues=regression_issues,
        rehearsal_disabled=rehearsal_disabled,
        citation_scope=citation_scope,
        change_audit=change_audit,
    )

    packet = {
        "packet_type": "requirement_regeneration_promotion_decision_packet",
        "packet_id": str(packet_input.get("packet_id") or "requirement-regeneration-promotion-decision-" + _stable_hash({"decisions": reviewer_decisions, "artifacts": candidate_ids})),
        "packet_mode": "fixture_first_metadata_only",
        "packet_status": "reviewer_decisions_recorded_activation_blocked",
        "does_not_mutate_active_requirements": True,
        "does_not_mutate_active_process_models": True,
        "does_not_mutate_active_guardrail_bundles": True,
        "active_requirement_mutated": False,
        "active_process_model_mutated": False,
        "active_guardrail_bundle_mutated": False,
        "metadata_only_artifact_ids": candidate_ids,
        "prerequisite_links": _prerequisite_links(candidate_ids),
        "reviewer_selected_decisions": decisions,
        "citation_refresh_scope": citation_scope,
        "change_citation_audit": change_audit,
        "rollback_notes": rollback_notes,
        "blocked_downstream_activation": True,
        "blocked_downstream_activation_reason": "metadata_only_decision_packet_requires_separate_validated_promotion_step",
        "activation_allowed": False,
        "execution_boundaries": {
            "calls_llm": False,
            "launches_devhub": False,
            "uses_authenticated_session": False,
            "reads_private_files": False,
            "writes_private_artifacts": False,
            "mutates_active_requirements": False,
            "mutates_active_process_models": False,
            "mutates_active_guardrail_bundles": False,
        },
        "input_validation_summary": {
            "reviewer_acknowledgement_complete": acknowledgement_complete,
            "guardrail_rehearsal_disabled": rehearsal_disabled,
            "regression_matrix_issue_count": len(regression_issues),
            "regression_matrix_issue_codes": sorted({issue["code"] for issue in regression_issues}),
            "change_citation_audit_complete": all(row.get("cited") is True for row in change_audit),
        },
    }

    if (acknowledgement_packet, regenerated_candidate, impact_candidate, rehearsal, regression_matrix) != originals:
        raise RequirementRegenerationPromotionDecisionPacketError("promotion decision inputs were mutated")

    findings = validate_requirement_regeneration_promotion_decision_packet(packet)
    if findings:
        detail = "; ".join(f"{item.code} at {item.path}: {item.message}" for item in findings)
        raise RequirementRegenerationPromotionDecisionPacketError(detail)
    return packet


def build_requirement_regeneration_promotion_decision_packet_from_file(path: str) -> dict[str, Any]:
    return build_requirement_regeneration_promotion_decision_packet(load_json_object(path))


def validate_requirement_regeneration_promotion_decision_packet(packet: Mapping[str, Any]) -> list[RequirementRegenerationPromotionDecisionFinding]:
    """Return validation findings for a metadata-only decision packet."""

    if not isinstance(packet, Mapping):
        return [RequirementRegenerationPromotionDecisionFinding("invalid_packet", "$", "Packet must be an object.")]

    findings: list[RequirementRegenerationPromotionDecisionFinding] = []
    findings.extend(_safety_findings(packet))

    if packet.get("packet_type") != "requirement_regeneration_promotion_decision_packet":
        findings.append(RequirementRegenerationPromotionDecisionFinding("invalid_packet_type", "$.packet_type", "Packet type must be requirement_regeneration_promotion_decision_packet."))
    if packet.get("packet_mode") != "fixture_first_metadata_only":
        findings.append(RequirementRegenerationPromotionDecisionFinding("not_fixture_first", "$.packet_mode", "Packet must be fixture-first and metadata-only."))
    if packet.get("blocked_downstream_activation") is not True:
        findings.append(RequirementRegenerationPromotionDecisionFinding("activation_not_blocked", "$.blocked_downstream_activation", "Downstream activation must remain blocked."))
    if packet.get("activation_allowed") is not False:
        findings.append(RequirementRegenerationPromotionDecisionFinding("activation_allowed", "$.activation_allowed", "Decision packet must not allow activation."))

    for key in ("active_requirement_mutated", "active_process_model_mutated", "active_guardrail_bundle_mutated"):
        if packet.get(key) is not False:
            findings.append(RequirementRegenerationPromotionDecisionFinding("active_artifact_mutation", f"$.{key}", "Active artifacts must not be mutated."))
    for key in ("does_not_mutate_active_requirements", "does_not_mutate_active_process_models", "does_not_mutate_active_guardrail_bundles"):
        if packet.get(key) is not True:
            findings.append(RequirementRegenerationPromotionDecisionFinding("missing_no_mutation_attestation", f"$.{key}", "Packet must attest that active artifacts are preserved."))

    artifact_ids = list(_sequence_of_mappings(packet.get("metadata_only_artifact_ids")))
    if not artifact_ids:
        findings.append(RequirementRegenerationPromotionDecisionFinding("missing_metadata_artifact_ids", "$.metadata_only_artifact_ids", "Packet must include metadata-only artifact IDs."))
    for index, artifact in enumerate(artifact_ids):
        path = f"$.metadata_only_artifact_ids[{index}]"
        if not _text(artifact.get("artifact_id")):
            findings.append(RequirementRegenerationPromotionDecisionFinding("missing_artifact_id", path + ".artifact_id", "Metadata artifact entry must include an artifact ID."))
        if artifact.get("metadata_only") is not True:
            findings.append(RequirementRegenerationPromotionDecisionFinding("artifact_not_metadata_only", path + ".metadata_only", "Artifact entry must be metadata-only."))
        if artifact.get("activation_allowed") is not False:
            findings.append(RequirementRegenerationPromotionDecisionFinding("artifact_activation_allowed", path + ".activation_allowed", "Artifact entry must not allow activation."))

    findings.extend(_prerequisite_link_findings(packet))
    findings.extend(_change_citation_findings(packet))

    decisions = list(_sequence_of_mappings(packet.get("reviewer_selected_decisions")))
    if not decisions:
        findings.append(RequirementRegenerationPromotionDecisionFinding("missing_reviewer_decisions", "$.reviewer_selected_decisions", "Packet must record reviewer-selected decisions."))
    for index, decision in enumerate(decisions):
        path = f"$.reviewer_selected_decisions[{index}]"
        if decision.get("reviewer_selected_decision") not in PROMOTION_DECISIONS:
            findings.append(RequirementRegenerationPromotionDecisionFinding("invalid_reviewer_decision", path + ".reviewer_selected_decision", "Reviewer decision must be promote or defer."))
        if decision.get("activation_allowed") is not False:
            findings.append(RequirementRegenerationPromotionDecisionFinding("decision_activation_allowed", path + ".activation_allowed", "Decision entries must not allow activation."))
        if decision.get("mutates_active_artifacts") is not False:
            findings.append(RequirementRegenerationPromotionDecisionFinding("decision_mutates_active_artifacts", path + ".mutates_active_artifacts", "Decision entries must not mutate active artifacts."))
        if decision.get("final_decision") == "promote_candidate_metadata_only" and decision.get("blocked_downstream_activation") is not True:
            findings.append(RequirementRegenerationPromotionDecisionFinding("promote_without_activation_block", path + ".blocked_downstream_activation", "Metadata-only promote decisions must still block downstream activation."))

    if not list(_sequence_of_mappings(packet.get("citation_refresh_scope"))):
        findings.append(RequirementRegenerationPromotionDecisionFinding("missing_citation_refresh_scope", "$.citation_refresh_scope", "Packet must include citation refresh scope."))
    if not list(_sequence_of_mappings(packet.get("rollback_notes"))):
        findings.append(RequirementRegenerationPromotionDecisionFinding("missing_rollback_notes", "$.rollback_notes", "Packet must include rollback notes."))

    boundaries = packet.get("execution_boundaries")
    if not isinstance(boundaries, Mapping):
        findings.append(RequirementRegenerationPromotionDecisionFinding("missing_execution_boundaries", "$.execution_boundaries", "Packet must include execution boundaries."))
    else:
        for key, value in boundaries.items():
            if value is not False:
                findings.append(RequirementRegenerationPromotionDecisionFinding("execution_boundary_enabled", f"$.execution_boundaries.{key}", "Execution boundaries must be explicitly disabled."))

    for path, key, value in _walk(packet):
        key_text = str(key) if key is not None else ""
        if key_text in _ACTIVE_CONTENT_KEYS and value not in (None, False, "", [], {}):
            findings.append(RequirementRegenerationPromotionDecisionFinding("active_content_present", path, "Decision packet must not include replacement active artifact content."))

    return findings


def require_valid_requirement_regeneration_promotion_decision_packet(packet: Mapping[str, Any]) -> None:
    findings = validate_requirement_regeneration_promotion_decision_packet(packet)
    if findings:
        detail = "; ".join(f"{item.code} at {item.path}: {item.message}" for item in findings)
        raise RequirementRegenerationPromotionDecisionPacketError(detail)


def finding_codes(findings: Iterable[RequirementRegenerationPromotionDecisionFinding]) -> set[str]:
    return {finding.code for finding in findings}


def _promotion_decisions(
    reviewer_decisions: Sequence[Mapping[str, Any]],
    *,
    acknowledgement_complete: bool,
    regression_issues: Sequence[Mapping[str, str]],
    rehearsal_disabled: bool,
    citation_scope: Sequence[Mapping[str, Any]],
    change_audit: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    uncited_changes = [row for row in change_audit if row.get("cited") is not True]
    for index, raw_decision in enumerate(reviewer_decisions):
        requested = _text(raw_decision.get("decision"), "defer").lower()
        if requested not in PROMOTION_DECISIONS:
            requested = "defer"
        blocked_reasons: list[str] = []
        if not acknowledgement_complete:
            blocked_reasons.append("reviewer_acknowledgement_incomplete")
        if not rehearsal_disabled:
            blocked_reasons.append("guardrail_rehearsal_not_disabled")
        if regression_issues:
            blocked_reasons.append("regression_matrix_validation_failed")
        if not citation_scope:
            blocked_reasons.append("citation_refresh_scope_missing")
        if uncited_changes:
            blocked_reasons.append("uncited_requirement_or_process_change")
        if requested == "defer":
            blocked_reasons.append(_text(raw_decision.get("defer_reason"), "reviewer_selected_defer"))

        final_decision = "promote_candidate_metadata_only" if requested == "promote" and not blocked_reasons else "defer"
        decisions.append(
            {
                "decision_id": _text(raw_decision.get("decision_id"), f"promotion-decision-{index + 1}"),
                "target_id": _text(raw_decision.get("target_id"), "unknown-target"),
                "target_type": _text(raw_decision.get("target_type"), "requirement_diff"),
                "reviewer_selected_decision": requested,
                "final_decision": final_decision,
                "decision_rationale": _text(raw_decision.get("decision_rationale")),
                "citation_refresh_scope_ids": sorted(_strings(raw_decision.get("citation_refresh_scope_ids"))),
                "blocked_reasons": tuple(sorted(set(blocked_reasons))),
                "blocked_downstream_activation": True,
                "activation_allowed": False,
                "mutates_active_artifacts": False,
                "metadata_only": True,
            }
        )
    return sorted(decisions, key=lambda item: item["decision_id"])


def _candidate_artifact_ids(*packets: Mapping[str, Any]) -> list[dict[str, Any]]:
    specs = (
        ("reviewer_acknowledgement_packet", ("packet_id", "acknowledgement_id")),
        ("regenerated_requirement_candidate", ("candidate_id", "packet_id")),
        ("process_model_impact_candidate", ("candidate_id", "packet_id")),
        ("guardrail_recompilation_rehearsal", ("rehearsal_id", "packet_id")),
        ("regenerated_agent_regression_matrix", ("matrix_id", "packet_id")),
    )
    artifacts: list[dict[str, Any]] = []
    for component, keys, packet in zip((spec[0] for spec in specs), (spec[1] for spec in specs), packets):
        artifact_id = ""
        for key in keys:
            artifact_id = _text(packet.get(key))
            if artifact_id:
                break
        if not artifact_id:
            artifact_id = component + "-metadata"
        artifacts.append(
            {
                "artifact_type": component,
                "artifact_id": artifact_id,
                "metadata_artifact_id": "metadata-only." + _slug(component) + "." + _stable_hash({"id": artifact_id}),
                "metadata_only": True,
                "payload_persisted": False,
                "activation_allowed": False,
            }
        )
    return artifacts


def _prerequisite_links(artifact_ids: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for artifact in artifact_ids:
        component = _text(artifact.get("artifact_type"), "unknown_component")
        artifact_id = _text(artifact.get("artifact_id"), "unknown_artifact")
        links.append(
            {
                "component": component,
                "artifact_id": artifact_id,
                "link_id": "prerequisite." + _slug(component) + "." + _stable_hash({"artifact_id": artifact_id}),
                "required_for_decision": True,
                "metadata_only": True,
            }
        )
    return sorted(links, key=lambda item: item["component"])


def _prerequisite_link_findings(packet: Mapping[str, Any]) -> list[RequirementRegenerationPromotionDecisionFinding]:
    links = list(_sequence_of_mappings(packet.get("prerequisite_links")))
    if not links:
        return [RequirementRegenerationPromotionDecisionFinding("missing_prerequisite_links", "$.prerequisite_links", "Decision packet must link every prerequisite artifact.")]
    findings: list[RequirementRegenerationPromotionDecisionFinding] = []
    seen = {_text(link.get("component")) for link in links}
    missing = sorted(_REQUIRED_PREREQUISITE_COMPONENTS - seen)
    if missing:
        findings.append(RequirementRegenerationPromotionDecisionFinding("missing_prerequisite_links", "$.prerequisite_links", "Missing prerequisite component links: " + ", ".join(missing) + "."))
    for index, link in enumerate(links):
        path = f"$.prerequisite_links[{index}]"
        if not _text(link.get("artifact_id")):
            findings.append(RequirementRegenerationPromotionDecisionFinding("missing_prerequisite_artifact_id", path + ".artifact_id", "Prerequisite link must identify its artifact."))
        if link.get("required_for_decision") is not True:
            findings.append(RequirementRegenerationPromotionDecisionFinding("prerequisite_not_required", path + ".required_for_decision", "Prerequisite links must be required for the decision."))
    return findings


def _change_citation_audit(regenerated_candidate: Mapping[str, Any], impact_candidate: Mapping[str, Any]) -> list[dict[str, Any]]:
    audit: list[dict[str, Any]] = []
    for index, diff in enumerate(_sequence_of_mappings(regenerated_candidate.get("requirement_diffs"))):
        evidence_ids = sorted(_strings(diff.get("source_evidence_ids")))
        audit.append(
            {
                "change_id": _text(diff.get("diff_id"), f"requirement_diff_{index + 1}"),
                "change_kind": "requirement_diff",
                "citation_ids": evidence_ids,
                "cited": bool(evidence_ids),
            }
        )
    for section_name in ("affected_process_stages", "affected_required_documents", "affected_unsupported_paths", "reviewer_prompts"):
        for index, change in enumerate(_sequence_of_mappings(impact_candidate.get(section_name))):
            citation_ids = sorted(_strings(change.get("source_requirement_diff_ids")) | _strings(change.get("source_requirement_diff_id")) | _strings(change.get("source_evidence_ids")))
            audit.append(
                {
                    "change_id": _text(change.get("stage_id") or change.get("required_document_id") or change.get("path_id") or change.get("prompt_id"), f"{section_name}_{index + 1}"),
                    "change_kind": "process_model_" + section_name,
                    "citation_ids": citation_ids,
                    "cited": bool(citation_ids),
                }
            )
    return sorted(audit, key=lambda item: (item["change_kind"], item["change_id"]))


def _change_citation_findings(packet: Mapping[str, Any]) -> list[RequirementRegenerationPromotionDecisionFinding]:
    audit = list(_sequence_of_mappings(packet.get("change_citation_audit")))
    if not audit:
        return [RequirementRegenerationPromotionDecisionFinding("missing_change_citation_audit", "$.change_citation_audit", "Decision packet must audit citations for requirement and process changes.")]
    findings: list[RequirementRegenerationPromotionDecisionFinding] = []
    for index, row in enumerate(audit):
        path = f"$.change_citation_audit[{index}]"
        if row.get("cited") is not True or not _strings(row.get("citation_ids")):
            findings.append(RequirementRegenerationPromotionDecisionFinding("uncited_requirement_or_process_change", path, "Requirement and process changes must cite source evidence or requirement diff IDs."))
    return findings


def _citation_refresh_scope(
    acknowledgement_packet: Mapping[str, Any],
    regenerated_candidate: Mapping[str, Any],
    reviewer_decisions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    scope_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for acknowledgement in _sequence_of_mappings(acknowledgement_packet.get("source_acknowledgements")):
        source_id = _text(acknowledgement.get("source_id"), "unknown-source")
        for scope_id in _strings(acknowledgement.get("citation_refresh_scope")):
            scope_by_key[(source_id, scope_id)] = {
                "source_id": source_id,
                "scope_id": scope_id,
                "scope_source": "reviewer_acknowledgement_packet",
                "refresh_required_before_activation": True,
            }
    for diff in _sequence_of_mappings(regenerated_candidate.get("requirement_diffs")):
        diff_id = _text(diff.get("diff_id"), _text(diff.get("requirement_id"), "unknown-diff"))
        for evidence_id in _strings(diff.get("source_evidence_ids")):
            scope_by_key[(diff_id, evidence_id)] = {
                "source_id": diff_id,
                "scope_id": evidence_id,
                "scope_source": "regenerated_requirement_candidate",
                "refresh_required_before_activation": True,
            }
    for decision in reviewer_decisions:
        target_id = _text(decision.get("target_id"), "unknown-target")
        for scope_id in _strings(decision.get("citation_refresh_scope_ids")):
            scope_by_key[(target_id, scope_id)] = {
                "source_id": target_id,
                "scope_id": scope_id,
                "scope_source": "reviewer_promotion_decision",
                "refresh_required_before_activation": True,
            }
    return sorted(scope_by_key.values(), key=lambda item: (item["source_id"], item["scope_id"]))


def _rollback_notes(
    rehearsal: Mapping[str, Any],
    regenerated_candidate: Mapping[str, Any],
    impact_candidate: Mapping[str, Any],
) -> list[dict[str, Any]]:
    notes: list[dict[str, Any]] = []
    for index, ref in enumerate(_sequence_of_mappings(rehearsal.get("rollback_references"))):
        notes.append(
            {
                "rollback_note_id": _text(ref.get("rollback_ref_id"), f"rollback-note-{index + 1}"),
                "active_guardrail_bundle_id": _text(ref.get("active_guardrail_bundle_id"), _text(rehearsal.get("active_guardrail_bundle_id"))),
                "active_guardrail_bundle_revision": _text(ref.get("active_guardrail_bundle_revision"), _text(rehearsal.get("active_guardrail_bundle_revision"))),
                "restore_action": _text(ref.get("restore_action"), "retain_active_bundle_and_discard_metadata_only_candidates"),
                "activation_blocked": True,
            }
        )
    if not notes:
        notes.append(
            {
                "rollback_note_id": "rollback-note." + _stable_hash({"candidate": regenerated_candidate, "impact": impact_candidate}),
                "active_guardrail_bundle_id": _text(rehearsal.get("active_guardrail_bundle_id"), "active-bundle-not-specified"),
                "active_guardrail_bundle_revision": _text(rehearsal.get("active_guardrail_bundle_revision"), "active-revision-not-specified"),
                "restore_action": "retain_existing_active_artifacts_and_discard_metadata_only_decision_packet",
                "activation_blocked": True,
            }
        )
    return sorted(notes, key=lambda item: item["rollback_note_id"])


def _acknowledgement_complete(packet: Mapping[str, Any]) -> bool:
    if packet.get("acknowledgement_complete") is False:
        return False
    acknowledgements = list(_sequence_of_mappings(packet.get("source_acknowledgements")))
    if not acknowledgements:
        return bool(packet.get("acknowledgement_complete") is True)
    return all(item.get("acknowledgement_complete") is True for item in acknowledgements)


def _rehearsal_disabled(packet: Mapping[str, Any]) -> bool:
    activation = packet.get("activation_state")
    if not isinstance(activation, Mapping):
        return False
    return activation.get("disabled") is True and activation.get("activation_enabled") is False and activation.get("promotion_target") == "none"


def _regression_matrix_issues(matrix: Mapping[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    for finding in _safety_findings(matrix):
        issues.append({"code": finding.code, "path": finding.path, "message": finding.message})
    for index, case in enumerate(_sequence_of_mappings(matrix.get("cases") or matrix.get("tests") or matrix.get("rows"))):
        expected = case.get("expected") or case.get("expected_outcome") or case.get("outcome")
        if expected not in (None, "", [], {}) and not _case_has_citation(case, expected):
            issues.append({"code": "uncited_expected_outcome", "path": f"$.cases[{index}]", "message": "Expected outcomes must cite source evidence."})
        action_text = _compact_text(case.get("action") or case.get("when") or case.get("name"))
        expected_text = _compact_text(expected)
        if _contains_consequential_action(action_text) and "blocked" not in expected_text and "manual_handoff" not in expected_text:
            issues.append({"code": "blocked_action_downgrade", "path": f"$.cases[{index}]", "message": "Consequential actions must remain blocked or handoff-gated."})
    return issues


def _case_has_citation(case: Mapping[str, Any], expected: Any) -> bool:
    citation_keys = ("citation", "citations", "source_evidence_id", "source_evidence_ids", "evidence", "evidence_ids", "sources")
    for container in (case, expected):
        if isinstance(container, Mapping):
            for key in citation_keys:
                value = container.get(key)
                if isinstance(value, str) and value.strip():
                    return True
                if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) and len(value) > 0:
                    return True
    return False


def _contains_consequential_action(text: str) -> bool:
    return any(word in text for word in ("submit", "certify", "upload", "payment", "pay", "schedule", "cancel", "withdraw"))


def _reject_unsafe_inputs(value: Any) -> None:
    findings = _safety_findings(value)
    if findings:
        detail = "; ".join(f"{finding.code} at {finding.path}: {finding.message}" for finding in findings)
        raise RequirementRegenerationPromotionDecisionPacketError(detail)


def _safety_findings(value: Any) -> list[RequirementRegenerationPromotionDecisionFinding]:
    findings: list[RequirementRegenerationPromotionDecisionFinding] = []
    for path, key, child in _walk(value):
        key_text = str(key).lower() if key is not None else ""
        if key_text in _LIVE_EXECUTION_KEYS and child is True:
            findings.append(RequirementRegenerationPromotionDecisionFinding("live_execution_enabled", path, "Live execution must be disabled."))
        if any(part in key_text for part in _PRIVATE_KEY_PARTS) and child not in (None, "", False, [], {}):
            findings.append(RequirementRegenerationPromotionDecisionFinding("private_case_or_session_fact", path, "Private case, credential, session, or payment facts are not allowed."))
        if any(part in key_text for part in _RAW_REFERENCE_KEY_PARTS) and child not in (None, "", False, [], {}):
            findings.append(RequirementRegenerationPromotionDecisionFinding("raw_document_or_crawl_reference", path, "Raw document, crawl, trace, screenshot, HAR, or WARC references are not allowed."))
        if key_text in _DOWNSTREAM_ACTIVATION_KEYS and child is True:
            findings.append(RequirementRegenerationPromotionDecisionFinding("downstream_activation_flag", path, "Downstream activation flags must remain disabled."))
        if key_text in _ACTIVE_MUTATION_KEYS and child is True:
            findings.append(RequirementRegenerationPromotionDecisionFinding("active_artifact_mutation", path, "Active artifact mutation is not allowed."))
        if key_text in _ACTIVE_CONTENT_KEYS and child not in (None, False, "", [], {}):
            findings.append(RequirementRegenerationPromotionDecisionFinding("active_content_present", path, "Replacement active artifact content is not allowed."))
        if isinstance(child, str) and _compact_text(child).replace(" ", "_") in _PRODUCTION_READY_LABELS:
            findings.append(RequirementRegenerationPromotionDecisionFinding("production_ready_label", path, "Production-ready labels are not allowed in metadata-only decision packets."))
    findings.extend(_stale_source_acceptance_findings(value))
    return findings


def _stale_source_acceptance_findings(value: Any) -> list[RequirementRegenerationPromotionDecisionFinding]:
    findings: list[RequirementRegenerationPromotionDecisionFinding] = []
    for path, _key, child in _walk(value):
        if not isinstance(child, Mapping):
            continue
        freshness = _text(child.get("freshness_status") or child.get("source_freshness_status")).lower()
        if freshness not in _STALE_SOURCE_STATUSES:
            continue
        decision = _text(child.get("reviewer_decision") or child.get("decision") or child.get("review_status")).lower()
        if decision not in _ACCEPTED_DECISIONS:
            continue
        acknowledged = child.get("stale_source_reviewer_acknowledgement") is True or child.get("reviewer_acknowledged_stale_source") is True or child.get("reviewer_acknowledgement") is True
        if not acknowledged:
            findings.append(RequirementRegenerationPromotionDecisionFinding("stale_source_accepted_without_acknowledgement", path, "Stale sources cannot be accepted without explicit reviewer acknowledgement."))
    return findings


def _mapping(value: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    child = value.get(key)
    if not isinstance(child, Mapping):
        raise RequirementRegenerationPromotionDecisionPacketError(f"missing object: {key}")
    return child


def _sequence_of_mappings(value: Any) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _strings(value: Any) -> set[str]:
    if isinstance(value, str):
        text = value.strip()
        return {text} if text else set()
    if isinstance(value, Mapping):
        return {_text(value.get("id"))} - {""}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        values: set[str] = set()
        for item in value:
            values.update(_strings(item))
        return values
    return set()


def _walk(value: Any, path: str = "$", key: object | None = None) -> Iterable[tuple[str, object | None, Any]]:
    yield path, key, value
    if isinstance(value, Mapping):
        for child_key, child_value in value.items():
            yield from _walk(child_value, f"{path}.{child_key}", child_key)
    elif isinstance(value, (list, tuple)):
        for index, child_value in enumerate(value):
            yield from _walk(child_value, f"{path}[{index}]", index)


def _compact_text(value: Any) -> str:
    if isinstance(value, str):
        return " ".join(value.lower().split())
    if isinstance(value, Mapping):
        return " ".join(_compact_text(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return " ".join(_compact_text(item) for item in value)
    return str(value).lower() if value is not None else ""


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _slug(value: Any) -> str:
    text = _text(value, "unknown").lower()
    return "".join(character if character.isalnum() else "-" for character in text).strip("-") or "unknown"


def _text(value: Any, default: str = "") -> str:
    if isinstance(value, str):
        text = value.strip()
        return text if text else default
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default
