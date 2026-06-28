"""Fixture-first requirement-to-guardrail traceability review packets.

This module joins already-built review packets into a deterministic reviewer packet.
It does not crawl, call processors, execute agents, compile guardrails, or mutate
active requirement, process-model, guardrail, prompt, or release-state artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import Any, Iterable, Mapping, Sequence


PACKET_TYPE = "fixture_first_requirement_guardrail_traceability_review_packet"
PACKET_MODE = "review_only_no_active_mutation"

_REQUIRED_INPUTS = (
    "requirement_rerun_work_queue_packet",
    "process_model_impact_review_packet",
    "guardrail_bundle_update_candidate_packet",
    "guardrail_explanation_regression_packet",
    "agent_prompt_regression_dry_run_packet",
)

_ATTESTATION_KEYS = (
    "no_active_requirement_mutation",
    "no_active_process_mutation",
    "no_active_guardrail_mutation",
    "no_active_prompt_mutation",
    "no_active_release_state_mutation",
    "no_live_crawl",
    "no_devhub_execution",
    "no_processor_invocation",
    "no_llm_execution",
    "fixture_first_inputs_only",
)

_MUTATION_EFFECT_KEYS = (
    "requirements_mutated",
    "process_models_mutated",
    "guardrails_mutated",
    "prompts_mutated",
    "release_state_mutated",
    "guardrail_bundle_compiled",
    "prompt_template_published",
)

_PRIVATE_OR_RAW_RE = re.compile(
    r"(auth[_-]?state|cookie|credential|password|secret|token|\.har\b|trace\.zip|screenshot|raw[_-]?crawl|raw[_-]?archive|raw[_-]?download|/downloads?/|/home/[^\s]+/(?:Desktop|Documents|Downloads)|C:\\\\Users\\\\)",
    re.IGNORECASE,
)

_PRIVATE_CASE_KEY_RE = re.compile(r"(?:private[_-]?)?(?:case|user|applicant|owner|property)[_-]?(?:facts?|values?|data|details?)", re.IGNORECASE)

_LIVE_EXECUTION_RE = re.compile(
    r"\b(?:called|ran|executed|queried|invoked|used|opened|drove|crawled)\s+(?:the\s+)?(?:live\s+)?(?:llm|agent|consumer|crawler|processor|devhub)\b|\blive\s+(?:llm|agent|consumer|crawler|processor|devhub)\s+(?:run|execution|call|crawl|session|browser|workflow)\b|\bdevhub\s+(?:browser|session|automation|execution)\b",
    re.IGNORECASE,
)

_OUTCOME_GUARANTEE_RE = re.compile(
    r"\b(?:guarantee[sd]?|assure[sd]?|promise[sd]?|will\s+be)\b[^.\n]{0,80}\b(?:approved|approval|permit(?:ted)?|issued|legal|lawful|compliant|accepted|outcome)\b|\b(?:approval|permit|issuance|legal|permitting)\s+(?:is\s+)?guaranteed\b",
    re.IGNORECASE,
)

_MUTATION_KEY_RE = re.compile(
    r"active_.*mutation|mutate_.*active|promote_.*active|replace_.*active|release[_-]?state.*mutation|mutates_release_state|publish_.*release_state",
    re.IGNORECASE,
)

_CONSEQUENTIAL_CONTROL_KEY_RE = re.compile(
    r"(?:submit|submission|upload|certif|acknowledg|payment|pay|schedule|inspection|cancel|withdraw|purchase|official|consequential|devhub_write|write_action).*enabled|enabled_.*(?:submit|upload|certif|payment|schedule|cancel|official|consequential)",
    re.IGNORECASE,
)

_CITATION_KEYS = ("source_evidence_ids", "evidence_ids", "citation_ids", "citations", "source_ids")

_LINK_REQUIREMENTS = (
    ("requirement", ("requirement_id", "requirement_ids", "cited_requirement_ids", "affected_requirement_ids", "impacted_requirement_ids")),
    ("process", ("process_id", "process_ids", "process_ref", "process_refs", "affected_process_ids", "affected_process_refs", "affected_process_model_ids", "impacted_process_ids")),
    ("guardrail", ("guardrail_id", "guardrail_ids", "guardrail_ref", "guardrail_refs", "affected_guardrail_ids", "affected_guardrail_refs", "known_predicate_ids", "predicate_ids")),
    ("prompt", ("prompt_id", "prompt_ids", "missing_fact_prompt_ids")),
)


@dataclass(frozen=True)
class TraceabilityReviewFinding:
    """A deterministic validation finding for traceability review packets."""

    code: str
    path: str
    message: str


@dataclass(frozen=True)
class TraceabilityReviewValidationResult:
    """Validation result for a requirement-to-guardrail traceability packet."""

    valid: bool
    findings: tuple[TraceabilityReviewFinding, ...]

    def codes(self) -> tuple[str, ...]:
        return tuple(finding.code for finding in self.findings)


class TraceabilityReviewPacketError(ValueError):
    """Raised when a traceability review packet fails validation."""

    def __init__(self, findings: Sequence[TraceabilityReviewFinding]) -> None:
        self.findings = tuple(findings)
        detail = "; ".join(f"{item.code} at {item.path}: {item.message}" for item in self.findings)
        super().__init__("invalid requirement-to-guardrail traceability review packet: " + detail)


def build_requirement_guardrail_traceability_review_packet(
    requirement_rerun_work_queue_packet: Mapping[str, Any],
    process_model_impact_review_packet: Mapping[str, Any],
    guardrail_bundle_update_candidate_packet: Mapping[str, Any],
    guardrail_explanation_regression_packet: Mapping[str, Any],
    agent_prompt_regression_dry_run_packet: Mapping[str, Any],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Build a fixture-first requirement-to-process-to-guardrail review packet."""

    inputs = {
        "requirement_rerun_work_queue_packet": _require_mapping(requirement_rerun_work_queue_packet, "requirement rerun work queue packet"),
        "process_model_impact_review_packet": _require_mapping(process_model_impact_review_packet, "process model impact review packet"),
        "guardrail_bundle_update_candidate_packet": _require_mapping(guardrail_bundle_update_candidate_packet, "guardrail bundle update candidate packet"),
        "guardrail_explanation_regression_packet": _require_mapping(guardrail_explanation_regression_packet, "guardrail explanation regression packet"),
        "agent_prompt_regression_dry_run_packet": _require_mapping(agent_prompt_regression_dry_run_packet, "agent prompt regression dry-run packet"),
    }

    requirement_ids = _ordered_unique(
        _extract_strings_by_key(
            inputs.values(),
            {"requirement_id", "requirement_ids", "cited_requirement_ids", "affected_requirement_ids", "impacted_requirement_ids"},
        )
    )
    process_ids = _ordered_unique(
        _extract_strings_by_key(inputs.values(), {"process_id", "process_ids", "process_ref", "process_refs", "affected_process_ids", "affected_process_refs", "affected_process_model_ids"})
    )
    guardrail_ids = _ordered_unique(
        _extract_strings_by_key(inputs.values(), {"guardrail_id", "guardrail_ids", "guardrail_ref", "guardrail_refs", "affected_guardrail_ids", "affected_guardrail_refs", "known_predicate_ids", "predicate_ids"})
    )
    evidence_ids = _ordered_unique(_extract_strings_by_key(inputs.values(), set(_CITATION_KEYS)))

    traceability_links = _explicit_traceability_links(inputs)
    if not traceability_links:
        traceability_links = [
            {
                "link_id": f"trace.{_slug(requirement_id)}",
                "requirement_id": requirement_id,
                "process_ids": process_ids,
                "guardrail_ids": guardrail_ids,
                "source_evidence_ids": evidence_ids,
                "review_status": "pending_reviewer_traceability_review",
            }
            for requirement_id in requirement_ids
        ]

    packet = {
        "packet_type": PACKET_TYPE,
        "packet_mode": PACKET_MODE,
        "packet_id": "requirement-guardrail-traceability-review-" + _stable_hash(
            {
                "generated_at": generated_at,
                "input_packet_ids": [_packet_id(packet) for packet in inputs.values()],
                "requirement_ids": requirement_ids,
                "process_ids": process_ids,
                "guardrail_ids": guardrail_ids,
            }
        ),
        "generated_at": generated_at,
        "fixture_first": True,
        "consumed_packets": {
            name: {
                "packet_id": _packet_id(packet),
                "source_evidence_ids": _ordered_unique(_extract_strings_by_key((packet,), set(_CITATION_KEYS))),
            }
            for name, packet in inputs.items()
        },
        "requirement_to_process_to_guardrail_links": traceability_links,
        "missing_fact_prompt_impacts": _prompt_impacts(agent_prompt_regression_dry_run_packet, process_ids, requirement_ids, evidence_ids),
        "blocked_action_carryovers": _blocked_action_carryovers(process_model_impact_review_packet, guardrail_bundle_update_candidate_packet, evidence_ids),
        "reviewer_owner_fields": _reviewer_owner_fields(inputs),
        "attestations": {
            "no_active_requirement_mutation": True,
            "no_active_process_mutation": True,
            "no_active_guardrail_mutation": True,
            "no_active_prompt_mutation": True,
            "no_active_release_state_mutation": True,
            "no_live_crawl": True,
            "no_devhub_execution": True,
            "no_processor_invocation": True,
            "no_llm_execution": True,
            "fixture_first_inputs_only": True,
            "attestation_basis": "committed fixture packets and review-only packet metadata",
        },
        "active_mutation_effects": {
            "requirements_mutated": False,
            "process_models_mutated": False,
            "guardrails_mutated": False,
            "prompts_mutated": False,
            "release_state_mutated": False,
            "guardrail_bundle_compiled": False,
            "prompt_template_published": False,
        },
    }
    assert_valid_requirement_guardrail_traceability_review_packet(packet)
    return packet


