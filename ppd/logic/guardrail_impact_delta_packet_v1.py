"""Fixture-first PP&D guardrail impact delta packet v1.

This module maps synthetic process dependency graph delta rows into inactive
review packets for guardrail impacts. It is deliberately offline-only: it does
not compile guardrails, promote bundles, change prompts, mutate process models,
write source registries, touch DevHub surfaces, update release state, or write
daemon state.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any


PACKET_VERSION = "guardrail_impact_delta_packet_v1"
PACKET_MODE = "fixture_first_delta_review_only"
MUTATION_POLICY = "no_compile_no_promotion_no_active_mutation"

EXACT_OFFLINE_VALIDATION_COMMANDS: tuple[tuple[str, ...], ...] = (
    ("python3", "-m", "py_compile", "ppd/logic/guardrail_impact_delta_packet_v1.py"),
    ("python3", "-m", "pytest", "ppd/tests/test_guardrail_impact_delta_packet_v1.py"),
    ("python3", "ppd/daemon/ppd_daemon.py", "--self-test"),
)

_REQUIRED_PACKET_FIELDS = (
    "packet_version",
    "packet_mode",
    "packet_id",
    "source_process_dependency_graph_delta_packet_id",
    "affected_deterministic_predicate_rows",
    "affected_deontic_rule_rows",
    "affected_temporal_rule_rows",
    "affected_reversible_action_predicate_rows",
    "affected_exact_confirmation_predicate_rows",
    "affected_refused_action_predicate_rows",
    "affected_explanation_template_placeholder_rows",
    "stale_source_hold_rows",
    "reviewer_disposition_rows",
    "offline_validation_commands",
    "mutation_policy",
    "no_active_mutation_attestations",
)

_ROW_GROUPS = (
    "affected_deterministic_predicate_rows",
    "affected_deontic_rule_rows",
    "affected_temporal_rule_rows",
    "affected_reversible_action_predicate_rows",
    "affected_exact_confirmation_predicate_rows",
    "affected_refused_action_predicate_rows",
    "affected_explanation_template_placeholder_rows",
    "stale_source_hold_rows",
    "reviewer_disposition_rows",
)

_ROW_PAYLOAD_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "affected_deterministic_predicate_rows": ("predicate_id", "predicate_name", "affected_inputs", "impact_summary"),
    "affected_deontic_rule_rows": ("rule_id", "rule_kind", "affected_terms", "impact_summary"),
    "affected_temporal_rule_rows": ("rule_id", "temporal_triggers", "impact_summary"),
    "affected_reversible_action_predicate_rows": ("predicate_id", "safe_action_boundary", "affected_process_stages", "impact_summary"),
    "affected_exact_confirmation_predicate_rows": ("predicate_id", "confirmation_scope", "affected_boundaries", "impact_summary"),
    "affected_refused_action_predicate_rows": ("predicate_id", "refusal_scope", "affected_unsupported_paths", "impact_summary"),
    "affected_explanation_template_placeholder_rows": ("template_id", "placeholders", "impact_summary"),
    "stale_source_hold_rows": ("hold_id", "hold_reason", "reviewer_holds"),
    "reviewer_disposition_rows": ("disposition_id", "allowed_dispositions", "current_disposition"),
}

_FALSE_ATTESTATIONS = (
    "compiled_guardrails",
    "promoted_guardrails",
    "mutated_active_guardrails",
    "changed_prompts",
    "changed_requirements",
    "changed_process_models",
    "changed_contracts",
    "changed_source_registries",
    "changed_devhub_surfaces",
    "changed_release_state",
    "changed_daemon_state",
)

_PRIVATE_OR_LIVE_TERMS = (
    "auth_state",
    "browser state",
    "cookie",
    "credential",
    "devhub session",
    "downloaded document",
    "har file",
    "private artifact",
    "raw crawl",
    "raw html",
    "screenshot",
    "session token",
    "storage_state",
)

_LIVE_DEVHUB_CLAIM_TERMS = (
    "authenticated devhub",
    "devhub login observed",
    "devhub live",
    "devhub session observed",
    "live crawl",
    "live devhub",
)

_LEGAL_OR_PERMITTING_GUARANTEE_TERMS = (
    "approval guaranteed",
    "guaranteed approval",
    "guaranteed permit",
    "legal advice",
    "legal guarantee",
    "permit guaranteed",
    "will be approved",
    "will be issued",
)

_OFFICIAL_ACTION_COMPLETION_TERMS = (
    "application submitted",
    "certification completed",
    "fee paid",
    "inspection scheduled",
    "official action completed",
    "payment completed",
    "permit purchased",
    "submitted successfully",
    "uploaded to official record",
)

_NON_OFFLINE_COMMAND_TERMS = (
    "curl",
    "devhub.portlandoregon.gov",
    "playwright",
    "wget",
)

_ACTIVE_OUTPUT_KEYS = {
    "active_guardrail_patch",
    "compiled_guardrail_bundle",
    "compiled_guardrail_bundle_path",
    "devhub_surface_patch",
    "process_model_patch",
    "prompt_patch",
    "release_state_patch",
    "source_registry_patch",
}

_ACTIVE_MUTATION_FLAG_KEYS = {
    "active_mutation",
    "active_mutation_enabled",
    "applied_active_mutation",
    "compiled_guardrails",
    "mutated_active_guardrails",
    "promoted_guardrails",
}

_REQUIRED_EXPLANATION_PLACEHOLDERS = {
    "{requirement_id}",
    "{missing_fact_or_document}",
    "{source_evidence_id}",
    "{next_safe_action}",
}


@dataclass(frozen=True)
class GuardrailImpactDeltaPacketV1Issue:
    path: str
    message: str


class GuardrailImpactDeltaPacketV1Error(ValueError):
    """Raised when a guardrail impact delta packet is incomplete or unsafe."""


def build_guardrail_impact_delta_packet_v1(process_delta_packet: Mapping[str, Any]) -> dict[str, Any]:
    """Build an inactive guardrail impact delta packet from process delta rows."""

    if not isinstance(process_delta_packet, Mapping):
        raise GuardrailImpactDeltaPacketV1Error("process_delta_packet must be a mapping")

    dependency_rows = _mapping_rows(process_delta_packet.get("dependency_delta_rows"))
    if not dependency_rows:
        raise GuardrailImpactDeltaPacketV1Error("dependency_delta_rows must be a non-empty list")

    packet_id = "guardrail-impact-delta-v1-" + str(process_delta_packet.get("packet_id", "synthetic-process-delta"))
    commands = [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]
    packet: dict[str, Any] = {
        "packet_version": PACKET_VERSION,
        "packet_mode": PACKET_MODE,
        "packet_id": packet_id,
        "source_process_dependency_graph_delta_packet_id": str(process_delta_packet.get("packet_id", "")),
        "source_fixture_id": str(process_delta_packet.get("source_fixture_id", "")),
        "affected_deterministic_predicate_rows": [],
        "affected_deontic_rule_rows": [],
        "affected_temporal_rule_rows": [],
        "affected_reversible_action_predicate_rows": [],
        "affected_exact_confirmation_predicate_rows": [],
        "affected_refused_action_predicate_rows": [],
        "affected_explanation_template_placeholder_rows": [],
        "stale_source_hold_rows": [],
        "reviewer_disposition_rows": [],
        "offline_validation_commands": commands,
        "mutation_policy": MUTATION_POLICY,
        "promotion_status": "not_promoted",
        "compiler_invocation": "not_invoked",
        "no_active_mutation_attestations": {
            "fixture_first": True,
            "offline_only": True,
            "compiled_guardrails": False,
            "promoted_guardrails": False,
            "mutated_active_guardrails": False,
            "changed_prompts": False,
            "changed_requirements": False,
            "changed_process_models": False,
            "changed_contracts": False,
            "changed_source_registries": False,
            "changed_devhub_surfaces": False,
            "changed_release_state": False,
            "changed_daemon_state": False,
        },
    }

    lookup = _source_lookup(process_delta_packet)
    for row in dependency_rows:
        candidate_id = _required_text(row, "candidate_id")
        requirement_id = _required_text(row, "requirement_id")
        delta_type = _required_text(row, "delta_type")
        basis = lookup.get(candidate_id, {})
        stages = _texts(basis.get("process_stage")) or _texts(basis.get("process_stages")) or ["process impact review"]
        facts = _texts(basis.get("required_user_fact")) or _texts(basis.get("required_user_facts")) or ["source-backed user fact"]
        documents = _texts(basis.get("required_document")) or _texts(basis.get("required_documents")) or ["source-backed document"]
        triggers = _texts(basis.get("trigger")) or _texts(basis.get("fee_deadline_triggers")) or ["source-backed temporal trigger"]
        boundaries = _texts(basis.get("devhub_boundary_ref")) or _texts(basis.get("devhub_boundary_refs")) or ["consequential action remains blocked"]
        unsupported = _texts(basis.get("unsupported_path")) or _texts(basis.get("unsupported_paths")) or ["unsupported paths require handoff"]
        holds = _texts(basis.get("reviewer_hold")) or _texts(basis.get("reviewer_holds")) or ["reviewer must confirm cited source before promotion"]

        common = {
            "candidate_id": candidate_id,
            "requirement_id": requirement_id,
            "delta_type": delta_type,
            "activation_allowed": False,
            "review_status": "pending_reviewer_disposition",
        }
        packet["affected_deterministic_predicate_rows"].append(
            common | {
                "predicate_id": _row_id("deterministic-predicate", candidate_id),
                "predicate_name": "has_required_user_fact_and_document_evidence",
                "affected_inputs": sorted(set(facts + documents)),
                "impact_summary": "Synthetic dependency row may change deterministic missing-information checks.",
            }
        )
        packet["affected_deontic_rule_rows"].append(
            common | {
                "rule_id": _row_id("deontic-rule", candidate_id),
                "rule_kind": "obligation_or_prohibition_review",
                "affected_terms": sorted(set(facts + documents + unsupported)),
                "impact_summary": "Reviewer must decide whether the delta changes an obligation, prohibition, permission, or exception.",
            }
        )
        packet["affected_temporal_rule_rows"].append(
            common | {
                "rule_id": _row_id("temporal-rule", candidate_id),
                "temporal_triggers": triggers,
                "impact_summary": "Synthetic trigger rows are held for temporal-rule review only.",
            }
        )
        packet["affected_reversible_action_predicate_rows"].append(
            common | {
                "predicate_id": _row_id("reversible-action", candidate_id),
                "safe_action_boundary": "draft_or_read_only_only",
                "affected_process_stages": stages,
                "impact_summary": "Only reversible draft or read-only action predicates may be reviewed from this packet.",
            }
        )
        packet["affected_exact_confirmation_predicate_rows"].append(
            common | {
                "predicate_id": _row_id("exact-confirmation", candidate_id),
                "confirmation_scope": "consequential_or_official_action",
                "affected_boundaries": boundaries,
                "impact_summary": "Consequential actions remain exact-confirmation gated.",
            }
        )
        packet["affected_refused_action_predicate_rows"].append(
            common | {
                "predicate_id": _row_id("refused-action", candidate_id),
                "refusal_scope": "unsupported_or_consequential_completion",
                "affected_unsupported_paths": unsupported,
                "impact_summary": "Unsupported or official completion paths remain refused unless later reviewed and separately implemented.",
            }
        )
        packet["affected_explanation_template_placeholder_rows"].append(
            common | {
                "template_id": _row_id("explanation-template", candidate_id),
                "placeholders": sorted(_REQUIRED_EXPLANATION_PLACEHOLDERS),
                "impact_summary": "Explanation templates may need placeholder coverage for the affected facts, documents, and boundaries.",
            }
        )
        packet["stale_source_hold_rows"].append(
            common | {
                "hold_id": _row_id("stale-source-hold", candidate_id),
                "hold_reason": "source_evidence_must_be_current_before_any_future_promotion",
                "reviewer_holds": holds,
            }
        )
        packet["reviewer_disposition_rows"].append(
            common | {
                "disposition_id": _row_id("reviewer-disposition", candidate_id),
                "allowed_dispositions": ["accept_for_later_compile_candidate", "needs_source_refresh", "reject_delta"],
                "current_disposition": "pending",
                "disposition_required_before_compile": True,
            }
        )

    validate_guardrail_impact_delta_packet_v1(packet)
    return packet


def validate_guardrail_impact_delta_packet_v1(packet: Mapping[str, Any]) -> None:
    """Raise when the packet is incomplete, unsafe, or not offline-only."""

    issues = list(iter_guardrail_impact_delta_packet_v1_issues(packet))
    if issues:
        detail = "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
        raise GuardrailImpactDeltaPacketV1Error(detail)


def iter_guardrail_impact_delta_packet_v1_issues(packet: Mapping[str, Any]) -> Iterable[GuardrailImpactDeltaPacketV1Issue]:
    if not isinstance(packet, Mapping):
        yield GuardrailImpactDeltaPacketV1Issue("$", "packet must be a mapping")
        return

    for field in _REQUIRED_PACKET_FIELDS:
        if field not in packet:
            yield GuardrailImpactDeltaPacketV1Issue(field, "missing required field")

    if packet.get("packet_version") != PACKET_VERSION:
        yield GuardrailImpactDeltaPacketV1Issue("packet_version", "unexpected packet version")
    if packet.get("packet_mode") != PACKET_MODE:
        yield GuardrailImpactDeltaPacketV1Issue("packet_mode", "packet must remain fixture-first delta review only")
    if packet.get("mutation_policy") != MUTATION_POLICY:
        yield GuardrailImpactDeltaPacketV1Issue("mutation_policy", "packet must forbid compile, promotion, and active mutation")
    if packet.get("promotion_status") not in (None, "not_promoted"):
        yield GuardrailImpactDeltaPacketV1Issue("promotion_status", "packet must not promote guardrails")
    if packet.get("compiler_invocation") not in (None, "not_invoked"):
        yield GuardrailImpactDeltaPacketV1Issue("compiler_invocation", "packet must not invoke a guardrail compiler")

    expected_commands = [list(command) for command in EXACT_OFFLINE_VALIDATION_COMMANDS]
    commands = packet.get("offline_validation_commands")
    if commands != expected_commands:
        yield GuardrailImpactDeltaPacketV1Issue("offline_validation_commands", "must match exact offline validation commands")
    if isinstance(commands, Sequence) and not isinstance(commands, (str, bytes)):
        for index, command in enumerate(commands):
            text = " ".join(str(part).lower() for part in command) if isinstance(command, Sequence) and not isinstance(command, (str, bytes)) else str(command).lower()
            if any(term in text for term in _NON_OFFLINE_COMMAND_TERMS):
                yield GuardrailImpactDeltaPacketV1Issue(f"offline_validation_commands[{index}]", "validation command must remain offline")

    yield from _validate_attestations(packet.get("no_active_mutation_attestations"))
    yield from _validate_row_groups(packet)
    yield from _reject_unsafe_content(packet, "$", set())


def _validate_attestations(attestations: Any) -> Iterable[GuardrailImpactDeltaPacketV1Issue]:
    if not isinstance(attestations, Mapping):
        yield GuardrailImpactDeltaPacketV1Issue("no_active_mutation_attestations", "mutation attestations are required")
        return
    if attestations.get("fixture_first") is not True or attestations.get("offline_only") is not True:
        yield GuardrailImpactDeltaPacketV1Issue("no_active_mutation_attestations", "fixture-first and offline-only attestations are required")
    for key in _FALSE_ATTESTATIONS:
        if attestations.get(key) is not False:
            yield GuardrailImpactDeltaPacketV1Issue(f"no_active_mutation_attestations.{key}", "active mutation attestation must be false")


def _validate_row_groups(packet: Mapping[str, Any]) -> Iterable[GuardrailImpactDeltaPacketV1Issue]:
    expected_candidate_ids = _expected_candidate_ids(packet)
    if not expected_candidate_ids:
        yield GuardrailImpactDeltaPacketV1Issue("affected_deterministic_predicate_rows", "must contain at least one predicate impact row")

    for group_name in _ROW_GROUPS:
        rows = packet.get(group_name)
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)) or not rows:
            yield GuardrailImpactDeltaPacketV1Issue(group_name, "must contain at least one row")
            continue
        observed = _candidate_ids(rows)
        missing = sorted(expected_candidate_ids - observed)
        for candidate_id in missing:
            yield GuardrailImpactDeltaPacketV1Issue(group_name, f"missing row for candidate_id: {candidate_id}")
        extra = sorted(observed - expected_candidate_ids)
        for candidate_id in extra:
            yield GuardrailImpactDeltaPacketV1Issue(group_name, f"unexpected row for candidate_id: {candidate_id}")
        for index, row in enumerate(rows):
            path = f"{group_name}[{index}]"
            if not isinstance(row, Mapping):
                yield GuardrailImpactDeltaPacketV1Issue(path, "row must be a mapping")
                continue
            for field in ("candidate_id", "requirement_id", "delta_type", "review_status"):
                if not _non_empty_text(row.get(field)):
                    yield GuardrailImpactDeltaPacketV1Issue(f"{path}.{field}", "required row field must be non-empty text")
            for field in _ROW_PAYLOAD_REQUIREMENTS[group_name]:
                if not _non_empty_payload(row.get(field)):
                    yield GuardrailImpactDeltaPacketV1Issue(f"{path}.{field}", "required impact payload must be present")
            if row.get("activation_allowed") is not False:
                yield GuardrailImpactDeltaPacketV1Issue(f"{path}.activation_allowed", "activation must remain blocked")
            if group_name == "affected_explanation_template_placeholder_rows":
                placeholders = set(_texts(row.get("placeholders")))
                missing_placeholders = sorted(_REQUIRED_EXPLANATION_PLACEHOLDERS - placeholders)
                if missing_placeholders:
                    yield GuardrailImpactDeltaPacketV1Issue(f"{path}.placeholders", "missing required explanation placeholders")
            if group_name == "reviewer_disposition_rows":
                if row.get("disposition_required_before_compile") is not True:
                    yield GuardrailImpactDeltaPacketV1Issue(f"{path}.disposition_required_before_compile", "reviewer disposition is required before compile")
                if row.get("current_disposition") != "pending":
                    yield GuardrailImpactDeltaPacketV1Issue(f"{path}.current_disposition", "reviewer disposition must remain pending")


def _expected_candidate_ids(packet: Mapping[str, Any]) -> set[str]:
    candidate_ids: set[str] = set()
    for group_name in _ROW_GROUPS:
        candidate_ids.update(_candidate_ids(packet.get(group_name)))
    return candidate_ids


def _reject_unsafe_content(value: Any, path: str, seen: set[int]) -> Iterable[GuardrailImpactDeltaPacketV1Issue]:
    value_id = id(value)
    if value_id in seen:
        return
    seen.add(value_id)
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            key_lower = key_text.lower()
            child_path = path + "." + key_text
            if key_text in _ACTIVE_OUTPUT_KEYS:
                yield GuardrailImpactDeltaPacketV1Issue(child_path, "active mutation output fields are not allowed")
            if key_lower in _ACTIVE_MUTATION_FLAG_KEYS and child is not False:
                yield GuardrailImpactDeltaPacketV1Issue(child_path, "active mutation flags must be absent or false")
            yield from _reject_unsafe_content(child, child_path, seen)
        return
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for index, child in enumerate(value):
            yield from _reject_unsafe_content(child, f"{path}[{index}]", seen)
        return
    if isinstance(value, str):
        lowered = value.lower()
        if any(term in lowered for term in _PRIVATE_OR_LIVE_TERMS):
            yield GuardrailImpactDeltaPacketV1Issue(path, "private, session, browser, raw crawl, or downloaded artifact references are not allowed")
        if any(term in lowered for term in _LIVE_DEVHUB_CLAIM_TERMS):
            yield GuardrailImpactDeltaPacketV1Issue(path, "live crawl or DevHub observation claims are not allowed")
        if any(term in lowered for term in _LEGAL_OR_PERMITTING_GUARANTEE_TERMS):
            yield GuardrailImpactDeltaPacketV1Issue(path, "legal or permitting guarantee claims are not allowed")
        if any(term in lowered for term in _OFFICIAL_ACTION_COMPLETION_TERMS):
            yield GuardrailImpactDeltaPacketV1Issue(path, "official-action completion claims are not allowed")


def _source_lookup(process_delta_packet: Mapping[str, Any]) -> dict[str, dict[str, list[str]]]:
    lookup: dict[str, dict[str, list[str]]] = {}
    source_groups = (
        ("process_stage_rows", "process_stage"),
        ("required_user_fact_rows", "required_user_fact"),
        ("required_document_rows", "required_document"),
        ("fee_deadline_trigger_rows", "trigger"),
        ("unsupported_path_rows", "unsupported_path"),
        ("devhub_boundary_reference_rows", "devhub_boundary_ref"),
        ("reviewer_hold_rows", "reviewer_hold"),
    )
    for group_name, value_key in source_groups:
        for row in _mapping_rows(process_delta_packet.get(group_name)):
            candidate_id = str(row.get("candidate_id", ""))
            if not candidate_id:
                continue
            lookup.setdefault(candidate_id, {}).setdefault(value_key, []).append(str(row.get(value_key, "")))
    return lookup


def _mapping_rows(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _candidate_ids(rows: Any) -> set[str]:
    return {str(row.get("candidate_id")) for row in _mapping_rows(rows) if _non_empty_text(row.get("candidate_id"))}


def _texts(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(item) for item in value if _non_empty_text(item)]
    return []


def _required_text(row: Mapping[str, Any], field: str) -> str:
    value = row.get(field)
    if not _non_empty_text(value):
        raise GuardrailImpactDeltaPacketV1Error(f"{field} must be non-empty text")
    return str(value)


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _non_empty_payload(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return bool(value) and all(_non_empty_payload(item) for item in value)
    return value is not None


def _row_id(prefix: str, candidate_id: str) -> str:
    safe_candidate = candidate_id.lower().replace("_", "-").replace(" ", "-")
    return f"gid-v1-{prefix}-{safe_candidate}"
