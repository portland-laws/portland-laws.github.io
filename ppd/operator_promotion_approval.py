"""Fixture-first operator promotion approval packet builder.

This module intentionally consumes committed fixture packets and returns a derived
approval packet. It does not write to active PP&D registries, manifests,
requirements, process models, guardrails, release notes, schedules, or agent
state.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse


REQUIRED_INPUT_FILES = {
    "offline_release_decision_packet": "offline_release_decision_packet.json",
    "dry_run_promotion_sequence_packet": "dry_run_promotion_sequence_packet.json",
    "release_notes_candidate": "release_notes_candidate.json",
    "post_release_monitoring_plan": "post_release_monitoring_plan.json",
}

PROHIBITED_MUTATION_TARGETS = (
    "active_ppd_registries",
    "active_manifests",
    "active_requirements",
    "active_process_models",
    "active_guardrails",
    "active_release_notes",
    "active_schedules",
    "agent_state",
)

REVIEWER_ROLES = (
    "release_supervisor",
    "operations_reviewer",
    "guardrail_reviewer",
    "monitoring_reviewer",
)

_BLOCKER_FIELDS = (
    "explicit_no_go_carryovers",
    "no_go_carryovers",
    "no_go_conditions",
    "promotion_blockers",
    "monitoring_no_go_thresholds",
    "unresolved_blockers",
    "unresolved_blocker_summaries",
    "release_blockers",
)

_PRIVATE_OR_RUNTIME_RE = re.compile(
    r"(^file://)|(^/home/[^/]+/)|(^/Users/[^/]+/)|(^/root/)|(^/tmp/)|(^/var/folders/)|"
    r"(auth[_-]?state|browser[_-]?state|cookie|credential|download[_-]?(path|url|ref)?|har|password|"
    r"private[_-]?path|raw[_-]?(archive|body|crawl|download|html)|session[_-]?state|screenshot|secret|"
    r"storage[_-]?state|token|trace\.zip|warc|\.warc(\.gz)?)",
    re.IGNORECASE,
)

_RAW_REFERENCE_RE = re.compile(
    r"\b(raw body|raw crawl|raw download|raw archive|downloaded document|crawl output|archive output|warc|har|trace zip)\b",
    re.IGNORECASE,
)

_LIVE_OR_PUBLICATION_CLAIM_RE = re.compile(
    r"\b(live promotion|promoted to active|active promotion complete|publication complete|published release notes|"
    r"release notes published|active artifact changed|active artifacts changed|live devhub executed|"
    r"live crawler executed|live processor executed|submitted to devhub|uploaded to devhub|paid fees|"
    r"scheduled inspection|certified application)\b",
    re.IGNORECASE,
)

_LEGAL_OR_PERMITTING_GUARANTEE_RE = re.compile(
    r"\b(guarantee[sd]?|ensures?|will ensure|will be approved|permit approval is assured|approval is guaranteed|"
    r"legally compliant|legal advice|binding legal determination|no legal risk|no permitting risk|"
    r"will satisfy code|will pass inspection)\b",
    re.IGNORECASE,
)

_PRIVATE_URL_HOST_MARKERS = ("localhost", "127.0.0.1", "0.0.0.0")
_AUTH_URL_MARKERS = (
    "/login",
    "/signin",
    "/sign-in",
    "/oauth",
    "/saml",
    "/session",
    "access_token=",
    "auth=",
    "token=",
)

_MUTATION_FLAG_KEYS = {
    "active_artifact_mutation",
    "active_artifact_mutation_enabled",
    "active_artifact_mutation_flag",
    "active_mutation",
    "changes_active_artifacts",
    "mutates_active_artifacts",
    "mutates_active_targets",
    "promotes_release",
    "publishes_release_notes",
    "writes_active_state",
}

_CONSEQUENTIAL_CONTROL_KEYS = {
    "consequential_controls_enabled",
    "consequential_control_enabled",
    "enabled_consequential_controls",
    "submission_enabled",
    "upload_enabled",
    "payment_enabled",
    "scheduling_enabled",
    "certification_enabled",
    "cancellation_enabled",
    "mutation_enabled",
}

_ACTIVE_MUTATION_POLICY_KEYS = {
    "active_registry_mutations",
    "active_manifest_mutations",
    "active_requirement_mutations",
    "active_process_model_mutations",
    "active_guardrail_mutations",
    "active_release_note_mutations",
    "active_schedule_mutations",
    "agent_state_mutations",
}


@dataclass(frozen=True)
class ApprovalPacketResult:
    """Derived approval packet plus validation metadata."""

    packet: dict[str, Any]
    validation_errors: tuple[str, ...]

    @property
    def is_valid(self) -> bool:
        return not self.validation_errors


def load_fixture_inputs(fixture_dir: Path) -> dict[str, dict[str, Any]]:
    """Load the required packet fixtures from a PP&D test fixture directory."""

    inputs: dict[str, dict[str, Any]] = {}
    for input_name, file_name in REQUIRED_INPUT_FILES.items():
        fixture_path = fixture_dir / file_name
        with fixture_path.open("r", encoding="utf-8") as fixture_file:
            loaded = json.load(fixture_file)
        if not isinstance(loaded, dict):
            raise ValueError(f"{fixture_path} must contain a JSON object")
        inputs[input_name] = loaded
    return inputs


def build_operator_promotion_approval_packet(
    inputs: dict[str, dict[str, Any]],
) -> ApprovalPacketResult:
    """Build a cited human approval packet from offline release fixtures."""

    input_errors = list(_validate_inputs(inputs))
    citations = _collect_citations(inputs)
    packet = {
        "packet_type": "operator_promotion_approval_packet",
        "packet_id": _stable_packet_id(inputs),
        "fixture_first": True,
        "source_packets": [
            {
                "input_name": input_name,
                "packet_id": str(inputs[input_name].get("packet_id", "")) if input_name in inputs else "",
                "citations": _source_citations(inputs[input_name]) if input_name in inputs else [],
            }
            for input_name in REQUIRED_INPUT_FILES
        ],
        "approval_checklist": _approval_checklist(inputs, citations) if not input_errors else [],
        "explicit_no_go_carryovers": _no_go_carryovers(inputs),
        "rollback_rehearsal_references": _rollback_rehearsal_references(inputs),
        "reviewer_signoff_slots": [
            {
                "role": role,
                "reviewer_name": "",
                "signed_at": "",
                "decision": "pending",
                "notes": "",
            }
            for role in REVIEWER_ROLES
        ],
        "no_active_promotion_attestations": _no_active_promotion_attestations(inputs),
        "mutation_policy": {
            "allowed": "derive approval packet from committed fixtures only",
            "prohibited_targets": list(PROHIBITED_MUTATION_TARGETS),
            "active_registry_mutations": [],
            "active_manifest_mutations": [],
            "active_requirement_mutations": [],
            "active_process_model_mutations": [],
            "active_guardrail_mutations": [],
            "active_release_note_mutations": [],
            "active_schedule_mutations": [],
            "agent_state_mutations": [],
        },
        "validation": {"status": "pending", "errors": []},
    }
    validation_errors = tuple(_dedupe(input_errors + _validate_approval_packet(packet, inputs)))
    packet["validation"] = {
        "status": "valid" if not validation_errors else "invalid",
        "errors": list(validation_errors),
    }
    return ApprovalPacketResult(packet=packet, validation_errors=validation_errors)


def _validate_inputs(inputs: dict[str, dict[str, Any]]) -> tuple[str, ...]:
    errors: list[str] = []
    for input_name in REQUIRED_INPUT_FILES:
        if input_name not in inputs:
            errors.append(f"missing required input: {input_name}")
            continue
        if not isinstance(inputs[input_name], dict):
            errors.append(f"input must be an object: {input_name}")

    for input_name, packet in inputs.items():
        mutation_targets = packet.get("mutates_active_targets", [])
        if mutation_targets:
            errors.append(f"{input_name} declares active target mutations: {mutation_targets}")
        promotion_state = packet.get("active_promotion_state", "inactive")
        if promotion_state != "inactive":
            errors.append(f"{input_name} active_promotion_state must be inactive, got {promotion_state}")

    return tuple(errors)


def _validate_approval_packet(packet: Mapping[str, Any], inputs: Mapping[str, Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    if packet.get("packet_type") != "operator_promotion_approval_packet":
        errors.append("packet_type must be operator_promotion_approval_packet")
    if packet.get("fixture_first") is not True:
        errors.append("fixture_first must be true")

    source_packets = _mapping_sequence(packet.get("source_packets"))
    if len(source_packets) != len(REQUIRED_INPUT_FILES):
        errors.append("source_packets must include every required input packet")
    for index, source_packet in enumerate(source_packets):
        if not _string_list(source_packet.get("citations")):
            errors.append(f"source_packets[{index}] lacks citations")

    checklist = _mapping_sequence(packet.get("approval_checklist"))
    if not checklist:
        errors.append("approval_checklist must be a non-empty list")
    for index, item in enumerate(checklist):
        if not _string_list(item.get("citations")):
            errors.append(f"approval_checklist[{index}] contains an uncited approval claim")
        if item.get("status") != "pending_human_review":
            errors.append(f"approval_checklist[{index}].status must be pending_human_review")
        if str(item.get("reviewer_role", "")) not in REVIEWER_ROLES:
            errors.append(f"approval_checklist[{index}] has unknown reviewer_role")

    if _inputs_contain_unresolved_blockers(inputs):
        carryovers = _mapping_sequence(packet.get("explicit_no_go_carryovers"))
        if not carryovers:
            errors.append("explicit_no_go_carryovers must carry unresolved blockers forward")
        for index, item in enumerate(carryovers):
            if item.get("status") != "open_no_go_until_human_clears":
                errors.append(f"explicit_no_go_carryovers[{index}] must remain open")
            if not _string_list(item.get("citations")):
                errors.append(f"explicit_no_go_carryovers[{index}] lacks citations")

    rollback_refs = _mapping_sequence(packet.get("rollback_rehearsal_references"))
    if not rollback_refs:
        errors.append("rollback_rehearsal_references must be a non-empty list")
    for index, reference in enumerate(rollback_refs):
        if reference.get("must_review_before_promotion") is not True:
            errors.append(f"rollback_rehearsal_references[{index}] must require review before promotion")
        if not _string_list(reference.get("citations")):
            errors.append(f"rollback_rehearsal_references[{index}] lacks citations")

    signoff_slots = _mapping_sequence(packet.get("reviewer_signoff_slots"))
    roles = [str(slot.get("role", "")) for slot in signoff_slots]
    if roles != list(REVIEWER_ROLES):
        errors.append("reviewer_signoff_slots must include every required reviewer role in order")
    for index, slot in enumerate(signoff_slots):
        if slot.get("decision") != "pending":
            errors.append(f"reviewer_signoff_slots[{index}].decision must be pending")
        if slot.get("reviewer_name") not in ("", None) or slot.get("signed_at") not in ("", None):
            errors.append(f"reviewer_signoff_slots[{index}] must remain unsigned")

    mutation_policy = packet.get("mutation_policy") if isinstance(packet.get("mutation_policy"), Mapping) else {}
    if set(mutation_policy.get("prohibited_targets", [])) != set(PROHIBITED_MUTATION_TARGETS):
        errors.append("mutation_policy.prohibited_targets must list all prohibited active PP&D targets")
    for key in sorted(_ACTIVE_MUTATION_POLICY_KEYS):
        if _as_list(mutation_policy.get(key)):
            errors.append(f"mutation_policy.{key} must be empty")

    errors.extend(_recursive_safety_problems(packet))
    return errors


def _approval_checklist(
    inputs: dict[str, dict[str, Any]], citations: list[dict[str, str]]
) -> list[dict[str, Any]]:
    decision = inputs["offline_release_decision_packet"]
    sequence = inputs["dry_run_promotion_sequence_packet"]
    notes = inputs["release_notes_candidate"]
    monitoring = inputs["post_release_monitoring_plan"]
    shared_citations = [citation["citation_id"] for citation in citations]

    return [
        {
            "item_id": "approve-offline-release-decision",
            "reviewer_role": "release_supervisor",
            "prompt": "Confirm the offline release decision packet remains approved for operator promotion review.",
            "required_evidence": decision.get("decision_summary", "offline release decision reviewed"),
            "citations": _citation_ids(decision, shared_citations),
            "status": "pending_human_review",
        },
        {
            "item_id": "approve-dry-run-promotion-sequence",
            "reviewer_role": "operations_reviewer",
            "prompt": "Confirm the dry-run promotion sequence completed without mutating active PP&D state.",
            "required_evidence": sequence.get("sequence_summary", "dry-run promotion sequence reviewed"),
            "citations": _citation_ids(sequence, shared_citations),
            "status": "pending_human_review",
        },
        {
            "item_id": "approve-release-notes-candidate",
            "reviewer_role": "release_supervisor",
            "prompt": "Confirm the release notes candidate is suitable for review but is not published as active release notes.",
            "required_evidence": notes.get("candidate_summary", "release notes candidate reviewed"),
            "citations": _citation_ids(notes, shared_citations),
            "status": "pending_human_review",
        },
        {
            "item_id": "approve-post-release-monitoring-plan",
            "reviewer_role": "monitoring_reviewer",
            "prompt": "Confirm the post-release monitoring plan has owners, checks, thresholds, and escalation paths.",
            "required_evidence": monitoring.get("monitoring_summary", "post-release monitoring plan reviewed"),
            "citations": _citation_ids(monitoring, shared_citations),
            "status": "pending_human_review",
        },
        {
            "item_id": "attest-no-active-promotion",
            "reviewer_role": "guardrail_reviewer",
            "prompt": "Attest that this packet authorizes no active promotion and performs no registry, manifest, requirement, process model, guardrail, release note, schedule, or agent-state mutation.",
            "required_evidence": "all consumed packets declare active_promotion_state=inactive and no active target mutations",
            "citations": shared_citations,
            "status": "pending_human_review",
        },
    ]


def _no_go_carryovers(inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    carryovers: list[dict[str, Any]] = []
    fields = ("no_go_carryovers", "no_go_conditions", "promotion_blockers", "monitoring_no_go_thresholds", "unresolved_blockers", "unresolved_blocker_summaries", "release_blockers")
    for input_name, packet in inputs.items():
        for field in fields:
            for index, item in enumerate(_as_list(packet.get(field))):
                if isinstance(item, dict):
                    description = str(item.get("description", item.get("summary", item)))
                    citations = _citation_ids(item, _citation_ids(packet, []))
                else:
                    description = str(item)
                    citations = _citation_ids(packet, [])
                carryovers.append(
                    {
                        "carryover_id": f"{input_name}:{field}:{index + 1}",
                        "source_input": input_name,
                        "source_field": field,
                        "description": description,
                        "citations": citations,
                        "status": "open_no_go_until_human_clears",
                    }
                )
    return carryovers


def _rollback_rehearsal_references(inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    for input_name, packet in inputs.items():
        for field in ("rollback_rehearsal", "rollback_rehearsal_references", "rollback_refs"):
            for index, item in enumerate(_as_list(packet.get(field))):
                if isinstance(item, dict):
                    summary = str(item.get("summary", item.get("description", item)))
                    reference_id = str(item.get("reference_id", f"{input_name}:{field}:{index + 1}"))
                    citations = _citation_ids(item, _citation_ids(packet, []))
                else:
                    summary = str(item)
                    reference_id = f"{input_name}:{field}:{index + 1}"
                    citations = _citation_ids(packet, [])
                references.append(
                    {
                        "reference_id": reference_id,
                        "source_input": input_name,
                        "summary": summary,
                        "citations": citations,
                        "must_review_before_promotion": True,
                    }
                )
    return references


def _no_active_promotion_attestations(inputs: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    attestations: list[dict[str, Any]] = []
    for input_name, packet in inputs.items():
        attestations.append(
            {
                "input_name": input_name,
                "packet_id": str(packet.get("packet_id", "")),
                "active_promotion_state": str(packet.get("active_promotion_state", "inactive")),
                "mutates_active_targets": list(_as_list(packet.get("mutates_active_targets"))),
                "attestation": "input consumed for offline approval packet derivation only",
                "citations": _citation_ids(packet, []),
            }
        )
    return attestations


def _collect_citations(inputs: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    citations: list[dict[str, str]] = []
    seen: set[str] = set()
    for input_name, packet in inputs.items():
        for citation_id in _source_citations(packet):
            if citation_id in seen:
                continue
            seen.add(citation_id)
            citations.append({"citation_id": citation_id, "source_input": input_name})
    return citations


def _source_citations(packet: dict[str, Any]) -> list[str]:
    return _citation_ids(packet, [])


def _citation_ids(value: Any, fallback: list[str]) -> list[str]:
    citation_values: list[str] = []
    if isinstance(value, dict):
        for key in ("citations", "citation_ids", "source_evidence_ids"):
            citation_values.extend(str(item) for item in _as_list(value.get(key)))
    citation_values = [item for item in citation_values if item]
    return citation_values or list(fallback)


def _inputs_contain_unresolved_blockers(inputs: Mapping[str, Mapping[str, Any]]) -> bool:
    for packet in inputs.values():
        for field in _BLOCKER_FIELDS:
            if _as_list(packet.get(field)):
                return True
    return False


def _recursive_safety_problems(value: Any) -> list[str]:
    problems: list[str] = []
    for path, child in _walk(value):
        key = _path_leaf(path)
        if isinstance(child, str):
            if _PRIVATE_OR_RUNTIME_RE.search(child):
                problems.append(f"private or runtime artifact reference is not allowed at {path}")
            if _RAW_REFERENCE_RE.search(child):
                problems.append(f"raw body/download/archive reference is not allowed at {path}")
            if _LIVE_OR_PUBLICATION_CLAIM_RE.search(child):
                problems.append(f"live promotion or publication claim is not allowed at {path}")
            if _LEGAL_OR_PERMITTING_GUARANTEE_RE.search(child):
                problems.append(f"legal or permitting outcome guarantee is not allowed at {path}")
            if _is_private_or_authenticated_url(child):
                problems.append(f"private or authenticated URL is not allowed at {path}")
        elif isinstance(child, bool):
            if child is True and key in _MUTATION_FLAG_KEYS:
                problems.append(f"active artifact mutation flag must not be true at {path}")
            if child is True and key in _CONSEQUENTIAL_CONTROL_KEYS:
                problems.append(f"enabled consequential control is not allowed at {path}")
        elif isinstance(child, Sequence) and not isinstance(child, (str, bytes, bytearray)):
            if key in _CONSEQUENTIAL_CONTROL_KEYS and len(child) > 0:
                problems.append(f"enabled consequential control is not allowed at {path}")
            if key in _MUTATION_FLAG_KEYS and len(child) > 0:
                problems.append(f"active artifact mutation flag must be empty at {path}")
    return problems


def _is_private_or_authenticated_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = (parsed.hostname or "").lower()
    lowered = value.lower()
    if host in _PRIVATE_URL_HOST_MARKERS or host.endswith(".local") or host.startswith("10.") or host.startswith("192.168."):
        return True
    return any(marker in lowered for marker in _AUTH_URL_MARKERS)


def _path_leaf(path: str) -> str:
    parts = [part for part in path.rstrip(".").split(".") if part and not part.isdigit()]
    return parts[-1] if parts else ""


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


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _stable_packet_id(inputs: dict[str, dict[str, Any]]) -> str:
    encoded = json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(encoded).hexdigest()[:16]
    return f"operator-promotion-approval-{digest}"