def validate_requirement_guardrail_traceability_review_packet(packet: Mapping[str, Any]) -> TraceabilityReviewValidationResult:
    """Validate a fixture-first requirement-to-guardrail traceability packet."""

    findings: list[TraceabilityReviewFinding] = []
    if not isinstance(packet, Mapping):
        return TraceabilityReviewValidationResult(False, (TraceabilityReviewFinding("invalid_packet", "$", "Packet must be an object."),))

    if packet.get("packet_type") != PACKET_TYPE:
        findings.append(TraceabilityReviewFinding("invalid_packet_type", "$.packet_type", "Unexpected packet type."))
    if packet.get("packet_mode") != PACKET_MODE:
        findings.append(TraceabilityReviewFinding("invalid_packet_mode", "$.packet_mode", "Packet must remain review-only."))
    if packet.get("fixture_first") is not True:
        findings.append(TraceabilityReviewFinding("not_fixture_first", "$.fixture_first", "Packet must declare fixture_first=true."))

    _validate_consumed_packets(packet.get("consumed_packets"), findings)
    _validate_traceability_links(packet.get("requirement_to_process_to_guardrail_links"), findings)
    _validate_prompt_impacts(packet.get("missing_fact_prompt_impacts"), findings)
    _validate_blocked_actions(packet.get("blocked_action_carryovers"), findings)
    _validate_reviewer_owners(packet.get("reviewer_owner_fields"), findings)
    _validate_attestations(packet.get("attestations"), packet.get("active_mutation_effects"), findings)
    _scan_for_unsafe_content(packet, "$", findings)
    return TraceabilityReviewValidationResult(not findings, tuple(findings))


def assert_valid_requirement_guardrail_traceability_review_packet(packet: Mapping[str, Any]) -> None:
    result = validate_requirement_guardrail_traceability_review_packet(packet)
    if not result.valid:
        raise TraceabilityReviewPacketError(result.findings)


def _validate_consumed_packets(value: Any, findings: list[TraceabilityReviewFinding]) -> None:
    if not isinstance(value, Mapping):
        findings.append(TraceabilityReviewFinding("missing_consumed_packets", "$.consumed_packets", "Consumed packet references are required."))
        return
    for name in _REQUIRED_INPUTS:
        row = value.get(name)
        if not isinstance(row, Mapping):
            findings.append(TraceabilityReviewFinding("missing_consumed_packet", f"$.consumed_packets.{name}", "Required source packet was not consumed."))
            continue
        if not _text(row.get("packet_id")):
            findings.append(TraceabilityReviewFinding("missing_consumed_packet_id", f"$.consumed_packets.{name}.packet_id", "Consumed packet must include packet_id."))
        if not _strings(row.get("source_evidence_ids")):
            findings.append(TraceabilityReviewFinding("uncited_consumed_packet", f"$.consumed_packets.{name}.source_evidence_ids", "Consumed packet must cite source evidence."))


def _validate_traceability_links(value: Any, findings: list[TraceabilityReviewFinding]) -> None:
    rows = _as_list(value)
    if not rows:
        findings.append(TraceabilityReviewFinding("missing_traceability_links", "$.requirement_to_process_to_guardrail_links", "At least one requirement-to-process-to-guardrail link is required."))
        return
    for index, row in enumerate(rows):
        path = f"$.requirement_to_process_to_guardrail_links[{index}]"
        if not isinstance(row, Mapping):
            findings.append(TraceabilityReviewFinding("invalid_traceability_link", path, "Traceability links must be objects."))
            continue
        evidence_ids = _citation_strings(row)
        if not _text(row.get("requirement_id")):
            findings.append(TraceabilityReviewFinding("missing_requirement_id", f"{path}.requirement_id", "Traceability link must identify a requirement."))
        elif not evidence_ids:
            findings.append(TraceabilityReviewFinding("uncited_requirement_link", f"{path}.source_evidence_ids", "Requirement links must cite source evidence."))
        if not _strings(row.get("process_ids")):
            findings.append(TraceabilityReviewFinding("missing_process_ids", f"{path}.process_ids", "Traceability link must identify process impacts."))
        elif not evidence_ids:
            findings.append(TraceabilityReviewFinding("uncited_process_link", f"{path}.source_evidence_ids", "Process links must cite source evidence."))
        if not _strings(row.get("guardrail_ids")):
            findings.append(TraceabilityReviewFinding("missing_guardrail_ids", f"{path}.guardrail_ids", "Traceability link must identify guardrail impacts."))
        elif not evidence_ids:
            findings.append(TraceabilityReviewFinding("uncited_guardrail_link", f"{path}.source_evidence_ids", "Guardrail links must cite source evidence."))
        if not evidence_ids:
            findings.append(TraceabilityReviewFinding("uncited_traceability_link", f"{path}.source_evidence_ids", "Traceability link must cite source evidence."))


def _validate_prompt_impacts(value: Any, findings: list[TraceabilityReviewFinding]) -> None:
    rows = _as_list(value)
    if not rows:
        findings.append(TraceabilityReviewFinding("missing_prompt_impacts", "$.missing_fact_prompt_impacts", "Missing-fact prompt impacts are required."))
        return
    for index, row in enumerate(rows):
        path = f"$.missing_fact_prompt_impacts[{index}]"
        if not isinstance(row, Mapping):
            findings.append(TraceabilityReviewFinding("invalid_prompt_impact", path, "Prompt impact rows must be objects."))
            continue
        if not _text(row.get("prompt_id")):
            findings.append(TraceabilityReviewFinding("missing_prompt_id", f"{path}.prompt_id", "Prompt impact must identify a prompt."))
        if not _citation_strings(row):
            findings.append(TraceabilityReviewFinding("uncited_prompt_link", f"{path}.source_evidence_ids", "Prompt links must cite source evidence."))
            findings.append(TraceabilityReviewFinding("uncited_prompt_impact", f"{path}.source_evidence_ids", "Prompt impacts must cite source evidence."))
        if row.get("requires_active_prompt_mutation") is not False:
            findings.append(TraceabilityReviewFinding("prompt_mutation_not_disabled", f"{path}.requires_active_prompt_mutation", "Prompt impacts must not require active prompt mutation."))


def _validate_blocked_actions(value: Any, findings: list[TraceabilityReviewFinding]) -> None:
    rows = _as_list(value)
    if not rows:
        findings.append(TraceabilityReviewFinding("missing_blocked_action_carryovers", "$.blocked_action_carryovers", "Blocked-action carryovers are required."))
        return
    for index, row in enumerate(rows):
        path = f"$.blocked_action_carryovers[{index}]"
        if not isinstance(row, Mapping):
            findings.append(TraceabilityReviewFinding("invalid_blocked_action", path, "Blocked action rows must be objects."))
            continue
        if not _text(row.get("action_id")):
            findings.append(TraceabilityReviewFinding("missing_action_id", f"{path}.action_id", "Blocked action carryover must identify an action."))
        if row.get("blocked") is not True:
            findings.append(TraceabilityReviewFinding("blocked_action_not_blocked", f"{path}.blocked", "Carried-over blocked actions must remain blocked."))
        if not _citation_strings(row):
            findings.append(TraceabilityReviewFinding("uncited_blocked_action", f"{path}.source_evidence_ids", "Blocked actions must cite source evidence."))


def _validate_reviewer_owners(value: Any, findings: list[TraceabilityReviewFinding]) -> None:
    if not isinstance(value, Mapping) or not value:
        findings.append(TraceabilityReviewFinding("missing_reviewer_owner_fields", "$.reviewer_owner_fields", "Reviewer owner fields are required."))
        return
    for name in ("requirement_owner", "process_owner", "guardrail_owner", "prompt_owner", "traceability_review_owner"):
        if not _text(value.get(name)):
            findings.append(TraceabilityReviewFinding("missing_reviewer_owner", f"$.reviewer_owner_fields.{name}", "Reviewer owner field is required."))


def _validate_attestations(attestations: Any, effects: Any, findings: list[TraceabilityReviewFinding]) -> None:
    if not isinstance(attestations, Mapping):
        findings.append(TraceabilityReviewFinding("missing_attestations", "$.attestations", "No-mutation attestations are required."))
        return
    for key in _ATTESTATION_KEYS:
        if attestations.get(key) is not True:
            findings.append(TraceabilityReviewFinding("missing_no_mutation_attestation", f"$.attestations.{key}", "Required no-mutation attestation must be true."))
    if not isinstance(effects, Mapping):
        findings.append(TraceabilityReviewFinding("missing_active_mutation_effects", "$.active_mutation_effects", "Active mutation effect flags are required."))
        return
    for key in _MUTATION_EFFECT_KEYS:
        if effects.get(key) is not False:
            findings.append(TraceabilityReviewFinding("active_mutation_effect_enabled", f"$.active_mutation_effects.{key}", "Active mutation effects must be false."))
    for key, value in effects.items():
        if value is not False:
            findings.append(TraceabilityReviewFinding("active_mutation_effect_enabled", f"$.active_mutation_effects.{key}", "Active mutation effects must be false."))


def _explicit_traceability_links(inputs: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for packet in inputs.values():
        for key in ("requirement_to_process_to_guardrail_links", "traceability_links"):
            for row in _as_list(packet.get(key)):
                if isinstance(row, Mapping):
                    rows.append(
                        {
                            "link_id": _text(row.get("link_id")) or "trace." + _slug(_text(row.get("requirement_id"))),
                            "requirement_id": _text(row.get("requirement_id")),
                            "process_ids": _strings(row.get("process_ids") or row.get("affected_process_ids")),
                            "guardrail_ids": _strings(row.get("guardrail_ids") or row.get("affected_guardrail_ids") or row.get("predicate_ids")),
                            "source_evidence_ids": _strings(row.get("source_evidence_ids") or row.get("citations")),
                            "review_status": _text(row.get("review_status")) or "pending_reviewer_traceability_review",
                        }
                    )
    return sorted(rows, key=lambda item: item["link_id"])


def _prompt_impacts(prompt_packet: Mapping[str, Any], process_ids: list[str], requirement_ids: list[str], fallback_evidence_ids: list[str]) -> list[dict[str, Any]]:
    source_rows = _as_list(prompt_packet.get("missing_fact_prompt_impacts") or prompt_packet.get("prompt_dry_run_results") or prompt_packet.get("missing_fact_prompts"))
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(source_rows):
        if not isinstance(row, Mapping):
            continue
        prompt_id = _text(row.get("prompt_id") or row.get("id")) or f"prompt-impact-{index + 1}"
        rows.append(
            {
                "prompt_id": prompt_id,
                "prompt_kind": _text(row.get("prompt_kind") or row.get("kind")) or "missing_fact_prompt",
                "impacted_requirement_ids": _strings(row.get("impacted_requirement_ids") or row.get("requirement_ids")) or requirement_ids,
                "impacted_process_ids": _strings(row.get("impacted_process_ids") or row.get("process_ids")) or process_ids,
                "impact_summary": _text(row.get("impact_summary") or row.get("summary") or row.get("expected_prompt_change")) or "Prompt remains a cited missing-fact prompt in the dry-run packet.",
                "source_evidence_ids": _strings(row.get("source_evidence_ids") or row.get("citations")) or fallback_evidence_ids,
                "reviewer_owner": _text(row.get("reviewer_owner") or row.get("owner")) or "ppd-agent-prompt-reviewer",
                "requires_active_prompt_mutation": False,
            }
        )
    return sorted(rows, key=lambda item: item["prompt_id"])


def _blocked_action_carryovers(process_packet: Mapping[str, Any], guardrail_packet: Mapping[str, Any], fallback_evidence_ids: list[str]) -> list[dict[str, Any]]:
    source_rows = []
    for packet in (process_packet, guardrail_packet):
        source_rows.extend(_as_list(packet.get("blocked_action_carryovers") or packet.get("blocked_actions") or packet.get("blocked_action_expectations")))
    rows: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(source_rows):
        if not isinstance(row, Mapping):
            continue
        action_id = _text(row.get("action_id") or row.get("id") or row.get("action")) or f"blocked-action-{index + 1}"
        rows[action_id] = {
            "action_id": action_id,
            "action_label": _text(row.get("action_label") or row.get("action")) or action_id,
            "blocked": True,
            "carryover_reason": _text(row.get("carryover_reason") or row.get("reason") or row.get("guardrail_reason")) or "Consequential PP&D action remains blocked pending exact confirmation or manual attendance.",
            "source_evidence_ids": _strings(row.get("source_evidence_ids") or row.get("citations")) or fallback_evidence_ids,
            "reviewer_owner": _text(row.get("reviewer_owner") or row.get("owner")) or "ppd-guardrail-reviewer",
        }
    return [rows[key] for key in sorted(rows)]


def _reviewer_owner_fields(inputs: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    owners = {
        "requirement_owner": "ppd-requirement-reviewer",
        "process_owner": "ppd-process-reviewer",
        "guardrail_owner": "ppd-guardrail-reviewer",
        "prompt_owner": "ppd-agent-prompt-reviewer",
        "traceability_review_owner": "ppd-traceability-reviewer",
    }
    for packet in inputs.values():
        owner_fields = packet.get("reviewer_owner_fields")
        if isinstance(owner_fields, Mapping):
            for key, value in owner_fields.items():
                if key in owners and _text(value):
                    owners[key] = _text(value)
        for source_key, target_key in (
            ("requirement_owner", "requirement_owner"),
            ("process_owner", "process_owner"),
            ("guardrail_owner", "guardrail_owner"),
            ("prompt_owner", "prompt_owner"),
            ("reviewer_owner", "traceability_review_owner"),
            ("owner", "traceability_review_owner"),
        ):
            if _text(packet.get(source_key)):
                owners[target_key] = _text(packet.get(source_key))
    return owners


def _scan_for_unsafe_content(value: Any, path: str, findings: list[TraceabilityReviewFinding]) -> None:
    if isinstance(value, Mapping):
        _validate_embedded_cited_links(value, path, findings)
        for key, child in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}"
            if _MUTATION_KEY_RE.search(key_text) and child not in (False, None, "false", "disabled"):
                findings.append(TraceabilityReviewFinding("active_mutation_flag_present", child_path, "Active requirement, process, guardrail, prompt, or release-state mutation flags must be disabled."))
            if _PRIVATE_CASE_KEY_RE.search(key_text) and _has_payload(child):
                findings.append(TraceabilityReviewFinding("private_case_fact_present", child_path, "Traceability review packets must not include private case facts."))
            if _CONSEQUENTIAL_CONTROL_KEY_RE.search(key_text) and child not in (False, None, "false", "disabled", [], {}):
                findings.append(TraceabilityReviewFinding("consequential_control_enabled", child_path, "Consequential controls must not be enabled in traceability review packets."))
            _scan_for_unsafe_content(child, child_path, findings)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_for_unsafe_content(child, f"{path}[{index}]", findings)
    elif isinstance(value, str):
        if _PRIVATE_OR_RAW_RE.search(value):
            findings.append(TraceabilityReviewFinding("private_or_raw_artifact_reference", path, "Packet must not reference private/session/raw crawl artifacts."))
        if _LIVE_EXECUTION_RE.search(value):
            findings.append(TraceabilityReviewFinding("live_execution_claim", path, "Packet must not claim live LLM, DevHub, crawler, or processor execution."))
        if _OUTCOME_GUARANTEE_RE.search(value):
            findings.append(TraceabilityReviewFinding("legal_or_permitting_outcome_guarantee", path, "Packet must not guarantee legal or permitting outcomes."))


def _validate_embedded_cited_links(row: Mapping[str, Any], path: str, findings: list[TraceabilityReviewFinding]) -> None:
    if _citation_strings(row):
        return
    keys = set(str(key) for key in row.keys())
    for link_kind, link_keys in _LINK_REQUIREMENTS:
        if keys.intersection(link_keys):
            findings.append(
                TraceabilityReviewFinding(
                    f"uncited_{link_kind}_link",
                    path,
                    f"{link_kind.title()} links must cite source evidence.",
                )
            )


def _require_mapping(value: Mapping[str, Any], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TraceabilityReviewPacketError((TraceabilityReviewFinding("invalid_input_packet", "$", f"{label} must be an object."),))
    return value


def _extract_strings_by_key(items: Iterable[Any], keys: set[str]) -> list[str]:
    values: list[str] = []
    for item in items:
        if isinstance(item, Mapping):
            for key, child in item.items():
                if str(key) in keys:
                    values.extend(_strings(child))
                values.extend(_extract_strings_by_key((child,), keys))
        elif isinstance(item, list):
            values.extend(_extract_strings_by_key(item, keys))
    return values


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _citation_strings(value: Mapping[str, Any]) -> list[str]:
    values: list[str] = []
    for key in _CITATION_KEYS:
        values.extend(_strings(value.get(key)))
    return _ordered_unique(values)


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Mapping):
        for key in ("id", "ref", "source_id", "evidence_id", "citation_id", "predicate_id", "guardrail_id", "process_id"):
            text = _text(value.get(key))
            if text:
                return [text]
        return []
    if isinstance(value, list):
        strings: list[str] = []
        for item in value:
            strings.extend(_strings(item))
        return strings
    return []


def _ordered_unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            ordered.append(normalized)
    return ordered


def _has_payload(value: Any) -> bool:
    if value in (None, False, "", [], {}):
        return False
    return True


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _packet_id(packet: Mapping[str, Any]) -> str:
    return _text(packet.get("packet_id") or packet.get("candidate_id")) or "fixture-packet-" + _stable_hash(packet)


def _stable_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _slug(value: str) -> str:
    lowered = value.strip().lower()
    result = []
    previous_dash = False
    for character in lowered:
        if character.isalnum():
            result.append(character)
            previous_dash = False
        elif not previous_dash:
            result.append("-")
            previous_dash = True
    return "".join(result).strip("-") or "unknown"


__all__ = [
    "PACKET_MODE",
    "PACKET_TYPE",
    "TraceabilityReviewFinding",
    "TraceabilityReviewPacketError",
    "TraceabilityReviewValidationResult",
    "assert_valid_requirement_guardrail_traceability_review_packet",
    "build_requirement_guardrail_traceability_review_packet",
    "validate_requirement_guardrail_traceability_review_packet",
]
